import streamlit as st
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

# --- UI Setup ---
st.set_page_config(page_title="VA Consulting Assistant", layout="centered")
st.image("va_logo.jpg", width=200)
st.title("VA CONSULTING – AI Tax Assistant")
st.markdown("""
Welcome to your AI-powered tax assistant. Ask any tax question or upload a document, and get smart, fast answers tailored to West African fiscal rules.
""")

# --- Admin Dashboard ---
with st.expander("📊 Admin: View Leads"):  
    if os.path.exists("va_leads.csv"):
        with open("va_leads.csv", newline='', encoding='utf-8') as f:
            rows = list(csv.reader(f))
            if rows:
                headers = ["Name", "Company", "Email", "Question", "Response"]
                st.dataframe(rows, use_container_width=True)
            else:
                st.info("No data yet.")
    else:
        st.info("Lead CSV file not found.")

# --- Testimonials ---
st.markdown("""
### 🌟 Testimonials from Users
> "This app helped me clarify VAT compliance in just 2 minutes!" — Awa, Burkina Faso  
> "An essential tool for any CFO in West Africa." — Youssouf, Mali
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
            SystemMessage(content="You are a helpful assistant."),
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
                SystemMessage(content="You are a helpful tax assistant."),
                UserMessage(content=text[:3000]),
            ],
            max_tokens=2048,
            model=model_name
        )
        st.success(doc_response.choices[0].message.content)

# --- Support Form ---
with st.expander("📩 Contact Support"):
    contact_name = st.text_input("Your Name", key="contact_name")
    contact_email = st.text_input("Your Email", key="contact_email")
    contact_msg = st.text_area("Your Message", key="contact_msg")
    if st.button("Send Message"):
        try:
            msg = EmailMessage()
            msg["Subject"] = "Support Request from VA Consulting App"
            msg["From"] = contact_email
            msg["To"] = "laminibelem@valeuraconsulting.onmicrosoft.com"
            msg.set_content(f"From: {contact_name}\nEmail: {contact_email}\n\n{contact_msg}")

            with smtplib.SMTP("smtp.office365.com", 587) as server:
                server.starttls()
                server.login("laminibelem@valeuraconsulting.onmicrosoft.com", "nntmnmdkdckywxjp")
                server.send_message(msg)
            st.success("✅ Message sent successfully!")
        except Exception as e:
            st.warning("⚠️ Failed to send message.")

# --- Payment Info ---
st.markdown("""
#### 💰 Monthly Access: 2,000 XOF
To continue using the assistant beyond the free limit:

📱 Pay via **Orange Money** to: **+226 76 43 73 58**

Once payment is made, check the box below and submit your email to unlock unlimited access.
""")
