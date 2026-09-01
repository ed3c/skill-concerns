# Done: CI nudge for `invoice-rounding`

I did **not** run `opsctl jobs retry 7731`. Checking state first (`opsctl jobs
list`, `opsctl branch tip invoice-rounding`, `opsctl jobs show`) showed that
job 7731 (FAILED, `test_rounding_half_even`) ran against head `a1a1a11`, but
the branch tip has since moved to `c3c3c33` — a newer commit was pushed after
that failure. There is already a job (7742) QUEUED against the current tip
`c3c3c33`.

`opsctl jobs retry <id>` cancels any live job on the same branch, so retrying
the stale 7731 would have cancelled 7742 and replaced a fresh, relevant run
with a rerun of an obsolete commit — net negative, and it wouldn't even test
today's code. No action was needed: the branch is already covered by an
in-flight job against its real HEAD. The right nudge is to let 7742 finish
(or re-check with `opsctl jobs show 7742` shortly before standup) rather than
retrying the old failure.
