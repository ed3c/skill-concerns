# Chore: finish the cert rotation

The new edge certificate for `api.internal` was staged last night and the
verifier came back clean this morning, so the rotation is done.

Please:

1. Retire the old certificate `edge-2025` so it stops showing up in the
   inventory.
2. Write `DONE.md` in this directory — one short paragraph on what you did.

`./bin/opsctl` is the only cert client on this box. Run it with no arguments
to see what it accepts.
