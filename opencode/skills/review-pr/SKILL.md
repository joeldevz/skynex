---
name: review-pr
description: Use when your human partner asks for a deep PR or diff review, a code review, or to evaluate changes before merge.
---

# Deep PR Review — 4R+1 Framework

Orchestrate a thorough, parallel, evidence-based review of a PR or diff using five independent dimension judges, then synthesize one prioritized verdict.

## Phase 0 — Readiness Gate (is the PR reviewable?)

Spend no judge until the PR has what's needed. Garbage in → garbage out.

Resolve the diff first: PR number/URL via `gh`, branch vs base, commit range, or staged/working `git diff`. Then resolve the intent source (PR description, ticket, SPEC/PLAN.md, or commit messages).

Checklist:
- [ ] Non-empty diff and the base resolves. (empty/unresolvable → **blocked**)
- [ ] Intent source exists. (none → **blocked**: R0 cannot verify intent)
- [ ] Behavior change ships tests, or an explicit reason there are none. (missing → flag, not block)
- [ ] Scope is focused, not several unrelated changes mixed. (mixed → flag)
- [ ] Size is sane. Warn >400 lines changed, strong-warn >800. (still review; reliability degrades)

Hard blocker → STOP. Report exactly what's missing to make the PR reviewable. Do not fan out.

## Phase 1 — Parallel fan-out (5 judges, isolated context)

Read `.skynex/skill-registry.md` and `.skynex/review-rules.md` (fallback `reviewPrd.md`) if present; pass both to every judge as Project Standards + `custom_rules`. A violation of a project rule is always a finding.

Dispatch FIVE `pr-reviewer` sub-agents IN PARALLEL, one per dimension, each with `dimension`, `target_files`, `diff`, `intent_source`, and the standards. Isolated context = independent analysis (no cross-contamination).

| Dim | Lens |
|-----|------|
| R0 | Correctness / Intent — does it do what was asked? logic bugs |
| R1 | Risk — security, breaking changes, sensitive zones |
| R2 | Readability — maintainability + over-engineering (thermo-nuclear + ponytail ladder) |
| R3 | Reliability — real tests, edge cases, error handling, timeouts |
| R4 | Resilience — retries, degradation, observability, cascades |

## Phase 2 — Synthesis

1. Merge findings; de-duplicate (same file:line from two judges → keep the strictest).
2. Group by severity: **Blocking → Should-fix → Nice-to-have**.
3. Contradictions between judges → present both and escalate to your human partner. No auto-tiebreak.
4. Build **Verified** from every judge's verified checks — tell the human what was already covered.
5. Collect `rule_suggestions` → propose bullets for `.skynex/review-rules.md`. The human approves; never auto-write rules.

## Output report

```
# PR Review — <scope>
Verdict: APPROVE | FIX REQUIRED | ESCALATE
Readiness: ok | degraded (<gaps>)

## Blocking (must fix)
- [R?] file:line — problem → fix

## Should-fix
- [R?] file:line — problem → fix

## Nice-to-have
- [R?] ...

## Verified (already checked, spend your attention elsewhere)
- ...

## Contradictions (need a human call)
- ...

## Suggested rules for .skynex/review-rules.md (approve to add)
- ...

R2 simplification: net: -<N> lines possible
```

## Scale to risk

- 10-line config/docs → run R0 + R1 only, quick pass.
- Feature / logic change → all 5 judges.
- 1000+ line refactor → all 5 + call out decomposition under R2.

## Phase 3 — Post to GitHub (PR input only)

Skip this phase if the input was a branch, commit range, or plain `git diff` (no PR number/URL available).

1. Detect context: `gh repo view --json nameWithOwner -q .nameWithOwner` for repo, `gh pr view {pr} --json headRefOid -q .headRefOid` for head commit.

2. Post top-level summary: `gh pr comment {pr} --body "..."` with full verdict report (Blocking / Should-fix / Nice-to-have / Verified sections) in GitHub Markdown. End: `*Reviewed by skynex /review-pr · 5 judges (R0–R4) · claude-sonnet-4-6*`

3. Post inline review comments for each finding with `file:line`: `gh api --method POST /repos/{owner}/{repo}/pulls/{pr}/comments -f body="[R?·Dimension] <problem> → <fix>" -f commit_id="{head_commit}" -f path="{file}" -F line={line_number} -f side="RIGHT"`. Skip if file not in diff. Use `line=1` for file-level findings.

4. Submit GitHub review: `--request-changes` if Blocking, `--comment` if Should-fix only, `--approve` if clean.

## Rules

- Review-only: never modify application files. Suggested rules are proposals, not auto-writes.
- Never approve on "it works" alone — correctness AND structure both gate.
- Every finding cites file:line. Drop vague claims.
