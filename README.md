# Skills for OpenCode and Claude Code

Repositorio con un workflow compartido de skills, agentes y slash commands para OpenCode y Claude Code.

## Estructura

```text
opencode/
  opencode.json
  commands/         # 15 slash commands para OpenCode
  skills/           # skills compartidas: prd, nestjs-patterns, ts advanced
  templates/
  plugins/
  evals/

claude-code/
  CLAUDE.md         # overlay para el orquestador en Claude Code

scripts/
  setup.sh
  install_claude_assets.py
```

## Qué instala en cada herramienta

### OpenCode

- **3 agentes** con roles claros: planner, manager y coder
- **15 commands** para todo el ciclo: onboard, planificar, estimar, ejecutar, revisar, testear, commitear, abrir PRs, y guardar memoria
- **Plugin Engram** para memoria persistente entre sesiones
- **Context7 MCP** para documentacion en vivo de librerias externas
- **Templates** para convenciones, commits/PRs, y 5 tipos de plan (CRUD, bugfix, integration, refactor, feature)
- **Skills** de PRD, TypeScript avanzado, y patrones NestJS DDD+CQRS
- **Eval framework** con 9 golden tests de regresion para los 3 agentes

### Claude Code

- **3 agentes instalables** en `~/.claude/agents`: `planner`, `manager`, `coder`
- **15 slash skills** en `~/.claude/skills` con los mismos nombres operativos: `/plan`, `/execute`, `/review`, etc.
- **Overlay de `CLAUDE.md`** para mantener el mismo workflow de `PLAN.md`, step-by-step y human review loop
- **Compatibilidad con Claude subagents**: el hilo principal actua como orquestador y delega trabajo acotado a los agentes instalados

## Setup rapido

```bash
# Opcion 1: instalar todo lo compatible en la maquina
git clone git@github.com:joeldevz/skills.git
cd skills
./scripts/setup.sh --all

# Opcion 2: instalar solo OpenCode
./scripts/setup.sh --opencode

# Opcion 3: instalar solo Claude Code
./scripts/setup.sh --claude
```

El setup hace backup de la configuracion existente antes de escribir. En OpenCode tambien restaura tu API key de Context7 si ya la tenias.

## Flujo de trabajo completo

```text
/onboard                        # explorar el proyecto
/plan <feature>                 # generar PLAN.md
/estimate                       # estimar esfuerzo por paso
/execute                        # implementar el siguiente paso
/diff                           # ver los cambios con anotaciones
/test                           # generar/correr tests del paso
/review                         # quality gate antes de commit
/apply-feedback <correcciones>  # aplicar feedback
/commit                         # commit con Conventional Commits
/pr                             # abrir pull request
/context                        # guardar aprendizajes en memoria
```

En Claude Code esos comandos se instalan como skills slash en `~/.claude/skills/`.

## Commands disponibles

| Command | Descripcion |
|---------|-------------|
| `/onboard` | Explora el proyecto: stack, arquitectura, convenciones |
| `/plan <tarea>` | Investiga el codebase y genera PLAN.md |
| `/plan-rewrite` | Revisa y mejora un PLAN.md existente |
| `/estimate` | Estima esfuerzo (XS-XL) por paso del plan |
| `/execute` | Ejecuta el siguiente paso del plan |
| `/apply-feedback <texto>` | Aplica correcciones al paso actual |
| `/diff` | Muestra cambios del paso con anotaciones |
| `/test [modulo]` | Genera o corre tests del paso actual |
| `/review` | Quality gate: verifica convenciones, tipos, arch, tests |
| `/rollback [step]` | Deshace el ultimo paso (pide confirmacion) |
| `/status` | Muestra progreso del PLAN.md |
| `/context [obs]` | Guarda descubrimientos en memoria persistente |
| `/docs <lib> <tema>` | Busca docs en vivo via Context7 |
| `/commit` | Crea commit con Conventional Commits |
| `/pr` | Abre pull request con `gh` |

## Convenciones clave

- Value Objects y objetos de dominio en la capa de dominio — nunca primitivos
- DDD + CQRS: commands para escritura, queries para lectura
- Controllers solo inyectan CommandBus/QueryBus
- DTOs en la frontera HTTP con Swagger + class-validator
- Review humano obligatorio entre pasos de ejecucion
- Commits con Conventional Commits

## Claude Code: nota importante

Claude Code no permite que un subagente lance otro subagente. Para mantener el mismo comportamiento general:

- el hilo principal de Claude hace de orquestador
- `planner` se usa para discovery y planes
- `coder` se usa para implementacion acotada
- `manager` se instala como agente de apoyo para scoping y review, pero la orquestacion multi-agente se queda en el hilo principal

Eso mantiene el mismo flujo practico: `PLAN.md` como fuente de verdad, un paso por vez, y review humana obligatoria.

## Recomendacion

En cada proyecto nuevo, copia `opencode/templates/CONVENTIONS.md` a la raiz del repo y ajustalo al stack real del proyecto. Eso hace que los agentes sean mucho mas consistentes para todo el equipo.
