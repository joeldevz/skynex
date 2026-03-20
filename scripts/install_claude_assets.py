#!/usr/bin/env python3

from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPENCODE_CONFIG = ROOT / "opencode" / "opencode.json"
OPENCODE_SKILLS = ROOT / "opencode" / "skills"
OPENCODE_COMMANDS = ROOT / "opencode" / "commands"
OPENCODE_TEMPLATES = ROOT / "opencode" / "templates"
CLAUDE_OVERLAY = ROOT / "claude-code" / "CLAUDE.md"


TOOLS = "Read, Write, Edit, Glob, Grep, Bash"


MANAGER_PROMPT = """EXECUTION ORCHESTRATOR (CLAUDE MAIN-THREAD COMPANION)
=====================================================

You are the implementation manager for PLAN-driven work inside Claude Code.

PRIMARY OBJECTIVE:
Keep `PLAN.md` as the source of truth, advance one approved step at a time, and prepare bounded implementation handoffs for the `coder` agent.

IMPORTANT CLAUDE CODE CONSTRAINT:
- Claude subagents cannot spawn other subagents.
- Because of that, when you are invoked as a subagent you do NOT attempt to delegate work yourself.
- Instead, you select the correct step, build the exact coder handoff, and return the orchestration summary that the main Claude conversation should use.

CORE RULES:
1. Read `PLAN.md` first on every run.
2. Work one step at a time. Prefer `[!] needs fixes` before `[ ] pending`.
3. Do not implement application code.
4. Keep the human review loop mandatory after each implementation pass.
5. Keep plan state explicit and recommend the next status update.

STATUS MODEL:
- `[ ] pending`
- `[~] in progress`
- `[!] needs fixes`
- `[x] done`

WHEN INVOKED:
1. Read `PLAN.md` and identify the next step to execute or review.
2. Read any obviously relevant files or conventions needed to scope that step safely.
3. Produce a bounded handoff for `coder` with:
   - step title
   - what/why/where/acceptance
   - relevant previous-step context
   - verification expectations
   - instruction to read local patterns first
4. If implementation already happened, evaluate the results and recommend whether the step should stay `[~] in progress`, move to `[!] needs fixes`, or become ready for human approval.
5. Return a concise orchestration note for the human.

RETURN FORMAT:
- Selected step
- Recommended PLAN.md status change
- Coder handoff prompt
- Human review handoff
- Risks or open questions

DO NOT:
- write application code
- silently advance multiple steps
- mark a step done without explicit human approval
"""


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text

    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text

    raw = text[4:end].splitlines()
    body = text[end + 5 :]
    data: dict[str, str] = {}
    for line in raw:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data, body.lstrip()


def dump_yaml_list(items: list[str], indent: int = 0) -> str:
    prefix = " " * indent
    return "\n".join(f"{prefix}- {item}" for item in items)


def normalize_command_body(body: str) -> str:
    replacements = {
        '"{argument}"': '"$ARGUMENTS"',
        "{argument}": "$ARGUMENTS",
        "{workdir}": "the current working directory",
        "{project}": "the current project",
        "Engram memory (`mem_search`)": "Claude project memory and existing notes",
        "Engram persistent memory": "Claude project memory",
        "Engram": "Claude memory",
        "`mem_search`": "Claude memory files",
        "~/.config/opencode/templates/": "~/.claude/templates/",
        "Use `topic_key` for evolving topics so they update instead of duplicating": "Prefer updating an existing memory note when the topic already exists",
    }
    for old, new in replacements.items():
        body = body.replace(old, new)
    return body.rstrip() + "\n"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def render_agents(target: Path) -> None:
    config = json.loads(OPENCODE_CONFIG.read_text(encoding="utf-8"))
    agents = config["agent"]

    skill_map = {
        "planner": ["prd"],
        "manager": [],
        "coder": ["nestjs-patterns", "typescript-advanced-types"],
    }

    for name in ("planner", "manager", "coder"):
        agent = agents[name]
        prompt = MANAGER_PROMPT if name == "manager" else agent["prompt"]
        description = agent["description"]
        skills = skill_map[name]

        frontmatter = [
            "---",
            f"name: {name}",
            f"description: {description}",
            f"tools: {TOOLS}",
            "model: inherit",
            "memory: local",
        ]

        if skills:
            frontmatter.append("skills:")
            frontmatter.append(dump_yaml_list(skills, indent=2))

        frontmatter.append("---")
        content = "\n".join(frontmatter) + "\n\n" + prompt.strip() + "\n"
        write_text(target / "agents" / f"{name}.md", content)


def render_shared_skills(target: Path) -> None:
    for skill_dir in OPENCODE_SKILLS.iterdir():
        if not skill_dir.is_dir():
            continue
        destination = target / "skills" / skill_dir.name
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(skill_dir, destination)


def render_templates(target: Path) -> None:
    destination = target / "templates"
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(OPENCODE_TEMPLATES, destination)


def command_intro(command_name: str, agent_name: str) -> str:
    if agent_name == "planner":
        return (
            f"Use the `planner` subagent for `/{command_name}` unless the task is too small to justify delegation.\n"
            "Keep the final answer concise and action-oriented.\n"
        )
    if agent_name == "coder":
        return (
            f"Use the `coder` subagent for `/{command_name}` whenever code or tests must be written or updated.\n"
            "Keep the work bounded to the requested scope.\n"
        )
    return (
        f"Run `/{command_name}` from the main Claude conversation following the `manager` workflow.\n"
        "Important: Claude subagents cannot spawn other subagents, so keep orchestration in the main thread and delegate any bounded code changes directly to `coder`.\n"
        "Use the installed `manager` agent as a review or scoping helper when useful, but do not rely on it to launch `coder`.\n"
    )


def render_command_skills(target: Path) -> None:
    for command_file in sorted(OPENCODE_COMMANDS.glob("*.md")):
        metadata, body = parse_frontmatter(command_file.read_text(encoding="utf-8"))
        name = command_file.stem
        description = metadata.get("description", f"Run /{name}")
        description = description.replace(
            "Engram persistent memory", "Claude project memory"
        )
        agent_name = metadata.get("agent", "manager")
        transformed = normalize_command_body(body)

        frontmatter = [
            "---",
            f"name: {name}",
            f"description: {description}",
            "disable-model-invocation: true",
            "---",
        ]

        content = "\n".join(frontmatter)
        content += "\n\n"
        content += command_intro(name, agent_name)
        content += "\n"
        content += transformed
        write_text(target / "skills" / name / "SKILL.md", content)


def main() -> None:
    target = Path.home() / ".claude"
    target.mkdir(parents=True, exist_ok=True)
    render_agents(target)
    render_shared_skills(target)
    render_templates(target)
    render_command_skills(target)
    print(f"Rendered Claude assets in {target}")
    print(f"Overlay file available at {CLAUDE_OVERLAY}")


if __name__ == "__main__":
    main()
