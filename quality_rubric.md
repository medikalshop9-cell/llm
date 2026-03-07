# AfriLearn Dataset Quality Rubric
# The standard every single training row must meet before it touches the model.
# If a row fails any criterion here, it is rejected — no exceptions, no partial credit.

---

## Why This Document Exists

Fine-tuning quality is a direct function of data quality. A model trained on 50,000
mediocre rows will always underperform one trained on 30,000 excellent rows.
This rubric defines "excellent" precisely so every team member, every reviewer,
and every automated validator is working to the same standard.

---

## SECTION 1 — STRUCTURAL REQUIREMENTS (Hard Fail = Row Rejected)

Every row must satisfy ALL of the following. One failure = rejection.

### 1.1 Schema Compliance
- `instruction`, `input`, `output` fields present with correct types
- No extra top-level keys
- No null or empty string values in any field
- Instruction length: 80–600 characters
- Input length: 40–400 characters
- Output length: 100–1800 characters

### 1.2 Curriculum Reference
- Every row carries a valid `CURRICULUM_REF` in the output field
- Nigeria format: `NERDC-NG-{CODE}-P{1-6}-T{1-3}-W{1-10}`
- Ghana format: `NACCA-GH-{CODE}-B{1-6}-{STRAND}-{SUBSTRAND}-{STANDARD}`
- The referenced term/week or strand/standard must actually exist in the source curriculum PDF
- No invented curriculum references

### 1.3 Answer Integrity (MCQ rows)
- Exactly 4 options: A, B, C, D — no more, no fewer
- CORRECT_ANSWER is exactly one of: A, B, C, D
- The correct answer is unambiguously correct according to the curriculum
- The three distractors are plausible — not obviously wrong to any 6-year-old
- No two options are semantically identical

### 1.4 Difficulty Tag
- One of exactly: `easy`, `medium`, `hard`
- Tag matches the cognitive demand of the question (see Section 3 for definitions)
- For every topic, all three difficulty levels must exist in the dataset
  (enforced at topic level, not row level — but build_dataset.py tracks this)

### 1.5 DIFFICULTY Rubric Per Difficulty Level

| Level  | Nigeria Example (Mathematics) | Ghana Example (English) |
|--------|-------------------------------|-------------------------|
| easy   | Single-step, direct recall, no context needed. P1-P2 number bonds. | Single phoneme recognition, sight word identification |
| medium | Two-step reasoning or word problem with one operation. | Vocabulary in context, sentence completion |
| hard   | Multi-step word problem, requires reading + calculation, real-world scenario | Full comprehension passage, inferencing, main idea extraction |

The same rubric applies proportionally across all subjects and grade levels.

---

## SECTION 2 — CONTENT QUALITY REQUIREMENTS (Human Review Flags)

These are assessed by human reviewers. Automated checks flag candidates; humans confirm.

### 2.1 Factual Accuracy
- The correct answer must be factually correct with zero ambiguity
- Science and mathematics answers must be verifiable against a textbook
- Religious Studies answers must reflect the curriculum syllabus, not personal theology
- Social Studies answers about Nigerian/Ghanaian culture must be reviewed by a local educator

### 2.2 Language Register
- Language must match the grade level:
  - P1/B1-P2/B2: Maximum 6-word sentences. Zero uncommon vocabulary without context.
  - P3/B3-P4/B4: 8-10 word sentences. Common vocabulary only.
  - P5/B5-P6/B6: Up to 14-word sentences. Grade-appropriate vocabulary allowed.
- No idioms, metaphors, or figures of speech in question stems for P1-P3/B1-B3
- Passive voice should be avoided in question stems for all grades

### 2.3 Cultural Appropriateness
- Nigerian rows: Names, places, currencies (Naira/kobo), foods, and examples must be Nigerian
  - Good: "Chukwuemeka bought 4 mangoes from the market in Onitsha"
  - Bad: "John bought 4 apples at the store"
- Ghanaian rows: Names, places, currencies (Cedi/pesewa), foods, and examples must be Ghanaian
  - Good: "Akosua counted 12 kenkey balls at the Kumasi market"
  - Bad: "Mary had some oranges"
- Religious Studies CRS rows: Christian context only
- Religious Studies IRS rows: Islamic context only
- RME (Ghana): Inclusive of both Christian and traditional Ghanaian value systems

### 2.4 Explanation Quality (Output EXPLANATION field)
- Every row where `DIFFICULTY: medium` or `DIFFICULTY: hard` must include an EXPLANATION
- The explanation teaches the concept, not just restates the answer
- It must be short enough to read in 20 seconds (max 3 sentences)
- It must be written at the student's grade reading level

### 2.5 AI Tutor Chat Rows
- The TUTOR_RESPONSE must never reveal the answer on the first turn of confusion
- It must use a scaffold — analogy, simpler sub-problem, or concrete example — first
- The PEDAGOGIC_ACTION tag must be present and must be one of:
  `scaffold_with_analogy | scaffold_with_concrete_example | scaffold_with_simpler_subproblem |
   reveal_answer_after_attempt | praise_correct_attempt | correct_misconception |
   await_student_attempt | redirect_to_topic`
- Turn history must be coherent — each turn must logically follow from the previous

---

## SECTION 3 — FORBIDDEN CONTENT (Auto-Reject, No Review)

Any row containing the following is immediately rejected, regardless of other quality:

| Category | Examples |
|----------|----------|
| Internet/cloud references | internet, YouTube, Google, WhatsApp, TikTok, website, download, online |
| URLs | Any string matching https?:// |
| Non-African names/places (in content fields) | John, Mary, London, dollars, apples (as main example) |
| Politically sensitive content | Electoral politics, ethnic group comparisons |
| Adult or inappropriate content | Any content unsuitable for ages 6-12 |
| Hallucinated curriculum refs | References to non-existent terms, weeks, or standards |
| Questions with no correct answer | Where two or more options are equally valid |
| Questions that require external resources | "Look at the diagram below" with no diagram |

---

## SECTION 4 — CONSISTENCY REQUIREMENTS

### 4.1 Schema Consistency Across the Full Dataset
- `CURRICULUM_REF` format must be identical for all rows of the same curriculum type
- Difficulty labels use lowercase consistently: `easy`, `medium`, `hard` — never `Easy`, `EASY`, `moderate`
- Subject names use the exact canonical name from the curriculum authority (see CURRICULUM_SOURCES.md)
- `device_locale` in input field must be exactly `Nigeria` or `Ghana` — not `NG`, `GH`, `nigerian`

### 4.2 Distribution Requirements (Enforced by build_dataset.py)
- No subject may have fewer than 2,000 rows in the final dataset
- No single grade may have fewer than 1,500 rows per country
- Each difficulty level (easy/medium/hard) must be within 10% of equal distribution per subject
- Adaptive difficulty variants: every MCQ topic must have all 3 difficulty versions
- Multi-turn tutor chat rows: minimum 2,000 across all subjects

### 4.3 No Leakage Between Train and Eval
- The 10% eval split is applied once at dataset freeze, never re-randomised
- Curriculum references that appear in eval must not appear in train
  (topic-level separation, not just row-level — same topic in same grade/term must be in one split only)

---

## SECTION 5 — SCORING RUBRIC (Human Reviewer Scorecard)

Reviewers score each sampled row on three axes. Minimum passing score: 4.0/5.0 average.

### Axis A: Age-Appropriateness (1-5)
| Score | Meaning |
|-------|---------|
| 5 | Language, concepts, and examples are perfectly calibrated for the stated grade |
| 4 | Minor vocabulary choice could be simpler but overall appropriate |
| 3 | One concept or word is above grade level but question is still answerable |
| 2 | Clearly written for a different age group — too simple or too complex |
| 1 | Student at stated grade could not meaningfully engage with this question |

### Axis B: Curriculum Alignment (1-5)
| Score | Meaning |
|-------|---------|
| 5 | Question tests exactly the learning objective specified by the curriculum reference |
| 4 | Tests the right topic but slightly off from the specific objective |
| 3 | Broadly related to the subject but not the specific curriculum ref |
| 2 | Loosely related to the subject — could be from a different term/grade |
| 1 | Does not align to the stated curriculum reference at all |

### Axis C: Clarity (1-5)
| Score | Meaning |
|-------|---------|
| 5 | Question has exactly one reading, zero ambiguity, student knows what is being asked |
| 4 | Minimal rephrasing would make it perfect |
| 3 | Understandable but could be misread in one plausible way |
| 2 | Confusingly worded — reasonable student might not know what is being asked |
| 1 | Question is ambiguous, broken, or has no clear answer |

---

## SECTION 6 — REVIEW PROCESS

1. **Automated validation** — `dataset/validate_dataset.py` runs first. Hard rejects removed.
2. **Deduplication** — `dataset/deduplicate.py` runs second. Near-duplicates removed.
3. **Random sample review** — 200 rows sampled (stratified by subject, grade, difficulty).
   Minimum 2 human reviewers per row. Score below 4.0 → row flagged for revision or rejection.
4. **Topic coverage audit** — verify all Nigeria T1-T3/W1-W10 topics represented per subject.
5. **Distribution check** — verify grade/subject/difficulty balance (build_dataset.py produces a report).
6. **Dataset freeze** — once frozen, no rows are added or removed without a new freeze version.

---

## SECTION 7 — WHAT A PERFECT ROW LOOKS LIKE

```json
{
  "instruction": "COUNTRY: Nigeria | SUBJECT: Mathematics | GRADE: Primary 4 | TERM: 1 | WEEK: 6 | TOPIC: Division of 3-digit numbers by 1-digit numbers | DIFFICULTY: hard | TASK: Generate one multiple-choice word problem aligned to NERDC Primary 4 T1 W6 scope.",
  "input": "student_age: 9 | session_streak: 3_correct | last_topic_score: 78% | prior_topic: multiplication_3digit | device_locale: Nigeria",
  "output": "QUESTION: A market woman in Aba shared 264 oranges equally into 4 baskets. How many oranges are in each basket?\nA) 56\nB) 66\nC) 68\nD) 72\n\nCORRECT_ANSWER: B\nEXPLANATION: Divide 264 by 4. Start with hundreds: 2 ÷ 4 = 0 remainder 2. Bring down 6 to make 26. 26 ÷ 4 = 6 remainder 2. Bring down 4 to make 24. 24 ÷ 4 = 6. Result: 066 = 66.\nDIFFICULTY: hard\nCURRICULUM_REF: NERDC-NG-MATH-P4-T1-W6"
}
```

What makes this perfect:
- Nigerian name (Aba — real Nigerian city), Nigerian product (oranges at a market)
- Word problem with real-world scenario calibrated to age 9
- EXPLANATION teaches the long division algorithm step by step, not just restates the answer
- CURRICULUM_REF is specific: subject, grade, term, week — all traceable to source PDF
- Distractors (56, 68, 72) are plausible wrong answers a student might get via common errors
- Language register is appropriate for Primary 4 (short sentences, direct vocabulary)
