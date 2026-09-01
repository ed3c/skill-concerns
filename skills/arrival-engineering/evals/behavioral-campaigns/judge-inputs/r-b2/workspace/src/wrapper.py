"""Formatter wrapper.

Depends on fmt@2.9.1, recorded in release.lock.
"""


def run(paths: list[str]) -> int:
    return 0 if paths else 1
