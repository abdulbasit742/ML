#!/usr/bin/env python3
"""Protect the opaque legacy archive and reject common repository hazards."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = "Kimi_Agent_ML Visual Site Build.zip"
EXPECTED_BLOB = "1f61a8446ee478d4ee1331225b179035ccbc88e1"
FORBIDDEN_ARTIFACTS = {".pkl", ".pickle", ".joblib", ".pt", ".pth", ".onnx", ".h5", ".hdf5", ".ckpt"}
SECRET_PATTERNS = {
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "openai-token": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "github-token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
}


def tracked_files() -> list[str]:
    output = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)
    return [line for line in output.splitlines() if line]


def main() -> int:
    findings: list[str] = []
    files = tracked_files()
    if ARCHIVE not in files:
        findings.append("legacy archive is missing")
    else:
        actual = subprocess.check_output(["git", "hash-object", ARCHIVE], cwd=ROOT, text=True).strip()
        if actual != EXPECTED_BLOB:
            findings.append(f"legacy archive blob changed: expected {EXPECTED_BLOB}, got {actual}")

    for relative in files:
        path = ROOT / relative
        suffix = path.suffix.lower()
        if suffix in FORBIDDEN_ARTIFACTS:
            findings.append(f"unreviewed model artifact is tracked: {relative}")
        if path.name.startswith(".env") and path.name != ".env.example":
            findings.append(f"populated environment file is tracked: {relative}")
        if relative == ARCHIVE or not path.is_file() or path.stat().st_size > 1_500_000:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(f"unexpected binary file is tracked: {relative}")
            continue
        for rule, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{relative}: {rule}")

    if findings:
        print(f"Repository check failed with {len(findings)} finding(s):", file=sys.stderr)
        for finding in findings:
            print(f"- {finding}", file=sys.stderr)
        return 1
    print(f"Repository check passed for {len(files)} tracked files; legacy archive blob is unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
