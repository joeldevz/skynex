# Preserved repository-only configuration

These files were reversibly moved out of active OpenCode discovery while
synchronizing the installed configuration. They are not installed or embedded
by the existing asset generator, which copies `opencode`, `claude-code` and
`skills`, not `docs`.

- `agents/`: repository-only workflow agent definitions.
- `plugins/neurox.ts`: repository-only auto-loaded plugin.
- `bun.lock`: previous repository lock, not compatible with the installed
  package manifest adopted by this sync.

The archived file contents are unchanged. Do not restore them into active
directories implicitly; doing so changes behavior relative to the installed
snapshot. See `opencode/INSTALLED-CONFIG.md` for portability and runtime limits.
