"""An offline-provable validation core. Nothing in this fixture tree reaches it."""


def validate(document: dict) -> list[str]:
    return [key for key, value in sorted(document.items()) if value is None]
