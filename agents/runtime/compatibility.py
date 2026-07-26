import ast
from typing import Dict, Any, Optional

class CompatibilityTransformer(ast.NodeTransformer):
    """Transforms restricted imports and incorrect tool calls inside AST."""
    def __init__(self, fallback_mappings: Dict[str, str], tool_parameter_aliases: Dict[str, Dict[str, str]]):
        self.fallback_mappings = fallback_mappings
        self.tool_parameter_aliases = tool_parameter_aliases
        self.modified = False

    def visit_Import(self, node: ast.Import):
        new_names = []
        for alias in node.names:
            base_module = alias.name.split('.')[0]
            if base_module in self.fallback_mappings:
                fallback_module = self.fallback_mappings[base_module]
                new_name = fallback_module + alias.name[len(base_module):]
                asname = alias.asname if alias.asname else base_module
                new_names.append(ast.alias(name=new_name, asname=asname))
                self.modified = True
            else:
                new_names.append(alias)
        node.names = new_names
        return node

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            base_module = node.module.split('.')[0]
            if base_module in self.fallback_mappings:
                fallback_module = self.fallback_mappings[base_module]
                new_module = fallback_module + node.module[len(base_module):]
                node.module = new_module
                self.modified = True
        return node

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            tool_name = node.func.id
            if tool_name in self.tool_parameter_aliases:
                aliases = self.tool_parameter_aliases[tool_name]
                for kw in node.keywords:
                    if kw.arg in aliases:
                        kw.arg = aliases[kw.arg]
                        self.modified = True
        self.generic_visit(node)
        return node


class ExecutionCompatibilityLayer:
    """
    Rewrites invalid or restricted imports and corrects minor tool invocation issues statically.
    """
    def __init__(self):
        self.fallback_mappings = {
            "requests": "agents.runtime.fallbacks.requests_fallback",
            "pandas": "agents.runtime.fallbacks.pandas_fallback",
            "numpy": "agents.runtime.fallbacks.numpy_fallback"
        }
        
        self.tool_parameter_aliases = {
            "file_reader": {"filepath": "path", "file_path": "path"},
            "pdf_reader": {"filepath": "path", "file_path": "path"},
            "webpage_reader": {"url_address": "url"},
            "web_search": {"search_query": "query"},
        }

    def rewrite_statically(self, code: str, validation_result: Any) -> Optional[str]:
        """
        Attempts to edit the code dynamically via AST rewriting.
        Returns the rewritten code string if successful and modified, otherwise returns None.
        """
        try:
            tree = ast.parse(code)
        except Exception:
            return None

        transformer = CompatibilityTransformer(self.fallback_mappings, self.tool_parameter_aliases)
        transformer.visit(tree)
        
        if transformer.modified:
            try:
                return ast.unparse(tree)
            except Exception:
                return None
        return None
