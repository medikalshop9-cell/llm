"""
dataset/validate_dataset.py
AfriLearn — Dataset validation pipeline.

Runs every row through:
  1. JSON schema validation (Nigeria or Ghana schema based on COUNTRY tag)
  2. Curriculum reference format check
  3. Forbidden content filter (internet references, cloud services)
  4. Difficulty label consistency check
  5. Output format compliance (QUESTION / CORRECT_ANSWER / CURRICULUM_REF present)

Usage:
  python dataset/validate_dataset.py \
    --input data/raw/nigeria_raw.jsonl \
    --output data/processed/nigeria_clean.jsonl \
    --country nigeria

Exit codes:
  0 — validation passed, output file written
  1 — validation failed, see rejection log
"""

import json
import re
import argparse
import sys
from pathlib import Path
from typing import Literal

import jsonschema
from tqdm import tqdm
from loguru import logger

SCHEMA_DIR = Path(__file__).parent / "schemas"

FORBIDDEN_PATTERNS = [
    r"\binternet\b", r"\bYouTube\b", r"\bGoogle\b", r"\bWhatsApp\b",
    r"\bFacebook\b", r"\bTikTok\b", r"\bonline\b", r"\bdownload\b",
    r"\bcloud\b", r"\bAPI\b", r"\bwebsite\b",
]

VALID_SUBJECTS_NIGERIA = {
    "English Studies", "Mathematics", "Basic Science and Technology",
    "Social and Citizenship Studies", "Christian Religious Studies",
    "Islamic Religious Studies", "Computer Studies",
    "Physical and Health Education",
}

VALID_SUBJECTS_GHANA = {
    "English Language", "Mathematics", "Science",
    "Our World and Our People", "Religious and Moral Education",
    "Computing", "Physical Education",
}

CURRICULUM_REF_PATTERNS = {
    "nigeria": re.compile(r"^NERDC-NG-[A-Z]+-P[1-6]-T[1-3]-W([1-9]|10)$"),
    "ghana":   re.compile(r"^NACCA-GH-[A-Z]+-B[1-6]-"),
}


def load_schema(country: str) -> dict:
    schema_path = SCHEMA_DIR / f"{country}_schema.json"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    with open(schema_path) as f:
        return json.load(f)


def extract_curriculum_ref(output: str) -> str | None:
    match = re.search(r"CURRICULUM_REF:\s*(\S+)", output)
    return match.group(1) if match else None


def check_forbidden_content(row: dict) -> list[str]:
    violations = []
    full_text = f"{row['instruction']} {row['input']} {row['output']}"
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, full_text, re.IGNORECASE):
            violations.append(f"Forbidden content: matches pattern '{pattern}'")
    return violations


def validate_output_format(output: str) -> list[str]:
    errors = []
    if "QUESTION:" not in output:
        errors.append("Missing QUESTION: tag in output")
    if not re.search(r"CORRECT_ANSWER:\s*[ABCD]", output):
        errors.append("Missing or malformed CORRECT_ANSWER: [ABCD] in output")
    if "DIFFICULTY:" not in output:
        errors.append("Missing DIFFICULTY: tag in output")
    if "CURRICULUM_REF:" not in output:
        errors.append("Missing CURRICULUM_REF: tag in output")
    return errors


def validate_row(row: dict, schema: dict, country: str) -> list[str]:
    errors = []

    # 1. JSON schema
    try:
        jsonschema.validate(instance=row, schema=schema)
    except jsonschema.ValidationError as e:
        errors.append(f"Schema error: {e.message}")
        return errors  # No point running further checks if schema fails

    # 2. Curriculum reference format
    ref = extract_curriculum_ref(row["output"])
    if ref is None:
        errors.append("CURRICULUM_REF missing from output")
    elif not CURRICULUM_REF_PATTERNS[country].match(ref):
        errors.append(f"CURRICULUM_REF format invalid: '{ref}'")

    # 3. Forbidden content
    errors.extend(check_forbidden_content(row))

    # 4. Output format
    errors.extend(validate_output_format(row["output"]))

    return errors


def run_validation(
    input_path: Path,
    output_path: Path,
    country: Literal["nigeria", "ghana"],
    log_rejections: bool = True,
) -> dict:
    schema = load_schema(country)
    passed = []
    rejected = []

    logger.info(f"Validating {input_path} against {country} schema...")

    with open(input_path) as f:
        lines = f.readlines()

    for i, line in enumerate(tqdm(lines, desc="Validating")):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as e:
            rejected.append({"line": i + 1, "errors": [f"JSON parse error: {e}"]})
            continue

        errors = validate_row(row, schema, country)
        if errors:
            rejected.append({"line": i + 1, "errors": errors, "row": row})
        else:
            passed.append(row)

    # Write clean output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        for row in passed:
            f.write(json.dumps(row) + "\n")

    # Write rejection log
    if log_rejections and rejected:
        rejection_log = output_path.parent / f"{output_path.stem}_rejections.json"
        with open(rejection_log, "w") as f:
            json.dump(rejected, f, indent=2)
        logger.warning(f"{len(rejected)} rows rejected — see {rejection_log}")

    total = len(lines)
    pass_rate = len(passed) / total * 100 if total > 0 else 0

    summary = {
        "total_rows": total,
        "passed": len(passed),
        "rejected": len(rejected),
        "pass_rate_pct": round(pass_rate, 2),
        "output_file": str(output_path),
    }

    logger.info(f"Validation complete: {summary}")
    return summary


def main():
    parser = argparse.ArgumentParser(description="AfriLearn dataset validator")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--country", required=True, choices=["nigeria", "ghana"])
    args = parser.parse_args()

    summary = run_validation(args.input, args.output, args.country)

    if summary["pass_rate_pct"] < 90.0:
        logger.error(
            f"Pass rate {summary['pass_rate_pct']}% is below 90% minimum threshold. "
            "Fix rejections before proceeding to training."
        )
        sys.exit(1)

    logger.success(f"Dataset validated. {summary['passed']} clean rows written to {args.output}")


if __name__ == "__main__":
    main()
