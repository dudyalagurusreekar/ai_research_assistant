import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.model import get_model

model = get_model()

messages = [
    {
        "role": "user",
        "content": [{"type": "text", "text": "What is 2 + 2?"}]
    }
]

response = model.generate(messages)

print(response)