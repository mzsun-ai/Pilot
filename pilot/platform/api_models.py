"""Pydantic models for HTTP request bodies shared by portal routes (knowledge, surrogate)."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class KnowledgeIngestTextBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    text: str = Field(..., min_length=10, max_length=500_000)


class KnowledgeChatMessage(BaseModel):
    role: str
    content: str


class KnowledgeChatBody(BaseModel):
    messages: list[KnowledgeChatMessage] = Field(..., min_length=1)
    source_doc_ids: list[str] = Field(
        default_factory=list,
        description="Restrict retrieval to these corpus document IDs; empty means all sources.",
    )

    @field_validator("source_doc_ids")
    @classmethod
    def _normalize_doc_ids(cls, v: list[str]) -> list[str]:
        out = [x.strip() for x in v if x and str(x).strip()]
        if len(out) > 48:
            raise ValueError("at most 48 source_doc_ids")
        return out


class KnowledgeArxivBody(BaseModel):
    query: str = Field(..., min_length=2, max_length=400)
    max_results: int = Field(3, ge=1, le=15)


class SurrogateRegisterBody(BaseModel):
    id: str = Field(..., min_length=2, max_length=80, pattern=r"^[a-z0-9._-]+$")
    schema_version: str = Field("1.0", max_length=32, description="Registry entry schema version for migrations.")
    title_en: str = Field("", max_length=300)
    title_zh: str = Field("", max_length=300)
    desc_en: str = Field("", max_length=4000)
    desc_zh: str = Field("", max_length=4000)
    paper_url: str = ""
    code_url: str = ""
    authors: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    scenarios: list[str] = Field(
        default_factory=list,
        description="Short labels for task or geometry regimes where the surrogate applies.",
    )
