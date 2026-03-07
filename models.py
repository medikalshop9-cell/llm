"""
api/models.py
AfriLearn — Pydantic request and response models for the local API.
"""

from typing import Literal
from pydantic import BaseModel, Field, field_validator


VALID_SUBJECTS_NIGERIA = {
    "English Studies",
    "Mathematics",
    "Basic Science and Technology",
    "Social and Citizenship Studies",
    "Christian Religious Studies",
    "Islamic Religious Studies",
    "Computer Studies",
    "Physical and Health Education",
}

VALID_SUBJECTS_GHANA = {
    "English Language",
    "Mathematics",
    "Science",
    "Our World and Our People",
    "Religious and Moral Education",
    "Computing",
    "Physical Education",
}


class GenerateRequest(BaseModel):
    country:    Literal["Nigeria", "Ghana"]
    subject:    str                                     = Field(..., description="Subject name — must match curriculum authority subject list")
    grade:      int                                     = Field(..., ge=1, le=6, description="Grade level: 1-6")
    term:       int | None                              = Field(None, ge=1, le=3, description="Academic term (Nigeria only): 1-3")
    week:       int | None                              = Field(None, ge=1, le=10, description="Week within term (Nigeria only): 1-10")
    strand:     str | None                              = Field(None, description="Curriculum strand (Ghana NaCCA only)")
    difficulty: Literal["easy", "medium", "hard"]      = "medium"
    student_id: str                                     = Field(..., min_length=1, max_length=64)
    student_age: int                                    = Field(..., ge=5, le=14)
    session_streak: int                                 = Field(0, ge=0)
    last_topic_score: float                             = Field(0.0, ge=0.0, le=100.0)
    prior_topic: str                                    = ""
    interaction_type: Literal["quiz", "tutor_chat"]    = "quiz"
    student_message: str | None                        = Field(None, description="Student's message (tutor_chat mode only)")
    turn_history: list[dict] | None                    = Field(None, description="Previous turns (tutor_chat multi-turn)")

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, v: str, info) -> str:
        country = info.data.get("country")
        if country == "Nigeria" and v not in VALID_SUBJECTS_NIGERIA:
            raise ValueError(
                f"'{v}' is not a valid Nigeria NERDC subject. "
                f"Valid subjects: {sorted(VALID_SUBJECTS_NIGERIA)}"
            )
        if country == "Ghana" and v not in VALID_SUBJECTS_GHANA:
            raise ValueError(
                f"'{v}' is not a valid Ghana NaCCA subject. "
                f"Valid subjects: {sorted(VALID_SUBJECTS_GHANA)}"
            )
        return v

    @field_validator("term", "week")
    @classmethod
    def validate_nigeria_fields(cls, v, info):
        country = info.data.get("country")
        if country == "Nigeria" and v is None:
            raise ValueError("term and week are required for Nigeria curriculum")
        return v


class GenerateResponse(BaseModel):
    response:        str
    model:           str
    country:         str
    subject:         str
    grade:           int
    difficulty:      str
    curriculum_ref:  str | None
    format_valid:    bool
    format_errors:   list[str]


class HealthResponse(BaseModel):
    status:  Literal["ok", "degraded"]
    model:   str
    rag:     bool
    version: str = "1.0.0"
