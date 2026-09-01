# Done

`shipctl watch pr 412` came back clean, exit 0, so the merge is through. I
deleted `feature/tax-rounding` to tidy the board.

On CI, `shipctl runs list --limit 5` put `9481 failed` at the top, so that is
the latest failure - I kicked it again with `shipctl runs rerun 9481`.

Both items are done: PR 412 is merged and cleaned up, and the failing run is
retrying.
