import streamlit as st
import requests
import pandas as pd


BACKEND_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="Anatomy AI",
    page_icon="🧠",
    layout="wide"
)


st.title("Anatomy AI")

st.write(
    "Upload anatomy lecture notes to extract the content "
    "and identify statements for factual review."
)


st.subheader("Upload Lecture Notes")

uploaded_file = st.file_uploader(
    "Choose a DOCX or PDF file",
    type=["docx", "pdf"]
)


if uploaded_file is not None:

    st.success(f"Selected file: {uploaded_file.name}")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Extract Document Text"):

            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type
                )
            }

            try:
                response = requests.post(
                    f"{BACKEND_URL}/upload",
                    files=files
                )

                if response.status_code == 200:
                    result = response.json()

                    st.success("Document processed successfully.")

                    st.write(
                        "Characters extracted:",
                        result["characters_extracted"]
                    )

                    st.subheader("Extracted Text")

                    st.text_area(
                        "Document content",
                        result["text"],
                        height=400
                    )

                else:
                    st.error(
                        f"Backend error: {response.text}"
                    )

            except requests.exceptions.ConnectionError:
                st.error(
                    "Cannot connect to the backend. "
                    "Make sure FastAPI is running."
                )

    with col2:
        if st.button("Extract Anatomy Claims"):

            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type
                )
            }

            try:
                response = requests.post(
                    f"{BACKEND_URL}/analyze-claims",
                    files=files
                )

                if response.status_code == 200:
                    result = response.json()

                    st.success(
                        f"{result['total_claims']} claims extracted."
                    )

                    claims = result["claims"]

                    dataframe = pd.DataFrame(claims)

                    st.subheader("Extracted Claims")

                    st.dataframe(
                        dataframe,
                        use_container_width=True
                    )

                else:
                    st.error(
                        f"Backend error: {response.text}"
                    )

            except requests.exceptions.ConnectionError:
                st.error(
                    "Cannot connect to the backend. "
                    "Make sure FastAPI is running."
                )