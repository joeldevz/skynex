---
description: Create a project plan from a task request
agent: step-builder-agent
---

Plan the task "{argument}" for the current project.

Workflow:
1. **Discovery phase** (before asking questions):
   a. Read `CONVENTIONS.md` from the project root if it exists
   b. Read `package.json` and `tsconfig.json` for stack context
   c. Glob for existing modules similar to the requested feature
   d. Read 1-2 existing tests to understand testing patterns
   e. Search Engram memory (`mem_search`) for past architectural decisions relevant to this task
   f. Note any external libraries that may need Context7 docs during implementation
2. Determine if the task matches a known plan template (CRUD, bugfix, integration, refactor) and read it from `~/.config/opencode/templates/` as a starting point
3. Ask the user the minimum necessary business and technical questions in thematic blocks
4. Confirm your understanding before writing the final plan
5. Generate or replace PLAN.md in the project root, adapting the template steps to the actual task

Context:
- Working directory: {workdir}
- Current project: {project}
- Requested task: {argument}

Important:
- Do not implement code
- Do not stop at a draft outline; produce a full PLAN.md
- Make each step small enough to be reviewed independently
- Include acceptance criteria and verification steps
- If the task involves external libs, add a note in the relevant step that the coder should consult Context7 for live docs

When finished, tell the user the plan is ready and that they can use `/execute` to start implementation.
