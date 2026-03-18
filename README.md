# Skills & OpenCode Config

Repositorio con una configuracion de OpenCode lista para compartir en equipo.

## Estructura

```text
skills/
  prd/

opencode/
  opencode.json
  package.json
  .gitignore
  tui.json
  README.md
  commands/
  plugins/
  skills/
  templates/
```

## Qué contiene `opencode/`

- 3 agentes con roles claros: planner, orchestrator y coder
- 8 commands para onboard, planificar, ejecutar, corregir, revisar estado, commitear y abrir PRs
- plugin de memoria persistente con Engram
- templates para convenciones, commits/PRs y planes por tipo de tarea
- skills compartidas para PRDs y tipos avanzados de TypeScript

## Setup rapido

1. Clona este repositorio
2. Copia `opencode/` a `~/.config/opencode/`
3. Ejecuta `bun install` dentro de `~/.config/opencode/`
4. Lee `~/.config/opencode/README.md`
5. Si quieres Context7, configura tu API key localmente en `opencode.json`

## Flujo de trabajo

```text
/onboard
/plan implementar feature X
/execute
/apply-feedback cambiar Y
/status
/commit
/pr
```

## Convenciones clave

- usar Value Objects y objetos de dominio, no primitivos, dentro del dominio
- seguir DDD + CQRS
- commands por repositorio, queries pueden usar Prisma directo
- DTOs con Swagger + class-validator
- review humano obligatorio entre pasos
- commits con Conventional Commits

## Recomendacion

En cada proyecto nuevo, copia `opencode/templates/CONVENTIONS.md` a la raiz del repo y ajustalo al stack real del proyecto. Eso hace que la IA sea mucho mas consistente para todo el equipo.
