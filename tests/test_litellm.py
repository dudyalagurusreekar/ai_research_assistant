import litellm

response = litellm.completion(
    model="ollama/qwen2:7b",
    api_base="http://127.0.0.1:11434",
    api_key="ollama",
    messages=[{"role": "user", "content": "Hello"}],
)

print(response.choices[0].message.content)