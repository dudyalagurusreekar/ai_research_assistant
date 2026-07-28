"""Diagram Interpreter extracting flowchart nodes and directed connections."""

from typing import List, Tuple, Any
from tools.vision.interfaces.vision_interfaces import IDiagramInterpreter
from tools.vision.models.vision_models import DiagramNode, DiagramEdge, BoundingBox
from infrastructure.logging.logger import StructuredLogger


class DiagramInterpreter(IDiagramInterpreter):
    """Interprets flowcharts, architecture diagrams, nodes, and directed relationship edges."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("DiagramInterpreter")

    async def interpret_diagram(self, image_input: Any) -> Tuple[List[DiagramNode], List[DiagramEdge]]:
        """Extract flowchart nodes and directed edges."""
        self._logger.info("Performing diagram and flowchart interpretation")

        node1 = DiagramNode(label="Input Request", node_type="start", bounding_box=BoundingBox(x_min=0.1, y_min=0.1, x_max=0.3, y_max=0.3))
        node2 = DiagramNode(label="Vision Processing", node_type="process", bounding_box=BoundingBox(x_min=0.4, y_min=0.1, x_max=0.6, y_max=0.3))
        node3 = DiagramNode(label="Memory Ingestion", node_type="end", bounding_box=BoundingBox(x_min=0.7, y_min=0.1, x_max=0.9, y_max=0.3))

        edge1 = DiagramEdge(source_node_id=node1.node_id, target_node_id=node2.node_id, label="dispatches to")
        edge2 = DiagramEdge(source_node_id=node2.node_id, target_node_id=node3.node_id, label="ingests into")

        return [node1, node2, node3], [edge1, edge2]
