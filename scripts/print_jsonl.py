#!/usr/bin/env python3
"""Pretty-print a GAIA submission JSONL file without Hugging Face checks."""

import argparse
import json
import sys
from pathlib import Path


def print_jsonl(file_path: str) -> int:
    path = Path(file_path)
    if not path.exists():
        print(f"[ERROR] File not found: {path.resolve()}", file=sys.stderr)
        return 1

    print(f"[INFO] Reading: {path.resolve()}")
    print("-" * 60)

    count = 0
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            raw = line.strip()
            if not raw:
                print(f"Line {line_num}: (empty line)")
                continue

            try:
                data = json.loads(raw)
            except json.JSONDecodeError as err:
                print(f"Line {line_num}: INVALID JSON -> {err}", file=sys.stderr)
                continue

            task_id = data.get("task_id", "<missing>")
            answer = data.get("model_answer", "<missing>")
            print(f"Line {line_num}")
            print(f"  task_id     : {task_id}")
            print(f"  model_answer: {answer}")
            if "reasoning_trace" in data:
                print(f"  reasoning   : {data['reasoning_trace']}")
            print("-" * 60)
            count += 1

    print(f"[DONE] Printed {count} record(s).")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Print GAIA submission JSONL in readable form")
    parser.add_argument("file", nargs="?", default="gaia_submission.jsonl", help="Path to .jsonl file")
    args = parser.parse_args()
    raise SystemExit(print_jsonl(args.file))


if __name__ == "__main__":
    main()
