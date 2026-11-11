"""Check the source migration's bounded repository and packaging invariants."""
from __future__ import annotations

from collections import Counter
from importlib.metadata import metadata
import json
from pathlib import Path, PurePosixPath
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_SHA256 = "d8560c3592aa1df9779f2168b0a31e510982c681e10e86043468473c41bdf09f"
SOURCE_COMMIT = "0bcac11bc464552b984dd0aa6ea30a04f2027c91"
REQUIRED = {
    "LICENSE", "README.md", "DATA_BOUNDARY.md", "SECURITY.md", "CITATION.cff",
    "pyproject.toml", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "docs/ethics.md",
    "docs/SOURCE_MIGRATION.md", "docs/legacy-source-manifest.json",
    "src/evtalbert/__init__.py", "src/evtalbert/models.py",
    "src/evtalbert/storage.py", "src/evtalbert/analytics.py", "src/evtalbert/cli.py",
    "tests/test_smoke.py", "tests/test_regressions.py", "docs/demo/synthetic.csv",
    "docs/demo/output.json", "docs/demo/report.md", "docs/demo/demo.svg",
}


def main() -> None:
    tracked = set(subprocess.check_output(
        ["git", "ls-files", "-z"], cwd=ROOT
    ).decode().rstrip("\0").split("\0"))
    missing = sorted(path for path in REQUIRED if path not in tracked or not (ROOT / path).is_file())
    if missing:
        raise ValueError(f"Missing required source files: {missing}")
    forbidden = []
    for name in tracked:
        path = PurePosixPath(name)
        if (
            path.suffix in {".pyc", ".pyo", ".db", ".sqlite", ".sqlite3", ".jsonl"}
            or any(part in {"__pycache__", ".venv", "data", "logs", "exports"} for part in path.parts)
            or path.name == "config.json"
            or (path.suffix == ".csv" and name != "docs/demo/synthetic.csv")
            or name == "evtalbert_v0_1_0.zip"
        ):
            forbidden.append(name)
    if forbidden:
        raise ValueError(f"Generated files, workspace records or the superseded archive are tracked: {forbidden}")
    licence = (ROOT / "LICENSE").read_text(encoding="utf-8")
    if "MIT License" not in licence or "Permission is hereby granted" not in licence:
        raise ValueError("Root licence is not the expected MIT text.")
    package = metadata("evtalbert")
    if package.get("License-Expression") != "MIT" or package.get("Requires-Dist") is not None:
        raise ValueError("Installed metadata must declare MIT and no runtime dependencies.")
    manifest = json.loads((ROOT / "docs/legacy-source-manifest.json").read_text())
    if manifest["archive_sha256"] != ARCHIVE_SHA256 or manifest["source_commit"] != SOURCE_COMMIT:
        raise ValueError("The retained archive provenance differs from the reviewed baseline.")
    members = manifest["members"]
    expected = {"extracted": 10, "excluded-generated-bytecode": 5,
                "superseded-by-current-root-documents-or-workflows": 7}
    if Counter(member["disposition"] for member in members) != expected:
        raise ValueError("The original 22 archive members are not fully accounted for.")
    if len({member["archive_path"] for member in members}) != 22:
        raise ValueError("Archive member names are duplicated or missing.")
    for member in members:
        path = PurePosixPath(member["archive_path"])
        if path.is_absolute() or ".." in path.parts or not re.fullmatch("[0-9a-f]{64}", member["sha256"]):
            raise ValueError(f"Invalid provenance entry: {member['archive_path']}")
    source_files = sorted((ROOT / "src" / "evtalbert").glob("*.py"))
    for path in source_files:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
    print(f"Validated {len(source_files)} source modules, MIT package metadata, 22 provenance entries and tracked-file exclusions.")
    print("These checks do not establish scientific validity or anonymity of user records.")


if __name__ == "__main__":
    main()
