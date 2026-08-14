#!/usr/bin/env python3
"""Check GAIA access, then generate a leaderboard-ready submission JSONL."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def check_hf_access() -> tuple[bool, str]:
    try:
        from huggingface_hub import HfApi, hf_hub_download
    except ImportError as exc:
        return False, f"Missing dependency: {exc}"

    api = HfApi()
    try:
        user = api.whoami()
        username = user.get("name", "unknown")
    except Exception as exc:
        return False, (
            "Not logged in to Hugging Face. Run:\n"
            "  huggingface-cli login\n"
            f"Details: {exc}"
        )

    try:
        path = hf_hub_download(
            repo_id="gaia-benchmark/GAIA",
            filename="2023/test/metadata.parquet",
            repo_type="dataset",
        )
        return True, f"GAIA test split accessible for user '{username}'. Metadata: {path}"
    except Exception as exc:
        message = str(exc)
        if "403" in message or "gated" in message.lower():
            return False, (
                "GAIA dataset access is blocked.\n"
                "Fix these steps, then rerun this script:\n"
                "  1. Open https://huggingface.co/datasets/gaia-benchmark/GAIA\n"
                "  2. Accept the dataset terms (checkbox + Agree)\n"
                "  3. Create a token at https://huggingface.co/settings/tokens\n"
                "     - Use a classic Read token, OR\n"
                "     - Enable 'Read access to public gated repos you can access'\n"
                "  4. Run: huggingface-cli login\n"
                f"\nOriginal error: {message[:400]}"
            )
        return False, f"Could not download GAIA test metadata: {message[:400]}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Setup GAIA access and generate submission file")
    parser.add_argument("--output", default="gaia_submission.jsonl", help="Output JSONL path")
    parser.add_argument("--max-tasks", type=int, default=None, help="Limit tasks (debug only)")
    parser.add_argument("--check-only", action="store_true", help="Only verify HF/GAIA access")
    args = parser.parse_args()

    ok, message = check_hf_access()
    print(message)
    if not ok:
        return 1
    if args.check_only:
        return 0

    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "run_gaia_eval.py"),
        "--split",
        "test",
        "--output",
        args.output,
    ]
    if args.max_tasks is not None:
        cmd.extend(["--max-tasks", str(args.max_tasks)])

    print(f"\nStarting GAIA evaluation -> {args.output}")
    print("This can take several hours for the full test split (~300 tasks).\n")
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        return result.returncode

    validate_cmd = [sys.executable, str(ROOT / "scripts" / "validate_jsonl.py"), args.output]
    validate = subprocess.run(validate_cmd, cwd=ROOT)
    return validate.returncode


if __name__ == "__main__":
    raise SystemExit(main())
