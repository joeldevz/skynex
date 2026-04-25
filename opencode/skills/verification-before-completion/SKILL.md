---
name: Verification Before Completion
description: Use before any sub-agent returns status:success or claims a task complete. Forces evidence-based verification of acceptance criteria. Mandatory for coder, verifier, test-reviewer.
license: Complete terms in LICENSE.txt
---

# Verification Before Completion

> **SUBAGENT-STOP gate**: if you are running as a subagent invoked by another subagent (nested >1 level deep), STOP. Return `status: blocked` with reason `nested-subagent-loop-detected`.

> **Principio destilado** (obra/Superpowers + gentle-ai TDD Cycle Evidence): "Done" without evidence is slop. Every completion claim must be backed by concrete proof.

## The Iron Rule

Before claiming `status: success` or "task complete", you MUST provide concrete evidence for each claim. If evidence cannot be provided → `status: blocked` with reason.

## Evidence required by claim

| Claim                       | Required evidence                                      |
|-----------------------------|--------------------------------------------------------|
| "Code compiles"             | Output of build command (last 20 lines)                |
| "Tests pass"                | Test runner output with green count + names           |
| "Feature works"             | Manual verification step OR e2e test name             |
| "Bug fixed"                 | Reproduction case BEFORE + AFTER                      |
| "Refactor safe"             | Tests still pass + no behavior change cited           |
| "Types correct"             | `tsc --noEmit` output (clean or specific errors)      |
| "Lint clean"                | Linter output                                         |
| "Documentation updated"     | List of files modified + diff summary                 |

## Anti-rationalization table

Reject these excuses immediately and either provide evidence or block:

| Excuse                                      | Reality                                          |
|---------------------------------------------|--------------------------------------------------|
| "It's a simple change, no need to test"     | Run the test anyway. 10 seconds.                 |
| "Tests aren't set up for this area"         | `status: blocked` + report missing setup        |
| "I'll verify in the next iteration"         | No. Verify now or block.                         |
| "Should work based on the code"             | "Should" is not evidence. Run it.               |
| "Looks good to me"                          | Subjective. Provide objective output.           |
| "I believe the change is correct"           | Belief is not evidence. Test it.                 |
| "The user can verify"                       | No. You verify before claiming complete.         |

## Required output structure

When returning `status: success`, the return envelope MUST include:

```yaml
verification:
  build: <output snippet or "skipped: not a build task">
  tests:
    ran: <test names or "skipped: docs-only">
    passed: <count>
    failed: <count>
  types: <tsc output or "n/a">
  lint: <linter output or "n/a">
  manual_check: <description or "n/a">
  evidence_quality: high | medium | low
```

If `evidence_quality: low` → reconsider returning `status: blocked` instead.

## When verification cannot be performed

If the environment doesn't allow verification (no test runner, missing deps, etc.):
1. `status: blocked`
2. `reason: cannot-verify`
3. `details:` what's missing
4. Do NOT claim success.

## Exceptions (no verification needed)

- Documentation-only changes (markdown, comments)
- Configuration files where syntax is the only validation needed
- Trivial refactors where types catch all errors

For these, declare the exception explicitly: `verification: { exception: docs-only }`.

## Cultural rules

- Address the user as "your human partner"
- Never use "should work" / "looks good" / "I believe" without evidence
- Never claim completion just because file edits succeeded

## Referencias

- obra/Superpowers — verification-before-completion pattern
- Gentleman/gentle-ai — TDD Cycle Evidence in return envelope
- Pragmatic Programmer — "trust but verify"
