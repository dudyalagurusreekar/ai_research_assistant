import litellm
from dotenv import load_dotenv
import os

load_dotenv()

response = litellm.completion(
    model=os.getenv("MODEL_NAME"),
    api_base=os.getenv("MODEL_API_BASE"),
    api_key=os.getenv("MODEL_API_KEY"),
    messages=[
        {
            "role": "user",
            "content": "Say hello in one sentence."
        }
    ],
    timeout=300,
)

print(response.choices[0].message.content)