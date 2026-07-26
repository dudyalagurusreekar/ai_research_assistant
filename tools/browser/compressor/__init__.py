"""Prompt Compressor Package.

Exposes strategy types, compressed context structures, base classes, and orchestrator pipelines.
"""

from tools.browser.compressor.base import (
    BaseCompressorStrategy,
    CompressedContext,
    CompressionStrategyType,
    PromptCompressorError,
)
from tools.browser.compressor.pipeline import PromptCompressor
from tools.browser.compressor.strategies import (
    AbstractiveCompressorStrategy,
    ExtractiveCompressorStrategy,
    RecencyWeightingStrategy,
    SemanticDeduplicationStrategy,
)

__all__ = [
    "PromptCompressor",
    "CompressedContext",
    "CompressionStrategyType",
    "BaseCompressorStrategy",
    "PromptCompressorError",
    "SemanticDeduplicationStrategy",
    "ExtractiveCompressorStrategy",
    "AbstractiveCompressorStrategy",
    "RecencyWeightingStrategy",
]
