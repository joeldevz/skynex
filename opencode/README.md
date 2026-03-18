# OpenCode Team Setup

Configuracion de OpenCode para trabajo en equipo con un flujo simple y controlado:

1. descubrir bien la tarea
2. generar `PLAN.md`
3. ejecutar un paso por vez
4. pedir revision humana
5. corregir o avanzar

## Contenido

```text
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

## Agentes

### `step-builder-agent`

- descubre contexto del proyecto
- hace preguntas de negocio y tecnicas en bloques
- recomienda defaults razonables
- genera `PLAN.md`

### `execution-orchestrator`

- lee `PLAN.md`
- ejecuta un solo paso por vez
- delega implementacion a `ts-expert-coder`
- actualiza estados del plan
- obliga a revision humana antes de continuar

Estados de `PLAN.md`:
- `[ ] pending`
- `[~] in progress`
- `[!] needs fixes`
- `[x] done`

### `ts-expert-coder`

- implementa una tarea acotada
- sigue patrones locales del repo
- trabaja principalmente en TypeScript, Node.js y NestJS
- corre verificaciones antes de devolver exito

## Commands

### Planificacion

- `/onboard`
  - explora un proyecto antes de trabajar
  - resume stack, arquitectura, comandos y convenciones
- `/plan <tarea>`
  - investiga el codebase
  - pregunta lo necesario
  - crea o reemplaza `PLAN.md`
- `/plan-rewrite`
  - revisa y mejora `PLAN.md`
  - rellena huecos y ajusta pasos

### Ejecucion

- `/execute`
  - toma el siguiente paso pendiente o con fixes
  - lo delega a `ts-expert-coder`
  - presenta cambios y pide review humana
- `/apply-feedback <cambios>`
  - toma feedback humano
  - vuelve a delegar correcciones
- `/status`
  - muestra completados, paso actual y siguientes pasos

### Git

- `/commit`
  - crea un commit local con Conventional Commits
- `/pr`
  - crea un pull request con `gh`
  - resume todos los cambios de la rama

## Flujo recomendado

```text
/onboard
/plan implementar login con JWT
/execute
/apply-feedback separar DTOs y agregar tests
/execute
/status
/commit
/pr
```

## Setup para cada miembro del equipo

1. Copiar el contenido de `opencode/` a `~/.config/opencode/`
2. Ejecutar `bun install` dentro de `~/.config/opencode/`
3. Tener instalado el binario `engram` si quieres memoria persistente
4. Tener `gh` autenticado si quieres usar `/pr`

## Configuracion local opcional

### Context7

Por seguridad, `context7` queda deshabilitado por defecto en `opencode.json`.

Para activarlo, cada persona debe editar localmente `~/.config/opencode/opencode.json` y poner su API key real:

```json
"context7": {
  "type": "remote",
  "url": "https://mcp.context7.com/mcp",
  "headers": {
    "CONTEXT7_API_KEY": "TU_API_KEY"
  },
  "enabled": true
}
```

No subir esa key al repositorio.

### Engram

`engram` ya esta habilitado en la configuracion. Si el binario no existe, el plugin no rompe el flujo: simplemente no habra memoria persistente.

## Templates

### `templates/CONVENTIONS.md`

Template de convenciones para copiar a cada proyecto. Esta basado en el backend real explorado y define:
- DDD + CQRS + capas
- uso obligatorio de Value Objects en lugar de primitivos en dominio
- naming, imports, controllers, DTOs, repositorios y errores
- como se escriben tests unitarios y E2E
- stack esperado: NestJS, Fastify, Prisma, SWC, Jest

### `templates/PLAN-crud.md`

Referencia para CRUDs completos.

### `templates/PLAN-bugfix.md`

Referencia para fixes con enfoque RED -> GREEN -> REFACTOR.

### `templates/PLAN-integration.md`

Referencia para integraciones con servicios externos.

### `templates/PLAN-refactor.md`

Referencia para refactors con red de seguridad de tests.

### `templates/COMMIT-CONVENTIONS.md`

Reglas de Conventional Commits y estructura de PR.

## Skills incluidas

- `prd`
- `typescript-advanced-types`

No hay familia `sdd-*` ni `find-skills`.

## Regla mas importante

En dominio, usar siempre objetos de dominio y Value Objects, no primitivos.

Ejemplos:
- `Money` en lugar de `number` para dinero
- `Uuid` en lugar de `string` para ids
- `Email` en lugar de `string` para correos
- `DateRange` en lugar de dos `Date` sueltas

DTOs si pueden usar primitivos porque son la frontera de serializacion.

## Que tocar cuando quieras ajustar algo

- `opencode.json` -> comportamiento base de agentes y MCPs
- `commands/*.md` -> comportamiento puntual de cada slash command
- `templates/*.md` -> referencia de convenciones, planes, commits y PRs

## Nota practica

Este repo esta pensado para ser portable. Por eso:
- incluye `package.json` para poder correr `bun install`
- incluye el skill `typescript-advanced-types` como archivo real, no como symlink local
- no incluye secretos en la configuracion compartida
