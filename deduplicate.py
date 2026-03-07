"""
dataset/deduplicate.py
AfriLearn — MinHash-based dataset deduplication.

Two rows are considered duplicates if their instruction + output text has a
Jaccard similarity >= SIMILARITY_THRESHOLD (default 0.85).

Keeps the first occurrence. Writes a deduplicated .jsonl file and a
deduplication report showing how many rows were removed per subject/grade.

Usage:
  python dataset/deduplicate.py \
    --input data/processed/nigeria_clean.jsonl \
    --output data/processed/nigeria_final.jsonl \
    --threshold 0.85
"""

import json
import re
import argparse
from pathlib import Path
from collections import defaultdict

from datasketch import MinHash, MinHashLSH
from tqdm import tqdm
from loguru import logger


DEFAULT_THRESHOLD = 0.85
NUM_PERM = 128  # Number of permutations — higher = more accurate, slower


def text_to_shingles(text: str, k: int = 3) -> set[str]:
    """Convert text to character k-shingles for MinHash."""
    text = re.sub(r"\s+", " ", text.lower().strip())
    return {text[i:i+k] for i in range(len(text) - k + 1)}


def build_minhash(text: str) -> MinHash:
    m = MinHash(num_perm=NUM_PERM)
    for shingle in text_to_shingles(text):
        m.update(shingle.encode("utf8"))
    return m


def extract_subject_grade(row: dict) -> str:
    """Pull subject + grade from instruction for the dedup report."""
    instruction = row.get("instruction", "")
    subject_match = re.search(r"SUBJECT:\s*([^|]+)", instruction)
    grade_match   = re.search(r"GRADE:\s*([^|]+)", instruction)
    subject = subject_match.group(1).strip() if subject_match else "Unknown"
    grade   = grade_match.group(1).strip()   if grade_match   else "Unknown"
    return f"{subject} | {grade}"


def deduplicate(
    input_path: Path,
    output_path: Path,
    threshold: float = DEFAULT_THRESHOLD,
) -> dict:
    logger.info(f"Loading {input_path}...")

    rows = []
    with open(input_path) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    logger.info(f"Loaded {len(rows)} rows. Building MinHash index with threshold={threshold}...")

    lsh = MinHashLSH(threshold=threshold, num_perm=NUM_PERM)
    kept = []
    duplicate_count = defaultdict(int)

    for i, row in enumerate(tqdm(rows, desc="Deduplicating")):
        # Fingerprint is instruction + first 300 chars of output
        fingerprint_text = row["instruction"] + " " + row["output"][:300]
        minhash = build_minhash(fingerprint_text)

        key = f"row_{i}"
        result = lsh.query(minhash)

        if len(result) == 0:
            # No near-duplicate found — keep this row
            lsh.insert(key, minhash)
            kept.append(row)
        else:
            # Near-duplicate of an existing row — discard
            subject_grade = extract_subject_grade(row)
            duplicate_count[subject_grade] += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        for row in kept:
            f.write(json.dumps(row) + "\n")

    removed = len(rows) - len(kept)
    report = {
        "input_rows":   len(rows),
        "output_rows":  len(kept),
        "removed":      removed,
        "removal_pct":  round(removed / len(rows) * 100, 2) if rows else 0,
        "duplicates_by_subject_grade": dict(duplicate_count),
    }

    report_path = output_path.parent / f"{output_path.stem}_dedup_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Deduplication report written to {report_path}")
    logger.success(
        f"Done: {len(rows)} → {len(kept)} rows "
        f"({removed} duplicates removed, {report['removal_pct']}%)"
    )

    return report


def main():
    parser = argparse.ArgumentParser(description="AfriLearn dataset deduplication")
    parser.add_argument("--input",     required=True, type=Path)
    parser.add_argument("--output",    required=True, type=Path)
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                        help="Jaccard similarity threshold (0.0-1.0). Default: 0.85")
    args = parser.parse_args()

    deduplicate(args.input, args.output, args.threshold)


if __name__ == "__main__":
    main()
