"""
evaluation/evaluate.py
AfriLearn — Automated model evaluation.

Three evaluation dimensions:
  1. Curriculum Accuracy   — correct answer match rate on held-out eval set
  2. Consistency           — same input → same correct answer across 5 runs
  3. Format Compliance     — output contains required structural tags

Generates a JSON report and prints a pass/fail summary.

Usage:
  python evaluation/evaluate.py \
    --model outputs/afrilearn-gemma-12b-qlora/final_adapters \
    --eval-set data/processed/eval_set.jsonl \
    --output evaluation/results/eval_report.json
"""

import json
import re
import argparse
from pathlib import Path
from collections import defaultdict

from tqdm import tqdm
from loguru import logger

try:
    from unsloth import FastLanguageModel
except ImportError:
    from transformers import AutoModelForCausalLM, AutoTokenizer

from training.alpaca_prompt import format_inference_prompt
from evaluation.format_validator import validate_output_format


ACCURACY_THRESHOLD_MATHS    = 0.92   # 92% on Mathematics
ACCURACY_THRESHOLD_ENGLISH  = 0.88   # 88% on English / comprehension
ACCURACY_THRESHOLD_DEFAULT  = 0.85   # 85% on all other subjects
CONSISTENCY_THRESHOLD       = 0.95   # 95% of questions must give same answer across 5 runs
FORMAT_THRESHOLD            = 0.97   # 97% format compliance
CONSISTENCY_RUNS            = 5


def load_eval_set(path: Path) -> list[dict]:
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def extract_correct_answer_from_ground_truth(output: str) -> str | None:
    match = re.search(r"CORRECT_ANSWER:\s*([ABCD])", output)
    return match.group(1) if match else None


def extract_correct_answer_from_model_output(output: str) -> str | None:
    match = re.search(r"CORRECT_ANSWER:\s*([ABCD])", output)
    return match.group(1) if match else None


def extract_subject(instruction: str) -> str:
    match = re.search(r"SUBJECT:\s*([^|]+)", instruction)
    return match.group(1).strip() if match else "Unknown"


def run_inference(model, tokenizer, prompt: str, temperature: float = 0.1, max_new_tokens: int = 512) -> str:
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with __import__("torch").no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=temperature > 0,
            pad_token_id=tokenizer.eos_token_id,
        )
    generated = outputs[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(generated, skip_special_tokens=True)


def evaluate(model_path: str, eval_set_path: Path, output_path: Path):
    logger.info(f"Loading model from {model_path}...")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_path,
        max_seq_length=2048,
        dtype=None,
        load_in_4bit=True,
    )
    FastLanguageModel.for_inference(model)

    eval_rows = load_eval_set(eval_set_path)
    logger.info(f"Evaluating {len(eval_rows)} examples...")

    accuracy_results   = defaultdict(lambda: {"correct": 0, "total": 0})
    consistency_flags  = []
    format_pass_count  = 0
    all_results        = []

    for row in tqdm(eval_rows, desc="Evaluating"):
        prompt         = format_inference_prompt(row["instruction"], row["input"])
        ground_truth   = extract_correct_answer_from_ground_truth(row["output"])
        subject        = extract_subject(row["instruction"])

        # --- Dimension 1: Accuracy ---
        model_output   = run_inference(model, tokenizer, prompt, temperature=0.1)
        predicted      = extract_correct_answer_from_model_output(model_output)
        is_correct     = (predicted == ground_truth)

        accuracy_results[subject]["total"]   += 1
        accuracy_results[subject]["correct"] += int(is_correct)

        # --- Dimension 2: Consistency (5 runs) ---
        predictions = [predicted]
        for _ in range(CONSISTENCY_RUNS - 1):
            out  = run_inference(model, tokenizer, prompt, temperature=0.1)
            pred = extract_correct_answer_from_model_output(out)
            predictions.append(pred)

        majority = max(set(predictions), key=predictions.count)
        consistent = all(p == majority for p in predictions)
        consistency_flags.append(consistent)

        # --- Dimension 3: Format compliance ---
        format_errors = validate_output_format(model_output)
        format_ok     = len(format_errors) == 0
        format_pass_count += int(format_ok)

        all_results.append({
            "instruction":    row["instruction"][:120],
            "ground_truth":   ground_truth,
            "predicted":      predicted,
            "correct":        is_correct,
            "consistent":     consistent,
            "format_ok":      format_ok,
            "format_errors":  format_errors,
        })

    # --- Compile report ---
    total = len(eval_rows)
    accuracy_by_subject = {
        subj: {
            "correct":    v["correct"],
            "total":      v["total"],
            "accuracy":   round(v["correct"] / v["total"], 4) if v["total"] else 0,
        }
        for subj, v in accuracy_results.items()
    }
    consistency_rate = sum(consistency_flags) / len(consistency_flags) if consistency_flags else 0
    format_rate      = format_pass_count / total if total else 0

    # Pass/fail per dimension
    all_pass = True
    for subj, res in accuracy_by_subject.items():
        threshold = (
            ACCURACY_THRESHOLD_MATHS   if "Math" in subj else
            ACCURACY_THRESHOLD_ENGLISH if "English" in subj else
            ACCURACY_THRESHOLD_DEFAULT
        )
        passed = res["accuracy"] >= threshold
        res["threshold"] = threshold
        res["passed"]    = passed
        if not passed:
            all_pass = False
            logger.warning(f"FAIL accuracy — {subj}: {res['accuracy']:.1%} < {threshold:.1%}")

    if consistency_rate < CONSISTENCY_THRESHOLD:
        all_pass = False
        logger.warning(f"FAIL consistency: {consistency_rate:.1%} < {CONSISTENCY_THRESHOLD:.1%}")

    if format_rate < FORMAT_THRESHOLD:
        all_pass = False
        logger.warning(f"FAIL format compliance: {format_rate:.1%} < {FORMAT_THRESHOLD:.1%}")

    report = {
        "eval_set":            str(eval_set_path),
        "total_examples":      total,
        "accuracy_by_subject": accuracy_by_subject,
        "consistency_rate":    round(consistency_rate, 4),
        "consistency_passed":  consistency_rate >= CONSISTENCY_THRESHOLD,
        "format_compliance":   round(format_rate, 4),
        "format_passed":       format_rate >= FORMAT_THRESHOLD,
        "overall_pass":        all_pass,
        "row_results":         all_results,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    status = "PASSED" if all_pass else "FAILED"
    logger.info(f"\n{'='*50}\nEVALUATION {status}\n{'='*50}")
    logger.info(f"Consistency: {consistency_rate:.1%} | Format: {format_rate:.1%}")
    logger.info(f"Full report: {output_path}")

    return report


def main():
    parser = argparse.ArgumentParser(description="AfriLearn model evaluator")
    parser.add_argument("--model",     required=True, type=str,  help="Path to trained model or adapter directory")
    parser.add_argument("--eval-set",  required=True, type=Path, help="Path to eval .jsonl file")
    parser.add_argument("--output",    default="evaluation/results/eval_report.json", type=Path)
    args = parser.parse_args()

    evaluate(args.model, args.eval_set, args.output)


if __name__ == "__main__":
    main()
