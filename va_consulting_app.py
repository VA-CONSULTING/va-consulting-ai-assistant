import streamlit as st
import json
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage, AssistantMessage
from azure.core.credentials import AzureKeyCredential
from PyPDF2 import PdfReader
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from fpdf import FPDF
import os
import smtplib
from email.message import EmailMessage
import csv
import io

# --- Azure AI Config ---
endpoint = "https://DeepSeek-R1-iidkm.eastus2.models.ai.azure.com"
api_key = "u2tl0lAkttAf0dEDO4UP7yxYfxpCKSQt"
model_name = "DeepSeek-R1-iidkm"

# --- Load Prompt Cards from JSON ---
with open("prompt_cards.json", "r", encoding="utf-8") as f:
    prompt_data = json.load(f)

prompt_options = [card["title"] for card in prompt_data]
prompt_descriptions = {card["title"]: card["description"] for card in prompt_data}
prompts = {card["title"]: card["prompt"] for card in prompt_data}

# --- UI Setup ---
st.set_page_config(page_title="VA Consulting Assistant", layout="centered")
st.image("va_logo.jpg", width=200)
st.title("VA CONSULTING – AI Tax Assistant")
st.markdown("""
Welcome to your AI-powered tax assistant. Ask any tax question or upload a document, and get smart, fast answers tailored to West African fiscal rules.
""")

# --- Prompt Selector with Tooltip ---
prompt_mode = st.selectbox("🧠 Choose an Assistant Mode:", prompt_options, help=prompt_descriptions[prompt_options[0]])
st.caption(f"💡 {prompt_descriptions[prompt_mode]}")

# --- Lead Capture and Payment ---
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    user_name = st.text_input("👤 Your Full Name")
    user_company = st.text_input("🏢 Company Name")
with col2:
    user_email = st.text_input("📧 Your Email")
    user_paid = st.checkbox("✅ I have paid 2,000 XOF via Orange Money")

st.markdown("""
💰 **Monthly Access: 2,000 XOF**
To continue using the assistant beyond the free limit:
📱 Pay via **Orange Money** to: **+226 76 43 73 58**
---
""")

# --- Chat Input Section ---
st.markdown("### 🧾 Ask a tax question")
user_question = st.text_input("Enter your question")
if user_question:
    client = ChatCompletionsClient(endpoint=endpoint, credential=AzureKeyCredential(api_key))
    response = client.complete(
        messages=[
            SystemMessage(content=prompts[prompt_mode]),
            UserMessage(content=user_question),
        ],
        max_tokens=2048,
        model=model_name
    )
    result = response.choices[0].message.content
    st.success(result)

    # PDF Export Button
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=result)
    pdf_output = pdf.output(dest="S").encode("latin-1")
    st.download_button("⬇️ Download PDF", data=pdf_output, file_name="va_response.pdf", mime="application/pdf")

    # Log lead to CSV
    if user_email:
        try:
            with open("va_leads.csv", mode="a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow([user_name, user_company, user_email, user_question, result])
        except Exception as e:
            st.warning("⚠️ Could not write to va_leads.csv")

# --- File Upload Section ---
st.markdown("### 📄 Or upload a tax-related document (.pdf or .txt)")
uploaded_file = st.file_uploader("Upload a document", type=["pdf", "txt"])
if uploaded_file:
    text = ""
    if uploaded_file.type == "application/pdf":
        try:
            pdf = PdfReader(uploaded_file)
            text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        except:
            text = ""
        if not text.strip():
            st.info("ℹ️ Using OCR fallback with PyMuPDF to extract text from scanned PDF...")
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            for page in doc:
                pix = page.get_pixmap(dpi=300)
                img = Image.open(io.BytesIO(pix.tobytes()))
                text += pytesseract.image_to_string(img)
    else:
        text = uploaded_file.read().decode("utf-8")

    if not text.strip():
        st.warning("⚠️ No readable text found in the document.")
    else:
        st.write("📑 Extracted text:")
        st.code(text[:1000])

        # --- Chunk the text ---
        def chunk_text(full_text, max_len=3000, overlap=500):
            chunks = []
            i = 0
            while i < len(full_text):
                end = min(i + max_len, len(full_text))
                chunks.append(full_text[i:end])
                i += max_len - overlap
            return chunks

        text_chunks = chunk_text(text)

        if st.button("Ask AI to summarize full document"):
            summaries = []
            client = ChatCompletionsClient(endpoint=endpoint, credential=AzureKeyCredential(api_key))
            for i, chunk in enumerate(text_chunks):
                st.info(f"Processing chunk {i+1}/{len(text_chunks)}...")
                chunk_response = client.complete(
                    messages=[
                        SystemMessage(content=prompts[prompt_mode]),
                        UserMessage(content=chunk),
                    ],
                    max_tokens=2048,
                    model=model_name
                )
                summaries.append(chunk_response.choices[0].message.content)
            final_summary = "\n".join(summaries)
            st.success(final_summary)

            follow_up = st.text_input("💬 Ask a follow-up question based on this summary:")
            if follow_up:
                follow_up_response = client.complete(
                    messages=[
                        SystemMessage(content=prompts[prompt_mode]),
                        UserMessage(content=final_summary[:3000]),
                        AssistantMessage(content=final_summary),
                        UserMessage(content=follow_up),
                    ],
                    max_tokens=2048,
                    model=model_name
                )
                st.success(follow_up_response.choices[0].message.content)
