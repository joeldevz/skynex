# Lesson Learned: Inline Self-Review ≥ Subagent Review Loop

> **Source**: obra/Superpowers RELEASE-NOTES, validated empirically with 5×5 trials.
> **Status**: Documented for Sprint 2 verifier redesign (M3).
> **Date**: 2026-04-25.

## TL;DR

In many cases, an **inline self-review checklist** in the implementer's own prompt produces equivalent or better quality than spawning a separate reviewer subagent — at ~25 min/iteration savings.

## Empirical finding (obra)

| Setup | Quality | Wall-clock | Token cost |
|---|---|---|---|
| Inline self-review checklist | 87% pass rate | baseline | baseline |
| Subagent reviewer + retry loop | 91% pass rate | +25 min/iteration | +40% tokens |

The 4% quality bump from a separate reviewer rarely justifies the 40% token cost and 25-minute wall-clock penalty.

## When inline self-review is enough

✅ **Use inline self-review when**:
- The implementer is in smart zone (<70K tokens)
- The change is bounded and verifiable mechanically (lint + types + tests)
- The implementer has clear acceptance criteria
- Time pressure favors fast iteration

❌ **Use subagent reviewer when**:
- Implementer has crossed 70K tokens (entering warning/dumb zone)
- Adversarial review needed (security, architecture decisions)
- Cross-domain expertise required (e.g. UX + accessibility + performance)
- Multiple independent perspectives needed for a high-stakes decision

## Implementation pattern (for Sprint 2)

### Inline self-review checklist (in coder's system prompt)

```
BEFORE returning status:success, run this self-check:

[ ] Tests pass (capture output in verification.tests)
[ ] Types clean (capture tsc output in verification.types)
[ ] Lint clean (capture linter output in verification.lint)
[ ] No banned patterns (assertion tautologies, ghost loops, mock>6)
[ ] Description Trap respected if I touched any SKILL.md
[ ] Smart zone OK (<80K tokens)
[ ] Anti-rationalization: I have NOT modified tests to pass
[ ] Evidence quality: every claim in executive_summary has proof

If ANY check fails → status:blocked with specific reason.
```

### When to escalate to subagent reviewer (orchestrator decides)

```python
# Orchestrator decision logic (pseudo)
if implementer_zone == "smart" and task_complexity == "bounded":
    use inline self-review
elif task_domain in ["security", "architecture", "high-stakes"]:
    spawn subagent reviewer (already done in our security skill)
elif implementer_tokens > 70K:
    clear context + spawn fresh subagent reviewer
```

## Implications for our verifier agent

Currently, our `verifier` is a separate sub-agent (in opencode.json). Two options for Sprint 2 (M3):

### Option A — Hybrid (recommended)

- Keep `verifier` as separate subagent for high-stakes verification
- Add inline self-review checklist to `coder` prompt for routine cases
- Orchestrator decides which to invoke based on task complexity

### Option B — Replace with inline only

- Move all verification logic to `coder`'s prompt
- Save verifier tokens
- Risk: less adversarial review, more cheating risk

### Option C — Two-stage subagent review

- Split `verifier` into `spec-compliance-checker` + `code-quality-reviewer`
- Inspired by obra's two-stage review (spec compliance THEN code quality)
- Stronger gates but higher cost

**Decision pending**: capture in M3 design notes, validate against eval suite before committing.

## Action items

- [ ] Sprint 2 M3: prototype Option A in branch
- [ ] Run our 9 golden tests with inline self-review vs subagent verifier
- [ ] Measure: pass rate, wall-clock, token cost
- [ ] Decide based on data

## Referencias

- obra/Superpowers RELEASE-NOTES (5×5 trial documented)
- Matt Pocock — smart zone awareness
- Our security skill (already adversarial dual-judge — keep that pattern)
