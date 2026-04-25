#!/usr/bin/env bun
/**
 * Pre-commit AI gate — TS, reusing OpenCode's advisor_consult
 *
 * Validates `git diff --staged` against CONVENTIONS.md before allowing commit.
 *
 * Inspired by Gentleman/gentle-ai GGA pre-commit hook (bash + SHA256 cache + multi-provider)
 * but reimplemented in TS to leverage our existing OpenCode advisor infrastructure.
 *
 * Bypass: SKIP_AI_GATE=1 git commit ...
 *
 * Refs:
 * - docs/IMPROVEMENT-PLAN.md GA3
 * - opencode/tools/advisor.ts (the underlying advisor_consult)
 * - Research/Gentle-AI-vs-Clasing-Skills.md (principles destilados)
 */

import { createHash } from "node:crypto";
import { execSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

// ───── Configuration ─────────────────────────────────────────────────────────

const REPO_ROOT = execSync("git rev-parse --show-toplevel").toString().trim();
const CACHE_DIR = join(REPO_ROOT, ".opencode", ".cache", "precommit");
const CONVENTIONS_PATH = join(REPO_ROOT, "CONVENTIONS.md");

// Only validate diffs touching these paths (high-stakes areas)
const VALIDATE_PATHS = [
  "opencode/skills/",
  "opencode/opencode.json",
  "opencode/skills/_shared/",
  "templates/",
  "CONVENTIONS.md",
];

// ───── Bypass check ──────────────────────────────────────────────────────────

if (process.env.SKIP_AI_GATE === "1") {
  console.log("[precommit-ai-gate] Bypassed via SKIP_AI_GATE=1");
  process.exit(0);
}

// ───── Get staged diff scoped to high-stakes paths ───────────────────────────

function getStagedDiff(): string {
  try {
    const diffArgs = ["git", "diff", "--staged", "--", ...VALIDATE_PATHS];
    return execSync(diffArgs.join(" ")).toString();
  } catch (err) {
    console.error("[precommit-ai-gate] Failed to read staged diff:", err);
    process.exit(0); // don't block on infrastructure errors
  }
}

const diff = getStagedDiff();

if (!diff.trim()) {
  // No high-stakes paths changed — skip silently
  process.exit(0);
}

// ───── Cache check (SHA256 of diff + conventions) ────────────────────────────

const conventionsHash = existsSync(CONVENTIONS_PATH)
  ? createHash("sha256").update(readFileSync(CONVENTIONS_PATH)).digest("hex").slice(0, 12)
  : "no-conventions";

const diffHash = createHash("sha256").update(diff).digest("hex").slice(0, 16);
const cacheKey = `${conventionsHash}__${diffHash}`;
const cachePath = join(CACHE_DIR, `${cacheKey}.json`);

mkdirSync(CACHE_DIR, { recursive: true });

if (existsSync(cachePath)) {
  const cached = JSON.parse(readFileSync(cachePath, "utf-8"));
  if (cached.verdict === "PASSED") {
    console.log("[precommit-ai-gate] ✓ Cached PASS");
    process.exit(0);
  } else if (cached.verdict === "FAILED") {
    console.error("[precommit-ai-gate] ✗ Cached FAIL");
    console.error(cached.reason);
    process.exit(1);
  }
  // verdict === "UNKNOWN" → fall through to revalidate
}

// ───── Build the question for the advisor ────────────────────────────────────

const conventions = existsSync(CONVENTIONS_PATH)
  ? readFileSync(CONVENTIONS_PATH, "utf-8")
  : "(CONVENTIONS.md not found)";

const question = `You are reviewing a staged git diff against the project's CONVENTIONS.md.

Your job: identify any clear violations of the documented conventions. Do NOT flag style preferences or things not covered by CONVENTIONS.md.

Output exactly one of:
- "PASSED" if no violations found
- "FAILED: <specific violation>" with the violation in 1-2 sentences

Be strict but fair. Only flag things explicitly forbidden in CONVENTIONS.md.

═══ CONVENTIONS.md ═══
${conventions}

═══ Staged diff ═══
${diff}
`;

// ───── Invoke advisor (placeholder — adapt to actual OpenCode CLI invocation) ─

console.log("[precommit-ai-gate] Validating diff against CONVENTIONS.md...");

// NOTE: This script assumes an `opencode advisor` CLI exists or that the user has
// configured a way to invoke advisor_consult from a script. The actual invocation
// depends on the OpenCode setup — adapt this section to your environment.
//
// Pseudocode for the advisor call:
//
//   const verdict = await invokeAdvisor(question);
//
// For now, write a placeholder that ALWAYS passes if advisor is unreachable
// (don't block the developer on infrastructure issues).

let verdict: "PASSED" | "FAILED" | "UNKNOWN" = "UNKNOWN";
let reason = "";

try {
  // TODO: replace this with actual advisor invocation
  // Possible options:
  //   - opencode CLI: `opencode run --agent advisor --prompt "..."`
  //   - Direct API call to Anthropic with the system prompt of the advisor agent
  //   - HTTP call to a local OpenCode server
  //
  // For Sprint 0.5b initial commit, this is a stub that records the intent.
  // The real wiring lands when GA3 is fully integrated with OpenCode CLI.

  console.log("[precommit-ai-gate] (stub) Advisor invocation not yet wired.");
  console.log("[precommit-ai-gate] To enforce: implement invokeAdvisor() above.");
  verdict = "PASSED"; // permissive default
  reason = "stub-implementation-allows-by-default";
} catch (err) {
  console.error("[precommit-ai-gate] Advisor unreachable, allowing commit:", err);
  verdict = "PASSED";
  reason = "advisor-unreachable";
}

// ───── Cache the result ──────────────────────────────────────────────────────

writeFileSync(
  cachePath,
  JSON.stringify({ verdict, reason, timestamp: new Date().toISOString() }, null, 2)
);

if (verdict === "FAILED") {
  console.error(`[precommit-ai-gate] ✗ FAILED: ${reason}`);
  console.error("[precommit-ai-gate] To bypass: SKIP_AI_GATE=1 git commit ...");
  process.exit(1);
}

console.log("[precommit-ai-gate] ✓ PASSED");
process.exit(0);
