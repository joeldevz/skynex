<div align="center">

# Skills

**Dale a tu agente de IA un equipo de sub-agentes especializados y un flujo de trabajo profesional.**

Un solo instalador. Funciona con Claude Code y OpenCode.

[Quick Start](#quick-start) · [Como funciona](#como-funciona) · [Commands](#commands) · [Herramientas soportadas](#herramientas-soportadas) · [Modos de trabajo](#modos-de-trabajo) · [Instalacion](docs/installation.md) · [Docs](#documentacion)

</div>

---

## El Problema

Los asistentes de IA para codigo son potentes, pero fallan con features complejas:

- **Sobrecarga de contexto** — Conversaciones largas llevan a compresion, detalles perdidos, alucinaciones
- **Sin estructura** — "Implementa login con JWT" produce resultados impredecibles
- **Sin gate de revision** — El codigo se escribe antes de que alguien acuerde que construir
- **Sin memoria** — Las decisiones viven en el historial del chat que desaparece

## La Solucion

**Skills** es un workflow portable de planificacion y ejecucion donde un orquestador liviano delega todo el trabajo real a agentes especializados. Cada agente arranca con contexto fresco, ejecuta una tarea acotada, y devuelve un resultado estructurado.

```
TU: "Quiero agregar export CSV a la app"

ORQUESTADOR (delega, contexto minimo):
  → lanza PLANNER        → retorna: discovery + PLAN.md
  → te muestra el plan, vos apruevas
  → lanza CODER          → retorna: paso 1 implementado
  → te muestra el diff, vos revisas
  → lanza CODER          → retorna: paso 2 implementado
  → ...hasta completar el plan
  → /review              → quality gate final
  → /commit + /pr        → entrega limpia
```

**La clave**: el orquestador NUNCA hace trabajo real directamente. Delega a sub-agentes, trackea estado en `PLAN.md`, y sintetiza resumenes. Esto mantiene el hilo principal liviano y estable.

**Neurox** como sistema de memoria persistente entre sesiones — las decisiones, patrones y descubrimientos sobreviven entre conversaciones.

## Como funciona

Tres conceptos:

1. **Arquitectura delegate-first** — Tu agente principal se convierte en orquestador y delega todo a sub-agentes especializados. Cada uno recibe contexto fresco, hace trabajo acotado, y devuelve solo un resumen. [Ver agentes →](#agentes)

2. **Command-driven workflow** — Un flujo estructurado con comandos de discovery, validacion y entrega. Cada fase es un skill que cualquier agente puede correr. [Ver commands →](#commands)

3. **Memoria persistente** — Neurox guarda decisiones, bugs, patrones y preferencias. El orquestador los consulta automaticamente al empezar cada sesion. [Ver memoria →](#memoria-persistente)

## Quick Start

```bash
# Opcion 1: instalar todo lo compatible (interactivo)
git clone git@github.com:joeldevz/skills.git
cd skills
./clasing-skill

# Opcion 2: solo OpenCode (no interactivo)
./clasing-skill --non-interactive --package skills --target opencode --version skills=latest --trust-setup-scripts

# Opcion 3: solo Claude Code (no interactivo)
./clasing-skill --non-interactive --package skills --target claude --version skills=latest --trust-setup-scripts

# Opcion 4: instalar tambien neurox
./clasing-skill --non-interactive --package skills --package neurox --target both --version skills=latest --version neurox=latest --trust-setup-scripts
```

Eso es todo. El instalador detecta que herramientas tenes instaladas y las configura.

> El instalador interactivo usa menus navegables (flechas/espacio/enter). Si no hay TTY/curses, cae a un menu numerado.

En modo `--non-interactive`, **no** se muestra confirmacion final; si falta algun dato requerido, el comando falla con exit code `2`.

> **Requisito**: `neurox` debe estar instalado y disponible en `PATH` para memoria persistente.

El setup hace backup de tu configuracion existente antes de escribir.

> **Nota**: `./clasing-skill` es el instalador unificado. El script `./scripts/setup.sh` se usa internamente como instalador especifico del paquete `skills`.

Para instalacion manual, verificacion post-instalacion, y troubleshooting, ver [docs/installation.md](docs/installation.md).

## Herramientas soportadas

| Herramienta | Sub-agentes | Setup |
|-------------|-------------|-------|
| Claude Code | Full (Agent tool) | `./scripts/setup.sh --claude` |
| OpenCode | Full (delegate/task) | `./scripts/setup.sh --opencode` |

> **Full** = el orquestador delega a sub-agentes con contexto independiente.

## Agentes

| Agente | Rol | Que hace |
|--------|-----|----------|
| `planner` | Discovery y planificacion | Inicia memoria con Neurox, lee convenciones, explora el codebase, hace preguntas, genera `PLAN.md` |
| `manager` | Orquestacion y review | Lee `PLAN.md`, ejecuta un paso por vez, delega a `coder`, exige revision humana |
| `coder` | Implementacion acotada | Implementa una tarea, sigue patrones locales, consulta Context7 para docs, verifica antes de entregar |

### Estados de PLAN.md

| Estado | Significado |
|--------|-------------|
| `[ ]` | Pendiente |
| `[~]` | En progreso |
| `[!]` | Necesita fixes |
| `[x]` | Completado |

## Commands

> **Nota**: solo se listan los commands realmente disponibles en `opencode/commands/`. Las matrices anteriores prometían commands ficticios (doc rot eliminado en QW1).

### Onboarding y exploracion

| Command | Que hace |
|---------|----------|
| `/onboard` | Explora el proyecto: stack, arquitectura, convenciones |
| `/docs <lib> <tema>` | Busca docs en vivo via Context7 MCP |

### Calidad y verificacion

| Command | Que hace |
|---------|----------|
| `/verify-skill [scope]` | Valida skills, convenciones y cobertura con agentes en paralelo |
| `/verify-security [scope]` | Valida seguridad con dos jueces adversariales en paralelo |
| `/rollback [step]` | Deshace el ultimo paso (pide confirmacion) |

### Git

| Command | Que hace |
|---------|----------|
| `/commit` | Crea commit con Conventional Commits |
| `/pr` | Abre pull request con `gh` |

### Backlog (commands planeados, aún no implementados)

Los siguientes commands están en el roadmap (`docs/IMPROVEMENT-PLAN.md`) pero **no existen aún**: `/grill`, `/skills:scan`, `/afk-run`. Hasta que se implementen, los flujos equivalentes se hacen invocando skills directamente o via el orchestrator.

## Modos de trabajo

|  | Supervisado | Vibe Coding |
|---|---|---|
| **Agentes** | planner + manager + coder | 1 solo (`vibe`) |
| **PLAN.md** | Obligatorio | Opcional |
| **Review humano** | Despues de cada paso | No existe |
| **Commands** | 12 | 4 (`/do`, `/fix`, `/commit`, `/done`) |
| **Velocidad** | Controlada | Maxima |
| **Cuando usarlo** | Features grandes, decisiones de arquitectura, equipos | Exploraciones rapidas, bugfixes, features chicos |

> El modo vibe coding esta en `vibe-coding/`. Para usarlo: `./scripts/setup.sh --opencode` con la config de vibe.

## Flujo recomendado

```text
/verify-skill                   # validar skills y convenciones en paralelo
/verify-security                # validar seguridad en paralelo
/apply-feedback <correcciones>  # aplicar feedback si hay issues
/commit                         # commit con Conventional Commits
/pr                             # abrir pull request
/context                        # guardar aprendizajes en memoria
```

## Memoria persistente

**Neurox** es el sistema de memoria que conecta sesiones de trabajo:

- `session_start` — Inicia una sesion con titulo, directorio y branch
- `context` — Carga memorias relevantes al namespace actual
- `recall` — Busca decisiones, patrones o bugs previos
- `save` — Guarda descubrimientos con tags y archivos relacionados
- `session_end` — Cierra la sesion con un resumen

El setup configura Neurox automaticamente en ambas herramientas.

## Estructura del proyecto

```text
skills/
├── claude-code/
│   └── CLAUDE.md              # overlay para el orquestador en Claude Code
├── opencode/
│   ├── opencode.json          # configuracion base de agentes y MCPs
│   ├── commands/              # 12 slash commands
│   ├── skills/                # prd, nestjs-patterns, ts advanced types
│   ├── templates/             # convenciones, commits, 5 tipos de plan
│   ├── evals/                 # 9 golden tests de regresion
│   └── plugins/
├── vibe-coding/
│   ├── opencode.json          # config del modo autonomo
│   └── commands/              # 4 commands minimos
├── skills/
│   └── prd/                   # skill compartida de PRD
└── scripts/
    ├── setup.sh               # instalador principal
    └── install_claude_assets.py
```

## Que instala en cada herramienta

### Claude Code

- **3 agentes** en `~/.claude/agents`: `planner`, `manager`, `coder`
- **12 slash skills** en `~/.claude/skills` con los mismos nombres operativos
- **Overlay de `CLAUDE.md`** para mantener el mismo workflow
- **Neurox MCP** configurado en `~/.claude.json`

### OpenCode

- **3 agentes** con roles claros en `opencode.json`
- **12 commands** para todo el ciclo
- **Neurox + Context7 MCP** como sistemas externos
- **Templates** para convenciones, commits/PRs, y 5 tipos de plan
- **Skills** de PRD, TypeScript avanzado, y patrones NestJS DDD+CQRS
- **Eval framework** con 9 golden tests

## Eval Framework

9 golden tests en `evals/golden/` que validan el comportamiento de los agentes:

| Test | Agente | Valida |
|------|--------|--------|
| 01 | planner | Lee CONVENTIONS.md antes de preguntar |
| 02 | planner | Usa template PLAN-crud para tareas CRUD |
| 03 | manager | Lee PLAN.md antes de hacer nada |
| 04 | manager | Se detiene tras un paso y pide review |
| 05 | coder | Lee codigo existente antes de escribir |
| 06 | coder | Corre verificacion antes de reportar exito |
| 07 | manager | /review lee CONVENTIONS.md y git diff |
| 08 | coder | /test lee tests existentes antes de generar |
| 09 | manager | /rollback pide confirmacion antes de revertir |

```bash
./evals/run-evals.sh
./evals/run-evals.sh --agent coder
```

## Documentacion

| Tema | Descripcion |
|------|-------------|
| [Instalacion](docs/installation.md) | Guia completa: requisitos, setup automatico/manual, verificacion, troubleshooting |
| [OpenCode setup](opencode/README.md) | Configuracion detallada de OpenCode |
| [Claude Code setup](claude-code/CLAUDE.md) | Overlay y reglas para Claude Code |
| [Vibe Coding](vibe-coding/README.md) | Modo autonomo con un solo agente |

## Claude Code: nota importante

Claude Code no permite que un subagente lance otro subagente. Para mantener el mismo comportamiento:

- El hilo principal de Claude hace de orquestador
- `planner` y `coder` se usan como subagentes
- `manager` es agente de apoyo para scoping y review
- La orquestacion multi-agente se queda en el hilo principal

## Recomendacion

En cada proyecto nuevo, copia `opencode/templates/CONVENTIONS.md` a la raiz del repo y ajustalo al stack real. Eso hace que los agentes sean mucho mas consistentes.

## Licencia

MIT

---

<div align="center">
  <sub>Built by <a href="https://github.com/joeldevz">joeldevz</a></sub>
</div>
