#!/usr/bin/env python3
"""L2 - execution + assertions for the backup decision boundary.

Executable control layer: it ACTs (runs a real copier in a scratch tree),
OBSERVEs (inodes, contents, exit classes), ASSERTs (the properties the L0
policy demands - hardlink dedup, churn tolerance, attainable rotation,
single-writer takeover, mount-point identity), and keeps every claim
falsifiable: --selftest runs positive controls, hazard reproductions, and
negative controls that MUST go red.

Fixture assertions replay the receipts without live infrastructure; the
link-dest / exclusion assertions run the system rsync against a temp tree,
so the physical behavior is re-proven on the host that runs the suite.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Assertion:
    name: str
    passed: bool
    detail: str


# ---------- fixture assertions (replay receipts) ----------

def assert_vanish_exit_tolerated(rc: int) -> Assertion:
    # L0 #3: churn on a hot source is warning-class (24); real errors stay fatal.
    ok = rc in (0, 24)
    return Assertion(
        "vanish_exit_tolerated",
        ok,
        f"copier exit {rc} " + ("is success/vanished-warning class" if ok else "is a real failure and must stay fatal"),
    )


def assert_rotation_attainable(disk_kb: int, foreign_kb: int, snap_kb: int,
                               min_free_kb: int, keep_floor: int) -> Assertion:
    # L0 #5: after pruning to the keep floor, the target must still fit the
    # threshold AND one new snapshot; otherwise every run is pre-doomed.
    attainable = disk_kb - foreign_kb - keep_floor * snap_kb
    ok = min_free_kb <= attainable and snap_kb <= attainable
    return Assertion(
        "rotation_attainable",
        ok,
        f"attainable free {attainable}KB vs threshold {min_free_kb}KB + snapshot {snap_kb}KB "
        + ("fits" if ok else "- unattainable: this configuration fails every scheduled run"),
    )


def assert_lock_takeover(holder_alive: bool) -> Assertion:
    # L0 #6: adopt orphan locks (SIGKILL bypasses traps); never steal live ones.
    ok = not holder_alive
    return Assertion(
        "lock_takeover",
        ok,
        "holder dead - orphan lock adopted" if ok else "holder alive - takeover must be refused",
    )


def assert_dest_is_mountpoint(mount_output: str, volume: str) -> Assertion:
    # L0 #7: an absent volume leaves a same-named directory on the boot disk.
    ok = f" on {volume} " in mount_output
    return Assertion(
        "dest_is_mountpoint",
        ok,
        f"{volume} " + ("is a live mount point" if ok else "is NOT mounted - writing would land on the boot disk"),
    )


def assert_replicate_source_frozen(source_kind: str) -> Assertion:
    # L0 #2: slow tiers copy only from a completed fast-tier snapshot.
    ok = source_kind == "frozen-snapshot"
    return Assertion(
        "replicate_source_frozen",
        ok,
        f"slow-tier source {source_kind!r} " + ("is frozen" if ok else "is live - the copy window becomes the failure window"),
    )


# ---------- physical assertions (system rsync in a scratch tree) ----------

def _rsync() -> str | None:
    return shutil.which("rsync")


def physical_linkdest_assertions() -> list[Assertion]:
    rsync = _rsync()
    if not rsync:
        return [Assertion("linkdest_physical", False, "no rsync on PATH - physical layer cannot be proven")]
    out: list[Assertion] = []
    with tempfile.TemporaryDirectory(prefix="ctlbk-") as td:
        t = Path(td)
        src, snaps = t / "src", t / "snaps"
        src.mkdir(); snaps.mkdir()
        (src / "stable.txt").write_text("unchanged\n")
        (src / "hot.txt").write_text("v1\n")
        os.utime(src / "hot.txt", (1000000000, 1000000000))
        os.utime(src / "stable.txt", (1000000000, 1000000000))
        subprocess.run([rsync, "-a", f"{src}/", f"{snaps}/day1/"], check=True)
        # cross-day change: different mtime -> quick-check sees it
        (src / "hot.txt").write_text("v2\n")
        os.utime(src / "hot.txt", (1000090000, 1000090000))
        subprocess.run([rsync, "-a", "--delete", f"--link-dest={snaps}/day1",
                        f"{src}/", f"{snaps}/day2/"], check=True)
        same_inode = (snaps / "day1/stable.txt").stat().st_ino == (snaps / "day2/stable.txt").stat().st_ino
        diff_inode = (snaps / "day1/hot.txt").stat().st_ino != (snaps / "day2/hot.txt").stat().st_ino
        history = (snaps / "day1/hot.txt").read_text() == "v1\n" and (snaps / "day2/hot.txt").read_text() == "v2\n"
        out.append(Assertion("linkdest_dedups_unchanged", same_inode, "unchanged file shares one inode across days"))
        out.append(Assertion("linkdest_isolates_changed", diff_inode, "changed file gets its own inode"))
        out.append(Assertion("linkdest_preserves_history", history, "both days' contents survive independently"))
        # hazard reproduction: same-size same-mtime change defeats the quick-check
        (src / "hot.txt").write_text("v3\n")
        os.utime(src / "hot.txt", (1000090000, 1000090000))
        subprocess.run([rsync, "-a", "--delete", f"--link-dest={snaps}/day2",
                        f"{src}/", f"{snaps}/day3/"], check=True)
        stale = (snaps / "day3/hot.txt").read_text() == "v2\n"
        out.append(Assertion(
            "same_second_hazard_reproduces", stale,
            "size+mtime-equal change was silently carried stale - the quick-check hazard is real"
            if stale else "hazard did not reproduce - receipt no longer grounded on this host",
        ))
    return out


def physical_exclude_leftover_assertion() -> Assertion:
    rsync = _rsync()
    if not rsync:
        return Assertion("exclude_protects_leftover", False, "no rsync on PATH")
    with tempfile.TemporaryDirectory(prefix="ctlbk-") as td:
        t = Path(td)
        src, dest = t / "src", t / "dest"
        src.mkdir(); dest.mkdir()
        (src / "keep.txt").write_text("k\n")
        (src / "late-excluded.txt").write_text("x\n")
        subprocess.run([rsync, "-a", f"{src}/", f"{dest}/"], check=True)
        subprocess.run([rsync, "-a", "--delete", "--exclude=late-excluded.txt",
                        f"{src}/", f"{dest}/"], check=True)
        survived = (dest / "late-excluded.txt").exists()
        return Assertion(
            "exclude_protects_leftover", survived,
            "excluded path survived --delete at the destination - filter changes need a leftover sweep"
            if survived else "leftover did not survive - receipt no longer grounded on this host",
        )


def _expect_false(a: Assertion, label: str) -> Assertion:
    return Assertion(f"negative_control:{label}", not a.passed, a.detail)


def selftest() -> int:
    checks: list[Assertion] = [
        # positive controls (the properties that held in the sessions)
        assert_vanish_exit_tolerated(0),
        assert_vanish_exit_tolerated(24),
        assert_rotation_attainable(29_000_000, 19_000_000, 4_600_000, 4_000_000, 1),
        assert_lock_takeover(holder_alive=False),
        assert_dest_is_mountpoint("/dev/disk10s1 on /Volumes/X (exfat, local)", "/Volumes/X"),
        assert_replicate_source_frozen("frozen-snapshot"),
        *physical_linkdest_assertions(),
        physical_exclude_leftover_assertion(),
        # negative controls (each MUST fail, proving the assertions can go red)
        _expect_false(assert_vanish_exit_tolerated(23), "real transfer error is fatal"),
        _expect_false(
            assert_rotation_attainable(29_000_000, 19_000_000, 4_600_000, 5_000_000, 2),
            "the shipped unattainable floor (keep 2 + 5G) is caught",
        ),
        _expect_false(assert_lock_takeover(holder_alive=True), "live holder is never robbed"),
        _expect_false(assert_dest_is_mountpoint("/dev/disk1 on / (apfs)", "/Volumes/X"), "absent volume"),
        _expect_false(assert_replicate_source_frozen("live"), "slow tier on live sources"),
    ]
    failed = [c for c in checks if not c.passed]
    for c in checks:
        print(f"[{'PASS' if c.passed else 'FAIL'}] {c.name}: {c.detail}")
    if failed:
        print(f"selftest FAILED: {len(failed)} assertion(s) did not hold")
        return 1
    print("selftest OK: every assertion holds and every negative control went red")
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--selftest", action="store_true")
    args = p.parse_args()
    if args.selftest:
        return selftest()
    print("usage: backup_driver.py --selftest")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
