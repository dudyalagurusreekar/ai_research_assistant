"""
Base tool class for all project tools.
"""

from abc import ABC
from smolagents import Tool


class BaseTool(Tool, ABC):
    """
    Base class for all tools used in the AI Research Assistant.

    Every tool in this project should inherit from BaseTool.
    """

    def __init__(self):
        super().__init__()