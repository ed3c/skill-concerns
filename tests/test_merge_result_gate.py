"""Falsifiers for grading the merge result, ed3c/skill-concerns#111.

Three things are under test and they are deliberately separate:

1. `scripts/merge_state.py` - the pure decision. Four provider states, four
   exits, and only MERGEABLE exits 0. Its own `--selftest` is the falsifier;
   this module runs it and asserts the exits are distinct here too.
2. The two-PR fixture. Real branches, a real `git merge`, and the repository's
   real `check_admissions.check()`. It measures the claim the atom rests on:
   two heads that are each green can merge with no textual conflict into a tree
   that is red, so "this commit is internally consistent" is not "main stays
   green after this lands".
3. `.github/workflows/verify.yml` as bytes. `workflow_gaps()` is the reader and
   every clause has a planted inverse - delete the clause from a copy and
   exactly that gap appears.

Ceiling: (3) reads the workflow's text, never a runner. Whether the job it
describes actually executes is L4 and is not claimed here; the workflow file
that grades a candidate comes from the default branch under
`pull_request_target`, so this reader's real subject is a PR that tries to
remove the job - and such a PR reds its own `candidate-self-tests`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_admissions  # noqa: E402
import merge_state  # noqa: E402
from common import digest_entries, regular_files, sha256_file, tree_digest  # noqa: E402

WORKFLOW = ROOT / ".github" / "workflows" / "verify.yml"

# Every clause verify.yml must carry for a merge result to be graded, paired
# with the byte that carries it. A clause with no needle is a claim with no
# reader, which is the defect class this atom is an instance of.
WORKFLOW_CLAUSES: tuple[tuple[str, str], ...] = (
    (
        "MERGE_REF_NEVER_CHECKED_OUT",
        "refs/pull/${{ github.event.pull_request.number }}/merge",
    ),
    ("MERGE_TREE_NEVER_GRADED", "working-directory: .merge"),
    ("MERGEABILITY_NOT_RESOLVED_FROM_TRUSTED_BYTES", ".trusted/scripts/merge_state.py"),
    ("MERGE_RESULT_FAILURE_NOT_REFUSED", "needs.merge-result.result"),
    # `merge_state.EXITS` splits UNMERGEABLE/UNKNOWN/UNREADABLE into three
    # codes, but the shell fails the job identically on all three. The refusal
    # string is the only place that split is ever read, so if it stops naming
    # the state word the three exits become one silent shape again.
    ("REFUSAL_DOES_NOT_NAME_THE_MERGEABILITY_STATE", "${MERGE_STATE:-ABSENT}"),
    ("VERIFY_CAN_BE_SKIPPED_INTO_A_PASS", "if: ${{ !cancelled() }}"),
    ("RECEIPT_DOES_NOT_NAME_THE_GRADED_TREE", '"merge_sha": os.environ["MERGE_SHA"]'),
    (
        "RECEIPT_DOES_NOT_NAME_THE_MERGEABILITY_STATE",
        '"merge_state": os.environ["MERGE_STATE"]',
    ),
)

GIT_IDENTITY = ("-c", "user.name=fixture", "-c", "user.email=fixture@invalid")


def workflow_gaps(text: str) -> list[str]:
    """Which merge-result clauses `text` does not carry."""
    return [name for name, needle in WORKFLOW_CLAUSES if needle not in text]


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *GIT_IDENTITY, *args], cwd=root, capture_output=True, text=True
    )


def repin_subject(root: Path, skill: str) -> None:
    """Re-pin one receipt's subject digests to the tree that is there now.

    Not `gen_admission.py`: the producer re-runs the whole Skill row before it
    writes, and this fixture is about what happens to two receipts that were
    each honest for their own tree. Recomputing exactly the two fields
    `check_admissions` ties keeps the fixture to the digest tie under test.
    """
    path = root / "admissions" / f"{skill}.json"
    body = json.loads(path.read_text(encoding="utf-8"))
    entries = digest_entries(root, regular_files(root / "skills" / skill))
    body["subject_files"] = entries
    body["skill_tree_sha256"] = tree_digest(entries)
    path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")


def move_contract(root: Path) -> None:
    """PR A: change a shared contract and repin every receipt that pins it TODAY."""
    path = root / "contracts" / "feature-map.schema.json"
    body = json.loads(path.read_text(encoding="utf-8"))
    body["description"] = "moved by the fixture's first pull request"
    path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    for receipt in sorted((root / "admissions").glob("*.json")):
        document = json.loads(receipt.read_text(encoding="utf-8"))
        entries = [
            entry
            for entry in document.get("contract_files", [])
            if entry["path"].endswith("feature-map.schema.json")
        ]
        if not entries:
            continue
        for entry in entries:
            entry["sha256"] = sha256_file(root / entry["path"])
        receipt.write_text(
            json.dumps(document, indent=2) + "\n", encoding="utf-8"
        )


def adopt_contract(root: Path) -> None:
    """PR B: a Skill starts pinning that contract, at whatever sha its base held.

    Nothing here touches the contract, and PR A never touches this Skill's
    receipt, so the two changes have no line in common. That is the point: the
    conflict machinery cannot see this, and both heads are green.
    """
    manifest = root / "skills" / "red-team" / "skill.json"
    document = json.loads(manifest.read_text(encoding="utf-8"))
    document["shared_contracts"].append("../../contracts/feature-map.schema.json")
    manifest.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    receipt = root / "admissions" / "red-team.json"
    body = json.loads(receipt.read_text(encoding="utf-8"))
    body["contract_files"].append(
        {
            "path": "contracts/feature-map.schema.json",
            "sha256": sha256_file(root / "contracts" / "feature-map.schema.json"),
        }
    )
    receipt.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    repin_subject(root, "red-team")


class MergeStateTests(unittest.TestCase):
    """The mergeability decision: never a skip, and only one state exits 0."""

    def test_selftest_passes(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "merge_state.py"), "--selftest"],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

    def test_unknown_and_unmergeable_never_share_the_green(self) -> None:
        # The absence control ed3c/skill-concerns#111 asks for: a PR whose
        # mergeable_state is `unknown` or `dirty` must not produce the same
        # outcome as a PR whose merge result was fetched and graded.
        self.assertEqual(0, merge_state.EXITS[merge_state.MERGEABLE])
        for state in (merge_state.UNMERGEABLE, merge_state.UNKNOWN, merge_state.UNREADABLE):
            with self.subTest(state=state):
                self.assertNotEqual(0, merge_state.EXITS[state])
        self.assertEqual(len(merge_state.EXITS), len(set(merge_state.EXITS.values())))

    def test_an_unrecognised_shape_is_unknown_not_mergeable(self) -> None:
        self.assertEqual(merge_state.UNKNOWN, merge_state.classify(None, None))
        self.assertEqual(merge_state.UNKNOWN, merge_state.classify("true", "clean"))

    def test_the_state_word_survives_a_failing_exit(self) -> None:
        """The channel that actually distinguishes 4 from 5, exercised.

        No process branches on the exit integers -- `verify.yml`'s shell fails
        the job identically on 3, 4 and 5. What tells a conflicting PR from an
        uncomputed one from an unreachable provider is the state WORD appended
        to `$GITHUB_OUTPUT`, which `verify` prints in its refusal. That word is
        only worth naming if it is written on the failing path too, so this
        asserts both halves together: the non-zero exit AND the word beside it.
        """
        original = merge_state.read_pull
        try:
            for state in (
                merge_state.UNMERGEABLE,
                merge_state.UNKNOWN,
                merge_state.UNREADABLE,
            ):
                with self.subTest(state=state), tempfile.TemporaryDirectory() as tmp:
                    output = Path(tmp) / "github_output"
                    merge_state.read_pull = (
                        lambda _repo, _pull, _state=state: (_state, "stub")
                    )
                    code = merge_state.main(
                        [
                            "--repository", "ed3c/skill-concerns",
                            "--pull", "1",
                            "--attempts", "1",
                            "--github-output", str(output),
                        ]
                    )
                    self.assertEqual(merge_state.EXITS[state], code)
                    self.assertNotEqual(0, code)
                    self.assertEqual(
                        f"merge_state={state}\n", output.read_text(encoding="utf-8")
                    )
        finally:
            merge_state.read_pull = original


class MergeResultFixtureTests(unittest.TestCase):
    """Two green heads, one clean merge, one red tree.

    This is the measurement the atom rests on rather than an illustration of
    it: real branches, a real `git merge`, and this repository's own
    `check_admissions.check()` on all four trees.
    """

    def setUp(self) -> None:
        # A fresh checkout per test rather than a shared one: these tests move
        # HEAD and merge, and a fixture whose second test inherits the first
        # one's tree would make an ordering accident look like a result.
        #
        # `.resolve()` because macOS hands out /tmp paths whose real prefix is
        # /private/tmp, and `safe_repo_path` compares resolved parents: an
        # unresolved root makes every receipt look like a path traversal.
        self.scratch = Path(tempfile.mkdtemp(prefix="merge-result-fixture-")).resolve()
        self.addCleanup(shutil.rmtree, self.scratch, ignore_errors=True)
        self.root = self.scratch / "tree"
        shutil.copytree(
            ROOT,
            self.root,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
        )
        git(self.root, "init", "-q", "-b", "main")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "base")
        self.base = git(self.root, "rev-parse", "HEAD").stdout.strip()

    def branch(self, name: str, start: str, change) -> list[str]:
        self.assertEqual(0, git(self.root, "checkout", "-q", start).returncode)
        self.assertEqual(0, git(self.root, "checkout", "-q", "-b", name).returncode)
        change(self.root)
        git(self.root, "add", "-A")
        self.assertEqual(0, git(self.root, "commit", "-q", "-m", name).returncode)
        return check_admissions.check(self.root)

    def test_two_green_heads_merge_clean_into_a_red_tree(self) -> None:
        # The positive control. Each head passes the gate the two existing
        # verify jobs run, the merge has no textual conflict for either job to
        # notice, and the tree that would become main is red.
        self.assertEqual([], self.branch("pr-a", self.base, move_contract))
        self.assertEqual([], self.branch("pr-b", self.base, adopt_contract))

        git(self.root, "checkout", "-q", "pr-a")
        merge = git(self.root, "merge", "--no-edit", "pr-b")
        self.assertEqual(0, merge.returncode, merge.stdout + merge.stderr)

        self.assertIn(
            "ADMISSION_CONTRACT:red-team_DIGEST_DRIFT:contracts/feature-map.schema.json",
            check_admissions.check(self.root),
        )

    def test_the_same_work_rebased_onto_the_landed_head_stays_green(self) -> None:
        """Planted negative: the new job is not simply always-red on stacked work.

        Same two changes, but B is built on top of A's landed head, so B pins
        the contract sha A left behind. Without this arm a job that reds on
        every stacked pull request would pass the positive control above.
        """
        self.assertEqual([], self.branch("pr-a", self.base, move_contract))
        landed = git(self.root, "rev-parse", "HEAD").stdout.strip()
        self.assertEqual([], self.branch("pr-b-rebased", landed, adopt_contract))

        git(self.root, "checkout", "-q", "pr-a")
        merge = git(self.root, "merge", "--no-edit", "pr-b-rebased")
        self.assertEqual(0, merge.returncode, merge.stdout + merge.stderr)
        self.assertEqual([], check_admissions.check(self.root))


class VerifyWorkflowTests(unittest.TestCase):
    """verify.yml as bytes: every clause present, every clause falsifiable."""

    def setUp(self) -> None:
        self.text = WORKFLOW.read_text(encoding="utf-8")

    def test_the_workflow_carries_every_merge_result_clause(self) -> None:
        self.assertEqual([], workflow_gaps(self.text))

    def test_deleting_any_clause_is_reported_by_name(self) -> None:
        for name, needle in WORKFLOW_CLAUSES:
            with self.subTest(clause=name):
                hollowed = self.text.replace(needle, "")
                self.assertIn(name, workflow_gaps(hollowed))

    def test_the_merge_tree_is_graded_by_the_same_gate_as_the_candidate(self) -> None:
        # Not "some command runs in .merge": the SAME entrypoint the candidate
        # job runs, or the third tree is graded by a weaker standard than the
        # first two and the receipt would say otherwise.
        self.assertIn(
            "working-directory: .merge\n        run: python3 scripts/run_all.py",
            self.text,
        )
        self.assertIn(
            "working-directory: .candidate\n        run: python3 scripts/run_all.py",
            self.text,
        )

    def test_the_resolver_is_read_from_the_trusted_checkout(self) -> None:
        # The candidate must not get to decide whether it is mergeable.
        self.assertIn("python3 .trusted/scripts/merge_state.py", self.text)
        self.assertNotIn("python3 .merge/scripts/merge_state.py", self.text)
        self.assertNotIn("python3 .candidate/scripts/merge_state.py", self.text)


if __name__ == "__main__":
    unittest.main()
