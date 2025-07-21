import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

LLM_API_URL = "https://dev01-llm-platform.itf.csodqa.com/v2/chat/completions"
LLM_API_TOKEN = os.getenv("LLM_API_TOKEN")  # Or paste your token directly (not recommended for security)

def chat_with_model(prompt: str, model: str = "llama-8b") -> str:
    print(f"🤖 Chatting with custom LLM model '{model}'...\n")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_TOKEN}"
    }
    payload = {
        "model": model,
        "max_tokens": 1100,
        "stream": False,
        "enable_guardrails": False,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    try:
        response = requests.post(LLM_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        # Adjust this if your API returns the message differently
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"❌ Error while calling custom LLM API: {e}")
        return "Error: Unable to get a response from the model."
