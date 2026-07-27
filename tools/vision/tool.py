"""Smolagents Tool wrapper for the Vision Intelligence Platform."""

from smolagents import Tool
from tools.vision.facade.facade import VisionToolFacade


class VisionTool(Tool):
    """Tool wrapper exposing VisionToolFacade capabilities to smolagents."""

    name = "vision_tool"
    description = "Unified visual understanding tool for image analysis, OCR, screenshots, layout, charts, tables, and diagrams."
    inputs = {
        "action": {
            "type": "string",
            "description": "Action to perform: 'analyze', 'ocr', 'screenshot', 'chart', 'table', or 'diagram'",
            "nullable": True,
        },
        "image": {
            "type": "string",
            "description": "Image file path or URL string",
            "nullable": True,
        },
    }
    output_type = "string"

    def __init__(self, facade: VisionToolFacade = None):
        super().__init__()
        self._facade = facade or VisionToolFacade()

    def forward(self, action: str = "analyze", image: str = "") -> str:
        import asyncio
        return asyncio.run(self._facade.forward(action=action, image=image))
