import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

if not SARVAM_API_KEY:
    raise ValueError("SARVAM_API_KEY not found in .env file. Please make sure it's set.")

model = ChatOpenAI(
    model="sarvam-105b",
    api_key=SARVAM_API_KEY,
    base_url="https://api.sarvam.ai/v1",
    temperature=0.2,
)

print("Sarvam AI (sarvam-105b) model initialized successfully using ChatOpenAI client.")





