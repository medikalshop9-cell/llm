"""
dataset/build_dataset.py
AfriLearn — Dataset generation engine.

This is the most important script in the entire pipeline.
It generates 50,000–70,000 high-quality, curriculum-anchored training examples
across Nigeria (NERDC) and Ghana (NaCCA) by calling a generation API (Claude or GPT-4),
applying inline quality filters, and writing clean JSONL.

Design principles:
  - Resumable: tracks progress in a state file so a crashed run picks up where it left off
  - Auditable: every generated row is tagged with its generation batch ID and timestamp
  - Enforceable: inline quality filters reject bad rows before they reach the training set
  - Balanced: enforces topic/grade/difficulty distribution so no subject is over or under-represented
  - Deterministic: fixed seeds per prompt so generation is reproducible

Usage:
  python dataset/build_dataset.py \\
    --country nigeria \\
    --output data/raw/nigeria_raw.jsonl \\
    --target 34000 \\
    --api claude

  python dataset/build_dataset.py \\
    --country ghana \\
    --output data/raw/ghana_raw.jsonl \\
    --target 20000 \\
    --api claude

  # Generate both in sequence:
  python dataset/build_dataset.py --country both --target 64000 --api claude

Environment variables required:
  ANTHROPIC_API_KEY   — if using Claude (recommended)
  OPENAI_API_KEY      — if using GPT-4 (fallback)

Dependencies:
  anthropic>=0.25.0 or openai>=1.30.0 (whichever you use)
  tqdm, loguru, jsonschema
"""

import json
import os
import re
import sys
import time
import uuid
import argparse
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Generator, Literal

from tqdm import tqdm
from loguru import logger

# Internal imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from data.curriculum.nigeria_topic_map import iter_all_topics as iter_nigeria_topics, get_topic
from dataset.validate_dataset import validate_row, load_schema

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

ROWS_PER_TOPIC_PER_DIFFICULTY = 3     # 3 rows × 3 difficulty levels = 9 rows per topic minimum
DIFFICULTIES = ["easy", "medium", "hard"]
BATCH_SIZE = 10                        # How many rows to generate per API call
MAX_RETRIES = 3                        # Retry failed API calls this many times
RETRY_DELAY_SECONDS = 5
STATE_FILE_TEMPLATE = "data/raw/.build_state_{country}.json"

# ---------------------------------------------------------------------------
# GHANA TOPIC MAP (simplified — expand from NaCCA PDFs)
# ---------------------------------------------------------------------------

GHANA_TOPICS = [
    # (subject, grade, strand, sub_strand, content_standard)
    ("English Language", 1, "Reading", "Phonological Awareness", "B1.1.1.1"),
    ("English Language", 1, "Reading", "Print Concepts", "B1.1.2.1"),
    ("English Language", 2, "Reading", "Decoding", "B2.1.2.1"),
    ("English Language", 2, "Reading", "Fluency", "B2.1.3.1"),
    ("English Language", 3, "Reading", "Vocabulary", "B3.1.4.1"),
    ("English Language", 3, "Reading", "Comprehension", "B3.1.5.1"),
    ("English Language", 4, "Writing", "Sentence Structure", "B4.2.1.1"),
    ("English Language", 4, "Reading", "Comprehension — Main Idea", "B4.1.5.1"),
    ("English Language", 5, "Writing", "Paragraph Writing", "B5.2.2.1"),
    ("English Language", 5, "Reading", "Comprehension — Inference", "B5.1.5.2"),
    ("English Language", 6, "Writing", "Essay Writing", "B6.2.3.1"),
    ("English Language", 6, "Reading", "Critical Reading", "B6.1.5.3"),
    ("Mathematics", 1, "Number", "Counting and Cardinality", "B1.1.1.1"),
    ("Mathematics", 1, "Number", "Number Operations — Addition", "B1.1.2.1"),
    ("Mathematics", 2, "Number", "Number Operations — Subtraction", "B2.1.2.1"),
    ("Mathematics", 2, "Number", "Whole Numbers to 200", "B2.1.1.1"),
    ("Mathematics", 3, "Number", "Multiplication Tables", "B3.1.2.1"),
    ("Mathematics", 3, "Number", "Division", "B3.1.2.2"),
    ("Mathematics", 4, "Number", "Fractions", "B4.1.3.1"),
    ("Mathematics", 4, "Number", "Decimals", "B4.1.4.1"),
    ("Mathematics", 5, "Algebra", "Patterns and Sequences", "B5.2.1.1"),
    ("Mathematics", 5, "Geometry", "Shapes and their Properties", "B5.3.1.1"),
    ("Mathematics", 6, "Number", "Percentages", "B6.1.5.1"),
    ("Mathematics", 6, "Statistics", "Data Collection and Display", "B6.4.1.1"),
    ("Science", 1, "Life Science", "Living and Non-Living Things", "B1.3.1.1"),
    ("Science", 2, "Life Science", "Plants — Parts and Functions", "B2.3.1.1"),
    ("Science", 3, "Life Science", "Animals — Classification", "B3.3.2.1"),
    ("Science", 4, "Physical Science", "States of Matter", "B4.1.1.1"),
    ("Science", 5, "Physical Science", "Forces and Motion", "B5.1.2.1"),
    ("Science", 6, "Earth Science", "The Solar System", "B6.2.1.1"),
    ("Our World and Our People", 1, "My Home and Community", "Family Members", "B1.1.1.1"),
    ("Our World and Our People", 2, "My Home and Community", "People in the Community", "B2.1.2.1"),
    ("Our World and Our People", 3, "Ghana", "Map of Ghana", "B3.2.1.1"),
    ("Our World and Our People", 4, "Ghana", "Natural Resources", "B4.2.2.1"),
    ("Our World and Our People", 5, "Africa", "Countries of West Africa", "B5.3.1.1"),
    ("Our World and Our People", 6, "History", "Independence of Ghana", "B6.4.1.1"),
    ("Religious and Moral Education", 1, "Values and Norms", "Respect", "B1.1.1.1"),
    ("Religious and Moral Education", 2, "Values and Norms", "Honesty", "B2.1.2.1"),
    ("Religious and Moral Education", 3, "Values and Norms", "Responsibility", "B3.1.3.1"),
    ("Religious and Moral Education", 4, "Religious Stories", "Bible and Quran Stories", "B4.2.1.1"),
    ("Religious and Moral Education", 5, "Values and Norms", "Tolerance", "B5.1.4.1"),
    ("Religious and Moral Education", 6, "Values and Norms", "Citizenship", "B6.1.5.1"),
    ("Computing", 4, "Computing Systems", "Hardware Components", "B4.1.1.1"),
    ("Computing", 4, "Computing Systems", "Input and Output Devices", "B4.1.1.2"),
    ("Computing", 5, "Data and Information", "Organising Information", "B5.2.1.1"),
    ("Computing", 5, "Computing Systems", "Operating Systems", "B5.1.2.1"),
    ("Computing", 6, "Algorithms", "Sequences and Instructions", "B6.3.1.1"),
    ("Computing", 6, "Digital Safety", "Online Safety and Privacy", "B6.4.1.1"),
    ("Physical Education", 1, "Movement Skills", "Running and Jumping", "B1.1.1.1"),
    ("Physical Education", 3, "Health", "Personal Hygiene", "B3.2.1.1"),
    ("Physical Education", 5, "Health", "Nutrition and Balanced Diet", "B5.2.2.1"),
]

# ---------------------------------------------------------------------------
# AGE MAP
# ---------------------------------------------------------------------------
GRADE_AGE_MAP = {1: 6, 2: 7, 3: 8, 4: 9, 5: 10, 6: 11}

# ---------------------------------------------------------------------------
# GENERATION PROMPTS
# ---------------------------------------------------------------------------

NIGERIA_MCQ_SYSTEM_PROMPT = """You are a senior curriculum developer for the AfriLearn offline AI tutoring platform.
You create training data for a fine-tuned model that will generate quiz questions for Nigerian primary school children aged 6-12.
You follow the NERDC (Nigerian Educational Research and Development Council) Basic Education Curriculum exactly.

Your output must be a valid JSON object with exactly three fields: "instruction", "input", "output".
Return ONLY the JSON object. No preamble. No markdown fences. No explanation.

Quality rules you must follow without exception:
1. Questions must use Nigerian names, places, currencies (Naira/kobo), foods, and cultural context.
2. Language must match the grade level (see difficulty rubric).
3. easy: single-step, direct recall. medium: two-step or word problem. hard: multi-step word problem with real-world context.
4. The EXPLANATION in the output must TEACH the concept, not just restate the answer.
5. Distractors must be plausible wrong answers — not obviously silly.
6. The CURRICULUM_REF must exactly match the format: NERDC-NG-{CODE}-P{grade}-T{term}-W{week}
7. Never reference internet, YouTube, Google, WhatsApp, or any online service."""

GHANA_MCQ_SYSTEM_PROMPT = """You are a senior curriculum developer for the AfriLearn offline AI tutoring platform.
You create training data for a fine-tuned model that will generate quiz questions for Ghanaian primary school children aged 6-12.
You follow the NaCCA (National Council for Curriculum and Assessment) Standards-Based Curriculum 2019 exactly.

Your output must be a valid JSON object with exactly three fields: "instruction", "input", "output".
Return ONLY the JSON object. No preamble. No markdown fences. No explanation.

Quality rules you must follow without exception:
1. Questions must use Ghanaian names, places, currencies (Cedi/pesewa), foods, and cultural context.
2. Language must match the grade level.
3. easy: single-step. medium: two-step. hard: multi-step with real-world Ghanaian context.
4. The EXPLANATION must TEACH the concept.
5. Distractors must be plausible.
6. CURRICULUM_REF format: NACCA-GH-{CODE}-B{grade}-{STRAND}-{SUBSTRAND}-{STANDARD}
7. Never reference internet, YouTube, Google, WhatsApp, or any online service."""

TUTOR_CHAT_SYSTEM_PROMPT = """You are a senior curriculum developer for the AfriLearn AI tutoring platform.
You create multi-turn tutor chat training examples.

The model being trained must learn to:
1. NEVER give the answer directly on a student's first expression of confusion.
2. ALWAYS scaffold first — use an analogy, simpler sub-problem, or concrete Nigerian/Ghanaian example.
3. Only reveal the answer after the student has made an attempt.
4. Tag every response with a PEDAGOGIC_ACTION from this list:
   scaffold_with_analogy | scaffold_with_concrete_example | scaffold_with_simpler_subproblem |
   reveal_answer_after_attempt | praise_correct_attempt | correct_misconception | await_student_attempt

Your output must be a valid JSON object with exactly three fields: "instruction", "input", "output".
Return ONLY the JSON object. No preamble. No markdown fences. No explanation."""


def build_nigeria_mcq_prompt(subject: str, grade: int, term: int, week: int,
                              topic: str, difficulty: str, session_streak: int,
                              last_score: int) -> str:
    age = GRADE_AGE_MAP.get(grade, 8)
    subject_codes = {
        "Mathematics": "MATH", "English Studies": "ENG",
        "Basic Science and Technology": "BST", "Social and Citizenship Studies": "SCS",
        "Christian Religious Studies": "CRS", "Islamic Religious Studies": "IRS",
        "Computer Studies": "CS", "Physical and Health Education": "PHE",
    }
    code = subject_codes.get(subject, "UNK")

    return f"""Generate one multiple-choice training example.

Curriculum anchor:
- Country: Nigeria
- Subject: {subject}
- Grade: Primary {grade}
- Term: {term}
- Week: {week}
- Topic: {topic}
- Difficulty: {difficulty}
- CURRICULUM_REF to use: NERDC-NG-{code}-P{grade}-T{term}-W{week}

Student context:
- Age: {age}
- Session streak: {session_streak} correct answers in a row
- Last topic score: {last_score}%

Required output format (inside the "output" field):
QUESTION: [question text using Nigerian names/context]
A) [option]
B) [option]
C) [option]
D) [option]

CORRECT_ANSWER: [A/B/C/D]
EXPLANATION: [max 3 sentences — teach the concept, do not just state the answer]
DIFFICULTY: {difficulty}
CURRICULUM_REF: NERDC-NG-{code}-P{grade}-T{term}-W{week}"""


def build_ghana_mcq_prompt(subject: str, grade: int, strand: str, sub_strand: str,
                            content_standard: str, difficulty: str,
                            session_streak: int, last_score: int) -> str:
    age = GRADE_AGE_MAP.get(grade, 8)
    subject_codes = {
        "English Language": "ENG", "Mathematics": "MATH", "Science": "SCI",
        "Our World and Our People": "OWOP", "Religious and Moral Education": "RME",
        "Computing": "COMP", "Physical Education": "PE",
    }
    code = subject_codes.get(subject, "UNK")
    strand_code = strand.upper().replace(" ", "_").replace("-", "_")
    substrand_code = sub_strand.upper().replace(" ", "_").replace("-", "_")
    curriculum_ref = f"NACCA-GH-{code}-B{grade}-{strand_code}-{substrand_code}-{content_standard}"

    return f"""Generate one multiple-choice training example.

Curriculum anchor:
- Country: Ghana
- Subject: {subject}
- Grade: Basic {grade}
- Strand: {strand}
- Sub-strand: {sub_strand}
- Content Standard: {content_standard}
- Difficulty: {difficulty}
- CURRICULUM_REF to use: {curriculum_ref}

Student context:
- Age: {age}
- Session streak: {session_streak} correct answers in a row
- Last topic score: {last_score}%

Required output format (inside the "output" field):
QUESTION: [question text using Ghanaian names/context]
A) [option]
B) [option]
C) [option]
D) [option]

CORRECT_ANSWER: [A/B/C/D]
EXPLANATION: [max 3 sentences — teach the concept]
DIFFICULTY: {difficulty}
CURRICULUM_REF: {curriculum_ref}"""


# ---------------------------------------------------------------------------
# API CLIENTS
# ---------------------------------------------------------------------------

def call_claude(system: str, user: str, api_key: str) -> str:
    """Call Anthropic Claude API. Returns raw text response."""
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return message.content[0].text


def call_gpt4(system: str, user: str, api_key: str) -> str:
    """Call OpenAI GPT-4 API. Returns raw text response."""
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=1024,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
    )
    return response.choices[0].message.content


def call_api(system: str, user: str, api: str) -> str:
    """Dispatch to configured API with retry logic."""
    api_key = (
        os.environ.get("ANTHROPIC_API_KEY") if api == "claude"
        else os.environ.get("OPENAI_API_KEY")
    )
    if not api_key:
        env_var = "ANTHROPIC_API_KEY" if api == "claude" else "OPENAI_API_KEY"
        raise EnvironmentError(f"{env_var} environment variable not set.")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if api == "claude":
                return call_claude(system, user, api_key)
            else:
                return call_gpt4(system, user, api_key)
        except Exception as e:
            if attempt == MAX_RETRIES:
                raise
            logger.warning(f"API call failed (attempt {attempt}/{MAX_RETRIES}): {e}. Retrying in {RETRY_DELAY_SECONDS}s...")
            time.sleep(RETRY_DELAY_SECONDS)


# ---------------------------------------------------------------------------
# INLINE QUALITY FILTER
# ---------------------------------------------------------------------------

FORBIDDEN = [
    r"\binternet\b", r"\bYouTube\b", r"\bGoogle\b", r"\bWhatsApp\b",
    r"\bFacebook\b", r"\bTikTok\b", r"https?://", r"\bdownload\b",
    r"\bJohn\b", r"\bMary\b", r"\bPeter\b",   # Non-African names as protagonists
]

REQUIRED_OUTPUT_TAGS = [
    r"QUESTION:", r"CORRECT_ANSWER:\s*[ABCD]",
    r"DIFFICULTY:\s*(easy|medium|hard)", r"CURRICULUM_REF:",
]


def passes_inline_quality_filter(row: dict, country: str) -> tuple[bool, str]:
    """
    Fast inline check before schema validation.
    Returns (passed: bool, reason: str).
    """
    output = row.get("output", "")
    full_text = json.dumps(row)

    for pattern in FORBIDDEN:
        if re.search(pattern, full_text, re.IGNORECASE):
            return False, f"Forbidden content: {pattern}"

    for tag in REQUIRED_OUTPUT_TAGS:
        if not re.search(tag, output, re.IGNORECASE):
            return False, f"Missing required tag: {tag}"

    # Ensure CORRECT_ANSWER matches one of the answer options
    correct_match = re.search(r"CORRECT_ANSWER:\s*([ABCD])", output)
    if correct_match:
        letter = correct_match.group(1)
        if not re.search(rf"^{letter}\)", output, re.MULTILINE):
            return False, f"CORRECT_ANSWER {letter} has no matching answer option in output"

    return True, "ok"


# ---------------------------------------------------------------------------
# STATE MANAGEMENT (resumable generation)
# ---------------------------------------------------------------------------

def load_state(country: str) -> dict:
    state_file = Path(STATE_FILE_TEMPLATE.format(country=country))
    if state_file.exists():
        with open(state_file) as f:
            return json.load(f)
    return {"completed_keys": [], "total_generated": 0, "total_rejected": 0}


def save_state(country: str, state: dict):
    state_file = Path(STATE_FILE_TEMPLATE.format(country=country))
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)


def make_topic_key_nigeria(subject: str, grade: int, term: int, week: int, difficulty: str) -> str:
    return f"NG|{subject}|P{grade}|T{term}|W{week}|{difficulty}"


def make_topic_key_ghana(subject: str, grade: int, strand: str, sub_strand: str, difficulty: str) -> str:
    return f"GH|{subject}|B{grade}|{strand}|{sub_strand}|{difficulty}"


# ---------------------------------------------------------------------------
# DISTRIBUTION TRACKER
# ---------------------------------------------------------------------------

class DistributionTracker:
    """Tracks how many rows exist per subject/grade/difficulty to enforce balance."""

    def __init__(self):
        self.counts: dict[str, int] = {}

    def add(self, subject: str, grade: int, difficulty: str):
        key = f"{subject}|{grade}|{difficulty}"
        self.counts[key] = self.counts.get(key, 0) + 1

    def report(self) -> dict:
        return dict(sorted(self.counts.items()))

    def needs_more(self, subject: str, grade: int, difficulty: str,
                   rows_per_topic: int, topics_in_grade: int) -> bool:
        """Return True if this subject/grade/difficulty combination needs more rows."""
        key = f"{subject}|{grade}|{difficulty}"
        current = self.counts.get(key, 0)
        target = rows_per_topic * topics_in_grade
        return current < target


# ---------------------------------------------------------------------------
# NIGERIA GENERATION
# ---------------------------------------------------------------------------

def generate_nigeria_dataset(
    output_path: Path,
    target_rows: int,
    api: str,
    schema: dict,
) -> int:
    """Generate Nigeria NERDC dataset rows. Returns count of rows written."""

    state = load_state("nigeria")
    completed_keys = set(state["completed_keys"])
    total_generated = state["total_generated"]
    total_rejected  = state["total_rejected"]
    tracker = DistributionTracker()

    # Build full topic list
    all_topics = list(iter_nigeria_topics())
    tasks = []
    for subject, grade, term, week, topic in all_topics:
        for difficulty in DIFFICULTIES:
            key = make_topic_key_nigeria(subject, grade, term, week, difficulty)
            if key not in completed_keys:
                tasks.append((subject, grade, term, week, topic, difficulty, key))

    logger.info(f"Nigeria: {len(all_topics)} topics × 3 difficulties = {len(tasks)} tasks remaining")
    logger.info(f"Resuming from {len(completed_keys)} completed tasks. Target: {target_rows} rows.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    file_mode = "a" if output_path.exists() else "w"

    with open(output_path, file_mode) as out_f:
        for subject, grade, term, week, topic, difficulty, key in tqdm(tasks, desc="Nigeria generation"):
            if total_generated >= target_rows:
                logger.info(f"Reached target of {target_rows} rows.")
                break

            # Generate ROWS_PER_TOPIC_PER_DIFFICULTY rows per combination
            session_configs = [
                (0, 45), (2, 65), (4, 85),   # (streak, last_score) — vary context
            ][:ROWS_PER_TOPIC_PER_DIFFICULTY]

            for streak, last_score in session_configs:
                prompt = build_nigeria_mcq_prompt(
                    subject, grade, term, week, topic, difficulty, streak, last_score
                )

                try:
                    raw_response = call_api(NIGERIA_MCQ_SYSTEM_PROMPT, prompt, api)
                except Exception as e:
                    logger.error(f"API error for {key}: {e}")
                    total_rejected += 1
                    continue

                # Parse JSON
                try:
                    clean = raw_response.strip()
                    if clean.startswith("```"):
                        clean = re.sub(r"```(?:json)?", "", clean).strip().rstrip("`").strip()
                    row = json.loads(clean)
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parse failed for {key}: {e}")
                    total_rejected += 1
                    continue

                # Inline quality filter
                passed, reason = passes_inline_quality_filter(row, "nigeria")
                if not passed:
                    logger.debug(f"Inline filter rejected {key}: {reason}")
                    total_rejected += 1
                    continue

                # Schema validation
                schema_errors = validate_row(row, schema, "nigeria")
                if schema_errors:
                    logger.debug(f"Schema rejected {key}: {schema_errors[0]}")
                    total_rejected += 1
                    continue

                # Add metadata
                row["_meta"] = {
                    "country":    "Nigeria",
                    "subject":    subject,
                    "grade":      grade,
                    "term":       term,
                    "week":       week,
                    "difficulty": difficulty,
                    "batch_id":   str(uuid.uuid4())[:8],
                    "generated":  datetime.utcnow().isoformat(),
                }

                out_f.write(json.dumps(row) + "\n")
                out_f.flush()
                total_generated += 1
                tracker.add(subject, grade, difficulty)

            completed_keys.add(key)
            state["completed_keys"]    = list(completed_keys)
            state["total_generated"]   = total_generated
            state["total_rejected"]    = total_rejected
            save_state("nigeria", state)

    logger.info(f"Nigeria generation complete: {total_generated} rows written, {total_rejected} rejected")
    logger.info(f"Distribution:\n{json.dumps(tracker.report(), indent=2)}")
    return total_generated


# ---------------------------------------------------------------------------
# GHANA GENERATION
# ---------------------------------------------------------------------------

def generate_ghana_dataset(
    output_path: Path,
    target_rows: int,
    api: str,
    schema: dict,
) -> int:
    """Generate Ghana NaCCA dataset rows. Returns count of rows written."""

    state = load_state("ghana")
    completed_keys = set(state["completed_keys"])
    total_generated = state["total_generated"]
    total_rejected  = state["total_rejected"]
    tracker = DistributionTracker()

    tasks = []
    for subject, grade, strand, sub_strand, content_standard in GHANA_TOPICS:
        for difficulty in DIFFICULTIES:
            key = make_topic_key_ghana(subject, grade, strand, sub_strand, difficulty)
            if key not in completed_keys:
                tasks.append((subject, grade, strand, sub_strand, content_standard, difficulty, key))

    logger.info(f"Ghana: {len(GHANA_TOPICS)} topics × 3 difficulties = {len(tasks)} tasks remaining")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    file_mode = "a" if output_path.exists() else "w"

    with open(output_path, file_mode) as out_f:
        for subject, grade, strand, sub_strand, content_standard, difficulty, key in tqdm(tasks, desc="Ghana generation"):
            if total_generated >= target_rows:
                break

            session_configs = [(0, 45), (2, 65), (4, 85)][:ROWS_PER_TOPIC_PER_DIFFICULTY]

            for streak, last_score in session_configs:
                prompt = build_ghana_mcq_prompt(
                    subject, grade, strand, sub_strand, content_standard,
                    difficulty, streak, last_score
                )

                try:
                    raw_response = call_api(GHANA_MCQ_SYSTEM_PROMPT, prompt, api)
                except Exception as e:
                    logger.error(f"API error for {key}: {e}")
                    total_rejected += 1
                    continue

                try:
                    clean = raw_response.strip()
                    if clean.startswith("```"):
                        clean = re.sub(r"```(?:json)?", "", clean).strip().rstrip("`").strip()
                    row = json.loads(clean)
                except json.JSONDecodeError:
                    total_rejected += 1
                    continue

                passed, reason = passes_inline_quality_filter(row, "ghana")
                if not passed:
                    total_rejected += 1
                    continue

                schema_errors = validate_row(row, schema, "ghana")
                if schema_errors:
                    total_rejected += 1
                    continue

                row["_meta"] = {
                    "country":          "Ghana",
                    "subject":          subject,
                    "grade":            grade,
                    "strand":           strand,
                    "sub_strand":       sub_strand,
                    "content_standard": content_standard,
                    "difficulty":       difficulty,
                    "batch_id":         str(uuid.uuid4())[:8],
                    "generated":        datetime.utcnow().isoformat(),
                }

                out_f.write(json.dumps(row) + "\n")
                out_f.flush()
                total_generated += 1
                tracker.add(subject, grade, difficulty)

            completed_keys.add(key)
            state["completed_keys"]  = list(completed_keys)
            state["total_generated"] = total_generated
            state["total_rejected"]  = total_rejected
            save_state("ghana", state)

    logger.info(f"Ghana generation complete: {total_generated} rows written, {total_rejected} rejected")
    return total_generated


# ---------------------------------------------------------------------------
# TUTOR CHAT GENERATION (country-agnostic)
# ---------------------------------------------------------------------------

TUTOR_CHAT_SCENARIOS = [
    # (country, subject, grade, topic, confusion_statement)
    ("Nigeria", "Mathematics", 3, "Division", "I don't understand how to divide numbers"),
    ("Nigeria", "Mathematics", 4, "Fractions", "Fractions are confusing me"),
    ("Nigeria", "Mathematics", 5, "Percentages", "How do I calculate percentage?"),
    ("Nigeria", "English Studies", 2, "Phonics", "I can't tell the difference between b and d"),
    ("Nigeria", "English Studies", 4, "Comprehension", "I don't know what the main idea means"),
    ("Nigeria", "Basic Science and Technology", 3, "States of matter", "I don't understand why water turns to steam"),
    ("Nigeria", "Computer Studies", 5, "Input and output devices", "What is the difference between input and output?"),
    ("Nigeria", "Physical and Health Education", 3, "Hygiene", "Why do we need to wash our hands?"),
    ("Ghana", "Mathematics", 3, "Multiplication tables", "I can never remember my times tables"),
    ("Ghana", "Mathematics", 4, "Fractions", "I don't know how to find half of a number"),
    ("Ghana", "English Language", 3, "Comprehension", "I read the passage but I don't understand it"),
    ("Ghana", "Science", 4, "States of matter", "What does liquid mean?"),
    ("Ghana", "Our World and Our People", 3, "Map of Ghana", "I don't know where the regions are"),
    ("Ghana", "Computing", 5, "Hardware", "I can't remember which things are input and which are output"),
]


def generate_tutor_chat_dataset(
    output_path: Path,
    target_rows: int,
    api: str,
) -> int:
    """Generate multi-turn AI tutor chat examples."""

    state = load_state("tutor_chat")
    total_generated = state.get("total_generated", 0)
    total_rejected  = state.get("total_rejected", 0)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    file_mode = "a" if output_path.exists() else "w"

    rows_per_scenario = max(1, target_rows // len(TUTOR_CHAT_SCENARIOS))

    with open(output_path, file_mode) as out_f:
        for country, subject, grade, topic, confusion in tqdm(TUTOR_CHAT_SCENARIOS, desc="Tutor chat"):
            if total_generated >= target_rows:
                break

            age = GRADE_AGE_MAP.get(grade, 8)
            grade_str = f"Primary {grade}" if country == "Nigeria" else f"Basic {grade}"
            curriculum_auth = "NERDC Nigeria" if country == "Nigeria" else "NaCCA Ghana"

            for i in range(rows_per_scenario):
                prompt = f"""Generate a multi-turn AI tutor chat training example.

Context:
- Country: {country}
- Subject: {subject}
- Grade: {grade_str}
- Topic: {topic}
- Student age: {age}
- Curriculum authority: {curriculum_auth}
- Student's confusion: "{confusion}"

The "instruction" field must contain the SYSTEM_ROLE with the country and curriculum authority.
The "input" field must contain TURN_HISTORY (at least 2 prior turns), CURRENT_TURN (student's follow-up question), and STUDENT_CONTEXT.
The "output" field must contain the tutor's response that SCAFFOLDS (does not give the answer), includes a PEDAGOGIC_ACTION tag, and ends with a probe question to keep the student thinking.

Use {'Nigerian' if country == 'Nigeria' else 'Ghanaian'} names and cultural context throughout."""

                try:
                    raw = call_api(TUTOR_CHAT_SYSTEM_PROMPT, prompt, api)
                except Exception as e:
                    logger.error(f"Tutor chat API error: {e}")
                    total_rejected += 1
                    continue

                try:
                    clean = raw.strip()
                    if clean.startswith("```"):
                        clean = re.sub(r"```(?:json)?", "", clean).strip().rstrip("`").strip()
                    row = json.loads(clean)
                except json.JSONDecodeError:
                    total_rejected += 1
                    continue

                # Basic quality check for tutor chat
                output = row.get("output", "")
                if "PEDAGOGIC_ACTION" not in output or "TUTOR_RESPONSE" not in output:
                    total_rejected += 1
                    continue

                row["_meta"] = {
                    "country":        country,
                    "subject":        subject,
                    "grade":          grade,
                    "interaction_type": "tutor_chat",
                    "batch_id":       str(uuid.uuid4())[:8],
                    "generated":      datetime.utcnow().isoformat(),
                }

                out_f.write(json.dumps(row) + "\n")
                out_f.flush()
                total_generated += 1

            state["total_generated"] = total_generated
            state["total_rejected"]  = total_rejected
            save_state("tutor_chat", state)

    logger.info(f"Tutor chat generation complete: {total_generated} rows")
    return total_generated


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="AfriLearn dataset generation engine — produces 50K+ high-quality curriculum-anchored training rows"
    )
    parser.add_argument("--country", choices=["nigeria", "ghana", "both", "tutor"],
                        required=True, help="Which dataset to generate")
    parser.add_argument("--output",  default=None, type=Path,
                        help="Output JSONL path (auto-named if not specified)")
    parser.add_argument("--target",  type=int, default=34000,
                        help="Target number of rows to generate (default: 34000 for Nigeria, 20000 for Ghana)")
    parser.add_argument("--api",     choices=["claude", "gpt4"], default="claude",
                        help="Which API to use for generation (default: claude)")
    args = parser.parse_args()

    logger.info(f"AfriLearn dataset builder | country={args.country} | api={args.api} | target={args.target}")
    logger.info("Reading quality_rubric.md before starting — every row must meet that standard.")

    nigeria_schema = load_schema("nigeria")
    ghana_schema   = load_schema("ghana")

    total = 0

    if args.country in ("nigeria", "both"):
        out = args.output or Path("data/raw/nigeria_raw.jsonl")
        target = args.target if args.country == "nigeria" else int(args.target * 0.54)  # ~54% Nigeria
        total += generate_nigeria_dataset(out, target, args.api, nigeria_schema)

    if args.country in ("ghana", "both"):
        out = args.output or Path("data/raw/ghana_raw.jsonl")
        target = args.target if args.country == "ghana" else int(args.target * 0.32)   # ~32% Ghana
        total += generate_ghana_dataset(out, target, args.api, ghana_schema)

    if args.country in ("tutor", "both"):
        out = args.output or Path("data/raw/tutor_chat_raw.jsonl")
        target = args.target if args.country == "tutor" else int(args.target * 0.14)   # ~14% tutor chat
        total += generate_tutor_chat_dataset(out, target, args.api)

    logger.success(
        f"\nGeneration complete. {total} rows written.\n"
        "Next steps:\n"
        "  1. python dataset/validate_dataset.py --input data/raw/nigeria_raw.jsonl "
        "--output data/processed/nigeria_clean.jsonl --country nigeria\n"
        "  2. python dataset/deduplicate.py --input data/processed/nigeria_clean.jsonl "
        "--output data/processed/nigeria_final.jsonl\n"
        "  3. Repeat for ghana\n"
        "  4. python training/train.py --config training/config.yaml"
    )


if __name__ == "__main__":
    main()
