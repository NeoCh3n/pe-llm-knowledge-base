import json
import os
from typing import Any

import httpx
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def get_client() -> httpx.Client:
    return httpx.Client(base_url=BACKEND_URL, timeout=180)


@st.cache_data(show_spinner=False)
def fetch_documents() -> list[dict[str, Any]]:
    with get_client() as client:
        resp = client.get("/documents")
        resp.raise_for_status()
        return resp.json()


@st.cache_data(show_spinner=False)
def fetch_deals() -> list[dict[str, Any]]:
    with get_client() as client:
        resp = client.get("/deals")
        resp.raise_for_status()
        return resp.json()


@st.cache_data(show_spinner=False)
def fetch_workflows() -> list[dict[str, Any]]:
    with get_client() as client:
        resp = client.get("/workflow/runs")
        resp.raise_for_status()
        return resp.json()


def create_deal(payload: dict[str, Any]) -> dict[str, Any]:
    with get_client() as client:
        resp = client.post("/deals", json=payload)
        resp.raise_for_status()
        return resp.json()


def upload_document(file, payload: dict[str, Any]) -> dict[str, Any]:
    files = {"file": (file.name, file, file.type or "application/octet-stream")}
    with get_client() as client:
        resp = client.post("/upload", data=payload, files=files)
        resp.raise_for_status()
        return resp.json()


def delete_document(document_id: str) -> None:
    with get_client() as client:
        resp = client.delete(f"/documents/{document_id}")
        resp.raise_for_status()


def post_chat(payload: dict[str, Any]) -> dict[str, Any]:
    with get_client() as client:
        resp = client.post("/chat", json=payload)
        resp.raise_for_status()
        return resp.json()


def post_precedents(payload: dict[str, Any]) -> dict[str, Any]:
    with get_client() as client:
        resp = client.post("/precedents", json=payload)
        resp.raise_for_status()
        return resp.json()


def post_workflow(payload: dict[str, Any]) -> dict[str, Any]:
    with get_client() as client:
        resp = client.post("/workflow/run", json=payload)
        resp.raise_for_status()
        return resp.json()


def fetch_connectors(root: str | None = None) -> dict[str, Any]:
    params = {"root": root} if root else None
    with get_client() as client:
        resp = client.get("/connectors/local", params=params)
        resp.raise_for_status()
        return resp.json()


def invalidate_caches() -> None:
    st.cache_data.clear()


def render_sidebar(documents: list[dict[str, Any]], deals: list[dict[str, Any]]) -> list[str]:
    st.sidebar.header("Evidence Scope")
    selected_ids: list[str] = []
    for doc in documents:
        if st.sidebar.checkbox(
            f"{doc['filename']} [{doc['category']}]",
            key=f"doc-select-{doc['id']}",
            value=False,
        ):
            selected_ids.append(doc["id"])

    st.sidebar.divider()
    st.sidebar.subheader("Deal Context")
    deal_options = {deal["name"]: deal["id"] for deal in deals}
    selected_deal_name = st.sidebar.selectbox(
        "Active deal shell",
        options=["None"] + list(deal_options.keys()),
        index=0,
    )
    st.session_state["active_deal_id"] = None if selected_deal_name == "None" else deal_options[selected_deal_name]
    return selected_ids


def render_overview(documents: list[dict[str, Any]], deals: list[dict[str, Any]], workflows: list[dict[str, Any]]) -> None:
    col1, col2, col3 = st.columns(3)
    col1.metric("Documents", len(documents))
    col2.metric("Deals", len(deals))
    col3.metric("Workflow Runs", len(workflows))

    st.caption("This interface is evidence-first. It supports local open-source inference or hosted providers through one OpenAI-compatible API surface.")


def render_upload(deals: list[dict[str, Any]]) -> None:
    st.subheader("Upload Evidence")
    uploaded_file = st.file_uploader("Upload PDF / DOCX / DOC", type=["pdf", "docx", "doc"])
    tags = st.text_input("Tags", placeholder="SaaS, Series B, healthcare")
    category = st.selectbox(
        "Category",
        ["historical_deal", "current_opportunity", "market_research", "portfolio_report", "other"],
    )
    deal_outcome = st.selectbox("Deal outcome", ["", "invested", "passed", "exited"])
    document_type = st.text_input("Document type", placeholder="IC memo, DD report, portfolio review")
    language = st.selectbox("Language", ["", "en", "zh", "bilingual"])
    deal_name_to_id = {"": ""} | {deal["name"]: deal["id"] for deal in deals}
    selected_deal = st.selectbox("Link to canonical deal", list(deal_name_to_id.keys()))
    metadata_text = st.text_area("Additional metadata JSON", value="{}")

    if st.button("Ingest Document", use_container_width=True, disabled=uploaded_file is None):
        try:
            metadata_json = json.loads(metadata_text or "{}")
            payload = {
                "tags": json.dumps([tag.strip() for tag in tags.split(",") if tag.strip()]),
                "category": category,
                "deal_outcome": deal_outcome or None,
                "deal_id": deal_name_to_id[selected_deal] or None,
                "document_type": document_type or None,
                "language": language or None,
                "metadata_json": json.dumps(metadata_json),
            }
            with st.spinner("Parsing and indexing..."):
                upload_document(uploaded_file, payload)
            invalidate_caches()
            st.success("Document ingested.")
        except Exception as exc:
            st.error(f"Upload failed: {exc}")


def render_deals(deals: list[dict[str, Any]]) -> None:
    st.subheader("Canonical Deals")
    with st.expander("Create deal shell"):
        name = st.text_input("Deal name")
        company_name = st.text_input("Company")
        col1, col2, col3 = st.columns(3)
        sector = col1.text_input("Sector")
        geography = col2.text_input("Geography")
        stage = col3.text_input("Stage")
        col4, col5, col6 = st.columns(3)
        fund_name = col4.text_input("Fund")
        vintage_year = col5.number_input("Vintage year", min_value=1990, max_value=2100, value=2025)
        strategy = col6.text_input("Strategy")
        decision_status = st.text_input("Decision status")
        outcome_status = st.text_input("Outcome status")
        partner_owner = st.text_input("Partner owner")
        summary = st.text_area("Summary")
        if st.button("Create Deal", use_container_width=True):
            try:
                create_deal(
                    {
                        "name": name,
                        "company_name": company_name or None,
                        "sector": sector or None,
                        "geography": geography or None,
                        "stage": stage or None,
                        "fund_name": fund_name or None,
                        "vintage_year": int(vintage_year) if vintage_year else None,
                        "strategy": strategy or None,
                        "decision_status": decision_status or None,
                        "outcome_status": outcome_status or None,
                        "partner_owner": partner_owner or None,
                        "summary": summary or None,
                    }
                )
                invalidate_caches()
                st.success("Deal created.")
            except Exception as exc:
                st.error(f"Deal creation failed: {exc}")

    for deal in deals:
        with st.container(border=True):
            st.markdown(f"**{deal['name']}**")
            st.caption(
                " | ".join(
                    [item for item in [deal.get("sector"), deal.get("stage"), deal.get("geography"), deal.get("fund_name")] if item]
                )
            )
            if deal.get("summary"):
                st.write(deal["summary"])


def render_documents(documents: list[dict[str, Any]]) -> None:
    st.subheader("Document Library")
    for doc in documents:
        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(f"**{doc['filename']}**")
                st.caption(f"{doc['category']} | outcome={doc.get('deal_outcome') or 'n/a'} | tags={', '.join(doc.get('tags', []))}")
            with c2:
                if st.button("Delete", key=f"delete-{doc['id']}"):
                    try:
                        delete_document(doc["id"])
                        invalidate_caches()
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Delete failed: {exc}")


def render_analysis(selected_doc_ids: list[str]) -> None:
    st.subheader("Evidence-grounded Chat")
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    query = st.text_area("Question", placeholder="Ask about precedent, risks, or specific evidence.")
    categories = st.multiselect(
        "Category filters",
        ["historical_deal", "current_opportunity", "market_research", "portfolio_report", "other"],
    )
    deal_outcomes = st.multiselect("Outcome filters", ["invested", "passed", "exited"])

    if st.button("Run Chat", use_container_width=True) and query.strip():
        try:
            with st.spinner("Generating answer..."):
                response = post_chat(
                    {
                        "query": query.strip(),
                        "doc_ids": selected_doc_ids or None,
                        "analysis_mode": "document_search",
                        "filters": {
                            "categories": categories or None,
                            "deal_outcomes": deal_outcomes or None,
                        },
                    }
                )
            st.session_state["chat_history"].append(response)
        except Exception as exc:
            st.error(f"Chat failed: {exc}")

    for index, turn in enumerate(reversed(st.session_state["chat_history"])):
        with st.container(border=True):
            st.markdown(turn["answer"])
            st.caption(f"Model: {turn['model_name']} | Prompt: {turn['prompt_version']}")
            with st.expander(f"Sources #{index + 1}"):
                for source in turn["sources"]:
                    st.markdown(f"**{source['filename']}** page {source['page_number']} | {source.get('category') or 'n/a'}")
                    st.code(source["chunk_text"])


def render_precedents(selected_doc_ids: list[str]) -> None:
    st.subheader("Precedent Retrieval")
    query = st.text_input("Precedent search query", placeholder="Find similar approved / rejected / exited cases")
    if st.button("Find Precedents", use_container_width=True) and query.strip():
        try:
            payload = {
                "query": query.strip(),
                "doc_ids": selected_doc_ids or None,
            }
            result = post_precedents(payload)
            st.session_state["precedent_result"] = result
        except Exception as exc:
            st.error(f"Precedent search failed: {exc}")

    result = st.session_state.get("precedent_result")
    if result:
        st.caption(f"Retrieved {result['total']} precedent chunks")
        for bucket_name, items in result["buckets"].items():
            if not items:
                continue
            with st.expander(f"{bucket_name.title()} ({len(items)})", expanded=bucket_name == "invested"):
                for item in items:
                    st.markdown(f"**{item['filename']}** | score={item['score']:.3f}")
                    if item.get("deal_name"):
                        st.caption(f"{item['deal_name']} | {item.get('sector') or 'n/a'} | {item.get('stage') or 'n/a'}")
                    st.code(item["evidence"])


def render_workflow(selected_doc_ids: list[str], deals: list[dict[str, Any]], workflows: list[dict[str, Any]]) -> None:
    st.subheader("IC Workflow Copilot")
    active_deal_id = st.session_state.get("active_deal_id")
    query = st.text_area(
        "Workflow prompt",
        placeholder="Evaluate fit against historical precedent, surface key risks, and draft an IC outline.",
        key="workflow-query",
    )
    if st.button("Run Workflow", use_container_width=True) and query.strip():
        try:
            result = post_workflow(
                {
                    "query": query.strip(),
                    "deal_id": active_deal_id,
                    "doc_ids": selected_doc_ids or None,
                }
            )
            st.session_state["workflow_result"] = result
            invalidate_caches()
        except Exception as exc:
            st.error(f"Workflow failed: {exc}")

    result = st.session_state.get("workflow_result")
    if result:
        with st.container(border=True):
            st.markdown("**Draft answer**")
            st.write(result["draft_answer"])
            st.markdown("**Risk gaps**")
            for item in result["risk_gaps"]:
                st.write(f"- {item}")
            st.markdown("**Diligence questions**")
            for item in result["diligence_questions"]:
                st.write(f"- {item}")
            st.markdown("**IC memo outline**")
            for item in result["ic_memo_outline"]:
                st.write(f"- {item}")
            st.markdown("**Committee challenges**")
            for item in result["committee_challenges"]:
                st.write(f"- {item}")

    st.markdown("**Recent workflow runs**")
    for run in workflows[:8]:
        with st.expander(f"{run['workflow_type']} | {run['created_at']}"):
            output = run.get("output") or {}
            st.caption(f"Model: {run.get('model_name') or 'n/a'} | Prompt: {run.get('prompt_version') or 'n/a'}")
            if output.get("deal"):
                st.write(output["deal"])
            if output.get("query"):
                st.write(output["query"])


def render_connectors() -> None:
    st.subheader("Connector Scan")
    root = st.text_input("Local scan root", value="./data/connectors")
    if st.button("Scan Local Connector Root", use_container_width=True):
        try:
            st.session_state["connector_result"] = fetch_connectors(root)
        except Exception as exc:
            st.error(f"Connector scan failed: {exc}")

    result = st.session_state.get("connector_result")
    if result:
        st.caption(f"Root: {result['root']}")
        for doc in result["documents"]:
            st.write(f"{doc['name']} | {doc['suffix']} | {doc['size_bytes']} bytes")


def main() -> None:
    st.set_page_config(page_title="PE Institutional Memory", layout="wide")
    documents = fetch_documents()
    deals = fetch_deals()
    workflows = fetch_workflows()
    selected_doc_ids = render_sidebar(documents, deals)

    st.title("PE Institutional Memory")
    render_overview(documents, deals, workflows)

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["Upload", "Deals", "Documents", "Analysis", "Precedents", "Workflow"]
    )
    with tab1:
        render_upload(deals)
    with tab2:
        render_deals(deals)
    with tab3:
        render_documents(documents)
    with tab4:
        render_analysis(selected_doc_ids)
    with tab5:
        render_precedents(selected_doc_ids)
    with tab6:
        render_workflow(selected_doc_ids, deals, workflows)

    st.divider()
    render_connectors()


if __name__ == "__main__":
    main()
