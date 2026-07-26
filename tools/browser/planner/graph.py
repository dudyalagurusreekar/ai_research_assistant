"""Task Graph representation and operations for the Browser Task Planner.

Defines the DAG/Graph of TaskNodes, dependency resolution, topological sorting,
syntax validation, and plan optimization rules.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Set


class TaskStatus(str, Enum):
    """Execution statuses for tasks inside the execution graph."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class TaskNode:
    """Represents a single atomic operation or routing branch in the task plan."""

    def __init__(
        self,
        node_id: str,
        name: str,
        action: str,
        params: Optional[Dict[str, Any]] = None,
        dependencies: Optional[List[str]] = None,
        max_retries: int = 0,
        condition: Optional[Dict[str, Any]] = None,
        loop_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the task node.

        Args:
            node_id (str): Unique node string ID.
            name (str): Label describing the task.
            action (str): Task action matching Executor API or routing hooks.
            params (Optional[Dict[str, Any]]): Action inputs.
            dependencies (Optional[List[str]]): IDs of prerequisite task nodes.
            max_retries (int): Retry limit on failure.
            condition (Optional[Dict[str, Any]]): Branching conditions checked at runtime.
            loop_config (Optional[Dict[str, Any]]): Loop/pagination options.
        """
        self.node_id = node_id.strip()
        self.name = name.strip()
        self.action = action.strip().lower()
        self.params = params or {}
        self.dependencies = [d.strip() for d in (dependencies or [])]
        self.max_retries = max_retries
        self.condition = condition
        self.loop_config = loop_config
        
        self.status = TaskStatus.PENDING
        self.retry_count = 0
        self.result: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize TaskNode to dictionary representation."""
        return {
            "id": self.node_id,
            "name": self.name,
            "action": self.action,
            "params": self.params,
            "dependencies": self.dependencies,
            "max_retries": self.max_retries,
            "condition": self.condition,
            "loop_config": self.loop_config,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "result": self.result.to_dict() if hasattr(self.result, "to_dict") else str(self.result) if self.result else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskNode":
        """Deserialize TaskNode from dictionary."""
        node = cls(
            node_id=data["id"],
            name=data["name"],
            action=data["action"],
            params=data.get("params"),
            dependencies=data.get("dependencies"),
            max_retries=data.get("max_retries", 0),
            condition=data.get("condition"),
            loop_config=data.get("loop_config"),
        )
        status_val = data.get("status")
        if status_val:
            node.status = TaskStatus(status_val)
        node.retry_count = data.get("retry_count", 0)
        return node


class TaskGraph:
    """Directed Acyclic Graph (DAG) containing plan tasks and dependency constraints."""

    def __init__(self) -> None:
        """Initialize empty TaskGraph."""
        self.nodes: Dict[str, TaskNode] = {}

    def add_node(self, node: TaskNode) -> None:
        """Add a TaskNode to the graph.

        Args:
            node (TaskNode): Task node to add.
        """
        self.nodes[node.node_id] = node

    def add_dependency(self, from_id: str, to_id: str) -> None:
        """Add a dependency relationship: from_id must complete before to_id runs.

        Args:
            from_id (str): Dependency source task ID.
            to_id (str): Target task ID.
        """
        if to_id in self.nodes:
            if from_id not in self.nodes[to_id].dependencies:
                self.nodes[to_id].dependencies.append(from_id)

    def validate(self) -> List[str]:
        """Validate dependencies and detect cycles.

        Returns:
            List[str]: List of validation error strings. Empty if valid.
        """
        errors = []

        # 1. Check for missing dependencies
        for node_id, node in self.nodes.items():
            for dep in node.dependencies:
                if dep not in self.nodes:
                    errors.append(f"Task '{node_id}' depends on missing task '{dep}'.")

        if errors:
            return errors

        # 2. Cycle Detection using DFS color labeling
        # Colors: 0 = unvisited, 1 = visiting, 2 = visited
        colors: Dict[str, int] = {node_id: 0 for node_id in self.nodes}

        def has_cycle(u: str) -> bool:
            colors[u] = 1  # visiting
            for v in self.nodes[u].dependencies:
                if colors[v] == 1:
                    return True
                if colors[v] == 0:
                    if has_cycle(v):
                        return True
            colors[u] = 2  # visited
            return False

        for node_id in self.nodes:
            if colors[node_id] == 0:
                if has_cycle(node_id):
                    errors.append("Cyclic dependency detected in task plan graph.")
                    break

        # 3. Basic Action Argument Validation
        for node_id, node in self.nodes.items():
            action = node.action
            params = node.params or {}
            if action == "open_url" and not params.get("url") and not params.get("text_input"):
                errors.append(f"Task '{node_id}' (open_url) is missing required 'url' param.")
            elif action in ("click", "double_click", "hover", "clear_input", "submit_form") and not params.get("selector"):
                errors.append(f"Task '{node_id}' ({action}) is missing required 'selector' param.")
            elif action in ("fill_input", "type_text") and (not params.get("selector") or params.get("text_input") is None):
                errors.append(f"Task '{node_id}' ({action}) is missing required 'selector' or 'text_input' params.")

        return errors

    def get_topological_order(self) -> List[str]:
        """Perform topological sort of nodes.

        Returns:
            List[str]: Ordered list of node IDs.
        """
        visited: Set[str] = set()
        order: List[str] = []

        def dfs(u: str):
            visited.add(u)
            for v in self.nodes[u].dependencies:
                if v not in visited:
                    dfs(v)
            order.append(u)

        for node_id in self.nodes:
            if node_id not in visited:
                dfs(node_id)

        return order

    def optimize(self) -> None:
        """Apply graph optimization rules to prune unnecessary browser actions."""
        # Get nodes sorted topologically
        topo_ids = self.get_topological_order()
        
        # Rule 1: Redundant consecutive open_url pruner
        # If u has a dependency on v, and both are open_url to the same URL, prune u
        last_url_by_node: Dict[str, str] = {}
        for node_id in topo_ids:
            node = self.nodes[node_id]
            if node.action == "open_url":
                url = node.params.get("url") or node.params.get("text_input")
                # Check if parent is also open_url with same URL
                same_parent_url = False
                for dep in node.dependencies:
                    parent_node = self.nodes.get(dep)
                    if parent_node and parent_node.action == "open_url":
                        parent_url = parent_node.params.get("url") or parent_node.params.get("text_input")
                        if parent_url == url:
                            same_parent_url = True
                
                if same_parent_url:
                    # Skip execution of this redundant URL open
                    node.status = TaskStatus.SKIPPED
                    node.name += " (Optimized: Redundant open_url)"

        # Rule 2: Prune redundant clear_input before fill_input/type_text
        # If clear_input is immediately followed by fill_input/type_text on the same selector,
        # and has no external dependencies, prune the clear_input.
        for node_id in topo_ids:
            node = self.nodes[node_id]
            if node.action in ("fill_input", "type_text"):
                sel = node.params.get("selector")
                for dep in list(node.dependencies):
                    dep_node = self.nodes.get(dep)
                    if dep_node and dep_node.action == "clear_input" and dep_node.params.get("selector") == sel:
                        # Make sure no other node depends on this clear_input
                        is_depended_elsewhere = False
                        for other_id, other_node in self.nodes.items():
                            if other_id != node_id and dep in other_node.dependencies:
                                is_depended_elsewhere = True
                        
                        if not is_depended_elsewhere:
                            dep_node.status = TaskStatus.SKIPPED
                            dep_node.name += " (Optimized: Merged clear before fill)"
                            # Transfer dependencies of clear_input to fill_input
                            for clear_dep in dep_node.dependencies:
                                if clear_dep not in node.dependencies:
                                    node.dependencies.append(clear_dep)
                            node.dependencies.remove(dep)

        # Rule 3: Scroll Consolidation
        # If u depends on v, both are scroll_page to the same selector & direction, consolidate
        for node_id in topo_ids:
            node = self.nodes[node_id]
            if node.action == "scroll_page" and node.status == TaskStatus.PENDING:
                sel = node.params.get("selector")
                dir_ = node.params.get("scroll_direction") or "down"
                
                for dep in list(node.dependencies):
                    dep_node = self.nodes.get(dep)
                    if (dep_node and dep_node.action == "scroll_page" 
                            and dep_node.status == TaskStatus.PENDING
                            and dep_node.params.get("selector") == sel 
                            and (dep_node.params.get("scroll_direction") or "down") == dir_):
                        
                        # Consolidate amount
                        node_amt = int(node.params.get("scroll_amount", 500))
                        dep_amt = int(dep_node.params.get("scroll_amount", 500))
                        node.params["scroll_amount"] = node_amt + dep_amt
                        
                        dep_node.status = TaskStatus.SKIPPED
                        dep_node.name += " (Optimized: Consolidated scroll)"
                        
                        # Adjust dependencies
                        for scroll_dep in dep_node.dependencies:
                            if scroll_dep not in node.dependencies:
                                node.dependencies.append(scroll_dep)
                        node.dependencies.remove(dep)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize TaskGraph to dictionary."""
        return {
            "tasks": [node.to_dict() for node in self.nodes.values()]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskGraph":
        """Deserialize TaskGraph from dictionary."""
        graph = cls()
        for node_data in data.get("tasks", []):
            node = TaskNode.from_dict(node_data)
            graph.add_node(node)
        return graph
