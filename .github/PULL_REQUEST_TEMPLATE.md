# Pull Request

## Summary

<!-- ES o EN: 1-3 frases sobre qué resuelve este PR -->

## Linked issue

<!-- Required: this PR must close an approved issue -->
Closes #

## Type

<!-- Mark only ONE -->
- [ ] `type:skill`
- [ ] `type:agent`
- [ ] `type:plugin`
- [ ] `type:command`
- [ ] `type:doc`
- [ ] `type:meta`

## Changes

<!-- Bullet list of concrete changes -->
-
-

## Verification

<!-- Required by verification-before-completion skill — provide evidence -->

- [ ] Tests pass (output captured below)
- [ ] Types clean (`tsc --noEmit` if applicable)
- [ ] Lint clean
- [ ] Manual smoke test described
- [ ] No banned patterns introduced (assertion tautologies, ghost loops, mock>6)

```
<!-- Paste test runner output / type check output / lint output here -->
```

## Skill design compliance (if PR touches `opencode/skills/*`)

- [ ] Description Trap respected (`description: Use when X` only, no workflow summary)
- [ ] SKILL.md ≤120 lines
- [ ] References modules ≤200 lines each
- [ ] No code copied from other projects — only principios destilados

## Smart-zone awareness

- [ ] No prompts >100K tokens injected
- [ ] CLAUDE.md / system prompts haven't grown excessively

## Cultural rules

- [ ] No banned phrases ("You're absolutely right!", "Great question!", etc.)
- [ ] User addressed as "your human partner" where applicable
- [ ] No marketing language

## Doc rot prevention

- [ ] Updated README/SPEC/PLAN if file structure changed
- [ ] No promises in docs that don't correspond to real files
- [ ] `grep -r` clean for any deleted symbols

## Risks / open questions

<!-- Honest list of risks, edge cases, things you're unsure about -->
-

## Refs

<!-- Link to docs/IMPROVEMENT-PLAN.md sections, vault notes, mem IDs -->
- Plan ref:
- Vault ref:
- Memory ref:
