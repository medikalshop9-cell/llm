"""
evaluation/format_validator.py
AfriLearn — Output format compliance checker.

Checks that model-generated outputs contain all required structural tags.
Used by evaluate.py and can be imported into the API for runtime validation.
"""

import re
from typing import NamedTuple


class FormatCheckResult(NamedTuple):
    passed: bool
    errors: list[str]


REQUIRED_PATTERNS = [
    (r"QUESTION:",                           "Missing QUESTION: tag"),
    (r"[A-D]\)",                             "Missing answer options (A/B/C/D format)"),
    (r"CORRECT_ANSWER:\s*[ABCD]",            "Missing or malformed CORRECT_ANSWER: [ABCD]"),
    (r"DIFFICULTY:\s*(easy|medium|hard)",    "Missing or invalid DIFFICULTY: tag"),
    (r"CURRICULUM_REF:\s*(NERDC|NACCA)-",   "Missing or malformed CURRICULUM_REF:"),
]

# Patterns that must NOT appear in output (offline-safety check)
FORBIDDEN_PATTERNS = [
    (r"\binternet\b",   "Output references 'internet'"),
    (r"\bYouTube\b",    "Output references 'YouTube'"),
    (r"\bGoogle\b",     "Output references 'Google'"),
    (r"\bWhatsApp\b",   "Output references 'WhatsApp'"),
    (r"https?://",      "Output contains a URL"),
]


def validate_output_format(output: str) -> list[str]:
    """
    Validate a model output string for required structure.

    Args:
        output: Raw model output text.

    Returns:
        List of error strings. Empty list = output passed all checks.
    """
    errors = []

    for pattern, error_msg in REQUIRED_PATTERNS:
        if not re.search(pattern, output, re.IGNORECASE):
            errors.append(error_msg)

    for pattern, error_msg in FORBIDDEN_PATTERNS:
        if re.search(pattern, output, re.IGNORECASE):
            errors.append(error_msg)

    return errors


def check_output(output: str) -> FormatCheckResult:
    """
    Convenience wrapper returning a named tuple with passed bool + errors list.
    """
    errors = validate_output_format(output)
    return FormatCheckResult(passed=len(errors) == 0, errors=errors)
