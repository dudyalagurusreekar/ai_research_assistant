"""Answer Formatter for GAIA normalization and formatting validation."""

import re
from typing import Optional
from tools.benchmark.interfaces.benchmark_interfaces import IAnswerFormatter
from tools.benchmark.models.benchmark_models import AnswerFormatConfig
from infrastructure.logging.logger import StructuredLogger


class AnswerFormatter(IAnswerFormatter):
    """Produces answers adhering strictly to GAIA and benchmark-specific formatting specifications."""

    def __init__(self, default_config: Optional[AnswerFormatConfig] = None) -> None:
        self._logger = StructuredLogger("AnswerFormatter")
        self._default_config = default_config or AnswerFormatConfig()

    def format_answer(self, raw_answer: str, config: Optional[AnswerFormatConfig] = None) -> str:
        """Format and normalize answer string according to configuration rules."""
        if not raw_answer:
            return ""

        cfg = config or self._default_config
        text = raw_answer.strip()

        # 1. Remove unnecessary explanations & prefixes
        if cfg.remove_explanations:
            text = self._strip_explanations(text)

        # 2. String normalization (strip markdown formatting, outer quotes, trailing periods)
        if cfg.normalize_strings:
            text = self._normalize_string(text)

        # 3. Numeric normalization
        if cfg.normalize_numbers:
            text = self._normalize_number(text)

        # 4. Comma-separated list normalization
        if cfg.normalize_lists and "," in text and not re.search(r"\d+,\d+", text):
            text = self._normalize_list(text, cfg)

        # 5. Apply custom regex if specified
        if cfg.custom_regex:
            match = re.search(cfg.custom_regex, text)
            if match:
                text = match.group(0)

        return text.strip()

    def validate_format(self, formatted_answer: str, config: Optional[AnswerFormatConfig] = None) -> bool:
        """Validate whether answer satisfies format constraints."""
        if not formatted_answer or not formatted_answer.strip():
            return False

        # Ensure no verbose conversational headers remain
        verbose_patterns = [
            r"^the answer is",
            r"^based on the data",
            r"^according to",
            r"here is the answer",
        ]
        low = formatted_answer.lower()
        for pat in verbose_patterns:
            if re.search(pat, low):
                return False

        return True

    def _strip_explanations(self, text: str) -> str:
        """Remove reasoning, lead-in phrases, and markdown wrappers."""
        # Strip lead-in markdown bold prefix like "**Answer:** "
        text = re.sub(r"^\*\*(?:Final Answer|Answer)\*\*:\s*", "", text, flags=re.IGNORECASE)

        # Check for explicit answer markers ending with colon or equals
        match = re.search(r"(?:final answer|the answer|result)\s*(?:is)?\s*[:=]\s*(.*)$", text, re.IGNORECASE | re.DOTALL)
        if match:
            text = match.group(1).strip()
        else:
            match_simple = re.search(r"^answer\s*[:=]\s*(.*)$", text, re.IGNORECASE | re.DOTALL)
            if match_simple:
                text = match_simple.group(1).strip()

        if re.match(r"^is[:\s]+", text, re.IGNORECASE):
            text = re.sub(r"^is[:\s]+", "", text, flags=re.IGNORECASE).strip()

        # Remove single/double backticks or quotes wrapping entire text
        if (text.startswith("`") and text.endswith("`")) or (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            text = text[1:-1].strip()

        # Take first line if multiple lines and first line looks complete
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if len(lines) > 1:
            if len(lines[0]) < 100 and not lines[0].lower().startswith("here"):
                text = lines[0]
            else:
                text = lines[-1]

        return text

    def _normalize_string(self, text: str) -> str:
        """Remove markdown syntax, trailing punctuation, and extra whitespace."""
        # Remove markdown bold/italics
        text = re.sub(r"\*\*|\*", "", text)
        # Remove trailing period if it's not a decimal point
        if text.endswith(".") and not re.search(r"\d+\.$", text):
            text = text[:-1].strip()
        # Collapse multi-spaces
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _normalize_number(self, text: str) -> str:
        """Normalize currency, percentage, and integer/float formatting."""
        val_str = text.replace("$", "").replace("%", "").replace(",", "").strip()
        try:
            val_float = float(val_str)
            if val_float.is_integer():
                return str(int(val_float))
            return str(round(val_float, 4))
        except ValueError:
            pass
        return text

    def _normalize_list(self, text: str, cfg: AnswerFormatConfig) -> str:
        """Sort and clean comma-separated lists."""
        items = [i.strip() for i in text.split(",") if i.strip()]
        if len(items) > 1:
            cleaned = [re.sub(r"^['\"]|['\"]$", "", item).strip() for item in items]
            if cfg.normalize_strings:
                cleaned = [item.lower() for item in cleaned]
            return ", ".join(sorted(cleaned))
        return text
