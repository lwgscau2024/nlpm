# NLPM Audit: deepseek-ai/deepseek-harness
**Date**: 2026-08-14  |  **Artifacts**: 28  |  **Strategy**: batched
**NL Score**: 97/100
**Security**: CLEAR
**Bugs**: 0  |  **Quality Issues**: 3  |  **Security Findings**: 0

Not a Claude Code plugin. `.agents/skills/` is the Codex-canonical layout, so
every `SKILL.md` is scored Tier 1 against the universal Agent Skills spec at
agentskills.io — no `plugin.json`, `## Output`, `version:`, or `model:`
penalties apply. The memory files form an `AGENTS.md` hierarchy with `CLAUDE.md`
symlinked onto it.

## Scope

Audited: 13 authored `SKILL.md` + 15 `AGENTS.md`.

Excluded: 3 `SKILL.md` and 9 `hooks.json` under
`examples/acp-agent/tests/snapshots/`. These are replay fixtures for the ACP
snapshot suite and several are invalid by design (`hook-cc-invalid-matcher`,
`hook-cc-pretool-deny`). Scoring a fixture whose purpose is to be rejected is
the path-scope error the rubric names; they are not authored artifacts.

## NL Score Summary
| File | Type | Score | Top Issue |
|------|------|-------|-----------|
| .agents/skills/dsh-pre-push-checks/SKILL.md | skill | 82 | "relevant" ×9 — 7 are defined in situ, see Rule Gap |
| .agents/skills/dsh-find-simplifications/SKILL.md | skill | 86 | "relevant" ×4, "reasonable" ×2, "several" ×1 |
| .agents/skills/dsh-code-review/SKILL.md | skill | 90 | "relevant" ×4, "appropriate" ×1 |
| apps/cli/config/agent-presets/cordis/skills/cordis-plugin-development/SKILL.md | skill | 92 | "appropriate" ×2, "relevant" ×1, "sufficient" ×1 |
| .agents/skills/dsh-merging-stacked-prs/SKILL.md | skill | 94 | "several" ×1, "relevant" ×2 |
| .agents/skills/record-browser-gif/SKILL.md | skill | 95 | description 504 chars (R04 band 500–800) |
| .agents/skills/dsh-prose-standard/SKILL.md | skill | 96 | "relevant" ×2 |
| docs/AGENTS.md | memory | 96 | "appropriate" ×1, "several" ×1 |
| packages/AGENTS.md | memory | 96 | "relevant" ×2 |
| packages/client/AGENTS.md | memory | 96 | "several" ×2 |
| AGENTS.md | memory | 100 | — |
| .agents/skills/dsh-archive-agent-notes/SKILL.md | skill | 100 | — |
| .agents/skills/dsh-doc-site-sync/SKILL.md | skill | 100 | — |
| .agents/skills/dsh-doc-standards/SKILL.md | skill | 100 | — |
| .agents/skills/dsh-translate-docs/SKILL.md | skill | 100 | — |
| .agents/skills/dsh-trim-cot-leakage/SKILL.md | skill | 100 | — |
| apps/cli/config/agent-presets/cordis/skills/editing-cordis-compositions/SKILL.md | skill | 100 | — |
| .agents/notes/AGENTS.md | memory | 100 | — |
| .agents/notes/archived/AGENTS.md | memory | 100 | — |
| .agents/notes/implemented/AGENTS.md | memory | 100 | — |
| .github/AGENTS.md | memory | 100 | — |
| examples/AGENTS.md | memory | 100 | — |
| native/landlock-run/AGENTS.md | memory | 100 | — |
| packages/schedule/AGENTS.md | memory | 100 | — |
| packages/web/AGENTS.md | memory | 100 | — |
| scripts/AGENTS.md | memory | 100 | — |
| vendor/AGENTS.md | memory | 100 | — |
| website/AGENTS.md | memory | 100 | — |

Frontmatter is valid on all 13 skills and every `name` matches its parent
directory. No missing required field anywhere in the corpus.

## Security Scan
| Severity | Count |
|----------|-------|
| Critical | 0 |
| High | 0 |
| Medium | 0 |
| Low | 0 |

### Execution Surface Inventory
| Surface | Files |
|---------|-------|
| Lifecycle scripts | `scripts/install-lefthook.mjs` (root postinstall), `packages/subprocess/subprocess-local/scripts/ensure-spawn-helper.mjs` |
| Git hooks | `lefthook.yml` |
| CI workflows | 15 under `.github/workflows/` |
| MCP configs | none |

Two patterns matched the scanner and both cleared on inspection. Recording
them because the naive read files each as High.

**`scripts/install-lefthook.mjs:560` — `spawnSync(..., { shell: true })` with an
interpolated path.** Windows-only branch; the comment above it states that Node
refuses to spawn Windows `.cmd` shims directly, so the quoted path is re-parsed
by `cmd.exe`. The POSIX branch spawns without a shell. `"` is not a legal
Windows path character, so the quoting cannot be broken out of. The same
function strips `GIT_CONFIG_PARAMETERS`, `GIT_CONFIG_COUNT`, and
`GIT_CONFIG_KEY/VALUE_n` from the child environment before invoking lefthook,
creates its hooks directory `0o700`, and writes its ownership marker `0o600`
with `flag: 'wx'`. CLEAR.

**`.github/workflows/e2e.yml` — `pull_request_target` matched.** The match is
inside a comment reading "SECURITY — NEVER change this trigger to
`pull_request_target`", followed by an explanation of why that trigger would let
an untrusted fork exfiltrate `DEEPSEEK_API_KEY_EXTERNAL`, and a link to the
Agent Note recording the decision. The live trigger is `pull_request`, with a
job-level `if:` that skips forked and Dependabot PRs. No workflow in the
repository uses the privileged trigger. CLEAR.

Neither lifecycle script performs network access, `eval`, `new Function`, or
credential reads. Git hooks invoke repo-local `tsx` scripts only.

### Security Findings
No security findings.

## Bugs (PR-worthy)
None.

## Quality Issues (informational)
| # | File | Issue | Penalty |
|---|------|-------|---------|
| 1 | .agents/skills/record-browser-gif/SKILL.md:3 | Description is 504 chars, inside the R04 500–800 band | −5 |
| 2 | .agents/skills/dsh-pre-push-checks/SKILL.md:35 | "run the relevant `pnpm run test:e2e` target" — the targets are never enumerated, so the selector resolves to nothing the reader can check | −2 |
| 3 | .agents/skills/dsh-pre-push-checks/SKILL.md:41 | "When unit coverage is relevant" — the condition under which coverage applies is not stated | −2 |

## Cross-Component

**`CLAUDE.md` ↔ `AGENTS.md` symlink claim — verified true.**
Root `AGENTS.md` states that `CLAUDE.md` symlinks it "at root, `packages/`, and
`examples/`". All three are symlinks resolving to `AGENTS.md`. The instruction
"edit the real file" is therefore enforceable rather than aspirational.

**Relative links — 201 of 203 resolve.**
The two that do not are `foo.md` and `foo.zh.md` in `dsh-translate-docs`. Both
sit inside a literal language-switcher template the skill instructs the reader
to paste (`[English](foo.md) | 中文`), where `foo` stands for the pair's real
filename. They are template text, not references. Zero genuine broken
references in the corpus.

**No contradictions found** between the root `AGENTS.md` and the 14 scoped
memory files, or between any skill and the conventions it cites.

## Rule Gap — R01 over-penalizes terms defined in situ

`dsh-pre-push-checks` scores 82, its penalty driven almost entirely by nine
occurrences of "relevant". Seven of those nine are false positives, and the
reason is structural rather than incidental.

The skill contains a section headed `## Select relevant evidence` whose body is
a decision table binding each changed surface to a specific command — package
behavior to the owning Vitest file, documentation to `pnpm run doc-sync`,
model-visible output to the owning keyless snapshot, manifests and build
configuration to `pnpm run build` plus hygiene plus the built-artifact smoke.
Later sentences such as "Run the relevant evidence selected by this skill" and
"Confirm the relevant non-platform evidence" are references back to that table.

R01 penalizes unbounded quantifiers **without measurable criteria**. These have
criteria, stated in the same artifact, ahead of every use. The rule's only
current carve-out is for markdown headers, so an author who does the right thing
— define the selection rule, then refer to it by name — is penalized precisely
for the structure that makes the skill usable. The two occurrences that survive
scrutiny are recorded above as genuine.

The same shape appears in `dsh-code-review` and `dsh-prose-standard`.

Recorded as `false_positive: true` findings with `rule_gap` set, so the signal
reaches `rule-health.py` as `self_false_positive` rather than as reach.

## Recommendation

CLEAR — no PR-worthy bugs, no security findings. Score 97 with security CLEAR
puts this above the exemplar bar (≥ 90). The corpus is unusually disciplined:
every convention in the root `AGENTS.md` is a self-contained rule carrying a
linked rationale, the pre-release section carries its own removal instruction
("Remove this section at the first tagged release"), and both scanner matches in
the security pass turned out to be places where the authors had already reasoned
about the exact failure mode and written the reasoning down.

No contribution proposed. The two genuine R01 findings are one-line wording
fixes not worth a first-contact PR on their own.
