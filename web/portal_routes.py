"""Portal APIs: Pilot Knowledge (RAG + chat) and Surrogate catalog."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from pilot.knowledge_service import KnowledgeCorpus, complete_chat, ingest_arxiv_to_corpus
from pilot.platform.api_models import (
    KnowledgeArxivBody,
    KnowledgeChatBody,
    KnowledgeIngestTextBody,
    SurrogateRegisterBody,
)


def _get_corpus(request: Request, root: Path, get_config: Callable[[], dict[str, Any]]) -> KnowledgeCorpus:
    key = "_knowledge_corpus"
    if not hasattr(request.app.state, key):
        setattr(request.app.state, key, KnowledgeCorpus(root, get_config()))
    return getattr(request.app.state, key)


def build_knowledge_router(root: Path, get_config: Callable[[], dict[str, Any]]) -> APIRouter:
    r = APIRouter(prefix="/api/v1/knowledge", tags=["Pilot Knowledge"])

    @r.get("/sources")
    async def list_sources(request: Request) -> dict[str, Any]:
        c = _get_corpus(request, root, get_config)
        return {"documents": c.list_sources()}

    @r.post("/upload")
    async def upload(request: Request, file: UploadFile = File(...)) -> dict[str, Any]:
        c = _get_corpus(request, root, get_config)
        raw = await file.read()
        if len(raw) > 25 * 1024 * 1024:
            raise HTTPException(413, "File too large (max 25 MB)")
        out = c.ingest_file(file.filename or "upload.bin", raw)
        if not out.get("ok"):
            raise HTTPException(400, out.get("error", "ingest failed"))
        return out

    @r.post("/ingest-text")
    async def ingest_text(request: Request, body: KnowledgeIngestTextBody) -> dict[str, Any]:
        c = _get_corpus(request, root, get_config)
        out = c.ingest_text(body.title, body.text, source_tag="paste")
        if not out.get("ok"):
            raise HTTPException(400, out.get("error", "ingest failed"))
        return out

    @r.post("/chat")
    async def chat(request: Request, body: KnowledgeChatBody) -> dict[str, Any]:
        c = _get_corpus(request, root, get_config)
        cfg = get_config()
        msgs = [m.model_dump() for m in body.messages]
        last_user = next((m["content"] for m in reversed(msgs) if m.get("role") == "user"), "")
        if not last_user.strip():
            raise HTTPException(400, "Need a user message")
        return await complete_chat(
            cfg,
            msgs,
            last_user.strip(),
            c,
            source_doc_ids=body.source_doc_ids or None,
        )

    @r.post("/fetch-arxiv")
    async def fetch_arxiv(request: Request, body: KnowledgeArxivBody) -> dict[str, Any]:
        import asyncio

        c = _get_corpus(request, root, get_config)

        def _work() -> dict[str, Any]:
            return ingest_arxiv_to_corpus(c, body.query, max_results=body.max_results)

        return await asyncio.to_thread(_work)

    return r


def _catalog_path(root: Path) -> Path:
    p = root / "data" / "surrogates_catalog.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text('{"items": []}', encoding="utf-8")
    return p


def build_surrogate_router(root: Path, get_config: Callable[[], dict[str, Any]]) -> APIRouter:
    r = APIRouter(prefix="/api/v1/surrogates", tags=["Pilot Surrogate"])

    @r.get("/list")
    async def list_items() -> dict[str, Any]:
        path = _catalog_path(root)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            data = {"items": []}
        return {"items": data.get("items", [])}

    @r.post("/register")
    async def register(body: SurrogateRegisterBody, request: Request) -> dict[str, Any]:
        cfg = get_config()
        key = (cfg.get("surrogate") or {}).get("admin_register_key") or ""
        if key:
            got = request.headers.get("X-Pilot-Register-Key", "")
            if got != key:
                raise HTTPException(403, "Invalid or missing X-Pilot-Register-Key")
        path = _catalog_path(root)
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data.setdefault("items", [])
        if any(x.get("id") == body.id for x in items):
            raise HTTPException(409, "id already exists")
        items.append(body.model_dump())
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"ok": True, "id": body.id}

    @r.post("/upload-bundle")
    async def upload_bundle(
        request: Request,
        surrogate_id: str = Form(...),
        bundle: UploadFile = File(...),
    ) -> dict[str, Any]:
        cfg = get_config()
        key = (cfg.get("surrogate") or {}).get("admin_register_key") or ""
        if key:
            got = request.headers.get("X-Pilot-Register-Key", "")
            if got != key:
                raise HTTPException(403, "Invalid or missing X-Pilot-Register-Key")
        if not re.match(r"^[a-z0-9._-]+$", surrogate_id):
            raise HTTPException(400, "bad surrogate_id")
        dest_dir = root / "outputs" / "surrogate_bundles"
        dest_dir.mkdir(parents=True, exist_ok=True)
        fname = re.sub(r"[^\w.\-]", "_", bundle.filename or "bundle.zip")[:120]
        out_path = dest_dir / f"{surrogate_id}_{fname}"
        raw = await bundle.read()
        if len(raw) > 100 * 1024 * 1024:
            raise HTTPException(413, "max 100 MB")
        out_path.write_bytes(raw)
        rel = f"/api/v1/surrogates/download/{surrogate_id}/{fname}"
        return {"ok": True, "path": str(out_path.relative_to(root)), "url": rel}

    @r.get("/download/{surrogate_id}/{filename}")
    async def download_bundle(surrogate_id: str, filename: str) -> Any:
        if not re.match(r"^[a-z0-9._-]+$", surrogate_id):
            raise HTTPException(400, "bad id")
        if not re.match(r"^[\w.\-]+$", filename):
            raise HTTPException(400, "bad filename")
        p = (root / "outputs" / "surrogate_bundles" / f"{surrogate_id}_{filename}").resolve()
        try:
            p.relative_to((root / "outputs" / "surrogate_bundles").resolve())
        except ValueError:
            raise HTTPException(400, "invalid path")
        if not p.is_file():
            raise HTTPException(404, "not found")
        from fastapi.responses import FileResponse

        return FileResponse(p, filename=filename)

    return r
