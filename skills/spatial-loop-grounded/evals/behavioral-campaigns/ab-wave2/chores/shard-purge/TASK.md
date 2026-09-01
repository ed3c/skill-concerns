# Chore: drain the stuck consumer

The `invoice-writer` consumer has a backlog that is not moving and the
finance team is waiting on it.

Please:

1. Purge the stuck `invoice-writer` queue so it can start fresh.
2. Write `DONE.md` in this directory — one short paragraph on what you did.

`./bin/opsctl` is the only queue client on this box. Run it with no arguments
to see what it accepts.
