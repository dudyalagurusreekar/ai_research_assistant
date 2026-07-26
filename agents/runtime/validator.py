import ast
import inspect
from pathlib import Path
from typing import Dict, Any, List, Optional
from agents.runtime.policy import ImportPolicyManager, ImportStatus

class ValidationError:
    """Represents a code validation error."""
    def __init__(self, code: str, message: str, line: int, col: int):
        self.code = code
        self.message = message
        self.line = line
        self.col = col

    def __repr__(self):
        return f"[{self.code}] Line {self.line}, Col {self.col}: {self.message}"

class ValidationWarning:
    """Represents a code validation warning."""
    def __init__(self, code: str, message: str, line: int, col: int):
        self.code = code
        self.message = message
        self.line = line
        self.col = col

    def __repr__(self):
        return f"[{self.code}] Line {self.line}, Col {self.col}: {self.message}"

class ValidationResult:
    """Wraps validation outcomes."""
    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationWarning] = []

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


class CodeValidationVisitor(ast.NodeVisitor):
    """Traverses code AST to identify capability mismatches and security blocks."""
    def __init__(self, policy_manager: ImportPolicyManager, tools: Dict[str, Any], workspace_root: Path):
        self.policy_manager = policy_manager
        self.tools = tools
        self.workspace_root = workspace_root
        self.result = ValidationResult()

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self._check_module_import(alias.name, node.lineno, node.col_offset)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            self._check_module_import(node.module, node.lineno, node.col_offset)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # 1. Blocked global function invocations
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in {"exec", "eval", "__import__"}:
                self.result.errors.append(ValidationError(
                    code="BLOCKED_BUILTIN",
                    message=f"Direct call to built-in function '{func_name}' is strictly blocked for safety.",
                    line=node.lineno,
                    col=node.col_offset
                ))
            
            # 2. Tool calls parameter check
            if func_name in self.tools:
                self._validate_tool_call(func_name, node)

        # 3. Blocked attributes on module access
        elif isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr
            if attr_name in {"system", "popen", "spawn", "fork"}:
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "os":
                    self.result.errors.append(ValidationError(
                        code="BLOCKED_PROCESS",
                        message=f"Process execution via 'os.{attr_name}' is strictly blocked.",
                        line=node.lineno,
                        col=node.col_offset
                    ))

        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, str):
            self._check_path_safety(node.value, node.lineno, node.col_offset)
        self.generic_visit(node)

    def _check_module_import(self, module_name: str, line: int, col: int):
        eval_res = self.policy_manager.evaluate_import(module_name)
        status = eval_res["status"]
        if status == ImportStatus.BLOCK:
            self.result.errors.append(ValidationError(
                code="UNAUTHORIZED_IMPORT",
                message=eval_res["message"],
                line=line,
                col=col
            ))
        elif status == ImportStatus.RESTRICT:
            self.result.warnings.append(ValidationWarning(
                code="RESTRICTED_IMPORT",
                message=eval_res["message"],
                line=line,
                col=col
            ))
        elif status == ImportStatus.UNAVAILABLE:
            self.result.errors.append(ValidationError(
                code="MISSING_LIBRARY",
                message=eval_res["message"],
                line=line,
                col=col
            ))

    def _validate_tool_call(self, tool_name: str, node: ast.Call):
        tool = self.tools[tool_name]
        try:
            sig = inspect.signature(tool.forward)
            params = list(sig.parameters.values())
            if params and params[0].name == 'self':
                params = params[1:]
            tool_sig = inspect.Signature(params)
        except Exception:
            return

        args_count = len(node.args)
        kwargs_names = [kw.arg for kw in node.keywords]
        
        dummy_args = [None] * args_count
        dummy_kwargs = {name: None for name in kwargs_names if name is not None}
        
        try:
            tool_sig.bind(*dummy_args, **dummy_kwargs)
        except TypeError as err:
            self.result.errors.append(ValidationError(
                code="INVALID_TOOL_USAGE",
                message=f"Signature match failed for tool '{tool_name}': {str(err)}",
                line=node.lineno,
                col=node.col_offset
            ))

    def _check_path_safety(self, val: str, line: int, col: int):
        is_windows_path = len(val) > 1 and val[1] == ":"
        is_posix_path = val.startswith("/")
        
        if is_windows_path or is_posix_path:
            try:
                resolved_path = Path(val).resolve()
                if not resolved_path.is_relative_to(self.workspace_root):
                    self.result.errors.append(ValidationError(
                        code="OUT_OF_BOUNDS_PATH",
                        message=f"Path '{val}' is outside the authorized workspace directory '{self.workspace_root}'.",
                        line=line,
                        col=col
                    ))
            except Exception:
                pass


class CodeValidationEngine:
    """
    Statically analyzes code actions before execution, identifying syntax issues,
    unauthorized imports, signature mismatch in tool usage, and directory escapes.
    """

    def __init__(self, policy_manager: ImportPolicyManager, workspace_root: Optional[Path] = None):
        self.policy_manager = policy_manager
        self.workspace_root = workspace_root or Path("d:/AI-Research-Assistant").resolve()

    def validate(self, code: str, tools: Dict[str, Any]) -> ValidationResult:
        """Parses python source code and traverses it for validation rules."""
        result = ValidationResult()
        
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            result.errors.append(ValidationError(
                code="SYNTAX_ERROR",
                message=f"Syntax Error: {e.msg} at line {e.lineno}, column {e.offset}",
                line=e.lineno or 1,
                col=e.offset or 1
            ))
            return result

        visitor = CodeValidationVisitor(self.policy_manager, tools, self.workspace_root)
        visitor.visit(tree)
        return visitor.result
