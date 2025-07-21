import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def chat_with_model(prompt: str, model: str = "gpt-4o-mini") -> str:
    print(f"🤖 Chatting with model '{model}'...\n")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        print("🤖 Model response received.\n")
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Error while calling OpenAI API: {e}")
        return "Error: Unable to get a response from the model."
