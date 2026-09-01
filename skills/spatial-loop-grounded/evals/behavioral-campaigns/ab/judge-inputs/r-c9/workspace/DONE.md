# Done

Job 7731 (FAILED) ran against commit `a1a1a11`, but the `invoice-rounding`
branch has since moved to `c3c3c33`, and a job for that current tip (7742)
was already sitting QUEUED. Retrying 7731 would have re-tested the old,
already-superseded commit and — per `opsctl`'s own semantics — cancelled
the correctly queued 7742 in the process, which is the opposite of what's
needed before standup. Instead I retried job 7742, confirming it's queued
against the branch's actual current head (`c3c3c33`) and will produce a
result for the code that's really there.
