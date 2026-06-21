---
description: Run a deep, parallel 4R+1 review of a PR or the current diff before merge
agent: orchestrator
subtask: true
---

Run a deep PR review for: "{argument}".

`{argument}` may be a PR number/URL, a branch, a commit range, or empty. If empty, review the current branch vs its base (fallback: staged/working `git diff`).

Load the `review-pr` skill and follow its phases exactly.

Workflow:

1. **Discovery**
   a. Start Neurox: `neurox_session_start`, then `neurox_context` + `neurox_recall` (project + cross-namespace) for prior review rules, gotchas, and product intent.
    b. Read `CONVENTIONS.md`, `.skynex/skill-registry.md`, and `.skynex/review-rules.md` if they exist.
   c. Resolve the diff scope and the intent source (PR description / ticket / SPEC / PLAN / commit messages).

2. **Phase 0 — Readiness Gate**
   Apply the skill's readiness checklist. If a hard blocker hits, STOP and report exactly what is missing. Do not fan out.

3. **Phase 1 — Parallel judges**
   Dispatch FIVE `pr-reviewer` sub-agents in parallel (R0–R4), each scoped to one dimension, each receiving the diff, target files, intent source, Project Standards, and custom rules.

4. **Phase 2 — Synthesis**
    Merge, de-duplicate, group by severity (Blocking / Should-fix / Nice-to-have), surface contradictions for a human call, build the Verified section, and propose new rules for `.skynex/review-rules.md` (human approves).

5. **Phase 3 — Post to GitHub** (only if input is a PR number/URL; skip for branch/diff)
   Follow the review-pr SKILL's Phase 3 exactly. Key invariants: human gate BEFORE posting; ONE summary comment; best-effort inline comments (one per file:line finding, skip on API error); and EXACTLY ONE `gh pr review` submission at the end — never one per judge.

6. **Report** using the skill's output format.

Context:
- Working directory: {workdir}
- Current project: {project}
- Scope: {argument}

Important:
- Do not fix code yourself; this is review-only.
- Do not modify application files. Suggested rules are proposals, not auto-writes.
- Do not skip Neurox or the Readiness Gate.
- Use five independent dimension judges in parallel.
- Phase 3 (GitHub posting) is skipped automatically if the input is not a PR number/URL.
- Inline comments use the GitHub API line parameter (actual line number, not diff position).
