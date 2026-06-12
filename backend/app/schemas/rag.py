"""Schemas for RAG endpoints."""

from pydantic import BaseModel, Field, field_validator


class QaRequest(BaseModel):
    question: str
    top_k: int = Field(default=5, ge=1, le=10)
    temperature: float = Field(default=0.7, ge=0.0, le=1.5)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("question 不能为空")
        return stripped


class SummaryRequest(BaseModel):
    text: str
    temperature: float = Field(default=0.5, ge=0.0, le=1.5)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("text 不能为空")
        return stripped


