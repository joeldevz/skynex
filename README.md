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
  commands/         # 15 slash commands
  evals/            # 9 golden tests para validar comportamiento de agentes
  plugins/
  skills/           # typescript-advanced-types, nestjs-patterns, prd
  templates/        # CONVENTIONS.md, COMMIT-CONVENTIONS.md, 5 PLAN-*.md
```

## Qué contiene `opencode/`

- **3 agentes** con roles claros: planner, orchestrator y coder
- **15 commands** para todo el ciclo: onboard, planificar, estimar, ejecutar, revisar, testear, commitear, abrir PRs, y guardar memoria
- **Plugin Engram** para memoria persistente entre sesiones
- **Context7 MCP** para documentacion en vivo de librerias externas
- **Templates** para convenciones, commits/PRs, y 5 tipos de plan (CRUD, bugfix, integration, refactor, feature)
- **Skills** de PRD, TypeScript avanzado, y patrones NestJS DDD+CQRS
- **Eval framework** con 9 golden tests de regresion para los 3 agentes

## Setup rapido

```bash
# Opcion 1: script automatico (recomendado)
git clone git@github.com:joeldevz/skills.git
cd skills
./setup-opencode.sh

# Opcion 2: manual
cp -r opencode/ ~/.config/opencode/
cd ~/.config/opencode && bun install
```

El script hace backup de tu config anterior, restaura tu API key de Context7 si ya la tenias, e instala las dependencias.

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

## Recomendacion

En cada proyecto nuevo, copia `opencode/templates/CONVENTIONS.md` a la raiz del repo y ajustalo al stack real del proyecto. Eso hace que los agentes sean mucho mas consistentes para todo el equipo.
