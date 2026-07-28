"""Project Indexer building NormalizedCodeProject models."""

import os
from typing import Optional
from tools.code.interfaces.code_interfaces import IProjectIndexer, ILanguageRegistry
from tools.code.models.code_models import NormalizedCodeProject, CodeFile
from tools.code.registry.language_registry import LanguageRegistry
from infrastructure.logging.logger import StructuredLogger


class ProjectIndexer(IProjectIndexer):
    """Scans project directory trees and delegates parsing to language providers."""

    SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".pytest_cache", "dist", "build", ".idea", ".vscode"}
    SKIP_EXTS = {".pyc", ".pyo", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".tar", ".gz", ".exe", ".dll", ".so", ".dylib"}

    def __init__(self, registry: Optional[ILanguageRegistry] = None) -> None:
        self._logger = StructuredLogger("ProjectIndexer")
        self._registry = registry or LanguageRegistry()

    async def index_project(self, root_path: str) -> NormalizedCodeProject:
        """Scan directory tree and construct NormalizedCodeProject."""
        if not os.path.exists(root_path):
            raise FileNotFoundError(f"Project root path '{root_path}' does not exist.")

        proj_name = os.path.basename(os.path.abspath(root_path)) or "Project"
        project = NormalizedCodeProject(
            project_name=proj_name,
            root_path=os.path.abspath(root_path),
        )

        languages_found = set()

        if os.path.isfile(root_path):
            # Single file indexing
            file_obj = await self._index_single_file(root_path, root_path)
            if file_obj:
                project.files.append(file_obj)
                languages_found.add(file_obj.language)
        else:
            # Recursive directory tree indexing
            for dirpath, dirnames, filenames in os.walk(root_path):
                dirnames[:] = [d for d in dirnames if d not in self.SKIP_DIRS]

                for fname in filenames:
                    ext = os.path.splitext(fname)[1].lower()
                    if ext in self.SKIP_EXTS:
                        continue

                    full_path = os.path.join(dirpath, fname)
                    rel_path = os.path.relpath(full_path, root_path)

                    file_obj = await self._index_single_file(full_path, rel_path)
                    if file_obj:
                        project.files.append(file_obj)
                        languages_found.add(file_obj.language)

        project.total_files = len(project.files)
        project.total_lines = sum(f.line_count for f in project.files)
        project.languages = sorted(list(languages_found))

        self._logger.info(
            f"Indexed project '{proj_name}': {project.total_files} files, {project.total_lines} lines across {len(project.languages)} languages."
        )
        return project

    async def _index_single_file(self, full_path: str, rel_path: str) -> Optional[CodeFile]:
        """Read single file and delegate to language provider."""
        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            ext = os.path.splitext(full_path)[1].lower()
            provider = self._registry.get_provider_for_extension(ext)

            if provider:
                file_obj = await provider.parse_file(rel_path, content)
                file_obj.absolute_path = os.path.abspath(full_path)
                return file_obj
        except Exception as e:
            self._logger.warning(f"Error reading file '{full_path}': {e}")
        return None
