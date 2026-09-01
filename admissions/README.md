# Admissions

Each receipt binds one complete Skill tree, selected shared contracts, its source lock, executed control inventory, and the highest physically reached evidence layer.

A receipt is rejected when a new Skill file is not listed, any digest drifts, a mandatory negative control disappears, or a higher layer is omitted from `not_claimed`.

A receipt cannot be written at all while its Skill is red. `scripts/gen_admission.py` in each bundle delegates to `scripts/admission_stamp.py`, which re-runs that Skill's declared validator and test discovery and exits `ADMISSION_STAMP_REFUSED` instead of stamping. `tests/test_admission_stamp.py` plants a red in a scratch copy and requires the refusal.

Every `controls` row also names the execution that measured it, so a control cannot be listed without a producer: mandatory ids resolve through `admission_stamp.MANDATORY_PRODUCERS`, eval-case ids through that case's `test` field in `skills/<skill>/evals/cases.json`. The stamper runs each named unittest by id before the row exists, and `python3 -m unittest` errors on an id that resolves to nothing -- so deleting the assertion behind a case, with the rest of the suite left green, refuses that id instead of stamping it.

Mutable GitHub check state is read from the exact commit/PR and is not embedded as a permanent PASS in these files.
