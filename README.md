# PE Institutional Memory MVP

This repository is a local-first private equity research system that is evolving from a document RAG demo into a more realistic PE knowledge operating system.

The target shape is:

`SQLite facts + DuckDB analytics + local files + MemPalace semantic memory + skills lifecycle`

It is not an autonomous investment engine. It is an evidence-first assistant for analysts, investors, and partners.

## Current Scope

The codebase now supports the Phase 1 foundation:

- FastAPI backend for ingestion, retrieval, and chat
- `docling` parsing with Markdown table preservation
- Qdrant vector search with metadata filtering
- SQLite system of record for documents, chunks, deals, contacts, tasks, provenance, and audit logs
- DuckDB analytics warehouse for parsed chunks, extracted tables, and workflow analysis outputs
- Local workspace layout for raw documents, parsed artifacts, reports, postmortems, and skill files
- MemPalace-compatible semantic memory export path for workflow summaries and reusable learnings
- OpenAI-compatible chat client that can point either to:
  - local open-source inference servers such as `vLLM` / `Ollama` / `LM Studio`
  - hosted LLM providers using the same API shape

## Architecture Direction

The intended PE-oriented architecture is:

1. SQLite owns business facts and workflow state
2. DuckDB owns analytical tables and heavy comparisons
3. Local filesystem owns raw documents and parsed artifacts
4. MemPalace owns semantic recall and cross-project experience
5. Skills own procedural memory and postmortem promotion

See [Open Source Architecture](./docs/open_source_architecture.md) for the detailed target design.

## Data Model

The backend now includes the minimum institutional objects needed beyond plain document RAG:

- `Document`: uploaded file metadata
- `Chunk`: parsed evidence unit for retrieval
- `Deal`: canonical deal shell for future precedent and outcome analysis
- `Company`: structured company registry
- `Contact`: people linked to companies and deals
- `DealDocumentLink`: link between a deal and supporting documents
- `DocumentProvenance`: hash, source path, language, document type, metadata
- `OutcomeSnapshot`: realized or interim investment outcomes
- `PipelineTask`: workflow and task tracking
- `ChatLog`: user query and assistant response
- `RetrievalTrace`: prompt version, model, selected docs, retrieved chunk references
- `WorkflowRun`: persisted IC copilot runs and outputs
- `SemanticMemory`: MemPalace-oriented summary writebacks
- `SkillRecord`: candidate and blessed workflow skills
- `AuditLog`: append-only local audit trail

## LLM Modes

The system uses the OpenAI Python client against any OpenAI-compatible endpoint.

### Mode A: local open-source inference

Examples:

- `vLLM`
- `Ollama` behind an OpenAI-compatible gateway
- `LM Studio`

Example `.env`:

```env
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=http://localhost:8001/v1
LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
LLM_API_KEY=
```

### Mode B: hosted provider

Example `.env`:

```env
LLM_PROVIDER=provider
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=your_provider_api_key_here
```

## Recommended Open-Source Stack

For this local-first PE workstation, the recommended stack is:

- Inference: `vLLM`
- Embeddings: `fastembed` or `sentence-transformers`
- Vector store: `Qdrant`
- Parser: `docling`
- System of record: `SQLite`
- Analytics: `DuckDB`
- Semantic recall: `MemPalace`
- Skills lifecycle: filesystem-backed Markdown skills

This repository now implements the local core. Qdrant remains the retrieval engine; Neo4j and other heavier services are optional extensions, not the default spine.

## Local Infrastructure

This application is designed to be a zero-config packaged application. It requires **no external databases or Docker containers**.

- **System of Record**: SQLite (`./data/app.db`)
- **Vector Search**: Embedded Vector DB (LanceDB - coming soon to replace Qdrant)
- **Document Parser**: In-process `docling`

## Run The Developer MVP

Until the single-file executable is built, you can run the developer MVP locally:

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure LLM

```bash
cp .env.example .env
```

Open `.env` and set your `LLM_API_KEY` (or configure a local provider like vLLM). No database configuration is required.

### 3. Start the application

Start the FastAPI backend with the Vite React frontend:

**Terminal 1 (Backend):**
```bash
uvicorn backend.main:app --reload
```

**Terminal 2 (Frontend):**
```bash
npm run dev
```

The application will be available at `http://localhost:5173`.

## API Summary

### `POST /deals`

Create a canonical deal shell.

### `GET /deals`

List deals.

### `POST /upload`

Upload a document, store it under `workspace/deals/.../raw`, parse it into `parsed/`, store evidence in SQLite, mirror chunk tables into DuckDB, and index it in Qdrant.

Important form fields:

- `file`
- `tags`
- `category`
- `deal_outcome`
- `deal_id`
- `document_type`
- `language`
- `metadata_json`

### `POST /chat`

Ask an evidence-grounded question.

Request body supports:

- `query`
- `doc_ids`
- `analysis_mode`
- `filters.categories`
- `filters.deal_outcomes`

The response includes:

- `answer`
- `sources`
- `prompt_version`
- `model_name`

### `POST /precedents`

Returns grouped precedent evidence buckets such as `invested`, `passed`, and `exited`.

### `POST /workflow/run`

Runs the IC copilot workflow pack:

- precedent scan
- risk gaps
- diligence questions
- IC memo outline
- committee challenge prompts
- writes a report to `workspace/deals/.../outputs`
- writes a postmortem to `workspace/postmortems`
- exports a semantic memory artifact to `workspace/mempalace/exports`
- creates a candidate skill in `workspace/skills/candidate`

### `GET /workflow/runs`

Lists recent persisted workflow runs.

### `GET /skills`

Lists persisted skill candidates and promoted skills tracked in SQLite.

### `GET /connectors/local`

Scans a local connector directory and returns ingestible document candidates.

## Notes

- Existing SQLite files created before the new schema will not auto-migrate columns or tables. For local development, the simplest reset is to remove `workspace/sqlite/pe_core.db` and restart.
- Page-level precision is still limited by the current `docling` integration because the parser does not yet surface page numbers reliably in this implementation.
- The React frontend under `src/` and the Streamlit frontend under [`frontend/app.py`](/Users/chaoyanchen/Desktop/pe-llm-knowledge-base/frontend/app.py) are both wired to the live FastAPI backend.
