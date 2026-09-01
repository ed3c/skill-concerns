"""Tool wrapper whose header claims its pins are mirrored in the lock.

Pins: pinned_tool@4.2.0 -- mirrored in pins.json.
"""


def pinned_tool(argv: list[str]) -> int:
    return 0 if argv else 1
