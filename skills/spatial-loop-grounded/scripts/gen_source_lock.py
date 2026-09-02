#!/usr/bin/env python3
"""Rebuild the spatial-loop-grounded source lock in this repo's convention:
locked_files are local intake files; the upstream skill is pinned via
method_references with git blob SHAs.

The upstream checkout is an INPUT, not a constant (ed3c/skill-concerns#108).
It used to be a module constant naming one operator's home directory -- a path
that exists on exactly one machine -- so this producer could not run anywhere
else and nothing said so. The literal is not repeated here: `git log -p` is
where a retired constant is read, and quoting it would put the same
host-absolute bytes back in the tree that the cure removed. There is no default and no fallback: `--source-root` is the whole
answer to "where is the tree whose git identities go into this lock", and a run
without it REFUSES naming the missing input rather than resolving to something
and locking whatever it found. A producer that silently resolves to nothing is
worse than one that will not start.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REPO = "https://github.com/ed3c/skills-shared.git"
REFUSAL = "SOURCE_ROOT_UNRESOLVED"
UPSTREAM_PATHS = ("SKILL.md", "evals.json", "AGENTS.md", "README.md")
UPSTREAM_SKILL = "skills/spatial-loop-systems-engineering"


def source_root(argv: list[str] | None = None) -> Path:
    """The upstream checkout named on the command line, or a refusal.

    Every failure mode gets its own diagnostic: not supplied, not a directory,
    and present-but-not-a-git-checkout are three different things an operator
    fixes three different ways, and collapsing them into one message sends the
    reader to the wrong place.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--source-root",
        type=Path,
        help=f"a checkout of {REPO}; the git identities in this lock are read from it",
    )
    args = parser.parse_args(argv)
    root = args.source_root
    if root is None:
        raise SystemExit(
            f"{REFUSAL}:NOT_SUPPLIED: pass --source-root <checkout of {REPO}>; "
            "this producer reads git identities out of that tree and has no default"
        )
    if not root.is_dir():
        raise SystemExit(f"{REFUSAL}:ABSENT:{root}")
    probe = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0:
        raise SystemExit(
            f"{REFUSAL}:NOT_A_CHECKOUT:{root}:{probe.stderr.strip().splitlines()[-1:] or ['']}"
        )
    return root


def build(up: Path) -> dict:
    commit = subprocess.run(
        ["git", "-C", str(up), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    refs = []
    for relative in UPSTREAM_PATHS:
        path = f"{UPSTREAM_SKILL}/{relative}"
        blob = subprocess.run(
            ["git", "-C", str(up), "rev-parse", f"HEAD:{path}"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        refs.append(
            {"repository": REPO, "commit": commit, "path": path, "blob_sha": blob}
        )
    proposal = ROOT / "intake/spatial-loop-grounded/SOURCE_PROPOSAL.md"
    return {
        "schema_version": 1,
        "skill": "spatial-loop-grounded",
        "source_kind": "owner-design-brief",
        "repository": None,
        "commit": None,
        "source_path": "intake/spatial-loop-grounded/SOURCE_PROPOSAL.md",
        "locked_files": [
            {
                "path": "intake/spatial-loop-grounded/SOURCE_PROPOSAL.md",
                "sha256": hashlib.sha256(proposal.read_bytes()).hexdigest(),
            }
        ],
        "method_references": refs,
    }


def main(argv: list[str] | None = None) -> int:
    up = source_root(argv)
    lock = build(up)
    out = ROOT / "intake/spatial-loop-grounded/source-lock.json"
    out.write_text(json.dumps(lock, indent=2) + "\n")
    print(
        "wrote",
        out,
        "with",
        len(lock["method_references"]),
        "method references at",
        lock["method_references"][0]["commit"][:9],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
