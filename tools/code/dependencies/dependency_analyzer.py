"""Dependency Analyzer for parsing project manifests."""

import os
import re
from typing import List
from tools.code.interfaces.code_interfaces import IDependencyAnalyzer
from tools.code.models.code_models import DependencyItem
from infrastructure.logging.logger import StructuredLogger


class DependencyAnalyzer(IDependencyAnalyzer):
    """Parses manifest files (requirements.txt, pyproject.toml, package.json, etc.) into DependencyItem list."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("DependencyAnalyzer")

    async def analyze_dependencies(self, root_path: str) -> List[DependencyItem]:
        """Scan project root for manifest files and parse dependencies."""
        deps: List[DependencyItem] = []

        if not os.path.exists(root_path):
            return deps

        # 1. requirements.txt
        req_path = os.path.join(root_path, "requirements.txt")
        if os.path.isfile(req_path):
            deps.extend(self._parse_requirements_txt(req_path))

        # 2. package.json
        pkg_path = os.path.join(root_path, "package.json")
        if os.path.isfile(pkg_path):
            deps.extend(self._parse_package_json(pkg_path))

        self._logger.info(f"Analyzed dependencies in '{root_path}': found {len(deps)} items.")
        return deps

    def _parse_requirements_txt(self, file_path: str) -> List[DependencyItem]:
        """Parse pip requirements.txt file."""
        items = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line_str = line.strip()
                    if line_str and not line_str.startswith("#"):
                        parts = re.split(r"[==|>=|<=|>|<|~=]", line_str, maxsplit=1)
                        pkg_name = parts[0].strip()
                        ver = parts[1].strip() if len(parts) > 1 else "*"
                        if pkg_name:
                            items.append(DependencyItem(package_name=pkg_name, version_spec=ver, ecosystem="pip"))
        except Exception as e:
            self._logger.warning(f"Error parsing requirements.txt: {e}")
        return items

    def _parse_package_json(self, file_path: str) -> List[DependencyItem]:
        """Parse npm package.json file."""
        items = []
        try:
            import json
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
                
            for pkg, ver in data.get("dependencies", {}).items():
                items.append(DependencyItem(package_name=pkg, version_spec=str(ver), ecosystem="npm", is_dev=False))
            for pkg, ver in data.get("devDependencies", {}).items():
                items.append(DependencyItem(package_name=pkg, version_spec=str(ver), ecosystem="npm", is_dev=True))
        except Exception as e:
            self._logger.warning(f"Error parsing package.json: {e}")
        return items
