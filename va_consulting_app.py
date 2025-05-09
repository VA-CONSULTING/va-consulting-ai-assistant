import streamlit as st
import json
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage, AssistantMessage
from azure.core.credentials import AzureKeyCredential
from PyPDF2 import PdfReader
from fpdf import FPDF
import os
import smtplib
from email.message import EmailMessage
import csv

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

# --- Chat Input Section ---
st.markdown("### 🧾 Ask a tax question")
user_question = st.text_input("Enter your question")
if user_question:
    client = ChatCompletionsClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(api_key),
    )
    response = client.complete(
        messages=[
            SystemMessage(content=prompts[prompt_mode]),
            UserMessage(content=user_question),
        ],
        max_tokens=2048,
        model=model_name
    )
    st.success(response.choices[0].message.content)

# --- File Upload Section ---
st.markdown("### 📄 Or upload a tax-related document (.pdf or .txt)")
uploaded_file = st.file_uploader("Upload a document", type=["pdf", "txt"])
if uploaded_file:
    if uploaded_file.type == "application/pdf":
        pdf = PdfReader(uploaded_file)
        text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    else:
        text = uploaded_file.read().decode("utf-8")
    st.write("📑 Extracted text:")
    st.code(text[:1000])
    if st.button("Ask AI based on this document"):
        client = ChatCompletionsClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key),
        )
        doc_response = client.complete(
            messages=[
                SystemMessage(content=prompts[prompt_mode]),
                UserMessage(content=text[:3000]),
            ],
            max_tokens=2048,
            model=model_name
        )
        st.success(doc_response.choices[0].message.content)
