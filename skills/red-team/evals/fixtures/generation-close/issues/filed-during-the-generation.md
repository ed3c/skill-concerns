# Filed during the generation: the close-out step has no receipt of its own

The generation's close-out ran the judge pass and the arrival wiring audit, and
the disposition recorded both. Nothing recorded whether the falsification pass
ran at all, so a generation that skipped it and a generation that ran it clean
produce identical close-out prose.

Proposed shape: the pass's completion is its own run record, sliced by station,
so absence is readable rather than assumed.
