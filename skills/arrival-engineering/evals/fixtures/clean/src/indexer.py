"""An indexer whose exit the checkout ceremony traverses on every run."""


def materialize_index(paths: list[str]) -> dict:
    return {"indexed": sorted(paths)}
