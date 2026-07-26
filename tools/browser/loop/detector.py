"""Loop Detector Engine.

Maintains execution histories, constructs state transition graphs, runs cycle scans,
filters polling behaviors, and recommends escape recovery options.
"""

import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from tools.browser.core.browser import Browser
from tools.browser.loop.base import LoopDetectionResult, LoopType
from tools.browser.loop.fingerprint import BrowserStateFingerprinter

logger = logging.getLogger("LoopDetector.Engine")


class LoopDetector:
    """Enterprise Loop Detector analyzing execution graphs and patterns.

    Attributes:
        browser: Active Browser facade.
        max_history: Sliding window history boundary constraint.
        min_cycle_repeats: Required consecutive repetitions to flag loops.
        escape_policies: Action suggestions per loop category.
    """

    def __init__(
        self,
        browser: Browser,
        max_history: int = 30,
        min_cycle_repeats: int = 2,
    ) -> None:
        """Initialize the LoopDetector.

        Args:
            browser: The active Browser facade.
            max_history: Maximum history trace size to look back.
            min_cycle_repeats: Minimum cycles count to flag a loop.
        """
        self.browser = browser
        self.max_history = max_history
        self.min_cycle_repeats = min_cycle_repeats
        self._logger = logger

        # Sliding window queues
        self.history_actions: List[Dict[str, Any]] = []
        self.history_urls: List[str] = []
        self.history_fingerprints: List[str] = []
        self.history_thoughts: List[str] = []
        self.history_recoveries: List[str] = []

        # Default escape recommendation strategies per LoopType
        self.escape_policies: Dict[LoopType, str] = {
            LoopType.NAVIGATION: "rollback",   # Go back in navigation history
            LoopType.ACTION: "skip",           # Skip repeating click/input
            LoopType.STATE: "replan",          # Re-route via planner
            LoopType.RECOVERY: "terminate",     # Terminal failure - recovery is repeating
            LoopType.PLANNER: "replan",        # Force planner to choose alternative action
        }

    def record_step(
        self,
        action_dict: Dict[str, Any],
        url: str,
        thought: Optional[str] = None,
        recovery_strategy: Optional[str] = None,
    ) -> None:
        """Record the current execution step properties in the history list.

        Args:
            action_dict: Parameters representing action executed.
            url: Active target URL.
            thought: Reasoning text from planner.
            recovery_strategy: Strategy name if step was a recovery attempt.
        """
        # Append and crop history to sliding window size
        self.history_actions.append(action_dict)
        self.history_urls.append(url)
        self.history_thoughts.append(thought or "")
        self.history_recoveries.append(recovery_strategy or "")

        # Compute page fingerprint
        fingerprint = BrowserStateFingerprinter.get_fingerprint(self.browser)
        self.history_fingerprints.append(fingerprint)

        if len(self.history_actions) > self.max_history:
            self.history_actions.pop(0)
            self.history_urls.pop(0)
            self.history_thoughts.pop(0)
            self.history_recoveries.pop(0)
            self.history_fingerprints.pop(0)

    def check_loop(self) -> LoopDetectionResult:
        """Analyze execution history paths and graphs to detect cyclic loops.

        Returns:
            LoopDetectionResult: Analysis diagnostic summary.
        """
        if len(self.history_actions) < 3:
            return LoopDetectionResult(loop_detected=False, explanation="History trace is too short.")

        # Filter out valid polling operations from checks
        if self._is_valid_polling():
            self._logger.info("Valid periodic polling or loading state detected. Skipping loop alert.")
            return LoopDetectionResult(loop_detected=False, explanation="Intentional polling or status checking.")

        # 1. Check Recovery loops (same recovery strategy applied to same selector/url)
        recovery_loop = self._detect_recovery_loop()
        if recovery_loop.loop_detected:
            return recovery_loop

        # 2. Check Action sequence cycles
        action_loop = self._detect_action_loop()
        if action_loop.loop_detected:
            return action_loop

        # 3. Check Navigation cycles
        nav_loop = self._detect_navigation_loop()
        if nav_loop.loop_detected:
            return nav_loop

        # 4. Check State Oscillation cycles (fingerprint graphs)
        state_loop = self._detect_state_loop()
        if state_loop.loop_detected:
            return state_loop

        # 5. Check Planner thought repeat loops
        planner_loop = self._detect_planner_loop()
        if planner_loop.loop_detected:
            return planner_loop

        return LoopDetectionResult(loop_detected=False, explanation="No repeating execution loops found.")

    def _is_valid_polling(self) -> bool:
        """Heuristically identify if repeats are part of a valid status polling.

        Returns:
            bool: True if repeats match polling signatures.
        """
        # Look at last 4 actions. If all click a selector containing "poll", "status", "refresh", "wait"
        # or if input contains polling query indicators.
        last_actions = self.history_actions[-4:]
        for act in last_actions:
            action_name = act.get("action", "").lower()
            selector = (act.get("selector") or "").lower()
            text_input = (act.get("text_input") or "").lower()
            
            # Action keywords representing polling
            if action_name in ["wait_for_selector", "wait_for_network_idle"]:
                return True
            if any(w in selector for w in ["poll", "status", "refresh", "loading", "spinner", "progress"]):
                return True
            if any(w in text_input for w in ["status", "check"]):
                return True
                
        # Also check current page source for loading message indicators
        try:
            text_res = self.browser.get_clean_text()
            page_text = (text_res.data or "").lower()
            if any(w in page_text for w in ["loading...", "updating...", "please wait"]):
                return True
        except Exception:
            pass

        return False

    def _detect_recovery_loop(self) -> LoopDetectionResult:
        """Scan for cyclic recovery attempts applied repeatedly."""
        non_empty_recoveries = [r for r in self.history_recoveries if r]
        if len(non_empty_recoveries) >= 3:
            # Check if same recovery is repeated on the same target selector
            last_three_revs = non_empty_recoveries[-3:]
            last_three_actions = [a for a, r in zip(self.history_actions, self.history_recoveries) if r][-3:]
            
            if len(set(last_three_revs)) == 1:
                # Same strategy name
                last_three_selectors = [a.get("selector") for a in last_three_actions]
                if len(set(last_three_selectors)) == 1:
                    strategy_name = last_three_revs[0]
                    target = last_three_selectors[0] or "unknown selector"
                    return LoopDetectionResult(
                        loop_detected=True,
                        loop_type=LoopType.RECOVERY,
                        confidence=0.95,
                        explanation=f"Cyclic self-healing recovery loops: Strategy '{strategy_name}' applied to selector '{target}' repeatedly.",
                        cycle_length=1,
                        recommended_escape=self.escape_policies[LoopType.RECOVERY],
                    )
        return LoopDetectionResult(loop_detected=False)

    def _detect_action_loop(self) -> LoopDetectionResult:
        """Scan for repeating sequences of action signatures."""
        action_keys = []
        for act in self.history_actions:
            action_keys.append((act.get("action"), act.get("selector"), act.get("text_input")))

        # Scan for cycle length k from 1 to 5
        n = len(action_keys)
        for k in range(1, 6):
            if n >= k * self.min_cycle_repeats:
                # Extract target pattern
                pattern = action_keys[-k:]
                is_loop = True
                for r in range(1, self.min_cycle_repeats):
                    segment = action_keys[-(r + 1) * k : -r * k]
                    if segment != pattern:
                        is_loop = False
                        break
                if is_loop and pattern[0][0] is not None:
                    # Valid loop detected
                    return LoopDetectionResult(
                        loop_detected=True,
                        loop_type=LoopType.ACTION,
                        confidence=0.85 + (0.05 * (self.min_cycle_repeats - 2)),
                        explanation=f"Cyclic execution actions: Repeating action patterns of length {k} detected.",
                        cycle_length=k,
                        recommended_escape=self.escape_policies[LoopType.ACTION],
                        details={"pattern": pattern},
                    )
        return LoopDetectionResult(loop_detected=False)

    def _detect_navigation_loop(self) -> LoopDetectionResult:
        """Scan for cyclic URL history redirection sequences."""
        n = len(self.history_urls)
        for k in range(1, 6):
            if n >= k * self.min_cycle_repeats:
                pattern = self.history_urls[-k:]
                is_loop = True
                for r in range(1, self.min_cycle_repeats):
                    segment = self.history_urls[-(r + 1) * k : -r * k]
                    if segment != pattern:
                        is_loop = False
                        break
                if is_loop and len(set(pattern)) > 1:
                    # A loop of at least 2 distinct URLs
                    return LoopDetectionResult(
                        loop_detected=True,
                        loop_type=LoopType.NAVIGATION,
                        confidence=0.9,
                        explanation=f"Cyclic url navigation loop: Oscillating between pages of cycle length {k}.",
                        cycle_length=k,
                        recommended_escape=self.escape_policies[LoopType.NAVIGATION],
                        details={"pattern": pattern},
                    )
        return LoopDetectionResult(loop_detected=False)

    def _detect_state_loop(self) -> LoopDetectionResult:
        """Scan for layout state fingerprint oscillations."""
        n = len(self.history_fingerprints)
        for k in range(1, 6):
            if n >= k * self.min_cycle_repeats:
                pattern = self.history_fingerprints[-k:]
                is_loop = True
                for r in range(1, self.min_cycle_repeats):
                    segment = self.history_fingerprints[-(r + 1) * k : -r * k]
                    if segment != pattern:
                        is_loop = False
                        break
                if is_loop and len(set(pattern)) > 1:
                    return LoopDetectionResult(
                        loop_detected=True,
                        loop_type=LoopType.STATE,
                        confidence=0.85,
                        explanation=f"Cyclic layout oscillations: Page layout state cycle of length {k} detected.",
                        cycle_length=k,
                        recommended_escape=self.escape_policies[LoopType.STATE],
                    )
        return LoopDetectionResult(loop_detected=False)

    def _detect_planner_loop(self) -> LoopDetectionResult:
        """Scan for identical reasoning thoughts continuously re-generated."""
        # Clean thoughts (exclude empty thought logs)
        thoughts = [t for t in self.history_thoughts if t]
        n = len(thoughts)
        if n >= 3:
            last_thought = thoughts[-1]
            # Simple check if same thought is repeated
            repeats = 1
            for t in reversed(thoughts[:-1]):
                if t == last_thought:
                    repeats += 1
                else:
                    break
            if repeats >= 3:
                return LoopDetectionResult(
                    loop_detected=True,
                    loop_type=LoopType.PLANNER,
                    confidence=0.9,
                    explanation=f"Repeating planner decisions: Thought '{last_thought[:40]}...' generated {repeats} times consecutive.",
                    cycle_length=1,
                    recommended_escape=self.escape_policies[LoopType.PLANNER],
                )
        return LoopDetectionResult(loop_detected=False)
