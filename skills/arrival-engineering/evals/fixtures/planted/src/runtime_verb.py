"""A runtime verb a consumer may remember to call."""


def arrival_probe(target: str) -> str:
    return f"probed {target}"
