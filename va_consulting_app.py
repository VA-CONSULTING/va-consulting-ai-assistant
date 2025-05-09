import streamlit as st
import json
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage, AssistantMessage
from azure.core.credentials import AzureKeyCredential
from PyPDF2 import PdfReader
import pytesseract
from pdf2image import convert_from_bytes
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
    result = response.choices[0].message.content
    st.success(result)

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
        if not text:
            st.info("ℹ️ Using OCR fallback to extract text from scanned PDF...")
            images = convert_from_bytes(uploaded_file.read())
            text = "\n".join([pytesseract.image_to_string(img) for img in images])
    else:
        text = uploaded_file.read().decode("utf-8")

    if not text.strip():
        st.warning("⚠️ No readable text found in the document.")
    else:
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
            document_summary = doc_response.choices[0].message.content
            st.success(document_summary)

            follow_up = st.text_input("💬 Ask a follow-up question based on this document:")
            if follow_up:
                follow_up_response = client.complete(
                    messages=[
                        SystemMessage(content=prompts[prompt_mode]),
                        UserMessage(content=text[:2000]),
                        AssistantMessage(content=document_summary),
                        UserMessage(content=follow_up),
                    ],
                    max_tokens=2048,
                    model=model_name
                )
                st.success(follow_up_response.choices[0].message.content)
