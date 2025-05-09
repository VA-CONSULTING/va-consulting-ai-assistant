import streamlit as st
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

# --- Azure AI Config ---
endpoint = "https://DeepSeek-R1-iidkm.eastus2.models.ai.azure.com"
api_key = "u2tl0lAkttAf0dEDO4UP7yxYfxpCKSQt"
model_name = "DeepSeek-R1-iidkm"

# --- UI Setup ---
st.set_page_config(page_title="Hello AI - VA Consulting", layout="centered")
st.title("💬 Hello from your AI Assistant")

user_input = st.text_input("Ask a question to the AI", "What are the VAT rules in Burkina Faso?")

if st.button("Send to AI"):
    with st.spinner("Thinking..."):
        try:
            client = ChatCompletionsClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(api_key)
            )

            response = client.complete(
                messages=[
                    SystemMessage(content="You are a helpful assistant for a tax consultant."),
                    UserMessage(content=user_input),
                ],
                max_tokens=1024,
                model=model_name
            )

            st.success("✅ Response received!")
            st.markdown("### 🧠 AI Response")
            st.write(response.choices[0].message.content)

        except Exception as e:
            st.error(f"❌ Error: {e}")
