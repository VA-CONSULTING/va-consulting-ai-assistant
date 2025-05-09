import streamlit as st import json from azure.ai.inference import ChatCompletionsClient from azure.ai.inference.models import SystemMessage, UserMessage, AssistantMessage from azure.core.credentials import AzureKeyCredential from PyPDF2 import PdfReader import fitz  # PyMuPDF import pytesseract from PIL import Image from fpdf import FPDF import os import smtplib from email.message import EmailMessage import csv import io

--- Azure AI Config ---

endpoint = "https://DeepSeek-R1-iidkm.eastus2.models.ai.azure.com" api_key = "u2tl0lAkttAf0dEDO4UP7yxYfxpCKSQt" model_name = "DeepSeek-R1-iidkm"

--- Load Prompt Cards from JSON ---

with open("prompt_cards.json", "r", encoding="utf-8") as f: prompt_data = json.load(f)

prompt_options = [card["title"] for card in prompt_data] prompt_descriptions = {card["title"]: card["description"] for card in prompt_data} prompts = {card["title"]: card["prompt"] for card in prompt_data}

--- UI Setup ---

st.set_page_config(page_title="VA Consulting Assistant", layout="centered") st.image("va_logo.jpg", width=200) st.title("VA CONSULTING – AI Tax Assistant") st.markdown(""" Welcome to your AI-powered tax assistant. Ask any tax question or upload a document, and get smart, fast answers tailored to West African fiscal rules. """)

--- Prompt Selector with Tooltip ---

prompt_mode = st.selectbox("🧠 Choose an Assistant Mode:", prompt_options, help=prompt_descriptions[prompt_options[0]]) st.caption(f"💡 {prompt_descriptions[prompt_mode]}")

--- Lead Capture and Payment ---

st.markdown("---") col1, col2 = st.columns(2) with col1: user_name = st.text_input("👤 Your Full Name") user_company = st.text_input("🏢 Company Name") with col2: user_email = st.text_input("📧 Your Email") user_paid = st.checkbox("✅ I have paid 2,000 XOF via Orange Money")

st.markdown(""" 💰 Monthly Access: 2,000 XOF To continue using the assistant beyond the free limit: 📱 Pay via Orange Money to: +226 76 43 73 58

""")

--- Chat Input Section ---

st.markdown("### 🧾 Ask a tax question") user_question = st.text_input("Enter your question") if user_question: client = ChatCompletionsClient( endpoint=endpoint, credential=AzureKeyCredential(api_key), ) response = client.complete( messages=[ SystemMessage(content=prompts[prompt_mode]), UserMessage(content=user_question), ], max_tokens=2048, model=model_name ) result = response.choices[0].message.content st.success(result)

# PDF Export Button
if st.download_button("⬇️ Download PDF", data=FPDF().output(dest='S').encode('latin-1'), file_name="va_response.pdf", mime="application/pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=result)
    pdf.output("va_response.pdf")

# Log lead to CSV
if user_email:
    try:
        with open("va_leads.csv", mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([user_name, user_company, user_email, user_question, result])
    except Exception as e:
        st.warning("⚠️ Could not write to va_leads.csv")

