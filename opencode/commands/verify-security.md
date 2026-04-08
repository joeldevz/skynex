---
description: Validate the current development with a dedicated security review
agent: orchestrator
subtask: true
---

Verify the current development for security issues only for: "{argument}".

If no argument is provided, verify the current project changes end-to-end for security.

Workflow:

1. **Discovery before security review**
   a. Read `CONVENTIONS.md` from the project root if it exists
   b. Read `PLAN.md` and `SPEC.md` if they exist to understand scope and intent
   c. Inspect the current `git diff` / staged changes to know what changed
   d. Start Neurox with `neurox_session_start`, then call `neurox_context` and `neurox_recall` for both project-specific and cross-namespace security/product context before any other validation work

2. **Launch adversarial review in parallel**
   - Run `security` judge A
   - Run `security` judge B
   - If the target spans multiple risk areas, include additional parallel reviewers only if they are security-relevant

3. **Synthesize security findings**
   a. Merge both judges' findings
   b. Prefer the stricter interpretation when there is disagreement
   c. Separate confirmed issues from hypothetical concerns

4. **Report clearly**
   Return:
   - Passing security areas
   - Confirmed vulnerabilities
   - Hardening suggestions
   - Recommendation: approve / fix / escalate

Context:

- Working directory: {workdir}
- Current project: {project}
- Scope: {argument}

Important:

- Do not fix code yourself
- Do not modify application files
- Do not skip Neurox
- Focus only on security risk, not general code quality
- Use two independent security judges in parallel
