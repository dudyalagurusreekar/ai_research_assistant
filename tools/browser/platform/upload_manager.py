"""Upload Manager for Sprint 11 Browser Automation Platform."""

import logging
import os
import time
from pathlib import Path
from typing import Any, List, Optional, Union
from tools.browser.platform.models import ActionResult, ActionType

logger = logging.getLogger("Tools.Browser.Platform.UploadManager")


class UploadManager:
    """Handles file uploads, file existence validation, and input target binding."""

    async def upload_files(
        self,
        page: Any,
        selector: str,
        file_paths: Union[str, List[str]],
        timeout_ms: int = 10000,
    ) -> ActionResult:
        """Upload one or more files to specified file input element selector."""
        start_time = time.time()
        url = getattr(page, "url", "about:blank")

        paths_list = [file_paths] if isinstance(file_paths, str) else file_paths
        valid_paths = []

        for p in paths_list:
            path_obj = Path(p)
            if not path_obj.exists():
                return ActionResult(
                    success=False,
                    action_type=ActionType.UPLOAD,
                    message=f"File not found: '{p}'",
                    url=url,
                    error=f"File '{p}' does not exist.",
                    execution_time_ms=(time.time() - start_time) * 1000,
                )
            valid_paths.append(str(path_obj.resolve()))

        try:
            if hasattr(page, "set_input_files"):
                await page.set_input_files(selector, valid_paths, timeout=timeout_ms)

            return ActionResult(
                success=True,
                action_type=ActionType.UPLOAD,
                message=f"Uploaded {len(valid_paths)} file(s) into selector '{selector}'.",
                url=url,
                data={
                    "selector": selector,
                    "uploaded_files": valid_paths,
                },
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            logger.error(f"Upload failed for selector '{selector}': {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.UPLOAD,
                message=f"Upload failed: {e}",
                url=url,
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
            )
