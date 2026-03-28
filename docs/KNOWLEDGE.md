# Knowledge pillar

## Purpose

Provide **retrieval-grounded** answers over a **local corpus** (uploads, pasted text, arXiv-fetched papers). Optional LLM composes answers; retrieval runs regardless.

## Code

- Implementation: `pilot/knowledge_service.py` (`KnowledgeCorpus`, `complete_chat`, `ingest_arxiv_to_corpus`).
- HTTP: `web/portal_routes.py` → prefix `/api/v1/knowledge`.

## Storage layout

Under `outputs/knowledge_corpus/` (configurable via `paths.outputs_dir`):

| Path | Content |
|------|---------|
| `manifest.json` | List of documents (id, title, source tag, paths, timestamps). |
| `chunks.jsonl` | One JSON object per line: chunk text, doc id, scores metadata. |
| `uploads/` | Raw uploaded files. |

## Configuration (`configs/config.yaml` → `knowledge`)

| Key | Meaning |
|-----|---------|
| `chunk_size` | Target characters per chunk. |
| `chunk_overlap` | Overlap between consecutive chunks. |
| `llm_provider` | `none` \| `ollama` \| `openai` (see code for exact strings). |
| `ollama_*` / `openai_*` | Endpoints and models when LLM enabled. |

## API (summary)

- `GET /sources` — document list from manifest.
- `POST /upload` — multipart file ingest (PDF/text via pypdf).
- `POST /ingest-text` — JSON title + body.
- `POST /chat` — messages array; last user message drives retrieval + optional LLM. Optional `source_doc_ids` restricts retrieval to selected manifest documents (empty = full corpus). Responses include `citations` (chunk id, doc id, source, score, text preview).
- `POST /fetch-arxiv` — query + max_results → ingest summaries.

## Extension points (roadmap)

- Vector embeddings + hybrid search.
- Per-message **citations** (chunk ids in response).
- **Filters** by document id / tag / date.
- Pluggable **readers** (more formats, URL fetch with safeguards).

## Operational notes

- Corpus is **process-local**; multiple uvicorn workers do not share in-memory corpus — use one worker or externalize index later.
- Large PDFs: watch memory; 25 MB upload limit enforced in routes.
