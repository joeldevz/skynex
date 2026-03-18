---
description: Fetch live documentation for an external library using Context7
agent: ts-expert-coder
---

Fetch live, version-specific documentation for the library or topic: "{argument}"

Workflow:
1. Use Context7 MCP to search for documentation matching the query
2. Filter results to only the sections relevant to the query
3. Present a concise summary of the key API surface, patterns, and gotchas
4. Include code examples when available
5. Link to official documentation

Important:
- Use Context7 as the primary source — it has up-to-date docs
- If Context7 is unavailable or returns nothing, use webfetch to check official docs
- Do NOT fabricate API signatures — only report what you can verify from live sources
- Keep the output practical: focus on "how to use it" rather than exhaustive reference
- If the user specified a version, filter to that version

Context:
- Working directory: {workdir}
- Current project: {project}
- Query: {argument}

Examples of valid queries:
- `/docs prisma client api`
- `/docs drizzle postgres schema`
- `/docs nestjs guards`
- `/docs zod discriminated unions`
