"""Pilot Web UI + versioned REST API for external integration."""

from __future__ import annotations

import asyncio
import logging
import re
import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pilot
from pilot.logging_utils import setup_logging
from pilot.platform.capabilities import PLATFORM_LINE, platform_pillars
from pilot.utils import load_config
from pilot.workflow import run_pilot_pipeline
from web.portal_routes import build_knowledge_router, build_surrogate_router

_CONFIG_PATH = ROOT / "configs" / "config.yaml"
_config: dict[str, Any] = {}
_static = Path(__file__).resolve().parent / "static"
_TASK_ID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
_ALLOWED_FILES = frozenset({"s11.png", "s11.csv", "run_openems_patch.py", "mock_meta.json"})


class SimulationRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=3,
        max_length=4000,
        description="User request in natural language (English recommended for parser).",
        examples=["Design a 2.4 GHz rectangular patch antenna on FR4 and show return loss near resonance."],
    )


class SimulationRunResponse(BaseModel):
    ok: bool
    task_id: str | None = None
    state: str | None = None
    report_markdown: str | None = None
    task_spec_path: str | None = None
    report_path: str | None = None
    generated_script: str | None = None
    summary: dict[str, Any] | None = None
    pipeline_trace: list[dict[str, Any]] | None = Field(
        None,
        description="Ordered stages: parse, plan, validate, generate, execute, report — for consoles and integrators.",
    )
    error: str | None = Field(None, description="Populated when ok=false")
    artifact_urls: dict[str, str] | None = Field(
        None,
        description="Relative URLs to fetch PNG/CSV/script for this task_id.",
    )


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "pilot"
    version: str = pilot.__version__
    api: str = "v1"
    platform_line: str = Field(
        default=PLATFORM_LINE,
        description="Product line id for integrators (see docs/PLATFORM_VISION.md).",
    )
    pillars: list[dict[str, str]] = Field(
        default_factory=platform_pillars,
        description="Capability pillars: id, name, api_base_path, description.",
    )


def _ensure_logging() -> None:
    cfg = _config or load_config(_CONFIG_PATH)
    log_dir = ROOT / cfg.get("paths", {}).get("logs_dir", "logs")
    log_cfg = cfg.get("logging", {})
    if not logging.getLogger("pilot").handlers:
        setup_logging(
            log_dir,
            level=log_cfg.get("level", "INFO"),
            file_name="pilot_web.log",
        )


def _artifact_paths_relative(task_id: str | None) -> dict[str, str] | None:
    if not task_id:
        return None
    base = f"/api/v1/artifacts/{task_id}"
    return {
        "s11_plot": f"{base}/s11.png",
        "s11_csv": f"{base}/s11.csv",
        "script": f"{base}/run_openems_patch.py",
    }


async def _run_simulation(body: SimulationRequest) -> SimulationRunResponse:
    _ensure_logging()
    q = body.query.strip()
    if not q:
        raise HTTPException(400, "Empty query")

    def _work() -> dict[str, Any]:
        return run_pilot_pipeline(q, config=_config, root=ROOT)

    try:
        out = await asyncio.to_thread(_work)
    except Exception as e:
        return SimulationRunResponse(ok=False, error=str(e))

    tid = out.get("task_id")
    return SimulationRunResponse(
        ok=True,
        task_id=tid,
        state=out.get("state"),
        report_markdown=out.get("report_markdown"),
        task_spec_path=out.get("task_spec_path"),
        report_path=out.get("report_path"),
        generated_script=out.get("generated_script"),
        summary=out.get("results"),
        pipeline_trace=out.get("pipeline_trace"),
        artifact_urls=_artifact_paths_relative(tid),
    )


def create_app() -> FastAPI:
    global _config
    _config = load_config(_CONFIG_PATH)

    app = FastAPI(
        title="Pilot — AI platform API (EM)",
        description=(
            "Unified platform: knowledge corpus, simulation agent (openEMS/mock), surrogate registry. "
            "OpenAPI: `/openapi.json`, docs: `/docs`. Discovery: `GET /api/v1/health` returns `pillars`."
        ),
        version=pilot.__version__,
        contact={"name": "Pilot", "url": "https://github.com/mzsun-ai/Pilot"},
        license_info={"name": "MIT", "url": "https://github.com/mzsun-ai/Pilot/blob/main/LICENSE"},
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def _serve_html(filename: str) -> HTMLResponse:
        path = _static / filename
        if not path.is_file():
            raise HTTPException(500, f"Missing web/static/{filename}")
        return HTMLResponse(path.read_text(encoding="utf-8"))

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def hub_page() -> HTMLResponse:
        return _serve_html("hub.html")

    @app.get("/agent", response_class=HTMLResponse, include_in_schema=False)
    async def agent_page() -> HTMLResponse:
        return _serve_html("agent.html")

    @app.get("/knowledge", response_class=HTMLResponse, include_in_schema=False)
    async def knowledge_page() -> HTMLResponse:
        return _serve_html("knowledge.html")

    @app.get("/surrogate", response_class=HTMLResponse, include_in_schema=False)
    async def surrogate_page() -> HTMLResponse:
        return _serve_html("surrogate.html")

    @app.get("/guide", response_class=HTMLResponse, include_in_schema=False)
    async def user_guide() -> HTMLResponse:
        p = _static / "guide.html"
        if not p.is_file():
            raise HTTPException(500, "Missing web/static/guide.html")
        return HTMLResponse(p.read_text(encoding="utf-8"))

    @app.get("/guide/", response_class=HTMLResponse, include_in_schema=False)
    async def user_guide_slash() -> HTMLResponse:
        return await user_guide()

    @app.get("/team", response_class=HTMLResponse, include_in_schema=False)
    async def team_page() -> HTMLResponse:
        p = _static / "team.html"
        if not p.is_file():
            raise HTTPException(500, "Missing web/static/team.html")
        return HTMLResponse(p.read_text(encoding="utf-8"))

    @app.get("/team/", response_class=HTMLResponse, include_in_schema=False)
    async def team_page_slash() -> HTMLResponse:
        return await team_page()

    @app.get("/api-reference", response_class=HTMLResponse, include_in_schema=False)
    async def api_reference_page() -> HTMLResponse:
        return _serve_html("api.html")

    @app.get("/api-reference/", response_class=HTMLResponse, include_in_schema=False)
    async def api_reference_page_slash() -> HTMLResponse:
        return _serve_html("api.html")

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon() -> RedirectResponse:
        return RedirectResponse(url="/static/favicon.svg", status_code=302)

    @app.post(
        "/api/run",
        response_model=SimulationRunResponse,
        deprecated=True,
        summary="Deprecated — use POST /api/v1/simulations",
        include_in_schema=True,
        tags=["Legacy"],
    )
    async def api_run_legacy(body: SimulationRequest) -> SimulationRunResponse:
        return await _run_simulation(body)

    @app.get("/api/artifact/{task_id}/{filename}", include_in_schema=False)
    async def get_artifact_legacy(task_id: str, filename: str) -> FileResponse:
        return _serve_artifact(task_id, filename)

    v1 = APIRouter(prefix="/api/v1", tags=["Pilot API v1"])

    @v1.get("/health", response_model=HealthResponse, summary="Liveness / version probe")
    async def health() -> HealthResponse:
        return HealthResponse()

    @v1.post(
        "/simulations",
        response_model=SimulationRunResponse,
        summary="Run one simulation from natural language",
    )
    async def create_simulation(body: SimulationRequest) -> SimulationRunResponse:
        return await _run_simulation(body)

    @v1.get("/artifacts/{task_id}/{filename}", summary="Download artifact")
    async def get_artifact_v1(task_id: str, filename: str) -> FileResponse:
        return _serve_artifact(task_id, filename)

    app.include_router(v1)

    def _cfg() -> dict[str, Any]:
        return _config

    app.include_router(build_knowledge_router(ROOT, _cfg))
    app.include_router(build_surrogate_router(ROOT, _cfg))

    app.mount("/static", StaticFiles(directory=str(_static)), name="static")

    return app


def _serve_artifact(task_id: str, filename: str) -> FileResponse:
    if not _TASK_ID_RE.match(task_id):
        raise HTTPException(400, "Invalid task id")
    if filename not in _ALLOWED_FILES:
        raise HTTPException(404, "File not allowed")
    runs = ROOT / _config.get("paths", {}).get("openems_runs_dir", "outputs/openems_runs")
    path = (ROOT / runs / task_id / filename).resolve()
    try:
        path.relative_to((ROOT / runs).resolve())
    except ValueError:
        raise HTTPException(400, "Invalid path")
    if not path.is_file():
        raise HTTPException(404, "Not found")
    media = "application/octet-stream"
    if filename.endswith(".png"):
        media = "image/png"
    elif filename.endswith(".csv"):
        media = "text/csv"
    elif filename.endswith(".py"):
        media = "text/x-python; charset=utf-8"
    return FileResponse(path, media_type=media, filename=filename)


app = create_app()

RunRequest = SimulationRequest
RunResponse = SimulationRunResponse
