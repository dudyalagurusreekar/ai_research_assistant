"""Interface for capability router."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from core.models.request import Request


@dataclass
class RoutingDecision:
    """Encapsulates a capability router decision without executing the tool."""

    tool_name: str
    capability: str
    confidence: float
    reason: str


class IRouter(ABC):
    """Abstract Interface for routing requests to suitable capabilities."""

    @abstractmethod
    def route(self, request: Request) -> Optional[RoutingDecision]:
        """Evaluate request and return a routing decision.

        Args:
            request: Unified request object.

        Returns:
            RoutingDecision if a matching tool/capability is found, else None.
        """
        pass
