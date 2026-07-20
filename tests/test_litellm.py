from litellm import completion
from dotenv import load_dotenv
import os

load_dotenv()

model_id = os.getenv("MODEL_NAME", "ollama_chat/qwen2:7b")
if model_id.startswith("ollama/") and not model_id.startswith("ollama_chat/"):
    model_id = model_id.replace("ollama/", "ollama_chat/", 1)

response = completion(
    model=model_id,
    api_base=os.getenv("MODEL_API_BASE", "http://127.0.0.1:11434"),
    api_key=os.getenv("MODEL_API_KEY") or None,
    timeout=300,
    messages=[
        {
            "role": "system",
            "content": (
                "Reply exactly in this format:\n"
                "Thought:\n"
                "<code>\n"
                "print(2+2)\n"
                "</code>"
            ),
        },
        {
            "role": "user",
            "content": "What is 2+2?",
        },
    ],
)
print("Response:", response.choices[0].message.content)