from enum import Enum
from typing import Dict, Any, List, Optional

class ImportStatus(str, Enum):
    ALLOW = "ALLOW"
    RESTRICT = "RESTRICT"
    BLOCK = "BLOCK"
    UNAVAILABLE = "UNAVAILABLE"

class ImportPolicyManager:
    """
    Manages allowed, restricted, and blocked packages for agent code execution.
    Exposes policies and fallback mappings.
    """

    def __init__(self, additional_authorized_imports: Optional[List[str]] = None):
        self.additional_authorized_imports = additional_authorized_imports or []
        
        # Base allowed builtins in smolagents
        self.base_allowed = {
            "collections", "datetime", "itertools", "math", "queue", "random", "re", 
            "stat", "statistics", "time", "unicodedata", "json", "csv"
        }
        
        # Strictly blocked for security/sandboxing
        self.blocked_modules = {
            "subprocess", "pty", "multiprocessing", "threading", "socket", 
            "os.system", "shutil", "pdb", "bdb"
        }
        
        # Restricted modules with configured fallbacks
        self.restricted_fallbacks = {
            "requests": "agents.runtime.fallbacks.requests_fallback",
            "pandas": "agents.runtime.fallbacks.pandas_fallback",
            "numpy": "agents.runtime.fallbacks.numpy_fallback"
        }

    def evaluate_import(self, module_name: str) -> Dict[str, Any]:
        """
        Determines the safety status and fallback path for a module import.
        Returns a dict: {"status": ImportStatus, "fallback": str, "message": str}
        """
        # Automatically allow safe fallback shims
        if module_name.startswith("agents.runtime.fallbacks"):
            return {
                "status": ImportStatus.ALLOW,
                "fallback": None,
                "message": f"Module '{module_name}' is a safe runtime fallback shim."
            }

        # Split dot notation to check base package
        base_module = module_name.split('.')[0]
        
        if base_module in self.blocked_modules or module_name in self.blocked_modules:
            return {
                "status": ImportStatus.BLOCK,
                "fallback": None,
                "message": f"Import of module '{module_name}' is strictly blocked for security and sandboxing constraints."
            }
            
        if base_module in self.restricted_fallbacks:
            return {
                "status": ImportStatus.RESTRICT,
                "fallback": self.restricted_fallbacks[base_module],
                "message": f"Module '{base_module}' is restricted. Redirecting to its standard-library compatible fallback shims."
            }

        # Check if allowed in base allowed or additional authorized list
        if base_module in self.base_allowed or base_module in self.additional_authorized_imports:
            return {
                "status": ImportStatus.ALLOW,
                "fallback": None,
                "message": f"Module '{module_name}' is explicitly authorized."
            }

        # Check if it's installed
        import importlib.util
        try:
            spec = importlib.util.find_spec(base_module)
            installed = spec is not None
        except Exception:
            installed = False
            
        if not installed:
            return {
                "status": ImportStatus.UNAVAILABLE,
                "fallback": None,
                "message": f"Module '{module_name}' is not installed in the python environment."
            }

        return {
            "status": ImportStatus.BLOCK,
            "fallback": None,
            "message": f"Module '{module_name}' is installed but not authorized in config. Consider passing it in additional_authorized_imports."
        }
