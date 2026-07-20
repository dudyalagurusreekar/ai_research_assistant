

import os
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from smolagents import LiteLLMModel, MessageRole
import litellm



load_dotenv()
litellm._turn_on_debug()
def get_model():
    model_id = os.getenv("MODEL_NAME", "ollama_chat/phi3:latest")
    if model_id.startswith("ollama/") and not model_id.startswith("ollama_chat/"):
        model_id = model_id.replace("ollama/", "ollama_chat/", 1)

    return LiteLLMModel(
        model_id=model_id,
        api_base=os.getenv("MODEL_API_BASE", "http://127.0.0.1:11434"),
        api_key=os.getenv("MODEL_API_KEY") or None,
        flatten_messages_as_text=False,
        custom_role_conversions={
            MessageRole.USER: "user",
            MessageRole.SYSTEM: "system",
            MessageRole.ASSISTANT: "assistant",
            MessageRole.TOOL_CALL: "assistant",
            MessageRole.TOOL_RESPONSE: "user",
        },
        temperature=0.0,
        max_tokens=512,
        num_ctx=8192,
        drop_params=False,
        timeout=600,
    )
