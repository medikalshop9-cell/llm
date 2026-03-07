# AfriLearn — Curriculum Sources Reference

All curriculum sources used to build the training dataset. Every dataset row must trace back to one of these.

---

## Nigeria — NERDC Basic Education Curriculum

| Source | URL | Use |
|--------|-----|-----|
| NERDC official curriculum portal | https://nerdc.gov.ng/content_manager/curriculum.html | Primary authority — Primary 1-6 all subjects |
| NERDC Scheme of Work reference | https://schemeofwork.com/nerdc-curriculum-scheme-of-work-for-primary-school | Week-by-week topic titles per grade |

**Structure:** 3 terms × 10 weeks per academic year. Primary 1 through Primary 6.

**Subjects covered:**
- English Studies (P1-P6)
- Mathematics (P1-P6)
- Basic Science and Technology (P1-P6)
- Social and Citizenship Studies (P1-P6)
- Christian Religious Studies / Islamic Religious Studies (P1-P6)
- Computer Studies (P1-P6)
- Physical and Health Education (P1-P6)

**Curriculum reference format:** `NERDC-NG-{SUBJECT_CODE}-P{GRADE}-T{TERM}-W{WEEK}`

Examples:
- `NERDC-NG-MATH-P3-T2-W4` — Mathematics, Primary 3, Term 2, Week 4
- `NERDC-NG-ENG-P5-T1-W7`  — English Studies, Primary 5, Term 1, Week 7
- `NERDC-NG-BST-P4-T3-W2`  — Basic Science & Tech, Primary 4, Term 3, Week 2

**Subject codes:**
| Subject | Code |
|---------|------|
| English Studies | ENG |
| Mathematics | MATH |
| Basic Science and Technology | BST |
| Social and Citizenship Studies | SCS |
| Christian Religious Studies | CRS |
| Islamic Religious Studies | IRS |
| Computer Studies | CS |
| Physical and Health Education | PHE |

---

## Ghana — NaCCA Standards-Based Curriculum 2019

| Source | URL | Use |
|--------|-----|-----|
| NaCCA official curriculum page | https://nacca.gov.gh/learning-areas-subjects/new-standards-based-curriculum-2019/ | Primary authority — all subject PDFs B1-B6 |
| NaCCA curriculum framework PDF | https://nacca.gov.gh/wp-content/uploads/2019/04/National-Pre-tertiary-Education-Curriculum-Framework-final.pdf | Assessment principles, 4Rs framework, progression phases |
| PDF download index (mirror) | https://avenuegh.com/ges-new-syllabus-all-subjects-download/ | Direct PDF downloads per subject |

**Structure:** Strand > Sub-strand > Content Standard > Indicator. Basic 1 through Basic 6.

**Phases:**
- Lower Primary: Basic 1-3 (ages 6-8)
- Upper Primary: Basic 4-6 (ages 9-12)

**Subjects covered:**
- English Language (B1-B6)
- Mathematics (B1-B6)
- Science (B1-B6)
- Our World and Our People — OWOP (B1-B6)
- Religious and Moral Education — RME (B1-B6)
- Computing (B4-B6 only — not introduced until B4)
- Physical Education (B1-B6)

**Curriculum reference format:** `NACCA-GH-{SUBJECT_CODE}-B{GRADE}-{STRAND}-{SUB_STRAND}-{CONTENT_STANDARD}`

Examples:
- `NACCA-GH-MATH-B4-NUMBER-FRACTIONS-B4.1.3.1`
- `NACCA-GH-ENG-B2-READING-PHONOLOGICAL-B2.1.1.1`
- `NACCA-GH-SCI-B5-LIFE_SCIENCE-LIVING_NONLIVING-B5.3.1.1`

**Subject codes:**
| Subject | Code |
|---------|------|
| English Language | ENG |
| Mathematics | MATH |
| Science | SCI |
| Our World and Our People | OWOP |
| Religious and Moral Education | RME |
| Computing | COMP |
| Physical Education | PE |

---

## Shared Sources (Both Countries)

| Source | URL | License | Use |
|--------|-----|---------|-----|
| African Storybook Project | https://www.africanstorybook.org/ | CC BY 4.0 | Reading comprehension passages in African English register |
| UNESCO IIEP open resources | https://www.iiep.unesco.org/en/tools-and-resources | Open | EGRA and EGMA validated question formats |
| Khan Academy early math | https://www.khanacademy.org/math/early-math | CC BY-NC-SA | Numeracy question scaffolding patterns only — rewrite before use |

---

## Validation Rule

Every dataset row submitted to training must contain a `CURRICULUM_REF` that matches one of the formats documented above. Rows without a valid curriculum reference are rejected by `dataset/validate_dataset.py`.
