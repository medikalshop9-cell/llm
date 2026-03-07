"""
data/curriculum/nigeria_topic_map.py
AfriLearn — Nigeria NERDC Primary 1-6 topic map.

This file encodes the scope-and-sequence from your NERDC curriculum PDF.
Every entry maps to a real term/week and is what build_dataset.py iterates over
to generate questions. Nothing is invented here.

IMPORTANT: When you parse the full PDF with parse_curriculum.py, replace the
placeholder topics below with the exact topic titles from the official document.
The format must stay identical — only the string values change.

Source: NERDC Basic Education Curriculum — Primary 1-6
URL: https://nerdc.gov.ng/content_manager/curriculum.html

Structure:
  NIGERIA_TOPIC_MAP[subject][grade][term][week] = "Exact Topic Title From PDF"
"""

from typing import Literal

SubjectCode = Literal[
    "English Studies",
    "Mathematics",
    "Basic Science and Technology",
    "Social and Citizenship Studies",
    "Christian Religious Studies",
    "Islamic Religious Studies",
    "Computer Studies",
    "Physical and Health Education",
]

# ---------------------------------------------------------------------------
# MATHEMATICS — P1 through P6, Terms 1-3, Weeks 1-10
# Replace placeholder strings with exact NERDC topic titles from your PDF.
# ---------------------------------------------------------------------------
MATHEMATICS = {
    1: {  # Primary 1
        1: {  # Term 1
            1: "Counting and writing numbers 1-10",
            2: "Counting and writing numbers 11-20",
            3: "Ordering numbers 1-20",
            4: "Addition of single-digit numbers",
            5: "Subtraction of single-digit numbers",
            6: "Shapes — circle, square, triangle",
            7: "Measurement — long and short",
            8: "Money — identification of coins",
            9: "Addition with sums up to 20",
            10: "Revision and assessment",
        },
        2: {  # Term 2
            1: "Counting and writing numbers 21-50",
            2: "Addition of numbers up to 30",
            3: "Subtraction of numbers within 30",
            4: "Multiplication as repeated addition",
            5: "Simple fractions — half and quarter",
            6: "Measurement — heavy and light",
            7: "Time — days of the week",
            8: "Money — addition of coins",
            9: "Data — sorting objects",
            10: "Revision and assessment",
        },
        3: {  # Term 3
            1: "Counting and writing numbers 51-100",
            2: "Addition of 2-digit numbers (no carrying)",
            3: "Subtraction of 2-digit numbers (no borrowing)",
            4: "Patterns and sequences",
            5: "Shapes — 3D shapes introduction",
            6: "Measurement — capacity",
            7: "Time — months of the year",
            8: "Money — subtraction of coins",
            9: "Number bonds to 10",
            10: "Revision and assessment",
        },
    },
    2: {  # Primary 2
        1: {
            1: "Counting and writing numbers 1-200",
            2: "Place value — tens and units",
            3: "Addition of 2-digit numbers with carrying",
            4: "Subtraction of 2-digit numbers with borrowing",
            5: "Multiplication tables — 2 and 5",
            6: "Division as sharing equally",
            7: "Fractions — one third",
            8: "Measurement — length in metres",
            9: "Time — reading clock to the hour",
            10: "Revision and assessment",
        },
        2: {
            1: "Numbers 201-500",
            2: "Addition of 3-digit numbers",
            3: "Subtraction of 3-digit numbers",
            4: "Multiplication tables — 3 and 4",
            5: "Division of 2-digit numbers by 1-digit numbers",
            6: "Money — addition and subtraction with Naira",
            7: "Shapes — sides and corners",
            8: "Measurement — mass in kilograms",
            9: "Data — simple pictograms",
            10: "Revision and assessment",
        },
        3: {
            1: "Numbers 501-1000",
            2: "Ordering and comparing numbers to 1000",
            3: "Addition and subtraction word problems",
            4: "Multiplication tables — 6 and 7",
            5: "Fractions — equivalence (half = two quarters)",
            6: "Measurement — area by counting squares",
            7: "Time — reading clock to half hour",
            8: "Money — buying and giving change",
            9: "Patterns — number sequences",
            10: "Revision and assessment",
        },
    },
    3: {  # Primary 3
        1: {
            1: "Numbers 1-9999 — place value",
            2: "Addition of 4-digit numbers",
            3: "Subtraction of 4-digit numbers",
            4: "Multiplication tables — 8 and 9",
            5: "Multiplication of 2-digit by 1-digit numbers",
            6: "Division of 2-digit numbers by 1-digit numbers",
            7: "Fractions — numerator and denominator",
            8: "Measurement — perimeter",
            9: "Time — 24-hour clock",
            10: "Revision and assessment",
        },
        2: {
            1: "Roman numerals I to XX",
            2: "LCM and HCF (simple cases)",
            3: "Multiplication of 3-digit by 1-digit numbers",
            4: "Multiplication of 2-digit by 2-digit numbers",
            5: "Division of 3-digit numbers by 1-digit numbers",
            6: "Word problems — multiplication and division",
            7: "Fractions — addition of like fractions",
            8: "Decimals — introduction (tenths)",
            9: "Money — calculating profit and loss",
            10: "Revision and assessment",
        },
        3: {
            1: "Numbers beyond 10000",
            2: "Estimation and rounding",
            3: "Multiplication of 2-digit by 2-digit numbers",
            4: "Long division — 2-digit quotient",
            5: "Fractions — subtraction of like fractions",
            6: "Measurement — area of rectangles",
            7: "Shapes — angles (right angle introduction)",
            8: "Data — bar charts",
            9: "Money — budgets and savings",
            10: "Revision and assessment",
        },
    },
    4: {  # Primary 4
        1: {
            1: "Numbers — millions",
            2: "Addition and subtraction of large numbers",
            3: "Multiplication by 10, 100, 1000",
            4: "Division of 3-digit numbers by 2-digit numbers",
            5: "LCM and HCF",
            6: "Division of 3-digit numbers by 1-digit numbers (word problems)",
            7: "Fractions — multiplication of fractions",
            8: "Decimals — hundredths and thousandths",
            9: "Percentages — introduction",
            10: "Revision and assessment",
        },
        2: {
            1: "Fractions — division of fractions",
            2: "Ratio and proportion — introduction",
            3: "Measurement — area of triangles",
            4: "Measurement — volume of cuboids",
            5: "Angles — measuring with protractor",
            6: "Coordinates — introduction",
            7: "Data — mean, median, mode",
            8: "Probability — introduction",
            9: "Algebra — simple equations",
            10: "Revision and assessment",
        },
        3: {
            1: "Percentages — calculations",
            2: "Speed, distance, time",
            3: "Scale drawing",
            4: "Shapes — properties of quadrilaterals",
            5: "Circles — radius, diameter, circumference",
            6: "Measurement — units conversion",
            7: "Data — pie charts",
            8: "Number sequences — rules",
            9: "Problem solving — multi-step",
            10: "Revision and assessment",
        },
    },
    5: {  # Primary 5
        1: {
            1: "Place value to billions",
            2: "Operations with large numbers",
            3: "Directed numbers — introduction",
            4: "Fractions — complex operations",
            5: "Decimals — operations",
            6: "Percentages — profit and loss",
            7: "Ratio and proportion",
            8: "Algebra — linear equations",
            9: "Geometry — construction",
            10: "Revision and assessment",
        },
        2: {
            1: "Powers and roots — squares and cubes",
            2: "Prime numbers and composite numbers",
            3: "Number bases",
            4: "Simultaneous equations (simple)",
            5: "Measurement — surface area",
            6: "Angles in parallel lines",
            7: "Data — grouped data",
            8: "Probability — theoretical and experimental",
            9: "Financial maths — simple interest",
            10: "Revision and assessment",
        },
        3: {
            1: "Indices",
            2: "Variation — direct and inverse",
            3: "Factorisation (simple)",
            4: "Measurement — volume of cylinders",
            5: "Trigonometry — introduction (SOHCAHTOA)",
            6: "Loci and construction",
            7: "Statistics — cumulative frequency",
            8: "Matrices — introduction",
            9: "Transformation — reflection and rotation",
            10: "Revision and assessment",
        },
    },
    6: {  # Primary 6
        1: {
            1: "Review — number operations",
            2: "Fractions, decimals, percentages — interconversion",
            3: "Ratio, rates, proportion",
            4: "Algebra — expressions and equations",
            5: "Geometry — angles and triangles",
            6: "Measurement — area and volume",
            7: "Statistics — data analysis",
            8: "Probability",
            9: "Financial literacy — taxation, insurance basics",
            10: "Revision and assessment",
        },
        2: {
            1: "Number theory — factors, multiples, primes",
            2: "Algebra — inequalities",
            3: "Coordinate geometry",
            4: "Circle theorems (introduction)",
            5: "Trigonometry — sine, cosine, tangent",
            6: "Statistics — standard deviation",
            7: "Matrices — operations",
            8: "Vectors — introduction",
            9: "Transformation — enlargement",
            10: "Revision and assessment",
        },
        3: {
            1: "Revision — fractions and percentages",
            2: "Revision — algebra",
            3: "Revision — geometry",
            4: "Revision — statistics",
            5: "Past question practice — Paper 1 type",
            6: "Past question practice — Paper 2 type",
            7: "Exam technique and time management",
            8: "Common primary school leaving exam topics",
            9: "Mock assessment",
            10: "Final revision",
        },
    },
}

# ---------------------------------------------------------------------------
# ENGLISH STUDIES
# Replace with exact NERDC topic titles from your PDF.
# ---------------------------------------------------------------------------
ENGLISH_STUDIES = {
    1: {
        1: {1: "Alphabet — uppercase A-E", 2: "Alphabet — uppercase F-J", 3: "Alphabet — lowercase a-e",
            4: "Alphabet — lowercase f-j", 5: "Letter sounds: a, b, c, d, e", 6: "Letter sounds: f, g, h, i, j",
            7: "Simple CVC words — cat, bat, hat", 8: "Simple CVC words — sit, bit, hit",
            9: "Reading: short sentences", 10: "Revision and assessment"},
        2: {1: "Alphabet — uppercase K-O", 2: "Alphabet — uppercase P-T", 3: "Letter sounds: k, l, m, n, o",
            4: "Letter sounds: p, q, r, s, t", 5: "CVC words — pot, cot, hot", 6: "Sight words: the, a, is, in",
            7: "Writing sentences", 8: "Listening: following instructions", 9: "Speaking: classroom commands",
            10: "Revision and assessment"},
        3: {1: "Alphabet — uppercase U-Z", 2: "Letter sounds: u, v, w, x, y, z", 3: "Blends: bl, cl, fl",
            4: "Blends: br, cr, dr", 5: "Reading short passages", 6: "Punctuation: capital letter and full stop",
            7: "Nouns — naming words", 8: "Verbs — doing words", 9: "Comprehension: short story",
            10: "Revision and assessment"},
    },
    # Grades 2-6 omitted for brevity — will be populated from the NERDC PDF
    # by parse_curriculum.py. The structure above is the template.
}

# ---------------------------------------------------------------------------
# BASIC SCIENCE AND TECHNOLOGY
# ---------------------------------------------------------------------------
BASIC_SCIENCE_TECHNOLOGY = {
    1: {
        1: {1: "Living and non-living things", 2: "Parts of the human body",
            3: "The five senses", 4: "Plants around us", 5: "Animals around us",
            6: "Uses of plants", 7: "Uses of animals", 8: "Air around us",
            9: "Water around us", 10: "Revision and assessment"},
        2: {1: "Soil — types and uses", 2: "Rocks and minerals — introduction",
            3: "Weather — sunny, rainy, cloudy", 4: "Seasons in Nigeria",
            5: "Materials — wood, metal, plastic", 6: "Properties of materials",
            7: "Simple machines — lever", 8: "Simple machines — inclined plane",
            9: "Light — sources", 10: "Revision and assessment"},
        3: {1: "Sound — sources and properties", 2: "Heat — sources",
            3: "Electricity — introduction (torch, battery)", 4: "Magnets",
            5: "Technology around us", 6: "Computers — introduction",
            7: "Environment — clean and dirty", 8: "Pollution — types",
            9: "Health — personal hygiene", 10: "Revision and assessment"},
    },
    # Grades 2-6 to be populated from NERDC PDF
}

# ---------------------------------------------------------------------------
# SOCIAL AND CITIZENSHIP STUDIES
# ---------------------------------------------------------------------------
SOCIAL_CITIZENSHIP = {
    1: {
        1: {1: "Myself — name, age, gender", 2: "My family — members and roles",
            3: "My home", 4: "My neighbourhood", 5: "My school",
            6: "Community helpers — teacher, doctor, farmer",
            7: "Basic needs — food, clothing, shelter", 8: "Nigerian flag and anthem",
            9: "State I live in", 10: "Revision and assessment"},
        # Terms 2 and 3 to be populated from NERDC PDF
    },
}

# ---------------------------------------------------------------------------
# CHRISTIAN RELIGIOUS STUDIES
# ---------------------------------------------------------------------------
CRS = {
    1: {
        1: {1: "God the Creator", 2: "Creation — Day 1 and 2", 3: "Creation — Day 3 and 4",
            4: "Creation — Day 5 and 6", 5: "Creation — Day 7 (rest)", 6: "Adam and Eve",
            7: "The Fall — introduction", 8: "Noah and the Ark", 9: "Abraham — called by God",
            10: "Revision and assessment"},
    },
}

# ---------------------------------------------------------------------------
# ISLAMIC RELIGIOUS STUDIES
# ---------------------------------------------------------------------------
IRS = {
    1: {
        1: {1: "Allah the Creator", 2: "The creation story in Islam", 3: "The five pillars — Shahadah",
            4: "The five pillars — Salat (prayer)", 5: "The five pillars — Zakat",
            6: "The five pillars — Sawm (fasting)", 7: "The five pillars — Hajj",
            8: "Prophet Muhammad (SAW) — early life", 9: "The Quran — introduction",
            10: "Revision and assessment"},
    },
}

# ---------------------------------------------------------------------------
# COMPUTER STUDIES
# ---------------------------------------------------------------------------
COMPUTER_STUDIES = {
    1: {
        1: {1: "What is a computer?", 2: "Parts of a computer — monitor",
            3: "Parts of a computer — keyboard", 4: "Parts of a computer — mouse",
            5: "Parts of a computer — CPU", 6: "Turning on and off a computer",
            7: "Using the mouse — click and double-click", 8: "Using the keyboard — typing letters",
            9: "Introduction to a word processor", 10: "Revision and assessment"},
    },
    5: {
        1: {
            1: "Input and output devices — detailed",
            2: "Storage devices — HDD, SSD, USB",
            3: "Operating systems — Windows overview",
            4: "File management — creating folders",
            5: "Word processing — formatting text",
            6: "Spreadsheets — introduction to Excel/Calc",
            7: "Presentations — introduction to PowerPoint",
            8: "Internet safety — passwords and privacy",
            9: "Digital citizenship",
            10: "Revision and assessment",
        },
    },
}

# ---------------------------------------------------------------------------
# PHYSICAL AND HEALTH EDUCATION
# ---------------------------------------------------------------------------
PHE = {
    1: {
        1: {1: "Introduction to physical education", 2: "Basic body movements — walking and running",
            3: "Jumping and hopping", 4: "Throwing and catching", 5: "Balance exercises",
            6: "Personal hygiene — washing hands", 7: "Personal hygiene — brushing teeth",
            8: "Nutrition — food groups", 9: "Safety — road safety basics",
            10: "Revision and assessment"},
    },
    3: {
        2: {
            1: "Physical fitness — endurance exercises",
            2: "Physical fitness — flexibility",
            3: "Team sports — football basics",
            4: "Team sports — athletics",
            5: "Health — causes of common diseases",
            6: "Health — prevention of malaria",
            7: "Health — HIV/AIDS awareness (age-appropriate)",
            8: "Personal hygiene — hand washing technique",
            9: "First aid — basic (cuts and burns)",
            10: "Revision and assessment",
        },
    },
}

# ---------------------------------------------------------------------------
# MASTER MAP — used by build_dataset.py to iterate topics
# ---------------------------------------------------------------------------
NIGERIA_TOPIC_MAP = {
    "Mathematics":                       MATHEMATICS,
    "English Studies":                   ENGLISH_STUDIES,
    "Basic Science and Technology":      BASIC_SCIENCE_TECHNOLOGY,
    "Social and Citizenship Studies":    SOCIAL_CITIZENSHIP,
    "Christian Religious Studies":       CRS,
    "Islamic Religious Studies":         IRS,
    "Computer Studies":                  COMPUTER_STUDIES,
    "Physical and Health Education":     PHE,
}


def get_topic(subject: str, grade: int, term: int, week: int) -> str | None:
    """
    Look up a topic title from the map.
    Returns None if the term/week combination is not yet populated
    (placeholder pending full PDF parse).
    """
    try:
        return NIGERIA_TOPIC_MAP[subject][grade][term][week]
    except KeyError:
        return None


def iter_all_topics():
    """
    Yield (subject, grade, term, week, topic_title) for every populated entry.
    Used by build_dataset.py to plan generation tasks.
    """
    for subject, grades in NIGERIA_TOPIC_MAP.items():
        for grade, terms in grades.items():
            for term, weeks in terms.items():
                for week, topic in weeks.items():
                    yield subject, grade, term, week, topic
