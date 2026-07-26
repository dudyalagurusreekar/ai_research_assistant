import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.model import get_model

model = get_model()

messages = [
    {
        "role": "user",
        "content": "Say hello in one sentence."
    }
]

if __name__ == "__main__":
    response = model.generate(messages)
    print(response)