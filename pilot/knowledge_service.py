"""Pilot Knowledge — local corpus, chunking, keyword retrieval, optional LLM chat."""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any, Optional, Sequence

from pilot.logging_utils import get_logger

_LOG = get_logger("pilot.knowledge")


def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return []
    chunks: list[str] = []
    i = 0
    while i < len(text):
        end = min(i + chunk_size, len(text))
        piece = text[i:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        i = max(end - overlap, i + 1)
    return chunks


def _tokenize(q: str) -> set[str]:
    qn = q.lower()
    tokens = {t for t in re.split(r"[^\w+.-]+", qn) if len(t) > 1}
    for ch in re.findall(r"[\u3040-\u30ff\u4e00-\u9fff\uac00-\ud7af]", q):
        tokens.add(ch)
    for bg in re.findall(r"[\u3040-\u30ff\u4e00-\u9fff\uac00-\ud7af]{2}", q):
        tokens.add(bg)
    return tokens


def _score_chunk(query_tokens: set[str], text: str) -> float:
    if not query_tokens:
        return 0.0
    tl = text.lower()
    return sum(tl.count(tok) for tok in query_tokens)


class KnowledgeCorpus:
    def __init__(self, root: Path, cfg: dict[str, Any]):
        self.root = root
        kcfg = cfg.get("knowledge") or {}
        self.chunk_size = int(kcfg.get("chunk_size", 900))
        self.chunk_overlap = int(kcfg.get("chunk_overlap", 120))
        self.corpus_dir = root / "outputs" / "knowledge_corpus"
        self.uploads_dir = self.corpus_dir / "uploads"
        self.chunks_path = self.corpus_dir / "chunks.jsonl"
        self.manifest_path = self.corpus_dir / "manifest.json"
        self.corpus_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        if not self.manifest_path.exists():
            self.manifest_path.write_text(json.dumps({"documents": []}, indent=2), encoding="utf-8")

    def _load_manifest(self) -> dict[str, Any]:
        try:
            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except Exception:
            return {"documents": []}

    def _save_manifest(self, m: dict[str, Any]) -> None:
        self.manifest_path.write_text(json.dumps(m, indent=2), encoding="utf-8")

    def _load_chunks(self) -> list[dict[str, Any]]:
        if not self.chunks_path.exists():
            return []
        out: list[dict[str, Any]] = []
        with self.chunks_path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return out

    def _append_chunks(self, rows: list[dict[str, Any]]) -> None:
        with self.chunks_path.open("a", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def list_sources(self) -> list[dict[str, Any]]:
        return list(self._load_manifest().get("documents", []))

    def ingest_text(
        self,
        title: str,
        text: str,
        source_tag: str = "paste",
        doc_id: Optional[str] = None,
    ) -> dict[str, Any]:
        doc_id = doc_id or str(uuid.uuid4())
        chunks = _chunk_text(text, self.chunk_size, self.chunk_overlap)
        if not chunks:
            return {"ok": False, "error": "empty text"}
        rows = [
            {
                "id": f"{doc_id}_{i}",
                "doc_id": doc_id,
                "text": c,
                "source": title,
                "source_tag": source_tag,
            }
            for i, c in enumerate(chunks)
        ]
        self._append_chunks(rows)
        m = self._load_manifest()
        m.setdefault("documents", []).append(
            {
                "doc_id": doc_id,
                "title": title,
                "source_tag": source_tag,
                "chunks": len(chunks),
            }
        )
        self._save_manifest(m)
        _LOG.info("Ingested text doc %s (%s chunks)", doc_id, len(chunks))
        return {"ok": True, "doc_id": doc_id, "chunks": len(chunks)}

    def ingest_file(self, filename: str, raw: bytes) -> dict[str, Any]:
        doc_id = str(uuid.uuid4())
        safe_name = re.sub(r"[^\w.\-]", "_", filename)[:180]
        up_path = self.uploads_dir / f"{doc_id}_{safe_name}"
        up_path.write_bytes(raw)
        ext = safe_name.lower().split(".")[-1] if "." in safe_name else ""
        text = ""
        if ext in ("txt", "md", "csv", "py", "json"):
            try:
                text = raw.decode("utf-8", errors="replace")
            except Exception:
                text = ""
        elif ext == "pdf":
            text = _extract_pdf_text(raw)
        elif ext in ("png", "jpg", "jpeg", "webp", "gif"):
            text = (
                f"[Image file uploaded: {filename}. "
                "OCR / vision is not enabled — describe the figure in chat or paste text.]"
            )
        else:
            text = f"[Binary or unknown type: {filename}. Convert to PDF or TXT for full-text ingestion.]"

        if not text.strip():
            text = f"[No extractable text from {filename}.]"

        return self.ingest_text(
            title=f"{safe_name} (upload)",
            text=text,
            source_tag=f"file:{ext or 'bin'}",
            doc_id=doc_id,
        )

    def search(
        self,
        query: str,
        top_k: int = 8,
        *,
        doc_ids: Optional[set[str]] = None,
    ) -> list[dict[str, Any]]:
        qtok = _tokenize(query)
        chunks = self._load_chunks()
        scored: list[tuple[float, dict[str, Any]]] = []
        for ch in chunks:
            if doc_ids is not None:
                did = str(ch.get("doc_id") or "")
                if did not in doc_ids:
                    continue
            s = _score_chunk(qtok, ch.get("text", ""))
            if s > 0:
                scored.append((s, ch))
        scored.sort(key=lambda x: -x[0])
        out = []
        for s, ch in scored[:top_k]:
            out.append(
                {
                    "score": s,
                    "text": ch.get("text", "")[:1200],
                    "source": ch.get("source", ""),
                    "id": ch.get("id", ""),
                    "doc_id": ch.get("doc_id", "") or "",
                }
            )
        return out

    def build_rag_prompt(
        self,
        user_message: str,
        history_note: str = "",
        *,
        source_doc_ids: Optional[Sequence[str]] = None,
    ) -> tuple[str, list[dict[str, Any]]]:
        filt: set[str] | None = None
        if source_doc_ids:
            filt = {str(x).strip() for x in source_doc_ids if str(x).strip()}
            if not filt:
                filt = None
        hits = self.search(user_message, top_k=6, doc_ids=filt)
        ctx = "\n\n---\n\n".join(f"[{h['source']}]\n{h['text']}" for h in hits) or "(no matching corpus chunks.)"
        system = (
            "You are Pilot Knowledge, an expert assistant for computational electromagnetics, antennas, "
            "FDTD (e.g. openEMS), materials, and simulation workflows. "
            "Use the CONTEXT below when relevant.\n\nCONTEXT:\n" + ctx
        )
        if history_note.strip():
            system += "\n\nRecent dialogue:\n" + history_note.strip()
        return system, hits


def _extract_pdf_text(raw: bytes) -> str:
    try:
        from io import BytesIO

        from pypdf import PdfReader

        reader = PdfReader(BytesIO(raw))
        parts: list[str] = []
        for page in reader.pages[:80]:
            t = page.extract_text()
            if t:
                parts.append(t)
        return "\n".join(parts) if parts else ""
    except Exception as e:
        _LOG.warning("PDF extract failed: %s", e)
        return f"[PDF text extraction failed: {e}. Try TXT or smaller PDF.]"


def _cjk_pat() -> str:
    return r"[\u3040-\u30ff\u4e00-\u9fff\uac00-\ud7af]"


async def complete_chat(
    cfg: dict[str, Any],
    messages: list[dict[str, str]],
    user_last: str,
    corpus: KnowledgeCorpus,
    *,
    source_doc_ids: Optional[Sequence[str]] = None,
) -> dict[str, Any]:
    kcfg = cfg.get("knowledge") or {}
    provider = str(kcfg.get("llm_provider", "none")).lower().strip()

    hist = ""
    for m in messages[-8:]:
        role = m.get("role", "user")
        content = (m.get("content") or "")[:2000]
        hist += f"{role}: {content}\n"

    system_msg, hits = corpus.build_rag_prompt(
        user_last, history_note=hist, source_doc_ids=source_doc_ids
    )
    cjk = bool(re.search(_cjk_pat(), user_last))

    if provider in ("none", ""):
        if cjk:
            intro = (
                "你好！我是 **Pilot Knowledge**。当前为「无大模型」模式：下面会列出关键词检索结果；"
                "可先 **上传 PDF / 文本** 或 **拉取 arXiv**，或在 `configs/config.yaml` 配置 `ollama` / `openai_compat`。\n\n"
            )
            empty_msg = "_暂无本地片段命中 — 请上传资料或拉取 arXiv 后再问。_"
            foot = (
                "**未配置对话 LLM。** 在 `configs/config.yaml` 设置 `knowledge.llm_provider` 为 `ollama` 或 `openai_compat`。"
            )
        else:
            intro = (
                "**Hi — Pilot Knowledge.** No-LLM mode: keyword retrieval below. Try **Upload** / **Fetch arXiv** "
                "or set `knowledge.llm_provider` in config.\n\n"
            )
            empty_msg = "_No local chunks matched yet — upload or fetch arXiv first._"
            foot = "**LLM not configured.** Set `knowledge.llm_provider` to `ollama` or `openai_compat` in config."

        return {
            "ok": True,
            "role": "assistant",
            "content": (
                intro
                + "### Retrieved context (keyword RAG)\n\n"
                + (
                    "\n\n".join(
                        f"- **{h['source']}** (score {h['score']:.1f}): _{h['text'][:400]}…_" for h in hits
                    )
                    if hits
                    else empty_msg
                )
                + "\n\n---\n\n"
                + foot
            ),
            "citations": hits,
            "provider": "none",
        }

    import httpx

    if provider == "ollama":
        base = kcfg.get("ollama_base", "http://127.0.0.1:11434").rstrip("/")
        model = kcfg.get("ollama_model", "llama3.2")
        omsg = [{"role": "system", "content": system_msg}] + [
            {"role": m["role"], "content": m["content"]}
            for m in messages[-6:]
            if m.get("role") in ("user", "assistant") and (m.get("content") or "").strip()
        ]
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                r = await client.post(
                    f"{base}/api/chat",
                    json={"model": model, "messages": omsg, "stream": False},
                )
                r.raise_for_status()
                data = r.json()
                txt = (data.get("message") or {}).get("content") or str(data)
                return {"ok": True, "role": "assistant", "content": txt, "citations": hits, "provider": "ollama"}
        except Exception as e:
            _LOG.exception("Ollama chat failed")
            return {
                "ok": False,
                "role": "assistant",
                "content": f"Ollama error: {e}",
                "citations": hits,
                "provider": "ollama",
            }

    if provider == "openai_compat":
        base = kcfg.get("openai_base", "https://api.openai.com/v1").rstrip("/")
        key = kcfg.get("openai_api_key") or ""
        model = kcfg.get("openai_model", "gpt-4o-mini")
        omsg = [{"role": "system", "content": system_msg}] + [
            {"role": m["role"], "content": m["content"]}
            for m in messages[-12:]
            if m.get("role") in ("user", "assistant") and (m.get("content") or "").strip()
        ]
        if not key:
            return {"ok": False, "role": "assistant", "content": "Missing openai_api_key in config.", "citations": hits}
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                r = await client.post(
                    f"{base}/chat/completions",
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={"model": model, "messages": omsg, "temperature": 0.3},
                )
                r.raise_for_status()
                data = r.json()
                txt = data["choices"][0]["message"]["content"]
                return {"ok": True, "role": "assistant", "content": txt, "citations": hits, "provider": "openai_compat"}
        except Exception as e:
            _LOG.exception("OpenAI-compat chat failed")
            return {"ok": False, "role": "assistant", "content": f"API error: {e}", "citations": hits}

    return {"ok": False, "role": "assistant", "content": f"Unknown llm_provider: {provider}", "citations": []}


def fetch_arxiv_summaries(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    import urllib.parse
    import xml.etree.ElementTree as ET
    from urllib.request import urlopen

    q = urllib.parse.quote(query)
    url = f"http://export.arxiv.org/api/query?search_query=all:{q}&start=0&max_results={max_results}"
    try:
        with urlopen(url, timeout=30) as resp:
            xml_data = resp.read()
    except Exception as e:
        return [{"error": str(e)}]

    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_data)
    out: list[dict[str, Any]] = []
    for ent in root.findall("a:entry", ns):
        title = (ent.find("a:title", ns).text or "").strip().replace("\n", " ")
        aid = (ent.find("a:id", ns).text or "").strip()
        summ_el = ent.find("a:summary", ns)
        summary = (summ_el.text or "").strip().replace("\n", " ")[:1500]
        out.append({"title": title, "id": aid, "summary": summary})
    return out


def ingest_arxiv_to_corpus(corpus: KnowledgeCorpus, query: str, max_results: int = 3) -> dict[str, Any]:
    items = fetch_arxiv_summaries(query, max_results=max_results)
    n = 0
    for it in items:
        if "error" in it:
            return {"ok": False, "error": it["error"]}
        title = it.get("title", "arXiv")
        body = f"{it.get('summary', '')}\n\nURL: {it.get('id', '')}"
        r = corpus.ingest_text(title=f"arXiv: {title[:200]}", text=body, source_tag="arxiv")
        if r.get("ok"):
            n += 1
    return {"ok": True, "ingested": n, "items": len(items)}
