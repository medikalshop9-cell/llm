"""
quantization/merge_and_export.py
AfriLearn — Merge LoRA adapters into base model and export for quantization.

Reads the trained adapter directory, merges weights back into Gemma 12B base,
and saves the merged fp16 model ready for llama.cpp GGUF conversion.

Usage:
  python quantization/merge_and_export.py \
    --adapters outputs/afrilearn-gemma-12b-qlora/final_adapters \
    --output outputs/afrilearn-gemma-12b-merged
"""

import argparse
from pathlib import Path
import sys

from loguru import logger

try:
    from unsloth import FastLanguageModel
except ImportError:
    logger.error("Unsloth not installed. Run: bash scripts/setup.sh")
    sys.exit(1)


def merge_and_export(adapters_dir: str, output_dir: str):
    adapters_path = Path(adapters_dir)
    output_path   = Path(output_dir)

    if not adapters_path.exists():
        logger.error(
            f"Adapter directory not found: {adapters_path}\n"
            "Run training first: python training/train.py --config training/config.yaml"
        )
        sys.exit(1)

    logger.info(f"Loading model + adapters from {adapters_path}...")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=str(adapters_path),
        max_seq_length=2048,
        dtype=None,
        load_in_4bit=True,
    )

    logger.info("Merging LoRA adapters into base weights (fp16)...")
    logger.info("This uses ~24GB RAM. If you run out of memory, reduce to bf16 or use a larger machine.")

    output_path.mkdir(parents=True, exist_ok=True)

    model.save_pretrained_merged(
        str(output_path),
        tokenizer,
        save_method="merged_16bit",
    )

    logger.success(f"Merged model saved to {output_path}")
    logger.info(
        f"\nNext step — run GGUF quantization:\n"
        f"  bash quantization/quantize.sh {output_path} outputs/afrilearn-gemma-12b-Q4_K_M.gguf"
    )


def main():
    parser = argparse.ArgumentParser(description="AfriLearn LoRA adapter merger")
    parser.add_argument("--adapters", default="outputs/afrilearn-gemma-12b-qlora/final_adapters", type=str)
    parser.add_argument("--output",   default="outputs/afrilearn-gemma-12b-merged",               type=str)
    args = parser.parse_args()

    merge_and_export(args.adapters, args.output)


if __name__ == "__main__":
    main()
