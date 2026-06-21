# Review Rules
# Enforced by /review-pr as findings. Edit freely.
# /review-pr suggests new rules when it detects repeated patterns — paste them here to lock them in.

## General
- No secrets, credentials, or API keys committed to source.

## Code quality
- Wrap errors with context: fmt.Errorf("doing X: %w", err).
- No panic in library or service code.
- No stray `fmt.Print*`/`println` console output in service code (`internal/`) — route user-facing output through the CLI/TUI layer, debug through the project logger.
- Input validation must happen at the system boundary, not deep in business logic.
- Function names must read as intent: descriptive verbs (`syncAssets`, `verifyChecksum`), not vague `do`/`handle`/`process` or single letters.

## Tests
- Behavior changes must ship at least one test covering the new path.
- Test names describe intent: "should <behavior> when <condition>".
- No mocks that prevent tests from exercising any real logic.

## PRs
- PR description must state what changed and why — not just a ticket number.
- Keep PRs under 600 lines changed; split larger changes into chained PRs.

## Agents & Skills
- `skill_resolution` in return envelopes must use `ok | fallback-registry | none` — never `injected`.
- File references in skill or command markdown must point to files that actually exist in the repo.
- Numeric thresholds in SKILL.md (line budgets, PR size limits) must align with `.skynex/project-config.yaml` when that file is present.
