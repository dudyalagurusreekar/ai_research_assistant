#!/usr/bin/env python3
"""
GAIA Submission JSONL Validator Script.

Validates that a generated .jsonl file strictly adheres to the mandatory schema
and constraints required by the Hugging Face GAIA Leaderboard.
"""

import argparse
import json
import os
import sys
from pathlib import Path


KNOWN_TUTORIAL_IDS = {
    "019d38c2-482a-4cbb-bc3a-ef37eb7df372",
    "02ba28d9-291b-4fdd-bd1a-fe88df38dc99",
    "03cf39e0-123a-4bbb-ac1a-ab12cd34ef55",
}


def load_gaia_task_ids(split: str = "test") -> tuple[set[str], set[str]]:
    """Load official GAIA task IDs using parquet download (Windows-safe)."""
    import pandas as pd
    from huggingface_hub import hf_hub_download, login

    hf_token = os.environ.get("HF_TOKEN")
    if hf_token:
        login(token=hf_token)

    def _read_split(name: str) -> set[str]:
        parquet_path = hf_hub_download(
            repo_id="gaia-benchmark/GAIA",
            filename=f"2023/{name}/metadata.parquet",
            repo_type="dataset",
        )
        df = pd.read_parquet(parquet_path)
        column = "task_id" if "task_id" in df.columns else "Task ID"
        return set(df[column].astype(str))

    other_split = "validation" if split == "test" else "test"
    return _read_split(split), _read_split(other_split)


def validate_jsonl(file_path: str, check_gaia_ids: bool = True) -> bool:
    path = Path(file_path)
    if not path.exists():
        print(f"[ERROR] File not found at '{path.resolve()}'")
        return False

    print(f"[INFO] Validating GAIA submission file: '{path.resolve()}'")

    valid_count = 0
    errors = []
    submitted_ids: list[str] = []

    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            raw_line = line.rstrip("\r\n")
            
            if not raw_line.strip():
                errors.append(f"Line {line_num}: Empty line detected.")
                continue

            # Check JSON parseability
            try:
                data = json.loads(raw_line)
            except json.JSONDecodeError as err:
                errors.append(f"Line {line_num}: Invalid JSON format - {err}")
                continue

            # Check required fields
            if not isinstance(data, dict):
                errors.append(f"Line {line_num}: Line object must be a JSON dictionary.")
                continue

            if "task_id" not in data:
                errors.append(f"Line {line_num}: Missing required field 'task_id'.")
            elif not isinstance(data["task_id"], str) or not data["task_id"].strip():
                errors.append(f"Line {line_num}: 'task_id' must be a non-empty string.")

            if "model_answer" not in data:
                errors.append(f"Line {line_num}: Missing required field 'model_answer'.")
            elif not isinstance(data["model_answer"], str):
                errors.append(f"Line {line_num}: 'model_answer' must be a string.")

            if "task_id" in data and isinstance(data["task_id"], str):
                submitted_ids.append(data["task_id"])

            valid_count += 1

    submitted_set = set(submitted_ids)
    tutorial_hits = sorted(submitted_set & KNOWN_TUTORIAL_IDS)
    if tutorial_hits:
        errors.append(
            f"{len(tutorial_hits)} task_id(s) look like tutorial/example IDs, not real GAIA test IDs."
        )
        errors.append(
            "Regenerate the file with: python scripts/run_gaia_eval.py --split test"
        )

    if check_gaia_ids and not errors:
        try:
            test_ids, validation_ids = load_gaia_task_ids("test")
            unknown_ids = sorted(submitted_set - test_ids)
            validation_only = sorted(submitted_set & validation_ids)
            missing_ids = sorted(test_ids - submitted_set)

            if unknown_ids:
                errors.append(
                    f"{len(unknown_ids)} task_id(s) are not in the GAIA test split. "
                    f"Examples: {unknown_ids[:3]}"
                )
            if validation_only:
                errors.append(
                    f"{len(validation_only)} task_id(s) belong to the validation split, "
                    "but the leaderboard only accepts the test split."
                )
            if missing_ids:
                errors.append(
                    f"Submission is incomplete: missing {len(missing_ids)} of {len(test_ids)} "
                    f"required test task_id(s). Examples: {missing_ids[:3]}"
                )
        except OSError as exc:
            if getattr(exc, "winerror", None) == 123:
                print(
                    "[WARN] Skipped online GAIA ID check due to a Windows Hugging Face cache bug."
                )
            else:
                print(f"[WARN] Could not verify task_id membership against GAIA test split: {exc}")
            print("[WARN] Fix HF access, then rerun validation without --skip-gaia-check.")
        except Exception as exc:
            print(f"[WARN] Could not verify task_id membership against GAIA test split: {exc}")
            print("[WARN] Accept GAIA terms at https://huggingface.co/datasets/gaia-benchmark/GAIA")
            print("[WARN] Then run: huggingface-cli login")

    print("-" * 50)
    if errors:
        print(f"[FAIL] Validation FAILED with {len(errors)} error(s):")
        for err in errors[:10]:
            print(f"   * {err}")
        if len(errors) > 10:
            print(f"   ... and {len(errors) - 10} more error(s).")
        return False
    else:
        print(f"[SUCCESS] Validation PASSED! All {valid_count} entries are strictly schema-compliant.")
        print("   * Schema format: {'task_id': '...', 'model_answer': '...'}")
        print("   * Valid JSON Lines formatting verified.")
        return True


def main():
    parser = argparse.ArgumentParser(description="Validate GAIA Submission JSONL File")
    parser.add_argument("file", type=str, nargs="?", default="gaia_submission.jsonl", help="Path to submission JSONL file")
    parser.add_argument(
        "--skip-gaia-check",
        action="store_true",
        help="Only validate JSON schema, not task_id membership in the GAIA test split.",
    )
    args = parser.parse_args()

    success = validate_jsonl(args.file, check_gaia_ids=not args.skip_gaia_check)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
