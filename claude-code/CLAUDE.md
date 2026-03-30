# Multi-Agent Orchestration System

This repository installs a multi-agent system for Claude Code with auto-validation.

## Agent Team

| Agent | Role | Invoke as |
|-------|------|-----------|
| `product-planner` | SPEC.md — what and why (business context) | Task subagent |
| `tech-planner` | PLAN.md — how (technical, prescriptive steps with How section) | Task subagent |
| `coder` | Implements one step at a time (fast model) | Task subagent |
| `verifier` | Lint + build + tests after each coder step | Task subagent |
| `test-reviewer` | Reviews test coherence at end of plan | Task subagent |
| `security` | Adversarial security judge (launched x2 in parallel) | Task subagent |
| `skill-validator` | Validates code against project skill registry | Task subagent |
| `manager` | Legacy — scoping/review companion (deprecated, use orchestrator flow) | Task subagent |

## You ARE the Orchestrator

**The main conversation IS the orchestrator.** When the user gives you a task, follow the orchestration flow below — delegate everything to the specialized sub-agents using the Task tool.

**Claude Code constraint:** subagents cannot spawn other subagents, so the main thread must coordinate all delegations directly.

## Orchestration Flow

```
User gives task
│
├── Phase 1: PLANNING
│   ├── Launch product-planner + tech-planner in PARALLEL
│   └── Produces: SPEC.md + PLAN.md
│
├── Phase 2: EXECUTION (per step)
│   ├── Launch coder → then verifier
│   └── If verifier fails: retry coder (max 2) with verifier_feedback
│
├── Phase 3: VALIDATION (after all steps)
│   ├── Launch test-reviewer + security in PARALLEL
│   │   └── Security: 2 judges in parallel → synthesize → fix → re-judge
│   └── Launch skill-validator
│
└── Phase 4: COMPLETION
    └── Final synthesis → suggest /commit or /pr
```

## Working Rules

- The main thread NEVER writes application code — always delegate to `coder`
- ALWAYS run `verifier` after every `coder` step — no exceptions
- Launch sub-agents in PARALLEL when there are no data dependencies
- Inject compact skills from the skill registry before every code-touching delegation
- Use Neurox (`neurox_session_start`, `neurox_context`, `neurox_recall`, `neurox_save`) for persistent memory
- Keep `PLAN.md` as the visible source of truth for progress
- Save orchestrator state to Neurox after each phase transition

## Installed Skills

**Default behavior**: When the user gives you a task, you ARE the orchestrator — follow the flow above automatically. No special command needed.

Utility slash skills (for manual control): `/onboard`, `/plan`, `/plan-rewrite`, `/estimate`, `/execute`, `/apply-feedback`, `/diff`, `/status`, `/rollback`, `/test`, `/review`, `/docs`, `/context`, `/commit`, `/pr`.

Shared conventions in `~/.claude/skills/_shared/`:
- `return-envelope.md` — standard return format for all sub-agents
- `neurox-protocol.md` — memory protocol
- `skill-resolver.md` — skill injection protocol for the orchestrator

## Installer

Run `scripts/setup.sh --claude` to install/update all agents, skills, and templates.
The installer also writes a Neurox MCP entry to `~/.claude.json`.
