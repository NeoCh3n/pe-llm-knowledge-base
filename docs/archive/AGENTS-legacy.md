# AGENTS.md

## Project Context: Private Equity Local RAG MVP

This repository implements a **local-first Retrieval-Augmented Generation (RAG)** MVP designed for **Private Equity (PE) Analysts / Associates** to search across **5–10 complex financial documents (PDF/DOCX)** quickly and safely.

**Core value:** “Save 30 minutes of manual searching.”  
**Primary KPI:** **Citation accuracy and verifiability** (Document + Page + Evidence), not creativity.

This project is intentionally scoped as a **research/reading assistant**. It is **not** an autonomous decision maker and does not provide investment advice.

---

## 1) Goal & Philosophy

### Objective
- Provide fast answers grounded in internal documents.
- Preserve **tables** and quantitative content for verification.
- Output **strict citations** and surface the raw evidence so the user can validate against the original document.

### Non-goals (Explicit)
- No autonomous investment decisions, scoring, ranking, or “recommend to invest” outputs.
- No “creative” writing. Avoid speculation.
- No hidden reasoning requirements. We prefer **auditable evidence** over verbose chain-of-thought.

### Design Principles
1. **Evidence-first**: If a claim is not supported by retrieved context, say so.
2. **Local privacy-first**: Documents stay local; Qdrant runs via Docker locally.
3. **Tables must survive**: Use `docling` → Markdown export; do not flatten tables into plain text.
4. **Deterministic demo**: Temperature is fixed at `0` for consistent responses.
5. **Computations are explicit**: If asked for a calculation, compute **step-by-step** using only numbers in context.
6. **Decision trace-lite** (MVP): Log inputs/outputs and provenance at the system level:
   - doc hash / id, page numbers, retrieved chunk ids, prompt id/version, model, timestamps.
   This is *not* full “investment decision accountability,” but it is the minimum provenance needed for trust.

---

## 2) What “Agents” Mean Here

In this MVP, “agents” are **bounded services/modules** (not autonomous multi-agent systems) with clear responsibilities and hard constraints. Each agent must:
- Produce outputs with **source provenance**
- Avoid fabricating facts
- Be compatible with the repo structure under `backend/services/`

**Agents do not**:
- Execute trades
- Make final investment decisions
- Invent numbers, tables, or citations

---

## 3) Tech Stack (Runtime Contracts)

- Language: Python 3.10+
- Backend: FastAPI
- Frontend: Streamlit
- Parsing: `docling` (Markdown export to preserve tables)
- Vector DB: Qdrant (Docker)
- Metadata DB: SQLite (SQLAlchemy)
- LLM: OpenAI-compatible API (local via vLLM/Ollama or OpenAI for testing)

---

## 4) MVP Agent Set

### 4.1 Ingestion Coordinator Agent (API-Orchestrated)
**Location:** `backend/main.py` + service calls  
**Purpose:** Coordinate upload → parse → store → embed → index.

**Responsibilities**
- Receive uploaded files + tags
- Persist file (local disk)
- Create `Document` record (UUID, filename, timestamp, tags)
- Invoke Parser Agent and Vector Index Agent
- Store `Chunk` records (content + page_number + chunk_index + FK to document)

**Must log**
- document_id, filename, upload_timestamp, tags
- ingestion status and errors

**Must NOT**
- Generate answers
- “Interpret” documents beyond orchestration

---

### 4.2 Parser Agent (Table-Preserving Document Parser) — *Most Critical*
**Location:** `backend/services/parser.py`  
**Purpose:** Convert documents into Markdown chunks with preserved table structure.

**Core Requirement**
- Use `docling` to parse PDFs and export **Markdown**.
- Maintain Markdown tables as tables; do not flatten or lose formatting.

**Function Contract**
`parse_and_chunk(file_path) -> List[ChunkPayload]`

**Chunking Rules**
- Split by headers / logical sections
- Target ~500–800 tokens per chunk
- Ensure a Markdown table stays in a single chunk where possible
- Attach metadata: page number, section header, chunk_index

**Outputs**
A list of payloads:
```json
{
  "content": "markdown text (tables preserved)",
  "page_number": 12,
  "chunk_index": 7,
  "section": "Financial Highlights"
}

Must NOT
	•	Summarize, infer, or compute
	•	“Fix” numbers
	•	Drop tables or reorder rows/columns

⸻

4.3 Vector Index Agent (Embedding + Qdrant Upsert)

Location: backend/services/vector.py
Purpose: Embed chunks and store them in Qdrant for retrieval.

Responsibilities
	•	Initialize Qdrant client (local Docker)
	•	Ensure collection exists: pe_docs
	•	Embed chunk content via local embedding model (fastembed or sentence-transformers)
	•	Upsert points with payload metadata:
	•	doc_id, filename, page_num, chunk_index

Functions
	•	upsert_chunks(chunks, doc_meta)
	•	search(query, doc_ids=None, top_k=5)

Filtering Rule
If doc_ids is provided, apply Qdrant filters to restrict retrieval.

Must NOT
	•	Call the LLM
	•	Alter chunk content
	•	Add interpretations to payload beyond provenance fields

⸻

4.4 Retriever Agent (Query → Evidence Pack)

Location: backend/services/vector.py (search) + small glue in rag.py
Purpose: Produce an “evidence pack” for the LLM with explicit provenance.

Responsibilities
	•	Run vector search with optional doc filter
	•	Return top-k chunks + metadata for citation
	•	Enforce minimum evidence threshold (optional in MVP):
	•	If retrieval is weak, return empty/low-confidence signal

Output (Evidence Pack)

{
  "query": "...",
  "results": [
    {
      "content": "...markdown...",
      "doc_id": "...",
      "filename": "...",
      "page_number": 12,
      "chunk_index": 7,
      "score": 0.78
    }
  ]
}

Must NOT
	•	Generate final answers
	•	Invent sources

⸻

4.5 RAG Answer Agent (LLM Drafting with Strict Citations)

Location: backend/services/rag.py
Purpose: Generate an answer only from the provided evidence pack, with strict citations.

System Prompt Requirements
	•	“Use ONLY the provided context.”
	•	“If context contains Markdown tables, render them nicely.”
	•	“Always cite Source Document and Page Number.”
	•	“If insufficient evidence, say you cannot find it in the selected documents.”
	•	“If the user asks for a calculation, perform it step-by-step using only numbers present in the context.”

Determinism
	•	temperature = 0 (hard-coded for demo consistency)

Outputs
	•	answer: user-facing response
	•	sources: structured list of cited items (filename + page + chunk ids)

Must NOT
	•	Provide investment recommendations (“you should invest”)
	•	Use external knowledge not in context
	•	Fabricate citations, page numbers, or table values

⸻

4.6 Trace & Logging Agent (Decision Trace-Lite)

Location: backend/models.py + backend/database.py + call sites in API
Purpose: Persist minimal provenance for audit and debugging.

Responsibilities
	•	Store:
	•	Document metadata (hash/version if available)
	•	Chunk metadata (page_number, chunk_index)
	•	Chat logs (query, response, timestamp)
	•	Retrieval trace (selected doc_ids, retrieved chunk ids, model, prompt version)

MVP Scope
	•	This is not a full decision accountability system.
	•	It is a traceability baseline enabling:
	•	“Which evidence supported this answer?”
	•	“What was retrieved?”
	•	“Which model/prompt produced it?”

⸻

5) Human-in-the-Loop (User Responsibilities)

The user is an Investment Analyst/Associate and is expected to:
	•	Verify outputs against the reference sources (tables/pages)
	•	Treat AI output as a reading accelerator, not a decision authority
	•	Use citations to validate claims

The UI must make verification easy (side-by-side evidence view).

⸻

6) API Endpoints (MVP Behavior)

POST /upload
	•	Input: file + tags
	•	Flow:
	1.	Save file
	2.	Parse into Markdown chunks
	3.	Store Document + Chunk records (SQLite)
	4.	Embed + upsert to Qdrant
	•	Output: document_id + ingestion summary

POST /chat
	•	Input: query + selected_doc_ids
	•	Flow:
	1.	Retrieve top-k chunks (filtered by doc_ids)
	2.	Generate answer with strict citations
	3.	Store ChatLog + retrieval trace
	•	Output: {answer, sources}

(Optionally) GET /documents
	•	Return list of uploaded docs for Streamlit selection UI

⸻

7) Demo Playbook (5-Doc Strategy)

Deterministic settings
	•	temperature=0 in backend/services/rag.py

Pre-load data
	•	Provide scripts/seed_data.py to ingest 5 PDFs before the live demo.

Gotcha prevention
	•	Ensure prompt includes explicit calculation instruction:
	•	“If asked for calculations (CAGR, sum, ratio), compute step-by-step using only contextual numbers.”

⸻

8) Safety & Compliance Notes (MVP)
	•	Do not leak document content beyond local environment.
	•	Do not claim facts not in evidence.
	•	If citations are ambiguous or missing:
	•	respond with “Not found in selected documents” and show closest evidence.

⸻

9) Extension Policy (After MVP)

Agents can be added only if they improve:
	•	Evidence quality (reranking, section-aware retrieval)
	•	Provenance (doc hashing, versioning, immutable logs)
	•	Table verification (page image snippets, table-to-CSV extraction)
	•	“Assumption tracking” and “decision accountability” (future phase)

Any new agent must specify:
	•	Inputs/outputs contract
	•	Hard constraints (what it must NOT do)
	•	Logging requirements

⸻

10) Guiding Statement

This system is a local, citation-first reading assistant for PE workflows.
It exists to reduce time spent searching and to increase confidence via verifiable sources—
not to replace investment judgment.
All agents must adhere to this core mission.
