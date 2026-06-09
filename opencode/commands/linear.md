---
description: Execute a Linear issue end-to-end with strict TDD and human gates
agent: linear-orchestrator
subtask: false
---

Drive the Linear issue through the full TDD pipeline using the linear-orchestrator state machine.

Issue: $ARGUMENTS

Context:
- Working directory: {workdir}
- Current project: {project}

Start at STEP 0 (intake):
1. Fetch the issue ($ARGUMENTS) with linear_get_issue; claim it and move it to the team's "In Progress" state.
2. Read and clarify (CLARITY GATE — wait for explicit human confirmation; run grill-me if unclear).
3. Post Comment #1 SPEC, then emit the copy-paste handoff prompt for a fresh execution session and stop.
4. Execution phase (same session through the validation gate): test plan + use-case grill (Comment #2) → write failing tests in parallel (RED, Comment #3) → wait for EXPLICIT human validation (Comment #4) → implement to green in parallel (Comment #5) → open PR + move to "In Review" (Comment #6).

Follow every HARD RULE in the linear-orchestrator prompt. Never write code or run tests yourself — delegate. Never auto-pass the human gates.
