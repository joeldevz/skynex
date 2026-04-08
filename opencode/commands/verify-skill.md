---
description: Validate the current development against all applicable skills and conventions
agent: orchestrator
subtask: true
---

Verify the current development against all relevant skills and project conventions for: "{argument}".

If no argument is provided, verify the current project changes end-to-end.

Workflow:

1. **Discovery before validation**
   a. Read `CONVENTIONS.md` from the project root if it exists
   b. Read `PLAN.md` and `SPEC.md` if they exist to understand intent and scope
   c. Inspect the current `git diff` / staged changes to know what was implemented
   d. Start Neurox with `neurox_session_start`, then call `neurox_context` and `neurox_recall` for both project-specific and cross-namespace product context before any other validation work

2. **Resolve applicable skills / standards**
   a. Read the skill registry if available (`.atl/skill-registry.md` or Neurox recall)
   b. Determine which skills apply to the changed files and feature area
   c. Build compact project standards for any skill-touching agents you will delegate to

3. **Parallel validation**
   Launch validation agents in parallel when they are independent:
   - `skill-validator` for skill/convention compliance
   - `test-reviewer` when tests were changed or need review
   - `verifier`-style checks when the scope includes runnable code changes

4. **Synthesize results**
   a. Merge the findings into a single report
   b. If agents disagree, prefer the stricter finding and explain the conflict
   c. If blockers exist, identify the minimum fixes needed before approval

5. **Report clearly**
   Return:
   - Passing areas
   - Warnings
   - Blocking issues
   - Missing tests / missing skill coverage
   - Recommendation: approve / fix / re-run

Context:

- Working directory: {workdir}
- Current project: {project}
- Scope: {argument}

Important:

- Do not fix code yourself
- Do not modify application files
- Do not skip Neurox
- Do not rely on a single reviewer when the scope needs independent checks
- If the task touches multiple skills, validate against all applicable ones, not just the most obvious
