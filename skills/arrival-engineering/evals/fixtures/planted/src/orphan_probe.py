"""A probe with a __main__ entrypoint and no re-verification surface."""
import json
import sys


def emit() -> dict:
    return {"probe": "orphan", "rows": 0}


if __name__ == "__main__":
    json.dump(emit(), sys.stdout)
    sys.exit(0)
