import os
from dotenv import load_dotenv
from smolagents import LiteLLMModel

load_dotenv()


def get_model():
    """
    Creates and returns the LLM used by the AI Research Assistant.

    Environment Variables:

    MODEL_NAME
    MODEL_API_BASE
    MODEL_API_KEY
    """

    model_name = os.getenv(
        "MODEL_NAME",
        "ollama/qwen2.5:7b-instruct"
    )

    api_base = os.getenv(
        "MODEL_API_BASE",
        "http://localhost:11434"
    )

    api_key = os.getenv(
        "MODEL_API_KEY",
        "ollama"
    )

    return LiteLLMModel(
        model_id=model_name,
        api_base=api_base,
        api_key=api_key,
        temperature=0.2,
        max_tokens=2048,
    )