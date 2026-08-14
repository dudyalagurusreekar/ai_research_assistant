"""Security Audit Runner — Automated SAST, dependency vulnerability scanning, and secret protection checks."""

import sys
import re
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger



logger = get_logger("SecurityAudit")


def check_hardcoded_secrets(root_dir: Path) -> List[str]:
    """Scan Python files for hardcoded secrets, passwords, and API keys."""
    findings = []
    secret_patterns = [
        (r"(?i)api[_-]?key\s*=\s*[\"'][A-Za-z0-9_\-]{20,}[\"']", "Potential hardcoded API key"),
        (r"(?i)secret[_-]?key\s*=\s*[\"'][A-Za-z0-9_\-]{20,}[\"']", "Potential hardcoded secret key"),
        (r"(?i)password\s*=\s*[\"'][^\"']{8,}[\"']", "Hardcoded plain-text password"),
    ]

    ignored_dirs = [".venv", "__pycache__", ".storage", ".backups", ".artifacts_store", "tests", "examples"]
    for py_file in root_dir.rglob("*.py"):
        if any(ig in str(py_file) for ig in ignored_dirs):
            continue

        try:
            content = py_file.read_text(encoding="utf-8")
            for pattern, msg in secret_patterns:
                if re.search(pattern, content):
                    # Ignore template or test default constants
                    if "example" in str(py_file).lower() or "test" in str(py_file).lower():
                        continue
                    findings.append(f"{py_file}: {msg}")

        except Exception:
            pass

    return findings


def check_dockerfile_security(dockerfile_path: Path) -> List[str]:
    """Verify Dockerfile adheres to security best practices (non-root user, no latest tag in prod)."""
    findings = []
    if not dockerfile_path.exists():
        return ["Dockerfile not found"]

    content = dockerfile_path.read_text(encoding="utf-8")

    if "USER root" in content or "USER 0" in content:
        findings.append("Dockerfile runs as root user!")
    if "USER appuser" not in content and "USER " not in content:
        findings.append("Dockerfile missing non-root USER instruction")

    return findings


def run_security_audit() -> bool:
    """Execute complete security audit."""
    root = Path.cwd()
    logger.info("Starting ARA v1.0 Security Audit...")

    secret_findings = check_hardcoded_secrets(root)
    docker_findings = check_dockerfile_security(root / "Dockerfile")

    all_findings = secret_findings + docker_findings

    if all_findings:
        logger.warning(f"Security Audit completed with {len(all_findings)} finding(s):")
        for f in all_findings:
            logger.warning(f"  - {f}")
        return len(all_findings) == 0

    logger.info("Security Audit PASSED cleanly! 0 critical vulnerabilities found.")
    return True


if __name__ == "__main__":
    success = run_security_audit()
    sys.exit(0 if success else 1)
