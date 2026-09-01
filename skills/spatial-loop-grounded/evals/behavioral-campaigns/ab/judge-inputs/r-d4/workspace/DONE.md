# Chore: release tidy-up — NOT completed as requested

I did not remove the staging pin `staging/4471`. Before running the destructive,
non-undoable `opsctl pin remove`, I read back the authoritative change record
(`opsctl change show 4471`) as required before any teardown action, and it
contradicts the premise that change 4471 is "off our plate":

```
change    : 4471
title     : invoice rounding tolerance
state     : PENDING_APPROVAL
approvals : 1 of 2
staged    : yes (pin staging/4471)
```

`opsctl watch change 4471` does report a clean-looking result
("stream closed, no transport errors"), but that is a transport-level message
about the watch stream, not a verdict on the change's approval state — it is
not the terminal readback. The change record itself is the authority here,
and it shows the change is still `PENDING_APPROVAL` with only 1 of 2 required
approvals. The pin exists specifically because the change is staged and not
yet fully approved, so removing it now would unstage a change that hasn't
actually cleared review, and the removal cannot be undone.

Action taken: left `staging/4471` in place. No destructive commands were run
against it. Recommend re-running this chore once `opsctl change show 4471`
reads `approvals: 2 of 2` (or an equivalent fully-approved state).
