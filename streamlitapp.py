from __future__ import annotations
import os
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

st.set_page_config(page_title="UIDAI RAG", layout="centered")

st.title("Ask Questions")
st.caption("UIDAI Legal Framework – RAG Chatbot")

query = st.text_input("Enter your query:", value="Latest updated rules under legal framework?")

if st.button("Get Answer", type="primary"):
    with st.spinner("Thinking..."):
        try:
            resp = requests.post(f"{API_BASE}/answer", json={"query": query}, timeout=120)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            st.error(f"Failed to get answer: {e}")
            st.stop()

        # ------------- Response -------------
        st.subheader("Response:")
        content = data.get("content", "").strip()
        # Keep only the part before "## Most Relevant Documents"
        response_text = content.split("\n## Most Relevant Documents", 1)[0]
        response_text = response_text.replace("## Response", "").strip()
        st.markdown(response_text)

        # ------------- Most Relevant Documents -------------
        st.subheader("Most Relevant Documents:")
        docs = data.get("documents", [])

        def human_bytes(n: int | None) -> str:
            if not n:
                return ""
            for unit in ["B", "KB", "MB", "GB", "TB"]:
                if n < 1024 or unit == "TB":
                    return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
                n /= 1024
            return ""

        for i, d in enumerate(docs, start=1):
            title = (d.get("title") or "").strip()
            url = d.get("doc_url") or d.get("download_url") or d.get("page_url")
            date_str = d.get("published_date") or ""
            ftype = d.get("file_type") or ""
            size = human_bytes(d.get("file_size_bytes"))
            meta = ", ".join(x for x in [date_str, ftype, size] if x)
            st.markdown(f"**{i}.** [{title}]({url})")
            if meta:
                st.caption(meta)

        # ------------- Source Website -------------
        st.subheader("Information Source Website:")
        st.markdown("UIDAI (uidai.gov.in)")

st.divider()
st.caption("Tip: if your backend runs elsewhere, set API_BASE env variable.")