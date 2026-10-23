
import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

backend_dir = Path(__file__).resolve().parent / "backend"
load_dotenv(backend_dir / ".env")

api_key = os.getenv("GROQ_API_KEY")
model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

if not api_key:
    raise RuntimeError("GROQ_API_KEY is missing from backend/.env")

client = Groq(api_key=api_key)

response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "system",
            "content": (
                "You are a multilingual social media copywriter. "
                "Write original captions, not literal translations. "
                "Use natural language and do not invent image details."
            ),
        },
        {
            "role": "user",
            "content": (
                "Image description: A young boy is smiling at the beach.\n"
                "Platform: Instagram\n"
                "Language: Marathi\n"
                "Style: Creative\n\n"
                "Write one short, natural Marathi Instagram caption "
                "with at most two relevant hashtags. Use Devanagari script."
            ),
        },
    ],
    temperature=0.7,
    max_completion_tokens=800,
)

print("Model:", model)
print("Finish reason:", response.choices[0].finish_reason)
print("Message:", response.choices[0].message)
print("Usage:", response.usage)
