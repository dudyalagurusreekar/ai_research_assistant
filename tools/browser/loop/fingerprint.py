"""Browser State Fingerprinter.

Generates stable hashes representing browser state configurations (layout, URL, scroll)
to detect matching state cycles.
"""

import hashlib
import json
import logging

from tools.browser.core.browser import Browser

logger = logging.getLogger("LoopDetector.Fingerprinter")


class BrowserStateFingerprinter:
    """Generates hashes representing the layout and navigation state of a page."""

    @staticmethod
    def get_fingerprint(browser: Browser) -> str:
        """Extract browser properties and hash them to form a state signature.

        Args:
            browser: The active Browser facade.

        Returns:
            str: SHA-256 hash representation of the page layout.
        """
        # 1. Fetch current URL
        url_res = browser.get_current_url()
        url = (url_res.data or "").split("?")[0].split("#")[0].lower()  # ignore query/hash parameters

        # 2. Fetch page title
        title_res = browser.get_page_title()
        title = (title_res.data or "").strip().lower()

        # 3. Query layout metrics via JS scroll + forms + element count
        element_count = 0
        scroll_pos = {"x": 0, "y": 0}
        forms_summary = ""

        try:
            # Query elements count and scroll coordinates directly
            stats_res = browser.execute_javascript(
                """(() => {
                    return JSON.stringify({
                        elementCount: document.getElementsByTagName('*').length,
                        scrollX: window.scrollX || window.pageXOffset || 0,
                        scrollY: window.scrollY || window.pageYOffset || 0
                    });
                })()"""
            )
            if stats_res.success and stats_res.data:
                stats = json.loads(stats_res.data)
                element_count = stats.get("elementCount", 0)
                scroll_pos = {
                    "x": int(stats.get("scrollX", 0)),
                    "y": int(stats.get("scrollY", 0)),
                }
        except Exception as e:
            logger.debug(f"Failed to query element count and scroll positions: {e}")

        try:
            # Query active forms fields counts to detect state changes during inputs
            forms_res = browser.execute_javascript(
                """(() => {
                    const forms = document.querySelectorAll('form');
                    return JSON.stringify(Array.from(forms).map(f => {
                        return {
                            inputs: f.querySelectorAll('input, select, textarea').length,
                            action: f.action || ''
                        };
                    }));
                })()"""
            )
            if forms_res.success and forms_res.data:
                forms_summary = forms_res.data
        except Exception as e:
            logger.debug(f"Failed to query form specifications: {e}")

        # Combine items into a serialized JSON string
        state_dict = {
            "url": url,
            "title": title,
            "element_count": element_count,
            "scroll_x": scroll_pos["x"],
            "scroll_y": scroll_pos["y"],
            "forms": forms_summary,
        }

        serialized = json.dumps(state_dict, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
