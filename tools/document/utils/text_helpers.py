"""Text manipulation, normalization, and token estimation helpers."""

import re
import hashlib


def clean_text_content(text: str) -> str:
    """Normalize whitespace, remove null bytes and control chars."""
    if not text:
        return ""
    # Remove null bytes
    text = text.replace("\x00", "")
    # Replace non-breaking spaces
    text = text.replace("\xa0", " ")
    # Replace multiple trailing/leading spaces on lines
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    # Remove excessive blank lines (>2)
    cleaned_lines = []
    blank_count = 0
    for line in lines:
        if not line:
            blank_count += 1
            if blank_count <= 2:
                cleaned_lines.append("")
        else:
            blank_count = 0
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()


def estimate_tokens(text: str) -> int:
    """Approximate word/token count using word split heuristic."""
    if not text:
        return 0
    words = re.findall(r"\w+", text)
    return max(1, int(len(words) * 1.3))


def compute_sha256(content: bytes) -> str:
    """Calculate SHA256 hex digest of bytes."""
    return hashlib.sha256(content).hexdigest()
