# Skills Repo — Improvement Plan

> **Status**: Active · **Owner**: Christopher · **Created**: 2026-04-25 · **Updated**: 2026-04-25 (added Sprint 0.5)
> **Source**: Análisis comparativo vs Matt Pocock + comunidad 2026 + Superpowers (obra)
> **Vault refs**: `Research/Skills-Repo-Improvement-Plan-v2.md`, `Research/Skills-Repo-vs-Matt-Pocock.md`, `Research/Superpowers-vs-Clasing-Skills.md`
> **Memory refs**: `mem_modkhttv_at7mz4`, `mem_modjtroj_6obphg`, `mem_modb71hc_96q5sf`, `mem_modl8u3x_8bk8rb`

---

## TL;DR

El repo coordina muy bien (orchestrator + advisor + dual-judge + return-envelope + Neurox) pero opera muy poco. Faltan: grill-me, TDD Iron Law, vertical slices, AFK loops, deep modules, cross-provider review, disciplina psicológica adversarial.

**Plan ejecutivo**: 5 quick wins (~2h) + Sprint 0.5 Inspiration Lift (~19h, patrones de obra/superpowers) + 3 sprints de 2 semanas. Dirección: simplificar (eliminar SKILLs grandes), añadir fundamentos operacionales con disciplina adversarial, escalar después.

---

## Compromisos invariantes (norte arquitectónico)

1. **Smart-zone hard cap 100K tokens** → reset automático
2. **SKILL.md ≤120 líneas** + `references/*.md` (≤200 c/u) — progressive disclosure obligatorio
3. **HITL default; AFK opt-in** explícito por slice tag
4. **TDD Iron Law** solo cuando `slice.tdd=true` (no fricciona bugfixes triviales)
5. **Return envelope** con `slice_id` + `mode: hitl|afk` en todos los agentes
6. **Doc rot prohibido** — toda promesa en README/SPEC/PLAN debe corresponder a archivos reales
7. **Description Trap rule** (Superpowers) — descripción de skill = SOLO "Use when X", NUNCA resume el workflow
8. **Disciplina cultural** — ban a "You're absolutely right!" / agradecimientos performativos; usar "your human partner"

---

## Fase 0 — Quick Wins (HOY, ~2h)

### QW1 · Limpiar README de commands ficticios
- **Archivo**: `README.md` líneas 117-150 (matriz de commands)
- **Acción**: Borrar 10 commands inexistentes: `/plan`, `/execute`, `/apply-feedback`, `/diff`, `/status`, `/test`, `/review`, `/estimate`, `/context`, `/plan-rewrite`
- **Mantener**: commit, docs, onboard, pr, rollback, verify-security, verify-skill (los 7 reales en `opencode/commands/`)
- **Esfuerzo**: 15 min · **Impact**: alto (credibilidad documental)

### QW2 · Crear skill `grill-me` (Matt Pocock + Superpowers Description Trap)
- **Archivo**: `opencode/skills/grill-me/SKILL.md` (NUEVO)
- **Estilo**: Matt Pocock (3-5 oraciones) + Description Trap rule de obra
- **Trigger**: features no triviales antes del PRD
- **Esfuerzo**: 30 min · **Impact**: alto (alineación inicial)

```markdown
---
description: Use when the user requests a non-trivial feature, change, or design decision before writing a PRD or plan. Do NOT use for trivial bug fixes or typos.
---

Interview your human partner relentlessly to reach a shared design concept (Brooks).
Walk down each branch of the design tree, resolving dependencies one by one.
For each question, provide your recommended answer and let the user agree or correct.
Ask questions ONE AT A TIME. Skip questions where Neurox or context already provides clear answers.
Stop when the design tree is fully resolved or the user says "just do it".
Output: design-tree.md with decisions and open assumptions, ready to feed PRD.
```

> **Description Trap aplicada**: la descripción dice solo CUÁNDO usar la skill, no resume el workflow. Esto mejora el matching del agente.

### QW3 · TDD Iron Law en coder (texto Superpowers + anti-rationalization)
- **Archivo**: `opencode/opencode.json` agente `coder`, campo `prompt` (líneas 36-52)
- **Acción**: Añadir bloque al final del system prompt con tabla anti-rationalization
- **Esfuerzo**: 15 min · **Impact**: crítico (anti-cheating tests)

```
═══════════════════════════════════════════════════════════════
🔒 TDD IRON LAW (when task includes tests OR slice.tdd=true)
═══════════════════════════════════════════════════════════════

1. NEVER modify a test to make it pass — fix the implementation instead.
2. If the task requires a new test, WRITE THE TEST FIRST (red phase).
3. Confirm the test fails for the EXPECTED REASON before implementing.
4. Implement minimal code to pass (green phase).
5. Refactor only after green.
6. If a pre-existing test fails after your change, the implementation is wrong.
7. If no failing test exists and task requires one → status: blocked.

ANTI-RATIONALIZATION TABLE (reject these excuses immediately):

| Excuse                                          | Reality                                           |
|-------------------------------------------------|---------------------------------------------------|
| "The test was wrong"                            | Fix the spec, then the test, then the impl.      |
| "It's just a small adjustment to the assert"    | That IS modifying the test. Stop.                |
| "The implementation is correct, test is flaky"  | Prove it: run 10x. If flaky, fix the test setup, not the assertion. |
| "Adding `.skip()` temporarily"                  | Never skip. Block and report.                    |
| "Updating snapshot to match new output"         | Only if the spec changed. Otherwise the impl is wrong. |

EXCEPTION: trivial bugfixes or non-code tasks (docs, configs) are exempt.
EXCEPTION: legitimate spec changes require explicit user approval BEFORE touching the test.
```

> **Inspirado en obra/superpowers** (verification-before-completion + anti-rationalization patterns).

### QW4 · Smart-zone budget shared
- **Archivo**: `opencode/skills/_shared/smart-zone-budget.md` (NUEVO)
- **Esfuerzo**: 20 min · **Impact**: alto (auto-prevención dumb zone)

```markdown
# Smart Zone Budget Protocol

Toda sesión de agente sigue estas reglas de presupuesto de contexto.

## Hard cap: 100K tokens
Por encima de 100K → el modelo empieza a degradar (context rot, Chroma 2025).

- Al llegar a **80K** (warning): planear punto de corte limpio.
- Al llegar a **100K** (alerta): el agente DEBE elegir una de estas 3 opciones:
  1. `/clear` — preferido si la tarea actual está completa
  2. Surgical compaction — Esc Esc + "summarize from here" (preserva decisiones, descarta exploración)
  3. Cerrar sesión y devolver return envelope al orchestrator

## Cuándo elegir cada estrategia
| Situación | Estrategia |
|---|---|
| Tarea terminada | `/clear` (Memento style) |
| Tarea viva pero context lleno de exploración inútil | Surgical compaction |
| Tarea bloqueada | Return envelope + `/clear` desde el orchestrator |

## Anti-patrones
- ❌ `/compact` full sin filtrar → deja sedimento que corrompe loops futuros
- ❌ Ignorar el cap y seguir → cheating tests, decisiones tontas, recall fallido
- ❌ Empezar tarea nueva sin `/clear` → mezcla contextos
```

### QW5 · Plugin advisor.ts + línea muerta README
- **Archivo 1**: mover `opencode/tools/advisor.ts` → `opencode/plugins/advisor.ts` (alineación con docs)
- **Archivo 2**: actualizar referencias en `opencode.json` y `package.json` si las hay
- **Archivo 3**: borrar línea 218 README ("No hay familia sdd-* ni find-skills")
- **Esfuerzo**: 10 min · **Impact**: medio (consistencia)

> **Nota commit reciente** (`23a7cb7 fix: move advisor from plugins/ to tools/`): el cambio fue al revés. Conviene confirmar con el usuario si revertir o mantener `tools/` y actualizar PLAN.md.

### QW6 · Skill `verification-before-completion` (Superpowers, comprimido)
- **Archivo**: `opencode/skills/verification-before-completion/SKILL.md` (NUEVO)
- **Estilo**: Description Trap + ≤120 líneas
- **Trigger**: antes de devolver `status: success` cualquier sub-agente
- **Esfuerzo**: 1h · **Impact**: crítico (anti-"Done!" sin evidencia)

```markdown
---
description: Use before any sub-agent returns status:success or claims a task complete. Forces evidence-based verification of acceptance criteria.
---

Before claiming task complete, you MUST provide concrete evidence:

| Claim                  | Required evidence                                       |
|------------------------|---------------------------------------------------------|
| "Code compiles"        | Output of build command (last 20 lines)                |
| "Tests pass"           | Test runner output with green count                    |
| "Feature works"        | Manual verification step OR e2e test name              |
| "Bug fixed"            | Reproduction case before/after                         |
| "Refactor safe"        | Tests still pass + no behavior change cited            |

If evidence cannot be provided → status: blocked with reason.
NEVER claim completion based on file edits alone.
NEVER use "should work" / "looks good" / "I believe" — provide evidence or block.

ANTI-RATIONALIZATION:
| Excuse                              | Reality                            |
|-------------------------------------|------------------------------------|
| "It's a simple change, no need to test" | Run the test anyway. 10 seconds. |
| "Tests aren't set up for this area" | status:blocked + report missing setup |
| "I'll verify in the next iteration" | No. Verify now or block.          |
```

---

## Fase 1 — Simplificación (ANTES de Sprint 1, ~30 min)

### S1 · Eliminar 3 SKILLs grandes (decisión confirmada)
**Total a eliminar: 1987 líneas** (724 + 656 + 607)

| Skill | Líneas | Acción |
|---|---|---|
| `opencode/skills/typescript-advanced-types/` | 724 | **DELETE** carpeta completa |
| `opencode/skills/nestjs-patterns/` | 607 | **DELETE** carpeta completa |
| `skills/clasing-ui-v2-beta/` | 656 | **DELETE** carpeta completa |

**Razón**: simplificar. Los modelos modernos ya conocen TS/NestJS suficientemente; estos SKILLs eran push masivo y violaban smart-zone. Si en el futuro hace falta convención específica, se reintroducen como `references/*.md` bajo demanda.

**Comandos**:
```bash
cd /home/clasing/skills
rm -rf opencode/skills/typescript-advanced-types
rm -rf opencode/skills/nestjs-patterns
rm -rf skills/clasing-ui-v2-beta
```

**Verificación post-delete**:
- Buscar referencias rotas: `grep -r "typescript-advanced-types\|nestjs-patterns\|clasing-ui-v2-beta" .`
- Actualizar README/SPEC/PLAN si los mencionan
- Re-correr golden tests para detectar dependencias

---

## Fase 1.5 — Sprint 0.5: Inspiration Lift (P0, ~19h)

> Branch: `feat/sprint-0.5-inspiration-lift`
> Pre-requisito: QW1-QW6 + Fase 1 completados
> Source: análisis de `obra/superpowers` (`mem_modl8u3x_8bk8rb`, `Research/Superpowers-vs-Clasing-Skills.md`)

**Razón**: Superpowers (Jesse Vincent, 167k stars, validado empíricamente con 94% rejection rate de PRs slop) tiene 10 patrones de disciplina adversarial que rellenan huecos reales en nuestro stack. Esta fase los integra ANTES de Sprint 1 para que los fundamentos (vertical slices, TDD) hereden la disciplina correcta.

### IL1 · Description Trap audit (CRÍTICO, prerrequisito de TODO)
- **Archivos**: TODAS las skills, agents y commands del repo
- **Acción**: reescribir el campo `description:` para que diga SOLO "Use when X". NUNCA resumir el workflow o las reglas internas.
- **Patrón malo**: `description: Skill that does X by following Y workflow with Z steps.`
- **Patrón bueno**: `description: Use when the user asks for X.`
- **Esfuerzo**: 2h · **Impact**: 🔴 crítico (afecta toda activación de skills)

### IL2 · Iron Law texto exacto + nuevo skill `tdd-iron-law`
- **Archivo 1**: `opencode/opencode.json` coder system prompt (ya hecho en QW3 reforzado)
- **Archivo 2**: `opencode/skills/tdd-iron-law/SKILL.md` (NUEVO, ≤120 líneas)
- **Esfuerzo**: 1h + 1h · **Impact**: 🔴 crítico (anti-cheating)

### IL3 · Skill `verification-before-completion` (ya en QW6)
- Marcar como completado cuando QW6 esté hecho.

### IL4 · Disciplina cultural — "your human partner" + ban frases performativas
- **Archivo 1**: search-and-replace en TODOS los prompts del repo: "the user" → "your human partner" (donde aplique).
- **Archivo 2**: `CONVENTIONS.md` (NUEVO o existente) — añadir sección:
  ```
  ## Forbidden phrases (anti-sycophancy)
  - "You're absolutely right!"
  - "Great question!"
  - "I apologize for the confusion"
  - Any agradecimiento performativo

  ## Required terminology
  - "your human partner" en contextos colaborativos
  - "evidence" en contextos de verificación
  ```
- **Esfuerzo**: 1h · **Impact**: 🟡 alto (calidad cultural)

### IL5 · Anti-rationalization tables en agentes disciplinarios
- **Archivos**: prompts de `coder`, `verifier`, `test-reviewer`, `security` en `opencode.json`
- **Acción**: añadir tabla `| Excuse | Reality |` con 3-5 entradas capturadas de evals reales o copiadas de Superpowers como baseline
- **Esfuerzo**: 3h · **Impact**: 🟡 alto

### IL6 · SUBAGENT-STOP gate al inicio de skills disciplinarios
- **Archivos**: skills disciplinarios (security, verification-before-completion, tdd-iron-law)
- **Acción**: añadir bloque al inicio: "If you are running as a subagent invoked by another subagent, STOP. Return status:blocked with reason 'nested-subagent-loop-detected'."
- **Esfuerzo**: 30min · **Impact**: 🟢 medio (previene loops anidados)

### IL7 · Skill `_shared/dispatching-parallel-agents.md`
- **Archivo**: NUEVO, ≤120 líneas
- **Contenido**: documenta el patrón actual del orchestrator usando guía de obra como base. Cubre: cuándo paralelizar, cómo construir prompts independientes, cómo agregar resultados.
- **Esfuerzo**: 2h · **Impact**: 🟢 medio (formaliza tribal knowledge)

### IL8 · Documentar inline-self-review insight
- **Archivo**: `docs/lessons-learned/inline-vs-subagent-review.md` (NUEVO)
- **Contenido**: hallazgo de obra (5×5 trials) — inline-self-review ≥ subagent-review-loop, ahorra ~25 min/iteración. Aplicar en Sprint 2 al rediseñar verifier.
- **Esfuerzo**: 1h · **Impact**: 🟢 medio (planning Sprint 2)

### IL9 · SessionStart hook custom OpenCode
- **Archivo**: `opencode/hooks/session-start.sh` (NUEVO)
- **Acción**: hook propio (NO el de Superpowers tal cual) que inyecta `using-clasing-skills` con cap de tokens y compatible con smart-zone budget. NO debe forzar "if 1% chance, invoke skill" (rompe orchestrator-delegate-first).
- **Esfuerzo**: 4h · **Impact**: 🟡 alto (auto-bootstrap)

### IL10 · Diseño two-stage review (verifier split)
- **Archivo**: `docs/design/two-stage-review.md` (NUEVO, solo diseño, no implementación)
- **Contenido**: separar verifier en `spec-compliance-checker` + `code-quality-reviewer`. Inspiración: code-reviewer agent de Superpowers. Implementación se hace en Sprint 2 (M3).
- **Esfuerzo**: 3h · **Impact**: 🟢 medio (gates más fuertes)

**Quick wins ejecutables HOY del Sprint 0.5 (~5h)**: IL1, IL2, IL3 (=QW6), IL4. El resto puede ir después de Sprint 1.

---

## Fase 2 — Sprint 1: Fundamentos (P0, 2 semanas)

> Branch: `feat/sprint-1-fundamentals`
> Pre-requisito: QW1-QW6 + Fase 1 + Sprint 0.5 completados

### M1 · PLAN-feature.md → vertical slices
- **Archivo**: `templates/PLAN-feature.md` (82 líneas)
- **Estado actual**: 8 fases horizontales (domain → app → infra → controller → tests)
- **Cambio**: reescribir a vertical slices (cada slice atraviesa todas las layers DDD + tests inline)
- **Esfuerzo**: medio · **Impact**: crítico

**Estructura objetivo**:
```markdown
# Plan: <feature>

## Vertical Slices

### Slice S1 — <user-visible behavior 1>
- mode: hitl | afk
- tdd: true | false
- Touches:
  - domain: ...
  - app: ...
  - infra: ...
  - controller: ...
  - tests: ...
- Acceptance:
  - End-to-end demoable: <how to test manually>
  - Test passes: <test files>

### Slice S2 — <user-visible behavior 2>
- blocks: [S1]  ← solo si depende
- ...
```

### A2 · Skill tdd-red-green-refactor formal
- **Archivo**: `opencode/skills/tdd-red-green-refactor/SKILL.md` (NUEVO)
- **Esfuerzo**: bajo · **Impact**: alto
- Formaliza el flujo Red → Green → Refactor con Iron Law (ya inyectado en coder via QW3)

### M4 · PRD slim
- **Archivo**: `opencode/skills/prd/SKILL.md` (167 líneas)
- **Cambio**: borrar "Phase 1: Interrogate" (delegado a `grill-me`)
- **Esfuerzo**: bajo · **Impact**: medio (elimina duplicación)

### A8 · `_shared/smart-zone-budget.md`
- Ya creado en QW4

### A11 · Golden test Iron Law
- **Archivo**: `opencode/evals/golden/iron-law.md`
- **Test**: dado un coder con un test que falla, verificar que NO modifica el test
- **Esfuerzo**: bajo · **Impact**: alto

### A12 · Golden test vertical slice
- **Archivo**: `opencode/evals/golden/vertical-slice.md`
- **Test**: dado un PRD, verificar que tech-planner produce slices verticales (no horizontales)
- **Esfuerzo**: medio · **Impact**: alto

### Limpieza E1, E2, E5
- E1: confirmar QW1 ya hecho
- E2: confirmar QW5 línea 218 borrada
- E5: revisar `claude-code/CLAUDE.md` y eliminar redundancias ya cubiertas por skills

---

## Fase 3 — Sprint 2: Arquitectura y operación (P1, 2 semanas)

> Branch: `feat/sprint-2-architecture`

### A3 · Skill improve-codebase-architecture
- **Archivo**: `opencode/skills/improve-codebase-architecture/SKILL.md` (NUEVO)
- Cita Ousterhout (deep modules); escanea repo y propone candidatos a deepening con argumentos
- **Esfuerzo**: medio · **Impact**: alto

### A9 · Agente architect
- **Archivo**: `opencode/opencode.json` añadir agente `architect`
- Modelo Opus, se invoca después de PRD y antes de tech-planner
- Output: `architecture-notes.md` + `deepening-candidates[]`
- **Esfuerzo**: medio · **Impact**: alto

### A5 · Template PLAN-vertical-slice.md formalizado
- Tras M1, generalizar el patrón en `templates/`

### M3 · Manager con HITL/AFK
- **Archivo**: `opencode/opencode.json` agente `manager`
- Distinguir slices `mode: hitl` vs `afk` y rutear acordemente
- **Esfuerzo**: medio · **Impact**: alto

### M14 · Orchestrator Opus + task_budget
- **Archivo**: `opencode/opencode.json` agente `orchestrator`
- Cambiar `model: anthropic/claude-sonnet-4-6` → `claude-opus-4-6`
- Añadir lógica de task_budget para descartar Opus en tareas triviales (mantener Sonnet como fallback)
- **Esfuerzo**: bajo (config) · **Impact**: alto · **Riesgo**: costo $$

### M10 · Test-reviewer Iron Law audit
- Añadir step explícito de auditoría Iron Law al test-reviewer

### A6 · Command `/grill`
- **Archivo**: `opencode/commands/grill.md` (NUEVO)
- Slash command que invoca el skill `grill-me` directamente

---

## Fase 4 — Sprint 3: Escalamiento (P2, 2 semanas)

> Branch: `feat/sprint-3-scale`

### A4 · AFK Ralph loop docker
- **Archivo**: `opencode/commands/afk-run.md` (NUEVO) + script bash
- Bash loop que ejecuta el manager dentro de Docker sandbox para slices `mode: afk`
- **Esfuerzo**: alto · **Impact**: alto · **Riesgo**: runaway (mitigar con budget cap + max iterations)

### A15 · Security cross-lab
- **Archivo**: `opencode/skills/security/SKILL.md` añadir Phase 5
- Cuando dual-judge contradice → invocar reviewer cross-provider
- **Esfuerzo**: medio · **Impact**: medio

### M13 · Security skill Phase 5
- Implementación concreta del cross-lab arriba

### A13 · Golden test cross-provider
- Test que verifica que en contradicción dual-judge se dispara cross-lab

### A7 · Command `/afk-run`
- Slash command para iniciar AFK loops manualmente

### Cross-provider advisor (Codex GPT-5.3)
- **Archivo**: `opencode/opencode.json` añadir provider `openai` y agente `advisor-cross`
- Opt-in para reviews críticos descorrelacionados (Jay Fowler / flux pattern)
- **Esfuerzo**: medio · **Impact**: medio

---

## Arquitectura objetivo (post-Sprint 3)

```
USUARIO: "implementar export CSV multi-tenant"
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ ORCHESTRATOR  [Opus + task_budget]                          │
│  Phase 0 → Neurox cross-namespace + project context         │
│  Decide HITL/AFK mix + invoca grill cuando feature no-triv  │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ GRILL-ME skill  ←─ 1 Q a la vez, design tree, ≤30 iter      │
│  output: design-tree.md + assumptions.md                    │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ PRD skill (slim)                                            │
│  consume design-tree → PRD.md con frontmatter:              │
│  slices: [S1, S2, S3], modes: [hitl, afk, hitl]             │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ ARCHITECT  [Opus]  ←─ Ousterhout deep-modules               │
│  output: deepening-candidates[] + architecture-notes.md     │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ TECH-PLANNER [Sonnet]                                       │
│  template: PLAN-vertical-slice.md                           │
│  output: PLAN.md con slices[S1..Sn] cada uno demoable       │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ MANAGER per slice:                                          │
│   ├─ mode=hitl → coder[Haiku] + verifier + review humano    │
│   └─ mode=afk  → /afk-run docker Ralph loop                 │
│  TDD Iron Law cuando slice.tdd=true                         │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ VALIDATION FAN-OUT (paralelo)                               │
│   ├── test-reviewer  (Iron Law audit)                       │
│   ├── security A + B [Haiku]                                │
│   │     └─ si contradicción → security CROSS-LAB            │
│   │        [Codex GPT-5.3]                                  │
│   └── skill-validator (registry compact rules)              │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ ADVISOR  [Opus, no tools, <100 palabras]  3 calls/session   │
│ ADVISOR-CROSS  [Codex GPT-5.3]  opt-in para review crítico  │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
NEUROX (transversal): decisions, patterns, bugfixes, gotchas
```

---

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Costo orchestrator Sonnet → Opus | task_budget threshold; Sonnet fallback en tareas triviales |
| AFK runaway loop | Hard cap iteraciones + budget cap + sandbox docker obligatorio |
| Refactors rompen URLs internas | Verificar con `grep -r` antes de borrar |
| Evals invalidados con vertical slices | Re-baselinar golden tests antes de migrar M1 |
| Migration shock | Hacer P0 en feature branch, validar evals, mergear atómico |
| Eliminar 3 SKILLs rompe codebase | Buscar referencias antes (`grep -r`); actualizar docs |

---

## Métricas de éxito

**De Fase 0/1 + Sprints 1-3**:
- [ ] 0 commands ficticios en README
- [ ] 0 SKILL.md > 120 líneas
- [ ] 100% slices verticales en PLAN-feature
- [ ] ≥ 3 golden tests cubren Iron Law / vertical / cross-provider
- [ ] Tiempo medio P0→PR sin fricción: medir antes/después
- [ ] 0 referencias rotas tras eliminar SKILLs grandes

**De Sprint 0.5 (Inspiration Lift)**:
- [ ] 0 SKILL.md con `description:` que resuma workflow (Description Trap)
- [ ] 0 frases performativas en prompts ("You're absolutely right!", etc.)
- [ ] 100% agentes disciplinarios con anti-rationalization tables
- [ ] CONVENTIONS.md con sección de terminología y frases prohibidas
- [ ] SessionStart hook custom funcionando en OpenCode
- [ ] Diseño two-stage review documentado en `docs/design/`

---

## Decisiones tomadas

- ✅ Eliminar `typescript-advanced-types`, `nestjs-patterns`, `clasing-ui-v2-beta` (simplificación)
- ✅ Aplicar TDD Iron Law con anti-rationalization table al coder (con excepción para bugfixes triviales)
- ✅ smart-zone-budget con cap 100K, warning 80K
- ✅ Adoptar Description Trap rule de Superpowers como compromiso invariante #7
- ✅ NO importar repo entero de Superpowers — solo extraer patrones (Sprint 0.5)
- ✅ NO adoptar SessionStart hook de Superpowers tal cual — diseñar uno propio compatible con orchestrator-delegate-first
- ✅ NO adoptar Visual Companion / brainstorm-server (~1200 LOC) — overengineering
- ✅ Disciplina cultural: ban "You're absolutely right!" + usar "your human partner"
- ⚠️ Plugin advisor.ts: hay conflicto con commit `23a7cb7` que lo movió de plugins/ a tools/. Decidir antes de QW5: mantener tools/ y actualizar PLAN.md, o revertir a plugins/.
- ⏳ Migración orchestrator a Opus → confirmar costo en Sprint 2
- ⏳ Adoptar Sandcastle externo o construir AFK propio → Sprint 3 decide
- ⏳ Two-stage review (verifier split): diseñar en Sprint 0.5 (IL10), implementar en Sprint 2 (M3)

---

## Open questions

- ¿Qué task_budget threshold define "tarea trivial" para mantener orchestrator en Sonnet?
- ¿Activar cross-provider review siempre / solo crítico / opt-in usuario?
- ¿Qué evals añadir para validar que vertical slices son efectivamente vertical y no falsos positivos?
- ¿Plugin advisor.ts: revertir a `plugins/` o mantener en `tools/` y actualizar docs? (commit `23a7cb7` es reciente)
- ¿SessionStart hook custom: opt-in por proyecto o siempre activo?
- ¿Anti-rationalization tables: capturar empíricamente de evals reales o copiar de Superpowers como baseline?

---

## Next steps

1. **HOY (~5h)**:
   - Quick wins críticos: QW1 (15min) + QW2 (30min) + QW3 (15min) + QW4 (20min) + QW5 (10min) + QW6 (1h)
   - Sprint 0.5 quick wins: IL1 Description Trap audit (2h) + IL4 disciplina cultural (1h)
   - Decidir: revertir advisor.ts o actualizar docs
2. **Esta semana (~14h)**:
   - Fase 1: simplificación (eliminar 3 SKILLs grandes, ~30 min)
   - Sprint 0.5 restante: IL5 (3h) + IL6 (30min) + IL7 (2h) + IL8 (1h) + IL9 (4h) + IL10 (3h)
3. **Próxima semana**: Branch `feat/sprint-1-fundamentals`, ejecutar M1 + A2 + M4 + A11 + A12 (P0 core)
4. **Después**: re-baseline evals + mergear + comenzar Sprint 2

---

## Referencias

- Workshop Matt Pocock: `vault://Research/Matt-Pocock-AI-Software-Engineering-Workshop.md`
- Validación comunitaria: `vault://Research/Matt-Pocock-Community-Validation.md`
- Gap analysis: `vault://Research/Skills-Repo-vs-Matt-Pocock.md`
- Plan v2 detallado: `vault://Research/Skills-Repo-Improvement-Plan-v2.md`
- Análisis Superpowers: `vault://Research/Superpowers-vs-Clasing-Skills.md`
- Research memory: `mem_modkhttv_at7mz4` (plan), `mem_modjtroj_6obphg` (gap analysis), `mem_modl8u3x_8bk8rb` (Superpowers)
- Brooks — *The Design of Design* (shared design concept)
- Ousterhout — *A Philosophy of Software Design* (deep modules)
- Pragmatic Programmer — Tracer bullets / vertical slices
- Chroma research — context rot benchmarks
- Anthropic Advisor Strategy (abr 2026)
