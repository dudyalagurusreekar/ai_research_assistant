import os
from dotenv import load_dotenv
from smolagents import LiteLLMModel

load_dotenv()


def create_model():
    provider = os.getenv("MODEL_PROVIDER", "ollama").lower()

    if provider == "ollama":
        return LiteLLMModel(
            model_id=f"ollama/{os.getenv('MODEL_NAME', 'qwen2:7b')}",
            api_base="http://127.0.0.1:11434",
            api_key="ollama",
            timeout=120,
            temperature=0.2,
            max_tokens=2048,
        )

    raise ValueError(f"Unsupported provider: {provider}")