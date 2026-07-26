"""Type Definitions, Aliases, and Protocols for the Browser Tool.

This module provides common type aliases, generic type definitions, and Python
Protocols defining component contracts for dependency inversion and extension.
"""

from typing import Dict, Any, Union, List, Optional, Tuple, Protocol, runtime_checkable

# Common Type Aliases
URL = str
HeaderDict = Dict[str, str]
QueryParams = Dict[str, Union[str, List[str]]]
Selector = str
JsonDict = Dict[str, Any]
Coordinates = Tuple[int, int]
ViewportSize = Tuple[int, int]


@runtime_checkable
class Validatable(Protocol):
    """Protocol for components that support runtime self-validation."""

    def validate(self) -> bool:
        """Validate internal state, returning True if valid or raising ValidationError."""
        ...


@runtime_checkable
class Serializable(Protocol):
    """Protocol for objects capable of serializing to and from dictionary representations."""

    def to_dict(self) -> JsonDict:
        """Convert object to JSON-serializable dictionary representation."""
        ...

    @classmethod
    def from_dict(cls, data: JsonDict) -> "Serializable":
        """Instantiate object from dictionary representation."""
        ...
