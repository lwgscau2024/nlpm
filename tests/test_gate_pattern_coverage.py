"""The release gate's selection pattern must cover every shipped NL artifact.

pre-release-quality-gate.yml scores only the NL artifacts a PR changed,
selected by a single regex. An artifact outside that regex is not judged
lower — it is never judged at all, on any PR, and the gate still reports
green. Silently unscorable looks exactly like clean.

That happened: `codex/skills/*/SKILL.md` sat outside the pattern from the
day the Codex layout shipped. Those files are byte-identical mirrors of
`skills/nlpm/*/SKILL.md`, so when the R01 carve-out list was edited on the
Claude side only, the two layouts disagreed about the rule — four
carve-outs for Claude users, three for Codex users — and v1.2.5 was cut
that way with every check green.

This test reads the pattern out of the workflow rather than restating it,
so the workflow stays the single source of truth, and fails when a shipped
artifact falls outside it.
"""

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "pre-release-quality-gate.yml"

# Paths that look like NL artifacts to a filename check but are not scored:
# placeholders that keep an empty directory in git, and tool config.
NOT_ARTIFACTS = {
    ".gemini/commands/.gitkeep",
    ".gemini/skills/.gitkeep",
    ".gemini/settings.json",
}


def gate_pattern() -> str:
    """Extract NL_PATTERN from the workflow, unquoted."""
    text = WORKFLOW.read_text(encoding="utf-8")
    match = re.search(r"^\s*NL_PATTERN='([^']+)'", text, re.M)
    assert match, "NL_PATTERN not found in pre-release-quality-gate.yml"
    return match.group(1)


def tracked_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT,
        capture_output=True, text=True, check=True,
    ).stdout
    return out.split()


def shipped_nl_artifacts(files: list[str]) -> list[str]:
    """Every tracked file this repo ships that an NL scorer should judge."""
    artifacts = []
    for path in files:
        if path in NOT_ARTIFACTS:
            continue
        name = path.rsplit("/", 1)[-1]
        if name in ("SKILL.md", "AGENTS.md", "CLAUDE.md", "GEMINI.md"):
            artifacts.append(path)
        elif re.match(r"^(commands|agents)/.*\.md$", path):
            artifacts.append(path)
    return sorted(artifacts)


class GatePatternCoverageTest(unittest.TestCase):
    """pre-release-quality-gate.yml: NL_PATTERN covers what we ship."""

    def setUp(self) -> None:
        self.pattern = re.compile(gate_pattern())
        self.files = tracked_files()

    def test_every_shipped_nl_artifact_is_selectable(self) -> None:
        artifacts = shipped_nl_artifacts(self.files)
        self.assertGreater(len(artifacts), 40, "artifact discovery found too few files")
        missed = [a for a in artifacts if not self.pattern.match(a)]
        self.assertEqual(
            missed, [],
            "these shipped NL artifacts fall outside the release gate's "
            "NL_PATTERN, so no PR can ever score them:\n  "
            + "\n  ".join(missed)
            + "\nAdd them to NL_PATTERN in "
              ".github/workflows/pre-release-quality-gate.yml, or add them "
              "to NOT_ARTIFACTS here with a reason.",
        )

    def test_codex_mirror_is_covered(self) -> None:
        """The specific regression this test was written for."""
        codex = [f for f in self.files if re.match(r"^codex/skills/[^/]+/SKILL\.md$", f)]
        self.assertGreater(len(codex), 0, "no codex skills found — layout moved?")
        for path in codex:
            self.assertRegex(path, self.pattern)

    def test_pattern_does_not_select_non_artifacts(self) -> None:
        """A pattern that matches everything would pass the test above."""
        for path in ("README.md", "package.json", "auditor/SCHEMAS.md",
                     "docs/for-authors.md", "analysis/ecosystem-gap.md"):
            self.assertIsNone(
                self.pattern.match(path),
                f"NL_PATTERN should not select {path}",
            )


def skill_body(path: Path) -> str:
    """Everything after the YAML frontmatter."""
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n.*?\n---\n", text, re.S)
    return text[match.end():] if match else text


class CodexMirrorParityTest(unittest.TestCase):
    """A skill duplicated into codex/ must state the same rules as its source.

    Bodies, not bytes: codex/ is build-codex.mjs output, and the converter
    normalizes frontmatter (description quoting differs across the tree).
    Frontmatter style is the converter's business. The body is the rulebook,
    and the two layouts disagreeing about a rule is the defect.

    Caught on first run: codex/skills/scoring said "minor or no issues" and
    "significant issues" where the Claude source says "findings", and
    codex/skills/rules said "security issues" for "security vulnerabilities".
    nlpm's own vocabulary registry marks `issue` deprecated in favour of
    `finding` with enforcement on, carving out only the GitHub-issue sense —
    so the Codex tree was shipping a violation of the rule nlpm enforces on
    every repo it audits.
    """

    def test_mirrored_skill_bodies_match(self) -> None:
        mismatched = []
        for codex_path in sorted(REPO_ROOT.glob("codex/skills/*/SKILL.md")):
            source = REPO_ROOT / "skills" / "nlpm" / codex_path.parent.name / "SKILL.md"
            if not source.exists():
                continue
            if skill_body(source) != skill_body(codex_path):
                mismatched.append(codex_path.parent.name)
        self.assertEqual(
            mismatched, [],
            "these skills state different rules in skills/nlpm/ and codex/"
            "skills/, so Claude and Codex users are given different "
            "instructions: " + ", ".join(mismatched)
            + "\nRe-sync the body, or regenerate with build-codex.mjs.",
        )


if __name__ == "__main__":
    unittest.main()
