import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.model import resolve_model_config
import litellm

load_dotenv()

model_name, model_kwargs = resolve_model_config()

kwargs = {
    "model": model_name,
    "messages": [
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
    "timeout": 300,
}
if "api_key" in model_kwargs:
    kwargs["api_key"] = model_kwargs["api_key"]
if "api_base" in model_kwargs:
    kwargs["api_base"] = model_kwargs["api_base"]

response = litellm.completion(**kwargs)
print("Response:", response.choices[0].message.content)