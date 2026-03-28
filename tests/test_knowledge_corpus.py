"""Knowledge corpus retrieval and document filters."""

from __future__ import annotations

from pilot.knowledge_service import KnowledgeCorpus


def test_knowledge_search_respects_doc_filter(tmp_path) -> None:
    cfg = {"knowledge": {"chunk_size": 200, "chunk_overlap": 20}}
    c = KnowledgeCorpus(tmp_path, cfg)
    out_a = c.ingest_text("Doc A", "patch antenna resonance microstrip FR4", source_tag="t")
    out_b = c.ingest_text("Doc B", "waveguide mode cutoff TE10 hollow", source_tag="t")
    id_a, id_b = out_a["doc_id"], out_b["doc_id"]
    assert c.search("patch antenna", top_k=5, doc_ids={id_a})
    assert not c.search("patch antenna", top_k=5, doc_ids={id_b})


def test_search_includes_doc_id_on_hits(tmp_path) -> None:
    cfg = {"knowledge": {"chunk_size": 120, "chunk_overlap": 10}}
    c = KnowledgeCorpus(tmp_path, cfg)
    doc_id = c.ingest_text("One", "microstrip patch 2.4 GHz FR4", source_tag="t")["doc_id"]
    hits = c.search("microstrip", top_k=3)
    assert hits and hits[0].get("doc_id") == doc_id
