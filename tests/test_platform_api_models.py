"""Shared portal API models — validation boundaries."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from pilot.platform.api_models import (
    KnowledgeArxivBody,
    KnowledgeChatBody,
    KnowledgeChatMessage,
    KnowledgeIngestTextBody,
    SurrogateRegisterBody,
)


def test_surrogate_register_id_pattern() -> None:
    SurrogateRegisterBody(id="plrnet.v1", title_en="t")
    with pytest.raises(ValidationError):
        SurrogateRegisterBody(id="Bad Id", title_en="t")


def test_knowledge_ingest_text_bounds() -> None:
    KnowledgeIngestTextBody(title="Doc", text="x" * 10)
    with pytest.raises(ValidationError):
        KnowledgeIngestTextBody(title="", text="short")
    with pytest.raises(ValidationError):
        KnowledgeIngestTextBody(title="t", text="x" * 9)


def test_knowledge_chat_requires_messages() -> None:
    KnowledgeChatBody(
        messages=[
            KnowledgeChatMessage(role="user", content="hello"),
        ]
    )
    with pytest.raises(ValidationError):
        KnowledgeChatBody(messages=[])


def test_knowledge_arxiv_max_results() -> None:
    KnowledgeArxivBody(query="antenna", max_results=1)
    with pytest.raises(ValidationError):
        KnowledgeArxivBody(query="x", max_results=0)
    with pytest.raises(ValidationError):
        KnowledgeArxivBody(query="x", max_results=20)


def test_knowledge_chat_source_doc_ids_cap() -> None:
    KnowledgeChatBody(
        messages=[KnowledgeChatMessage(role="user", content="hi")],
        source_doc_ids=["a"] * 48,
    )
    with pytest.raises(ValidationError):
        KnowledgeChatBody(
            messages=[KnowledgeChatMessage(role="user", content="hi")],
            source_doc_ids=["x"] * 49,
        )


def test_surrogate_register_extended_metadata() -> None:
    b = SurrogateRegisterBody(
        id="demo.v1",
        authors=["A. Example"],
        tags=["patch"],
        scenarios=["2.4 GHz"],
    )
    d = b.model_dump()
    assert d["authors"] == ["A. Example"]
    assert d["schema_version"] == "1.0"
