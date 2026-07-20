from pathlib import Path


PROMPT_DIR = Path(__file__).parent


def load_prompt(category: str, name: str) -> str:
    """
    Load a prompt from the prompts directory.

    Example:
        load_prompt("system", "research")
    """
    file_path = PROMPT_DIR / category / f"{name}.md"

    if not file_path.exists():
        raise FileNotFoundError(f"Prompt not found: {file_path}")

    return file_path.read_text(encoding="utf-8")