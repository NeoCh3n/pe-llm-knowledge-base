import os
from typing import Any, Dict, List

import httpx
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def get_client() -> httpx.Client:
    return httpx.Client(base_url=BACKEND_URL, timeout=120)


@st.cache_data(show_spinner=False)
def fetch_documents() -> List[Dict[str, Any]]:
    with get_client() as client:
        resp = client.get("/documents")
        resp.raise_for_status()
        return resp.json()


def upload_document(file, tags: List[str], category: str):
    data = {"tags": st.session_state.get("tag_json", "[]"), "category": category}
    files = {"file": (file.name, file, file.type)}
    with get_client() as client:
        resp = client.post("/upload", data=data, files=files)
        resp.raise_for_status()
        return resp.json()


def post_chat(query: str, doc_ids: List[str]):
    payload = {"query": query, "doc_ids": doc_ids or None}
    with get_client() as client:
        resp = client.post("/chat", json=payload)
        resp.raise_for_status()
        return resp.json()


def sidebar(documents: List[Dict[str, Any]]):
    st.sidebar.header("Documents")
    st.sidebar.caption("Upload and select documents to ground answers.")

    uploaded_file = st.sidebar.file_uploader("Upload PDF/DOCX", type=["pdf", "docx", "doc"])
    tag_text = st.sidebar.text_input("Tags (comma separated)", value="")
    category = st.sidebar.selectbox(
        "Category",
        options=[
            "historical_deal",
            "current_opportunity",
            "market_research",
            "portfolio_report",
            "other",
        ],
        index=0,
    )

    if uploaded_file and st.sidebar.button("Ingest"):
        tags = [tag.strip() for tag in tag_text.split(",") if tag.strip()]
        st.session_state["tag_json"] = str(tags).replace("'", '"')
        with st.spinner("Uploading and parsing..."):
            upload_document(uploaded_file, tags, category)
        st.cache_data.clear()
        st.experimental_rerun()

    st.sidebar.divider()
    st.sidebar.subheader("Select documents")
    selected_ids = []
    for doc in documents:
        checked = st.sidebar.checkbox(
            f"{doc['filename']} ({doc['category']})", value=False, key=f"doc-{doc['id']}"
        )
        if checked:
            selected_ids.append(doc["id"])

    return selected_ids


def render_chat():
    if "history" not in st.session_state:
        st.session_state["history"] = []

    documents = fetch_documents()
    selected_ids = sidebar(documents)

    st.title("PE Local RAG")
    st.write("Ask questions grounded in your deal documents and research.")

    with st.form("chat-form"):
        query = st.text_area("Question", height=120, placeholder="Ask about metrics, risks, or deal patterns...")
        submitted = st.form_submit_button("Send", use_container_width=True)

    if submitted and query.strip():
        with st.spinner("Thinking..."):
            try:
                response = post_chat(query.strip(), selected_ids)
                st.session_state.history.append(
                    {"query": query.strip(), "answer": response["answer"], "sources": response["sources"]}
                )
            except Exception as exc:
                st.error(f"Request failed: {exc}")

    for turn in reversed(st.session_state.history):
        st.markdown(f"**You:** {turn['query']}")
        st.markdown(turn["answer"])
        with st.expander("Reference sources"):
            for src in turn["sources"]:
                st.markdown(
                    f"- **{src.get('filename','')}**, page {src.get('page_number','?')}\n\n```\n{src.get('chunk_text','')}\n```"
                )
        st.divider()


def main():
    st.set_page_config(page_title="PE Local RAG", layout="wide")
    render_chat()


if __name__ == "__main__":
    main()
