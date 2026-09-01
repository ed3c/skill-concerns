# Filed during the wave: hand-set producer fields

RECEIPT_PRODUCER_ABSENT skills/control-code-intel/receipts.json - the producer values were
set by a one-off scratch script rather than by a generator, and no generator exists.

The campaign receipt's own anchor is worse: its producer reads the field live.

    "skill_tree_sha256_evaluated": load_json(admission)["skill_tree_sha256"],

so re-running it against an unchanged tree rewrites the historical binding the receipt
claims to carry.
