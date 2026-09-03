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

2. **Run the pass, and persist its report in the same invocation.**

   `python3 skills/red-team/scripts/shadow_driver.py --bundle <dir> --wave <generation> --boundary generation-close --subject noodles-generation-close --save-report skills/red-team/domain/persisted-reports/<generation>.json --append-record`

   Exit 0 is "no findings", the honest steady state. Exit 1 carries findings, or
   the curve report. Exit 2 is a refusal - the bundle moved underneath the pass,
   or a finding the schema rejects - and a refusal appends nothing.

   `--save-report` is not a convenience. The bundle this pass measured stops
   existing the moment the generation's changes land: the landing machine
   rewrites every referenced issue body and every branch head moves, so
   ed3c/skill-concerns#131's re-measure procedure has nothing left to
   re-measure (ed3c/skill-concerns#158). Three waves in a row lost their record
   to that ordering. The artifact is committed with the wave, before the lands.

   If the append could not happen here, it happens later from the artifact and
   from nothing else:

   `python3 skills/red-team/scripts/shadow_driver.py --from-report skills/red-team/domain/persisted-reports/<generation>.json --append-record`

   And if no artifact was persisted and the wave has already landed, the run
   cannot produce a record at all. It goes into
   [`unpersistable-runs.json`](unpersistable-runs.json) with its reason and
   without its numbers - typing those in is refused by `derived_column_errors`
   and by the `run_id` instant, and it would be refused here anyway: the
   numbers are exactly what was lost.

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
