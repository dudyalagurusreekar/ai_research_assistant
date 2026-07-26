import sys
import importlib.metadata
import inspect
from pathlib import Path
from typing import Dict, Any, List

class RuntimeCapabilityManager:
    """
    Discovers the active Python interpreter capabilities, available libraries,
    registered tools, execution boundaries, and file constraints.
    """

    def __init__(self, agent: Any = None):
        self.agent = agent
        self.workspace_root = Path("d:/AI-Research-Assistant").resolve()

    def get_installed_packages(self) -> List[str]:
        """Discovers all installed pip packages in the active environment."""
        try:
            packages = sorted(list({dist.name for dist in importlib.metadata.distributions()}))
            return packages
        except Exception:
            # Fallback to standard check if metadata scanning fails
            common_packages = [
                "requests", "pandas", "numpy", "matplotlib", "scipy", "bs4", 
                "playwright", "httpx", "yaml", "litellm", "smolagents", "pytest"
            ]
            installed = []
            for pkg in common_packages:
                try:
                    importlib.import_module(pkg)
                    installed.append(pkg)
                except ImportError:
                    pass
            return installed

    def get_tools_info(self) -> List[Dict[str, Any]]:
        """Extracts names, descriptions, and input arguments for registered tools."""
        tools_info = []
        if self.agent and hasattr(self.agent, "tools"):
            for tool_name, tool in self.agent.tools.items():
                # Extract signature parameters
                try:
                    sig = inspect.signature(tool.forward)
                    params = []
                    for name, param in sig.parameters.items():
                        if name == 'self':
                            continue
                        default_val = param.default if param.default is not inspect.Parameter.empty else None
                        
                        annotation = param.annotation
                        if annotation is inspect.Parameter.empty:
                            type_name = "Any"
                        elif hasattr(annotation, "__name__"):
                            type_name = annotation.__name__
                        else:
                            type_name = str(annotation)
                            
                        params.append({
                            "name": name,
                            "type": type_name,
                            "required": param.default is inspect.Parameter.empty,
                            "default": default_val
                        })
                except Exception:
                    params = []

                tools_info.append({
                    "name": tool.name or tool_name,
                    "description": tool.description,
                    "arguments": params
                })
        return tools_info

    def discover_capabilities(self) -> Dict[str, Any]:
        """Collects all environment and configuration specifications."""
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        max_steps = 3
        planning_interval = None
        max_print_outputs_length = 5000
        
        if self.agent:
            max_steps = getattr(self.agent, "max_steps", max_steps)
            planning_interval = getattr(self.agent, "planning_interval", planning_interval)
            max_print_outputs_length = getattr(self.agent, "max_print_outputs_length", max_print_outputs_length) or max_print_outputs_length

        capabilities = {
            "python_version": python_version,
            "os_platform": sys.platform,
            "installed_packages": self.get_installed_packages(),
            "registered_tools": self.get_tools_info(),
            "workspace_root": str(self.workspace_root),
            "execution_limits": {
                "max_steps": max_steps,
                "planning_interval": planning_interval,
                "max_print_outputs_length": max_print_outputs_length,
                "timeout_seconds": 300,
            },
            "constraints": {
                "file_system_write_boundary": str(self.workspace_root),
                "unauthorized_modules": ["subprocess", "pty", "multiprocessing", "threading", "socket"]
            }
        }
        return capabilities

    def generate_capability_prompt(self) -> str:
        """Formats the capability report as a clear prompt addition for the LLM."""
        caps = self.discover_capabilities()
        
        tools_desc = []
        for t in caps["registered_tools"]:
            args_str = ", ".join(
                f"{a['name']}: {a['type']}{' (required)' if a['required'] else ''}" 
                for a in t["arguments"]
            )
            tools_desc.append(f"- `{t['name']}({args_str})`: {t['description']}")
        
        tools_prompt = "\n".join(tools_desc) if tools_desc else "- No custom tools registered."
        
        packages_of_interest = ["requests", "pandas", "numpy", "bs4", "litellm", "playwright", "smolagents", "httpx"]
        available_pkg = [p for p in caps["installed_packages"] if p.lower() in packages_of_interest]
        
        prompt = f"""
### RUNTIME ENVIRONMENT CAPABILITIES & CONSTRAINTS
- **Python Version**: {caps['python_version']} (Platform: {caps['os_platform']})
- **Available Third-Party Libraries**: {', '.join(available_pkg) if available_pkg else 'None'}
- **Authorized Workspace Directory**: `{caps['workspace_root']}` (All file reads/writes must be relative or inside this directory)
- **Execution Limits**: Max Steps: {caps['execution_limits']['max_steps']} | Print Output Limit: {caps['execution_limits']['max_print_outputs_length']} chars
- **Security Restrictions**:
  - Direct execution of processes (e.g. `subprocess`, `os.system`, `shutil`) is STRICTLY BLOCKED.
  - Do not use raw socket networking.
- **Available Helper Tools (can be called as python functions inside your code block)**:
{tools_prompt}
"""
        return prompt
