Project Context: Private Equity Local RAG MVP

1. Project Goal & Philosophy
Objective: Build a local RAG system to help PE Associates find information across 5-10 complex financial documents (PDF/DOCX) quickly.
Core Value: "Save 30 minutes of manual searching." Accuracy of source citations is more important than AI creativity.
Deployment: Local execution (Privacy first).
Target User: Investment Analyst/Associate (needs to verify data against original tables).
2. Tech Stack Specification
Language: Python 3.10+
Backend: FastAPI (API layer)
Frontend: Streamlit (Rapid UI development)
Parsing: docling (Specifically using Markdown export to preserve Tables)
Vector DB: Qdrant (Dockerized)
Database: SQLite (Metadata & Chat Logs)
LLM: OpenAI API compatible interface (pointing to local LLM via vLLM/Ollama, or OpenAI for testing).
3. Directory Structure (Skeleton)
code
Text
pe-rag-mvp/
├── .env                  # API Keys, Qdrant URL, Model Paths
├── docker-compose.yml    # Qdrant service
├── requirements.txt      # fastapi, streamlit, qdrant-client, docling, pandas, sqlalchemy
├── backend/
│   ├── main.py           # FastAPI entry point
│   ├── config.py         # Pydantic Settings
│   ├── database.py       # SQLite connection & SessionLocal
│   ├── models.py         # SQL Tables: Document, Chunk, ChatLog
│   └── services/
│       ├── parser.py     # CORE: Docling logic with Table preservation
│       ├── vector.py     # Qdrant ingestion & retrieval
│       └── rag.py        # Prompt engineering & LLM response generation
└── frontend/
    └── app.py            # Streamlit Application
4. Implementation Steps (Codex Prompts)

Step 1: Infrastructure & Data Models
Context: Set up SQLite schemas to track documents and chunks.
Prompt for Codex:

"Create backend/models.py using SQLAlchemy.

Document table: id (UUID), filename, upload_timestamp, tags (JSON).
Chunk table: id (UUID), document_id (FK), content (Text), page_number (Int), chunk_index (Int).
ChatLog table: id, user_query, ai_response, timestamp.
Also create backend/database.py for setup."
Step 2: The Core Parser (Table Focused)
Context: This is the most critical part. We need to keep tables readable.
Prompt for Codex:

"Create backend/services/parser.py.
Use docling library to parse PDF files.
Critical Requirement: Convert the document to Markdown format to preserve Table structures. Do NOT flatten tables into unstructured text.
Function parse_and_chunk(file_path) should:

Load document with Docling.
Export to Markdown.
Split text by headers or logical sections (approx 500-800 tokens), ensuring Markdown tables are kept within a single chunk if possible.
Return a list of chunks with metadata (page number, source)."
Step 3: Vector Store Logic
Context: Interface with Qdrant.
Prompt for Codex:

"Create backend/services/vector.py.

Initialize QdrantClient.
Implement upsert_chunks(chunks): Convert text to vectors (use fastembed or sentence-transformers locally) and upload to Qdrant collection 'pe_docs'. Store metadata (doc_id, page_num, filename) in payload.
Implement search(query, doc_ids=None, top_k=5): Perform vector search. If doc_ids is provided, apply a Qdrant Filter to restrict search to those specific documents."
Step 4: RAG & LLM Service
Context: Generate the answer with strict citations.
Prompt for Codex:

"Create backend/services/rag.py.
Implement generate_answer(query, retrieved_chunks).
Construct a System Prompt: 'You are a financial analyst assistant. Use ONLY the provided context. If the context contains Markdown tables, format them nicely in the output. Always cite the Source Document and Page Number at the end of the answer.'
Call the LLM (use openai client pointing to local base_url or real API)."
Step 5: FastAPI Endpoints
Context: Glue the backend services together.
Prompt for Codex:

"Update backend/main.py.

POST /upload: Accept file + tags. Save to disk -> Parse (Service) -> Store in DB -> Vectorize.
POST /chat: Accept query + list of selected doc_ids. -> Vector Search (filtered by doc_ids) -> Generate Answer -> Save Log -> Return {answer, sources}."
Step 6: Streamlit Frontend (The Demo UI)
Context: Simple, clean, side-by-side view.
Prompt for Codex:

"Create frontend/app.py using Streamlit.
Layout:

Sidebar: File Uploader. List of uploaded files with Checkboxes (to select which docs to query).
Main Area: Chat Interface.
Logic:
When user uploads, call POST /backend/upload.
Display available documents from GET /backend/documents.
User selects 1 or more docs (e.g., 'Fund III Q4 Report').
User types query. App calls POST /backend/chat with query and selected_doc_ids.
Display: Show the AI Answer. Below the answer, use st.expander to show 'Reference Sources' (filename + page number + raw chunk text) so the user can verify."
5. "Tactical" Demo Preparation (The 5-Doc Strategy)
Instructions for the Developer (You):

Hardcode for Speed: In backend/services/rag.py, hardcode the temperature=0 to ensure consistency during the demo.
Pre-load Script: Don't rely on uploading files during the demo if they are large. Create a script scripts/seed_data.py that loops through your friend's 5 PDF files and hits the ingestion API. Run this before you walk over to his desk.
The "Gotcha" Prevention:
In the system prompt, add: "If the user asks for a calculation (e.g., CAGR, Sum), perform the calculation step-by-step explicitly based on the numbers in the context."