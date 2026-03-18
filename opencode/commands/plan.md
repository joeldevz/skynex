---
description: Create a project plan from a task request
agent: step-builder-agent
---

Plan the task "{argument}" for the current project.

Workflow:
1. Read `CONVENTIONS.md` from the project root if it exists
2. Scan the codebase to gather technical context
3. Determine if the task matches a known plan template (CRUD, bugfix, integration, refactor) and read it from `~/.config/opencode/templates/` as a starting point
4. Ask the user the minimum necessary business and technical questions in thematic blocks
5. Confirm your understanding before writing the final plan
6. Generate or replace PLAN.md in the project root, adapting the template steps to the actual task

Context:
- Working directory: {workdir}
- Current project: {project}
- Requested task: {argument}

Important:
- Do not implement code
- Do not stop at a draft outline; produce a full PLAN.md
- Make each step small enough to be reviewed independently
- Include acceptance criteria and verification steps

When finished, tell the user the plan is ready and that they can use `/execute` to start implementation.
