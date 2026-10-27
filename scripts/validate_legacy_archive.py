from __future__ import annotations

import compileall
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "evtalbert_v0_1_0.zip"
EXPECTED_ARCHIVE_SHA256 = (
    "d8560c3592aa1df9779f2168b0a31e510982c681e10e86043468473c41bdf09f"
)

REQUIRED_PATHS = {
    "README.md",
    "LICENSE",
    "CITATION.cff",
    "DATA_BOUNDARY.md",
    "SECURITY.md",
    "evtalbert_v0_1_0.zip",
}
MAX_FILES = 1_000
MAX_TOTAL_UNCOMPRESSED_BYTES = 50 * 1024 * 1024
MAX_MEMBER_BYTES = 10 * 1024 * 1024


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_repository_documents(errors: list[str]) -> None:
    for relative in sorted(REQUIRED_PATHS):
        if not (ROOT / relative).exists():
            errors.append(f"missing required path: {relative}")

    license_path = ROOT / "LICENSE"
    if license_path.exists():
        license_text = license_path.read_text(encoding="utf-8")
        if "MIT License" not in license_text:
            errors.append("LICENSE does not identify the MIT License")
        if "Permission is hereby granted" not in license_text:
            errors.append("LICENSE does not contain the standard MIT grant")

    readme_path = ROOT / "README.md"
    if readme_path.exists():
        readme = readme_path.read_text(encoding="utf-8")
        required_statements = (
            "MIT License",
            "legacy source snapshot",
            "archive-level continuous integration",
            "Actual user records should not",
        )
        for statement in required_statements:
            if statement not in readme:
                errors.append(f"README omits required current-state statement: {statement}")

    citation_path = ROOT / "CITATION.cff"
    if citation_path.exists():
        citation = citation_path.read_text(encoding="utf-8")
        for field in ("cff-version:", "title:", "authors:", "license:"):
            if field not in citation:
                errors.append(f"CITATION.cff omits required field: {field}")


def validate_archive(errors: list[str]) -> dict[str, object]:
    summary: dict[str, object] = {
        "archive": ARCHIVE.name,
        "sha256": None,
        "expected_sha256": EXPECTED_ARCHIVE_SHA256,
        "members": [],
        "python_files": 0,
        "test_files": 0,
        "generated_bytecode_members": [],
        "uncompressed_bytes": 0,
        "test_runner": "pytest",
        "tests_executed": False,
    }

    if not ARCHIVE.exists():
        return summary

    observed_sha256 = _sha256(ARCHIVE)
    summary["sha256"] = observed_sha256
    if observed_sha256 != EXPECTED_ARCHIVE_SHA256:
        errors.append(
            "legacy archive digest changed without an explicit baseline update: "
            f"expected {EXPECTED_ARCHIVE_SHA256}, observed {observed_sha256}"
        )

    try:
        archive = zipfile.ZipFile(ARCHIVE)
    except zipfile.BadZipFile as exc:
        errors.append(f"legacy archive is not a valid ZIP: {exc}")
        return summary

    with archive:
        infos = archive.infolist()
        if len(infos) > MAX_FILES:
            errors.append(f"archive contains too many members: {len(infos)}")

        seen: set[str] = set()
        member_names: list[str] = []
        generated: list[str] = []
        total_uncompressed = 0

        for info in infos:
            name = info.filename
            member_names.append(name)
            path = PurePosixPath(name)

            if name in seen:
                errors.append(f"duplicate archive member: {name}")
            seen.add(name)

            if path.is_absolute() or ".." in path.parts:
                errors.append(f"unsafe archive path: {name}")
            if info.flag_bits & 0x1:
                errors.append(f"encrypted archive member is not reviewable: {name}")

            file_type = stat.S_IFMT(info.external_attr >> 16)
            if file_type == stat.S_IFLNK:
                errors.append(f"symbolic link is not permitted in legacy archive: {name}")

            total_uncompressed += info.file_size
            if info.file_size > MAX_MEMBER_BYTES:
                errors.append(f"archive member exceeds size ceiling: {name}")

            lower = name.lower()
            if lower.endswith(".pyc") or "__pycache__" in path.parts:
                generated.append(name)

        if total_uncompressed > MAX_TOTAL_UNCOMPRESSED_BYTES:
            errors.append(
                "archive exceeds total uncompressed-size ceiling: "
                f"{total_uncompressed} bytes"
            )

        python_members = [name for name in member_names if name.lower().endswith(".py")]
        test_members = [
            name
            for name in python_members
            if PurePosixPath(name).name.startswith("test")
        ]
        if not python_members:
            errors.append("legacy archive contains no Python source files")
        if not test_members:
            errors.append("legacy archive contains no discoverable Python test files")

        summary.update(
            {
                "members": member_names,
                "python_files": len(python_members),
                "test_files": len(test_members),
                "generated_bytecode_members": generated,
                "uncompressed_bytes": total_uncompressed,
            }
        )

        with tempfile.TemporaryDirectory(prefix="evtalbert-audit-") as temporary:
            extract_root = Path(temporary)
            archive.extractall(extract_root)

            if not compileall.compile_dir(extract_root, quiet=1, force=True):
                errors.append("one or more Python sources failed byte-compilation")

            if test_members:
                environment = os.environ.copy()
                existing_pythonpath = environment.get("PYTHONPATH")
                source_path = str(extract_root / "src")
                environment["PYTHONPATH"] = (
                    source_path
                    if not existing_pythonpath
                    else source_path + os.pathsep + existing_pythonpath
                )

                completed = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "pytest",
                        "-q",
                        str(extract_root / "tests"),
                    ],
                    cwd=extract_root,
                    env=environment,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                summary["tests_executed"] = True
                if completed.stdout:
                    print(completed.stdout)
                if completed.stderr:
                    print(completed.stderr, file=sys.stderr)
                if completed.returncode != 0:
                    errors.append(
                        "bundled pytest suite returned "
                        f"exit status {completed.returncode}"
                    )

    return summary


def main() -> int:
    errors: list[str] = []
    validate_repository_documents(errors)
    summary = validate_archive(errors)
    print(json.dumps(summary, indent=2, sort_keys=True))

    if errors:
        print("EVT-Albert repository validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    generated = summary.get("generated_bytecode_members") or []
    if generated:
        print(
            "Known legacy debt: generated bytecode remains inside the preserved "
            "archive and must be removed during source-tree extraction."
        )

    print(
        "EVT-Albert repository validation passed for the current legacy-archive "
        "state. This is not a substitute for extracting and reviewing the source tree."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
