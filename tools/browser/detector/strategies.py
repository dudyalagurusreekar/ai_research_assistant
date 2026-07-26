"""Core evaluation strategies for completion detection.

Implements strategies parsing evidence, artifacts, redirection pages, auth blockers,
and execution traces.
"""

import logging
import re
from typing import Any, Dict, List, Set

from tools.browser.detector.base import (
    BaseCompletionStrategy,
    CompletionContext,
    CompletionState,
    CompletionStatus,
)

logger = logging.getLogger("CompletionDetector.Strategies")


class ObjectiveEvidenceStrategy(BaseCompletionStrategy):
    """Scans clean page text and tags for indicator keywords matching the objective."""

    @property
    def name(self) -> str:
        return "objective_evidence"

    def evaluate(self, ctx: CompletionContext) -> CompletionStatus:
        if not ctx.objective:
            return CompletionStatus(CompletionState.INCOMPLETE, 0.0, "Objective is empty.")

        # 1. Fetch current clean page text
        text_res = ctx.browser.get_clean_text()
        page_text = (text_res.data or "").lower()

        # 2. Extract keywords from objective (alphanumeric words > 3 characters)
        obj_words = set(re.findall(r"\b\w{4,}\b", ctx.objective.lower()))
        # Remove common stopwords
        stopwords = {"this", "that", "with", "from", "then", "into", "their", "after", "find", "search", "show"}
        keywords = obj_words - stopwords

        if not keywords:
            return CompletionStatus(CompletionState.INCOMPLETE, 0.0, "No unique keywords extracted from objective.")

        # 3. Check matched keywords
        matches = [kw for kw in keywords if kw in page_text]
        match_ratio = len(matches) / len(keywords) if keywords else 0.0

        evidence = [f"Matched objective keywords: {matches}"]
        details = {"match_ratio": match_ratio, "total_keywords": len(keywords), "matches_count": len(matches)}

        if match_ratio >= 0.7:
            return CompletionStatus(
                CompletionState.COMPLETED,
                confidence=match_ratio,
                explanation=f"High keyword matching density ({match_ratio:.1%}) on page content.",
                evidence=evidence,
                details=details,
            )
        elif match_ratio >= 0.25:
            return CompletionStatus(
                CompletionState.PARTIAL,
                confidence=match_ratio,
                explanation=f"Moderate keyword match density ({match_ratio:.1%}).",
                evidence=evidence,
                details=details,
            )
        else:
            return CompletionStatus(
                CompletionState.INCOMPLETE,
                confidence=match_ratio,
                explanation="Low keyword match density.",
                evidence=evidence,
                details=details,
            )


class ArtifactSuccessStrategy(BaseCompletionStrategy):
    """Validates the collection and existence of files, downloads, or variables."""

    @property
    def name(self) -> str:
        return "artifact_success"

    def evaluate(self, ctx: CompletionContext) -> CompletionStatus:
        objective_lower = ctx.objective.lower()

        # 1. Check if objective implies file download
        implies_download = any(w in objective_lower for w in ["download", "save", "pdf", "csv", "xlsx", "zip", "export"])

        if implies_download:
            # Look inside extracted_artifacts or context variables for files
            downloaded_files = ctx.extracted_artifacts.get("downloaded_files") or ctx.metadata.get("downloaded_files")
            file_path = ctx.extracted_artifacts.get("file_path") or ctx.metadata.get("file_path")

            evidence = []
            if downloaded_files:
                evidence.append(f"Downloaded files list: {downloaded_files}")
            if file_path:
                evidence.append(f"Output file path: {file_path}")

            if downloaded_files or file_path:
                return CompletionStatus(
                    CompletionState.COMPLETED,
                    confidence=1.0,
                    explanation="Required file downloads or export paths have been verified in execution cache.",
                    evidence=evidence,
                )
            
            # Look inside history for completed download actions
            download_actions = [h for h in ctx.history if h.get("action") in ["download_file", "macro_download_file"]]
            successful_downloads = [d for d in download_actions if d.get("success")]
            if successful_downloads:
                return CompletionStatus(
                    CompletionState.COMPLETED,
                    confidence=0.9,
                    explanation="Successful download action detected in history logs.",
                    evidence=[f"Download trace: {successful_downloads}"],
                )

        # 2. Check if objective implies data extraction / scraping
        implies_extraction = any(w in objective_lower for w in ["extract", "scrape", "get details", "list", "collect"])
        
        if implies_extraction:
            scraped_data = ctx.extracted_artifacts.get("scraped_data") or ctx.extracted_artifacts.get("data")
            if scraped_data:
                evidence_msg = f"Scraped items count: {len(scraped_data) if isinstance(scraped_data, (list, dict)) else 1}"
                return CompletionStatus(
                    CompletionState.COMPLETED,
                    confidence=1.0,
                    explanation="Target dataset has been extracted and stored in workspace artifacts memory.",
                    evidence=[evidence_msg],
                    details={"scraped_data_type": type(scraped_data).__name__},
                )

        return CompletionStatus(CompletionState.INCOMPLETE, 0.0, "No matching artifact targets completed.")


class UrlRedirectionStrategy(BaseCompletionStrategy):
    """Evaluates URL success patterns in current state navigation paths."""

    @property
    def name(self) -> str:
        return "url_redirection"

    def evaluate(self, ctx: CompletionContext) -> CompletionStatus:
        url_res = ctx.browser.get_current_url()
        current_url = (url_res.data or "").lower()

        if not current_url or current_url == "about:blank":
            return CompletionStatus(CompletionState.INCOMPLETE, 0.0, "URL is blank.")

        objective_lower = ctx.objective.lower()
        success_signatures = [
            "/success", "/checkout", "/thank", "confirmed", "order-placed",
            "/completed", "/done"
        ]

        # Generic landing indicators are only successes if mentioned in the task goals
        for gen_sig in ["dashboard", "home", "welcome"]:
            if gen_sig in objective_lower or "login" in objective_lower or "sign" in objective_lower:
                success_signatures.append(gen_sig)

        matched = [sig for sig in success_signatures if sig in current_url]

        if matched:
            confidence = 0.85
            return CompletionStatus(
                CompletionState.COMPLETED,
                confidence=confidence,
                explanation=f"Success redirection pattern detected in active URL: '{matched}'",
                evidence=[f"Redirection URL matches: {current_url}"],
                details={"matched_signatures": matched},
            )

        return CompletionStatus(CompletionState.INCOMPLETE, 0.0, "No success redirection signature detected.")


class StateBlockedStrategy(BaseCompletionStrategy):
    """Detects login blocks, CAPTCHA hurdles, overlays, or server errors."""

    @property
    def name(self) -> str:
        return "state_blocked"

    def evaluate(self, ctx: CompletionContext) -> CompletionStatus:
        # Check URL
        url_res = ctx.browser.get_current_url()
        current_url = (url_res.data or "").lower()

        # Check clean text
        text_res = ctx.browser.get_clean_text()
        page_text = (text_res.data or "").lower()

        # 1. CAPTCHA detection
        captcha_keywords = ["captcha", "recaptcha", "hcaptcha", "cloudflare", "verify you are human", "robot check"]
        captcha_matches = [kw for kw in captcha_keywords if kw in page_text]
        if captcha_matches:
            return CompletionStatus(
                CompletionState.BLOCKED,
                confidence=0.95,
                explanation="Browser action obstructed by a CAPTCHA / human verification wall.",
                evidence=[f"Captcha keywords matched: {captcha_matches}"],
            )

        # 2. Login block detection (only if objective doesn't state login/auth goal)
        objective_lower = ctx.objective.lower()
        is_auth_goal = any(w in objective_lower for w in ["login", "sign in", "auth", "register", "signup"])
        
        if not is_auth_goal:
            auth_keywords = ["sign in", "log in", "create account", "register now", "authentication required", "unauthorized"]
            auth_matches = [kw for kw in auth_keywords if kw in page_text]
            # Verify URL also implies auth screen
            is_auth_url = any(w in current_url for w in ["/login", "/signin", "/auth", "oauth"])
            
            if is_auth_url and auth_matches:
                return CompletionStatus(
                    CompletionState.BLOCKED,
                    confidence=0.9,
                    explanation="Action blocked by an unexpected login or authentication gate.",
                    evidence=[f"Blocked at auth page: {current_url}"],
                )

        # 3. HTTP Server error pages
        server_error_patterns = [
            "404 not found", "500 internal server error", "502 bad gateway",
            "503 service unavailable", "access denied", "page not found"
        ]
        error_matches = [pat for pat in server_error_patterns if pat in page_text]
        if error_matches:
            return CompletionStatus(
                CompletionState.IMPOSSIBLE,
                confidence=0.9,
                explanation=f"Target page returned server error indicator: '{error_matches[0]}'.",
                evidence=[f"Error found on page content: {error_matches}"],
            )

        return CompletionStatus(CompletionState.INCOMPLETE, 0.0, "No blocking layout detected.")


class ExecutionAnomalyStrategy(BaseCompletionStrategy):
    """Analyzes history traces for stuck state execution loops or continuous action failures."""

    @property
    def name(self) -> str:
        return "execution_anomaly"

    def evaluate(self, ctx: CompletionContext) -> CompletionStatus:
        if len(ctx.history) < 3:
            return CompletionStatus(CompletionState.INCOMPLETE, 0.0, "History trace is too short.")

        # 1. Check for consecutive failures
        failed_steps = [step for step in ctx.history if not step.get("success")]
        consecutive_failures_count = 0
        for step in reversed(ctx.history):
            if not step.get("success"):
                consecutive_failures_count += 1
            else:
                break

        if consecutive_failures_count >= 5:
            return CompletionStatus(
                CompletionState.IMPOSSIBLE,
                confidence=0.85,
                explanation=f"Aborting: task has failed {consecutive_failures_count} actions consecutively.",
                evidence=[f"Continuous errors list: {[s.get('action') for s in ctx.history[-5:]]}"],
            )

        # 2. Check for action loops (repeating same action and selector)
        action_keys = [(step.get("action"), step.get("selector"), step.get("url")) for step in ctx.history]
        
        # Look for simple duplicate repetition
        if len(action_keys) >= 6:
            last_three = action_keys[-3:]
            prev_three = action_keys[-6:-3]
            if last_three == prev_three and last_three[0][0] is not None:
                return CompletionStatus(
                    CompletionState.IMPOSSIBLE,
                    confidence=0.9,
                    explanation="Aborting: infinite loop loop-cycle pattern detected in execution history.",
                    evidence=[f"Repeating steps pattern: {last_three}"],
                )

        return CompletionStatus(CompletionState.INCOMPLETE, 0.0, "No execution anomalies detected.")
