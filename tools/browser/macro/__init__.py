"""Macro Action Engine Package.

Exposes registry, context, base macro interfaces, and macro orchestrator engine.
Registers all built-in macros on import.
"""

from tools.browser.macro.base import (
    BaseMacro,
    MacroError,
    MacroExecutionContext,
    MacroExecutionError,
    MacroRollbackError,
    MacroValidationError,
    global_registry,
    register_macro,
)
from tools.browser.macro.engine import MacroActionEngine

# Import builtins to register them
import tools.browser.macro.builtins

__all__ = [
    "BaseMacro",
    "MacroError",
    "MacroValidationError",
    "MacroExecutionError",
    "MacroRollbackError",
    "MacroExecutionContext",
    "MacroRegistry",
    "MacroActionEngine",
    "global_registry",
    "register_macro",
]
