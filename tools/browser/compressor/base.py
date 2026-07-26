"""Base classes, enums, DTOs, and exception types for prompt context compression.
"""

import abc
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class PromptCompressorError(Exception):
    """Base exception for all prompt compression errors."""
    pass


class CompressionStrategyType(str, Enum):
    """Supported prompt context compression strategies."""

    EXTRACTIVE = "EXTRACTIVE"          # Filters low-importance steps, preserves vital ones
    ABSTRACTIVE = "ABSTRACTIVE"        # Replaces raw steps list with template summaries
    DEDUPLICATION = "DEDUPLICATION"    # Consolidated repeating loops/duplicate transitions
    RECENCY = "RECENCY"                # Details recent history, summaries older steps


@dataclass
class CompressedContext:
    """Consolidated outcome of the context compression operation.

    Attributes:
        compressed_text: The finalized compressed text string.
        original_tokens: Estimate of input tokens before compression.
        compressed_tokens: Estimate of tokens after compression.
        compression_ratio: Ratio showing size reduction (0.0 to 1.0).
        preserved_checkpoints: List of preserved checkpoint details.
        details: Diagnostic parameters mapping.
    """

    compressed_text: str
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    preserved_checkpoints: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert compressed context info to dictionary."""
        return {
            "compressed_text": self.compressed_text,
            "original_tokens": self.original_tokens,
            "compressed_tokens": self.compressed_tokens,
            "compression_ratio": self.compression_ratio,
            "preserved_checkpoints": self.preserved_checkpoints,
            "details": self.details,
        }


class BaseCompressorStrategy(abc.ABC):
    """Abstract base class for all prompt compression strategies."""

    @property
    @abc.abstractmethod
    def strategy_type(self) -> CompressionStrategyType:
        """The strategy categorization type."""
        pass

    @abc.abstractmethod
    def compress(
        self,
        steps: List[Dict[str, Any]],
        max_tokens_target: int,
        is_aggressive: bool = False,
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Run compression over step traces and return compressed step dictionaries.

        Args:
            steps: List of step dictionaries.
            max_tokens_target: Target maximum token limit.
            is_aggressive: If True, executes aggressive compression rules.

        Returns:
            Tuple[List[Dict[str, Any]], List[str]]: Compressed step list, and list of preserved details.
        """
        pass
