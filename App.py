import streamlit as st
from pathlib import Path
from pypdf import PdfReader
from docx import Document
from openai import OpenAI
import io
import os

import database

st.set_page_config(
    page_title="Kerala Study AI",
    page_icon="📚",
    layout="wide"
)

database.initialize()

st.title("📚 Kerala Study AI")
st.caption("Your AI-powered Kerala school study assistant")

with st.sidebar:

    st.header("Study settings")

    class_name = st.selectbox(
        "Select class",
        [f"Class {i}" for i in range(1, 11)]
        + ["Plus One", "Plus Two"]
    )

    language = st.selectbox(
        "Language",
        ["Malayalam", "English", "Both"]
    )

    subject = st.text_input("Subject")

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        st.warning("AI API key is not configured.")

tabs = st.tabs([
    "🔎 Website Search",
    "📂 Upload Notes",
    "🤖 AI Chat",
    "📝 Exam Generator"
])

# WEBSITE SEARCH

with tabs[0]:

    st.header("Search educational pages")

    query = st.text_input("Search HSSLive index")

    if query:

        results = database.search_pages(query)

        for title, url, description in results:

            st.subheader(title or "Untitled page")
            st.write(description)
            st.link_button("Open website", url)

# UPLOAD NOTES

with tabs[1]:

    st.header("Upload study materials")

    file = st.file_uploader(
        "Upload PDF, DOCX or TXT",
        type=["pdf", "docx", "txt"]
    )

    if file and st.button("Extract and save"):

        data = file.getvalue()

        if file.name.endswith(".pdf"):

            reader = PdfReader(io.BytesIO(data))

            text = "\n".join(
                page.extract_text() or ""
                for page in reader.pages
            )

        elif file.name.endswith(".docx"):

            doc = Document(io.BytesIO(data))

            text = "\n".join(
                p.text for p in doc.paragraphs
            )

        else:

            text = data.decode(
                "utf-8", errors="replace"
            )

        if text.strip():

            database.save_note(
                file.name,
                text
            )

            st.success("Notes saved successfully!")

        else:
            st.warning("No readable text found.")

# AI CHAT

with tabs[2]:

    st.header("Ask your Study AI")

    question = st.text_area(
        "Enter your question"
    )

    if st.button("Ask AI"):

        if not api_key:
            st.error("Configure OPENAI_API_KEY first.")

        elif not question.strip():
            st.warning("Enter a question.")

        else:

            sources = database.search_notes(
                question
            )

            context = "\n\n".join(
                f"File: {name}\n{text}"
                for name, text in sources
            )

            client = OpenAI(api_key=api_key)

            response = client.responses.create(
                model=os.getenv("OPENAI_MODEL", "gpt-5.5"),
                instructions=(
                    f"You are a Kerala school study assistant. "
                    f"Explain at {class_name} level. "
                    f"Respond in {language}. "
                    "Use supplied notes when available. "
                    "Clearly identify when the notes do not contain an answer."
                ),
                input=(
                    f"Subject: {subject}\n"
                    f"Question: {question}\n"
                    f"Study material:\n{context}"
                ),
                store=False
            )

            st.markdown(response.output_text)

# EXAM GENERATOR

with tabs[3]:

    st.header("Practice exam generator")

    topic = st.text_input("Chapter or topic")

    number = st.slider(
        "Number of questions",
        5, 20, 10
    )

    if st.button("Generate questions"):

        if not api_key:
            st.error("Configure your API key.")

        elif not topic.strip():
            st.warning("Enter a topic.")

        else:

            client = OpenAI(api_key=api_key)

            response = client.responses.create(
                model=os.getenv("OPENAI_MODEL", "gpt-5.5"),
                instructions=(
                    f"You are a Kerala {class_name} teacher. "
                    f"Use {language}. Create original practice questions "
                    "with answers and explanations. Do not claim they are "
                    "official or predicted exam questions."
                ),
                input=(
                    f"Subject: {subject}\n"
                    f"Chapter: {topic}\n"
                    f"Create {number} practice questions."
                ),
                store=False
            )

            st.markdown(response.output_text)