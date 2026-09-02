# Generation-close runbook (L1 domain)

The supervised generation's close-out procedure belongs to the dispatcher's
ceremony and is not restated here. This document owns exactly one of its steps
and the receipt that proves the step happened, so a close-out that skipped it is
visible in the next disposition instead of being silently absent.

The station this step serves is the `noodles-generation-close` row of
[`observation-topology.json`](observation-topology.json): read-only against the
generation's artifacts, feedback out through issues and this bundle's ledger
only, and nothing at all mid-generation.

## Step `red-team-generation-close-shadow`

1. **Assemble the bundle from the closed generation.** Three directories, from
   the inputs the topology row enumerates: `diffs/` (the PR diffs landed during
   the generation), `receipts/` (the generation's session receipts, copied out
   of a clone or a fixture - never read from a live working tree), `issues/`
   (every issue filed during the generation). A kind the generation genuinely
   has none of is an empty directory, never a missing one: an absent kind and a
   clean kind must not look alike.

2. **Run the pass.**

   `python3 skills/red-team/scripts/shadow_driver.py --bundle <dir> --wave <generation> --boundary generation-close --subject noodles-generation-close --append-record`

   Exit 0 is "no findings", the honest steady state. Exit 1 carries findings, or
   the curve report. Exit 2 is a refusal - the bundle moved underneath the pass,
   or a finding the schema rejects - and a refusal appends nothing.

3. **Completion receipt: the appended record.** The step is complete when
   [`domain/run-ledger.json`](run-ledger.json) carries one more record whose `subject`
   is `noodles-generation-close` and whose `wave` names this generation. That
   record IS the completion evidence; there is no separate sign-off. A
   generation whose close-out carries no such record is incomplete rather than
   clean, and the next disposition reads that off the ledger.

4. **Hand the findings to the dispatcher.** `render_demonstration()` emits each
   finding as a block that drops verbatim into an issue body's observer
   demonstration section. The dispatcher files; nothing in this bundle does.

## What this step is not

It does not judge clauses (that is the slg pass sharing the same boundary), it
does not classify runtime liveness, and it never runs while the generation is
still open. A class whose recipe has graduated into a consumer CI gate is
already `gated` in the catalogue and drops out of this pass's sampling - the
step gets cheaper as the machine takes classes over, which is the whole point of
the graduation split.
