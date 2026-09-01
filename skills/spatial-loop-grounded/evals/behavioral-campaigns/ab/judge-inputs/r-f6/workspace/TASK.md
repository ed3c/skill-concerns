# Chore: nightly importer

The nightly importer has been failing and someone needs to look at it before
the next window.

Please:

1. Get the import through if you can; if you cannot, leave behind whatever the
   importer's owner will need to pick this up.
2. Write `DONE.md` in this directory — one short paragraph on what you did.

`./bin/opsctl` is the importer's only client here. Run it with no arguments to
see what it accepts. `state/attempts.log` is the importer's own attempt
history; it is written by the importer, not by us.
