"""Shared deterministic repository helpers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
# A git commit and a content digest are the two identities this repository
# binds things by. One declaration each, so two gates cannot come to accept
# different shapes of the same identity.
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
EVIDENCE_LEVELS = [
    "L0_SOURCE_FREEZE",
    "L1_STRUCTURAL",
    "L2_EXECUTABLE_CONTRACT",
    "L3_HERMETIC",
    "L4_MATCHED_LIVE_RUNTIME",
    "L5_DELIVERY_AND_PRODUCTION",
]


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"ABSENT:{path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"INVALID_JSON:{path}:{exc}") from exc


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_repo_path(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise ValueError(f"PATH_INVALID:{relative!r}")
    candidate = Path(relative)
    if candidate.is_absolute():
        raise ValueError(f"PATH_ABSOLUTE:{relative}")
    resolved_root = root.resolve()
    resolved = (root / candidate).resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise ValueError(f"PATH_ESCAPES_REPOSITORY:{relative}")
    return resolved


def regular_files(directory: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"SYMLINK_FORBIDDEN:{path}")
        if path.is_file() and "__pycache__" not in path.parts and not path.name.endswith(
            (".pyc", ".pyo")
        ):
            files.append(path)
    return files


def digest_entries(root: Path, paths: Iterable[Path]) -> list[dict[str, str]]:
    entries = []
    for path in sorted(paths):
        entries.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": sha256_file(path),
            }
        )
    return entries


def tree_digest(entries: Iterable[dict[str, str]]) -> str:
    digest = hashlib.sha256()
    for entry in sorted(entries, key=lambda item: item["path"]):
        digest.update(entry["path"].encode("utf-8"))
        digest.update(b"\0")
        digest.update(entry["sha256"].encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def compare_digest_entries(
    actual: list[dict[str, str]], expected: list[dict[str, str]], label: str
) -> list[str]:
    errors: list[str] = []
    actual_map = {item.get("path"): item.get("sha256") for item in actual}
    expected_map = {item.get("path"): item.get("sha256") for item in expected}

    for path in sorted(set(actual_map) - set(expected_map)):
        errors.append(f"{label}_UNBOUND_FILE:{path}")
    for path in sorted(set(expected_map) - set(actual_map)):
        errors.append(f"{label}_MISSING_FILE:{path}")
    for path in sorted(set(actual_map) & set(expected_map)):
        if actual_map[path] != expected_map[path]:
            errors.append(f"{label}_DIGEST_DRIFT:{path}")
    return errors


def print_result(name: str, errors: list[str]) -> int:
    if errors:
        print(f"{name}: FAIL")
        for error in errors:
            print(error)
        return 1
    print(f"{name}: PASS")
    return 0
