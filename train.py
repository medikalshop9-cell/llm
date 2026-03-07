"""
training/train.py
AfriLearn — QLoRA fine-tuning via Unsloth + TRL SFTTrainer.

Reads all configuration from training/config.yaml.
Loads base Gemma 12B, applies QLoRA adapters, trains on AfriLearn dataset,
saves LoRA adapter weights to outputs/.

Usage:
  python training/train.py --config training/config.yaml

Requirements:
  - GPU with >=24GB VRAM (RTX 4090 minimum, A100 recommended)
  - Unsloth installed (see scripts/setup.sh)
  - HuggingFace account with Gemma access accepted at https://ai.google.dev/gemma/terms
  - HF_TOKEN env variable set: export HF_TOKEN=hf_your_token_here
"""

import os
import sys
import argparse
from pathlib import Path

import yaml
from loguru import logger
from datasets import load_dataset, concatenate_datasets

# Guard: Unsloth must be imported before transformers in the same process
try:
    from unsloth import FastLanguageModel
except ImportError:
    logger.error(
        "Unsloth is not installed. Run: bash scripts/setup.sh\n"
        "Or manually: pip install 'unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git'"
    )
    sys.exit(1)

from trl import SFTTrainer
from transformers import TrainingArguments
from training.alpaca_prompt import batch_format


def load_config(config_path: str) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_and_prepare_dataset(cfg: dict, tokenizer):
    """Load train/eval splits and apply Alpaca prompt formatting."""
    train_path = cfg["data"]["train_file"]
    eval_path  = cfg["data"].get("eval_file")

    if not Path(train_path).exists():
        logger.error(
            f"Training file not found: {train_path}\n"
            "Run the dataset pipeline first:\n"
            "  python dataset/validate_dataset.py ...\n"
            "  python dataset/deduplicate.py ..."
        )
        sys.exit(1)

    dataset = load_dataset("json", data_files={"train": train_path}, split="train")

    if eval_path and Path(eval_path).exists():
        eval_dataset = load_dataset("json", data_files={"train": eval_path}, split="train")
    else:
        split_ratio = cfg["data"].get("eval_split_ratio", 0.1)
        logger.warning(
            f"No eval file found at {eval_path}. "
            f"Splitting {split_ratio*100:.0f}% from training data."
        )
        splits = dataset.train_test_split(test_size=split_ratio, seed=42)
        dataset      = splits["train"]
        eval_dataset = splits["test"]

    # Apply Alpaca prompt formatting
    num_proc = cfg["data"].get("dataset_num_proc", 2)
    dataset      = dataset.map(lambda ex: batch_format(ex, tokenizer), batched=True, num_proc=num_proc)
    eval_dataset = eval_dataset.map(lambda ex: batch_format(ex, tokenizer), batched=True, num_proc=num_proc)

    logger.info(f"Train: {len(dataset)} rows | Eval: {len(eval_dataset)} rows")
    return dataset, eval_dataset


def main():
    parser = argparse.ArgumentParser(description="AfriLearn QLoRA fine-tuning")
    parser.add_argument("--config", default="training/config.yaml", type=str)
    args = parser.parse_args()

    cfg = load_config(args.config)
    logger.info(f"Loaded config from {args.config}")

    # HuggingFace auth — required for gated Gemma model
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        logger.warning(
            "HF_TOKEN environment variable not set. "
            "You may get a 401 error if Gemma access hasn't been granted on this machine. "
            "Set it with: export HF_TOKEN=hf_your_token_here"
        )

    model_name = cfg["model"]["base_model"]
    logger.info(f"Loading base model: {model_name}")

    # Step 1: Load base model in 4-bit (QLoRA)
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=cfg["model"]["max_seq_length"],
        dtype=cfg["model"]["dtype"],
        load_in_4bit=cfg["model"]["load_in_4bit"],
        token=hf_token,
    )

    # Step 2: Apply QLoRA adapters
    lora_cfg = cfg["lora"]
    model = FastLanguageModel.get_peft_model(
        model,
        r=lora_cfg["r"],
        target_modules=lora_cfg["target_modules"],
        lora_alpha=lora_cfg["lora_alpha"],
        lora_dropout=lora_cfg["lora_dropout"],
        bias=lora_cfg["bias"],
        use_gradient_checkpointing=lora_cfg["use_gradient_checkpointing"],
        random_state=lora_cfg["random_state"],
        use_rslora=lora_cfg["use_rslora"],
    )

    logger.info(f"LoRA adapters applied — rank={lora_cfg['r']}, alpha={lora_cfg['lora_alpha']}")

    # Step 3: Load and format dataset
    train_dataset, eval_dataset = load_and_prepare_dataset(cfg, tokenizer)

    # Step 4: Training arguments
    t = cfg["training"]
    training_args = TrainingArguments(
        output_dir=t["output_dir"],
        num_train_epochs=t["num_train_epochs"],
        per_device_train_batch_size=t["per_device_train_batch_size"],
        gradient_accumulation_steps=t["gradient_accumulation_steps"],
        learning_rate=t["learning_rate"],
        warmup_ratio=t["warmup_ratio"],
        lr_scheduler_type=t["lr_scheduler_type"],
        fp16=t["fp16"],
        bf16=t["bf16"],
        logging_steps=t["logging_steps"],
        save_steps=t["save_steps"],
        save_total_limit=t["save_total_limit"],
        optim=t["optim"],
        report_to=t["report_to"],
        seed=t["seed"],
        dataloader_num_workers=t["dataloader_num_workers"],
        evaluation_strategy="steps",
        eval_steps=t["save_steps"],
        load_best_model_at_end=True,
    )

    # Step 5: Trainer
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        dataset_text_field=cfg["data"]["text_field"],
        max_seq_length=cfg["model"]["max_seq_length"],
        dataset_num_proc=cfg["data"]["dataset_num_proc"],
        args=training_args,
    )

    # Step 6: Train
    logger.info("Starting training...")
    trainer_stats = trainer.train()

    logger.info(f"Training complete. Stats: {trainer_stats}")

    # Step 7: Save adapter weights
    output_dir = Path(t["output_dir"])
    adapter_dir = output_dir / "final_adapters"
    model.save_pretrained(str(adapter_dir))
    tokenizer.save_pretrained(str(adapter_dir))
    logger.success(f"LoRA adapters saved to {adapter_dir}")
    logger.info("Next step: python quantization/merge_and_export.py")


if __name__ == "__main__":
    main()
