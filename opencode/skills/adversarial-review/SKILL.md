---
name: Adversarial Review
description: Use when a decision or output needs adversarial dual-judge review (security, tests, architecture, refactor safety). Generalizes the security skill pattern to any domain.
license: Complete terms in LICENSE.txt
---

# Adversarial Review — Dual-Judge, Domain-Parameterized

> **Principio destilado** (Gentleman/gentle-ai judgment-day + nuestro `security` existente): the dual-judge adversarial pattern works across domains, not only security. Generalizar para reusar la mecánica madura.

## Activation

Caller MUST specify `domain`:

| Domain | Use case |
|---|---|
| `security` | Vulnerability review (delegates to `security` skill specifics) |
| `tests` | Test coherence and quality |
| `architecture` | Module boundaries, deep modules, cohesion |
| `refactor` | Refactor safety (no behavior change) |
| `other` | Caller-defined criteria via `criteria:` field |

## Protocol

### Phase 1 — Launch two judges in parallel

The orchestrator launches **two independent judge sub-agents** with identical inputs:

```yaml
domain: <domain>
target_files: [<paths>]
criteria: <domain-specific rules from skill registry>
```

Each judge:
- Operates in **isolation** (no shared context, no awareness of the other)
- Has read-only tools (read, glob, grep, bash for diagnosis)
- Returns its own verdict in the standard envelope

### Phase 2 — Synthesize verdicts

| Verdict A | Verdict B | Synthesis |
|---|---|---|
| APPROVED | APPROVED | `Confirmed: APPROVED` → proceed |
| REJECTED | REJECTED | `Confirmed: REJECTED` → return findings to coder |
| APPROVED | REJECTED | `Contradiction` → invoke `advisor_consult` for tiebreak |
| REJECTED | APPROVED | `Contradiction` → invoke `advisor_consult` for tiebreak |
| any | uncertain | `Suspect` → ask user |

### Phase 3 — Fix Agent + Re-judge (if Confirmed REJECTED)

If both judges reject, coder fixes the findings. Then **re-launch both judges** on the fixed version. Maximum 2 iterations.

If still rejected after 2 iterations → `status: blocked` with reason `adversarial-review-stuck`.

## Why dual-judge generalizes

The security skill validated this pattern empirically. The mechanics are domain-agnostic:
- Independence prevents groupthink
- Synthesis catches blind spots
- Fix Agent loop ensures findings are addressable, not just described

## Domain criteria sources

Each domain pulls criteria from a different source:

| Domain | Criteria source |
|---|---|
| `security` | `opencode/skills/security/SKILL.md` (review areas: injection, auth, data exposure, rate limiting, crypto) |
| `tests` | TDD Discipline + skill registry test rules |
| `architecture` | CONVENTIONS.md + Ousterhout deep modules principles |
| `refactor` | Original tests must still pass + no behavior change |
| `other` | `criteria:` field passed by caller |

## Return envelope per judge

```yaml
domain: <domain>
verdict: APPROVED | REJECTED | UNCERTAIN
findings:
  - file: <path>
    line: <number>
    severity: critical | high | medium | low
    issue: <description>
    fix_hint: <1-line suggestion>
synthesis_notes: <judge's reasoning>
```

## Backward compatibility

The existing `security` skill continues to work as a preset:
- `security` skill = `adversarial-review --domain security` (same mechanics)
- No breaking changes to orchestrator's existing security flow

## Smart-zone awareness

Each judge has its own 100K cap. If a judge returns `zone: warning` or `dumb` → orchestrator re-launches with smaller scope (slice-by-slice instead of all-at-once).

## Cultural rules

- Judges are **adversarial**: assume the code has bugs until proven otherwise
- No sycophancy in findings; be direct and specific
- Address author as "your human partner" in feedback

## Referencias

- Gentleman/gentle-ai — `judgment-day` skill validated dual-judge generalizes
- Our `security` skill — original implementation of the pattern
- obra/Superpowers — anti-rationalization for judges
