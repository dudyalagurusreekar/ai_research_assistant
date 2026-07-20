import os
from dotenv import load_dotenv
from smolagents import LiteLLMModel
import litellm


load_dotenv()
litellm._turn_on_debug()

def get_model():
    return LiteLLMModel(
        model_id=os.getenv("MODEL_NAME"),
        api_base=os.getenv("MODEL_API_BASE"),
        api_key=os.getenv("MODEL_API_KEY"),
        temperature=0.2,
        max_tokens=2048,
        timeout=120,      # <-- IMPORTANT
    )