# Answer key — the planted campaign arm

The driver never opens this file. It takes one `--diff` path and reads that
path only, so the blindness is structural rather than promised; the validator
also refuses any script in this bundle whose bytes name an answer key
(`ANSWER_KEY_VISIBLE`), which is the reader for that claim.

The campaign compares the driver's report against this key **after** the run.

## `over-designed.diff` — every clause below must be raised

| Clause | The planted shape | Bytes the finding must quote |
|---|---|---|
| `P1` | two fields added to a policy document whose only code mentions are refusals | `if not isinstance(document.get("reviewed_by"), str):` |
| `P3` | a private `HEX40` literal of an identity a shared module already owns | `HEX40 = re.compile(r"^[0-9a-f]{40}$")` |
| `P5` | a repository checker's own predicate moved inside the atom that needed it moved | `if document.get("mode") != "strict":` |
| `P6` | another owner's adjudication restated in full instead of pointed at | `ed3c/skill-concerns#93` |
| `P7` | a host-absolute path with no pin and no digest | `cp /Users/operator/cache/limits.json ./policy/limits.json` |

`P2` and `P4` must **not** be raised here: no path prefix test is added, and no
machine-read enum column moves.

## `clean.diff` — no clause may be raised

The atom changes one number, narrows one function to take its limit set from
its caller, and lands the test that reds when the narrowing breaks. It carries
a policy document, a repository checker and a test, so a silent pass is a
judgement about the shapes and not about which file types the pass happened to
see.

A finding on this fixture is a false positive and reds the campaign.
