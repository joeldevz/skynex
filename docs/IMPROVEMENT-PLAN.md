# Skills Repo — Improvement Plan

> **Status**: Active · **Owner**: Christopher · **Created**: 2026-04-25 · **Updated**: 2026-04-25 (refactored to Principle-Driven Design)
> **Source**: Destilación de Matt Pocock + obra/Superpowers + Gentleman/gentle-ai aplicada al stack propio
> **Vault refs**: `Research/Skills-Repo-Improvement-Plan-v2.md`, `Research/Skills-Repo-vs-Matt-Pocock.md`, `Research/Superpowers-vs-Clasing-Skills.md`, `Research/Gentle-AI-vs-Clasing-Skills.md`
> **Memory refs**: `mem_modkhttv_at7mz4`, `mem_modjtroj_6obphg`, `mem_modb71hc_96q5sf`, `mem_modl8u3x_8bk8rb`, `mem_modmkklu_rhc45p`

---

## Filosofía del plan

**No copiamos código ni skills de otros proyectos.** Destilamos los principios validados que han demostrado funcionar y diseñamos NUESTRAS piezas con todo el conocimiento acumulado, encajando en nuestro stack (OpenCode + Claude Code + Neurox + return envelope + 9 agentes coordinados).

Las menciones a Matt Pocock, obra/Superpowers o Gentleman/gentle-ai a lo largo del documento son **referencias de procedencia del principio**, no instrucciones de copia.

---

## TL;DR

El repo coordina muy bien (orchestrator + advisor + dual-judge + return-envelope + Neurox) pero opera muy poco. Faltan: grill-me, TDD Iron Law, vertical slices, AFK loops, deep modules, cross-provider review, disciplina psicológica adversarial.

**Plan ejecutivo**: 5 quick wins (~2h) + Sprint 0.5 (~19h, disciplina adversarial) + Sprint 0.5b (~10h, gobernanza y profiles) + 3 sprints de 2 semanas. Dirección: simplificar (eliminar SKILLs grandes), añadir fundamentos operacionales con disciplina adversarial, escalar después.

---

## Compromisos invariantes (norte arquitectónico)

1. **Smart-zone hard cap 100K tokens** → reset automático
2. **SKILL.md ≤120 líneas** + `references/*.md` (≤200 c/u) — progressive disclosure obligatorio
3. **HITL default; AFK opt-in** explícito por slice tag
4. **TDD Iron Law** solo cuando `slice.tdd=true` (no fricciona bugfixes triviales)
5. **Return envelope** con `slice_id` + `mode: hitl|afk` en todos los agentes
6. **Doc rot prohibido** — toda promesa en README/SPEC/PLAN debe corresponder a archivos reales
7. **Description Trap rule** — descripción de skill = SOLO "Use when X", NUNCA resume el workflow
8. **Disciplina cultural** — ban a "You're absolutely right!" / agradecimientos performativos; usar "your human partner"

---

## Principios rectores (destilación de la investigación)

Estos son los principios que han demostrado funcionar en la industria 2026. Los aplicamos a TODO lo que diseñemos, no como items separados.

### De Matt Pocock — fundamentos cognitivos del trabajo con LLMs

| Principio | Esencia |
|---|---|
| **Smart zone** | La atención degrada cuadráticamente; el cap real es ~100K, no el nominal |
| **Memento problem** | Reset > resumen; los artefactos persistentes son la memoria |
| **Grilling sobre planning** | Alineación humano-AI antes que documentos prematuros |
| **Vertical slices** | Feedback temprano > completitud por capas |
| **Canban DAG** | Plans secuenciales son loops disfrazados; preferir grafos |
| **Bad codebase = bad agent** | La calidad de los feedback loops es el ceiling del agente |
| **Push vs Pull** | Standards al reviewer (push); skills al implementer (pull) |
| **HITL vs AFK** | Distinguir explícitamente qué requiere humano y qué no |

### De obra/Superpowers — disciplina psicológica adversarial

| Principio | Esencia |
|---|---|
| **Description Trap** | Descripciones que resumen workflow rompen el matching del agente |
| **Iron Law adversarial** | Disciplina explícita y nombrada > reglas suaves implícitas |
| **Anti-rationalization tables** | Anticipar excusas concretas del LLM en el prompt |
| **Verification before completion** | "Done" sin evidencia es slop; exigir prueba |
| **"Your human partner"** | Lenguaje colaborativo, no servicial ni jerárquico |
| **Ban frases performativas** | "You're absolutely right!" es ruido cognitivo |
| **Subagents NO heredan contexto** | Construir prompts limpios, no transferir mensajes |
| **Inline-self-review ≥ subagent loop** | Validado empíricamente con 5×5 trials |

### De Gentleman/gentle-ai — operación industrial

| Principio | Esencia |
|---|---|
| **TDD Cycle Evidence** | El return debe demostrar el ciclo, no solo afirmar que pasó |
| **Banned Assertion Patterns** | Tautologías, ghost loops y smoke tests son detectables |
| **Mock Hygiene cap (max 6)** | Si hay >6 mocks, el módulo está mal diseñado |
| **Adversarial dual-judge generalizable** | El patrón sirve más allá de seguridad |
| **PR-issue gating con `status:approved`** | Gobierno duro antes de mergear |
| **Pre-commit AI gate con cache SHA256** | Validar diff vs convenciones, sin re-validar igual |
| **Skill-registry físico** | El registry es un archivo escaneable, no un concepto |
| **Profiles switchables** | Control de costo runtime > config estática |
| **Skill-creator meta-skill** | Crear skills es trabajo recurrente, mereció skill propia |

### Lo que NOSOTROS ya tenemos (no perder)

| Fortaleza propia | Por qué importa |
|---|---|
| **Return envelope estandarizado** | Contrato claro entre agentes — superior a SDD lineal |
| **9 agentes con responsabilidades claras** | Más maduro que workflows monolíticos |
| **Advisor strategy con `advisor_consult`** | Senior model bajo demanda, no siempre |
| **Neurox con kinds + types + 4D scoring + brain power** | Más rico semánticamente que Engram |
| **Dual-judge ya en `security`** | Solo falta generalizarlo, no inventarlo |
| **Bilingüe ES/EN** | Refleja contexto real de uso |
| **Stack TS + OpenCode coherente** | Foco, no genérico |

### Cómo se aplican en este plan

Cada item del plan (QW, IL, GA, M, A, R) se diseña aplicando **estos principios + el stack propio**, no copiando código ajeno. Cuando el documento dice "inspirado en X", significa: "el principio viene de X, el diseño es nuestro".

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

### QW5 · Alinear docs con ubicación real de advisor.ts + línea muerta README ✅
- **Decisión tomada**: mantener `opencode/tools/advisor.ts` (commit `23a7cb7` lo movió allí para arreglar colisión de tool registry — registra correctamente como `advisor_consult`)
- **Archivo 1**: ✅ `PLAN.md` línea 15 actualizada — refleja ubicación real
- **Archivo 2**: borrar línea 218 README ("No hay familia sdd-* ni find-skills") (pendiente)
- **Archivo 3**: confirmar que `gap analysis` (mem_modjtroj_6obphg) interpretó mal — NO hay inconsistencia
- **Esfuerzo**: 5 min · **Impact**: medio (consistencia)

> **Lección aprendida**: el gap analysis original asumió que `plugins/` vacía + archivo en `tools/` = error. En realidad fue un fix deliberado para evitar colisión con el agente `advisor`. Verificar siempre el git log antes de proponer "consistencia".

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
> Principios destilados aplicados: Description Trap, Iron Law adversarial, Anti-rationalization, "your human partner", Verification before completion, Subagent context isolation, Inline-self-review

**Razón**: la disciplina psicológica adversarial (validada empíricamente en obra/Superpowers con 94% rejection rate de PRs slop) llena huecos reales en nuestro stack. Esta fase aplica los principios destilados ANTES de Sprint 1 para que los fundamentos (vertical slices, TDD, grilling) hereden la disciplina correcta. **Cada item se DISEÑA usando nuestros principios + nuestro stack — no se copia código ajeno.**

### IL1 · Description Trap audit (CRÍTICO, prerrequisito de TODO)
- **Archivos**: TODAS las skills, agents y commands del repo
- **Acción**: reescribir el campo `description:` para que diga SOLO "Use when X". NUNCA resumir el workflow o las reglas internas.
- **Patrón malo**: `description: Skill that does X by following Y workflow with Z steps.`
- **Patrón bueno**: `description: Use when the user asks for X.`
- **Esfuerzo**: 2h · **Impact**: 🔴 crítico (afecta toda activación de skills)

### IL2 · Diseñar skill `tdd-discipline` aplicando principios destilados
- **Archivo 1**: `opencode/opencode.json` coder system prompt (ya reforzado en QW3 con anti-rationalization)
- **Archivo 2**: `opencode/skills/tdd-discipline/SKILL.md` (NUEVO, ≤120 líneas)
- **Principios aplicados**:
  - Iron Law nombrado y explícito (de Superpowers)
  - Anti-rationalization table con excusas concretas (de Superpowers)
  - **TDD Cycle Evidence** en el return envelope (de gentle-ai) — campos `red_proof`, `green_proof`, `assertion_quality`
  - **Banned Assertion Patterns** detectables: tautologías, ghost loops, smoke tests (de gentle-ai)
  - **Mock Hygiene cap (max 6)** — si excede, status:blocked con razón "design smell" (de gentle-ai)
  - Description Trap aplicada (de Superpowers)
  - Bilingüe ES/EN (nuestro)
- **Importante**: NO copiamos `strict-tdd.md` de gentle-ai — destilamos sus principios (cycle evidence, banned patterns, mock cap) y los integramos a nuestro return envelope y stack TS.
- **Esfuerzo**: 1h + 2h · **Impact**: 🔴 crítico (anti-cheating + design smell detection)

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
- **Acción**: añadir tabla `| Excuse | Reality |` con 3-5 entradas capturadas de evals propios reales (preferido) o derivadas de patrones Superpowers como baseline inicial
- **Principio aplicado**: anti-rationalization de Superpowers, pero las excusas son las que VEMOS en nuestros logs, no las suyas
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

## Fase 1.6 — Sprint 0.5b: Designs informados por gobernanza y operación (P0, ~10h)

> Branch: `feat/sprint-0.5b-designs`
> Pre-requisito: Sprint 0.5 (disciplina adversarial) completado
> Principios destilados aplicados: TDD Cycle Evidence, Banned Assertion Patterns, Mock Hygiene, Adversarial dual-judge generalizable, PR-issue gating, Pre-commit AI gate, Skill-registry físico, Profiles switchables

**Razón**: la operación industrial (gobernanza de contribución, gates pre-commit, profiles de costo) es donde gentle-ai está validado. Destilamos sus principios y diseñamos NUESTRAS piezas — no migramos a Go ni copiamos bash. **Cada item se diseña aplicando los principios + nuestro stack TS + return envelope + Neurox.**

### GA1 · Diseñar gobernanza issue→PR aplicando principios destilados
- **Archivos NUEVOS**:
  - `.github/ISSUE_TEMPLATE/bug-report.yml`
  - `.github/ISSUE_TEMPLATE/feature-request.yml`
  - `.github/ISSUE_TEMPLATE/skill-proposal.yml`
  - `.github/PULL_REQUEST_TEMPLATE.md`
  - `.github/workflows/pr-check.yml`
- **Principios aplicados**:
  - **PR-issue gating con `status:approved`** (de gentle-ai) — solo issues aprobadas disparan work
  - **Type labels obligatorios** (`type:skill`, `type:agent`, `type:plugin`, `type:doc`, `type:meta`)
  - **Bilingüe ES/EN** (nuestro contexto, no el inglés-only de gentle-ai)
  - Status labels: `needs-review`, `approved`, `in-progress`, `blocked`
  - PR template con checklist de tests + lint + doc-rot detection (nuestros checks, no los de gentle-ai)
- **Diseño propio**: el oro NO son las plantillas yml, es el `pr-check.yml` con github-script para `Closes #N` regex + label gating. Adaptado a nuestros checks (no a los suyos).
- **Esfuerzo**: 2h · **Impact**: 🟡 alto

### GA2 · Generalizar `security` → `adversarial-review` parameterizado
- **Archivo**: `opencode/skills/adversarial-review/SKILL.md` (NUEVO, ≤120 líneas)
- **Principios aplicados**:
  - **Dual-judge generalizable** (de gentle-ai) — el patrón sirve más allá de seguridad
  - **Description Trap** (de Superpowers)
  - Reusar nuestra mecánica dual-judge existente — solo abstraer dominio
- **Diseño propio**:
  - Skill nuevo `adversarial-review` con parámetro `domain: security | tests | architecture | refactor | other`
  - `security` se mantiene como preset (`domain=security`) o se hace alias de `adversarial-review --domain security`
  - **NO copiamos** `judgment-day` de gentle-ai. Reusamos NUESTRA verdict matrix actual (Confirmed/Suspect/Contradiction) y añadimos Fix Agent + re-judge loop
  - Return envelope con campo `judges: [verdict_a, verdict_b, synthesis]`
- **Esfuerzo**: 2h · **Impact**: 🟡 alto

### GA3 · Diseñar pre-commit AI gate en TypeScript (no bash)
- **Archivo**: `scripts/precommit-ai-gate.ts` (NUEVO)
- **Principios aplicados**:
  - **Pre-commit AI gate con cache SHA256** (de gentle-ai) — patrón, no implementación
  - **Reusar nuestra infraestructura** — `advisor_consult` ya existente
- **Diseño propio**:
  - Hook node/bun, no bash (nuestro stack)
  - Reusa `advisor_consult` para validar `git diff --staged` vs `CONVENTIONS.md`
  - Cache SHA256 en `.opencode/.cache/precommit/{sha}` (nuestra estructura)
  - Solo aplica a paths críticos: `opencode/skills/`, `opencode/opencode.json`, `templates/`
  - Bypass con `SKIP_AI_GATE=1` para emergencias
  - Multi-provider opcional: si `OPENAI_API_KEY` disponible, second opinion descorrelacionada (cross-provider review de Matt)
- **Esfuerzo**: 4h · **Impact**: 🟡 alto

### GA4 · Diseñar `_shared/skill-registry.md` físico generado
- **Archivo**: `opencode/skills/_shared/skill-registry.md` (CONCEPTUAL ya existe en `_shared/skill-resolver.md`)
- **Acción nueva**: comando `/skills:scan` que escanea `opencode/skills/` y genera `.opencode/skill-registry.md` físico
- **Principios aplicados**:
  - **Skill-registry físico** (de gentle-ai) — el registry no es conceptual, es archivo escaneable
  - **Description Trap** verificada en cada SKILL.md leído
  - **Smart-zone** — registry compacto (≤200 líneas total)
- **Diseño propio**:
  - Auto-actualización con git pre-commit hook (sinergia con GA3)
  - Formato: nombre + description (validada Description Trap) + triggers + path
  - Orchestrator inyecta el registry al inicio de cada sesión (push, no pull)
- **Esfuerzo**: 2h · **Impact**: 🟢 medio

**Quick wins ejecutables HOY del Sprint 0.5b (~4h)**: GA1 + GA2. GA3 + GA4 al día siguiente (~6h).

### Backlog post-Sprint 1 (P1, ~2 días total — NO ejecutar ahora)
- **GA5 — Profiles switchables**: 3 archivos `opencode/profiles/{explore,balanced,production}.json` con configs de modelos por sprint. Principio: control de costo runtime (de gentle-ai). 4-6h
- **GA6 — Skill creator meta-skill**: `opencode/skills/skill-creator/SKILL.md` que toma NL → genera SKILL.md válido aplicando Description Trap + ≤120 líneas + bilingüe. Principio: skill-creator (de gentle-ai). 2h
- **GA7 — Neurox interop study**: documentar similitudes/diferencias con Engram para futura interop opcional (no migración). 1 día
- **GA8 — Cross-provider advisor**: añadir Codex GPT-5.3 al advisor para reviews descorrelacionados. Principio: cross-provider review (de Matt). 4-6h

### Backlog P2 (post-publicación si abre comunidad)
- **GA9** — Persona system opt-in bilingüe (no Gentleman-only): 2-3h
- **GA10** — Backup automático antes de cada `opencode/skills/` write: 4h
- **GA11** — Commands de comunidad (`/contribute`, `/propose-skill`): 2h

---

## Fase 2 — Sprint 1: Fundamentos (P0, 2 semanas)

> Branch: `feat/sprint-1-fundamentals`
> Pre-requisito: QW1-QW6 + Fase 1 + Sprint 0.5 + Sprint 0.5b completados

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

### Filosofía
- ✅ **Plan principle-driven, no copy-driven**: destilar principios validados de Matt Pocock + obra/Superpowers + Gentleman/gentle-ai y diseñar piezas propias informadas, no copiar código ajeno
- ✅ Compromisos invariantes ampliados con #7 (Description Trap) y #8 (Disciplina cultural)
- ✅ Sección "Principios rectores" como norte del plan

### Simplificación
- ✅ Eliminar `typescript-advanced-types`, `nestjs-patterns`, `clasing-ui-v2-beta` (modelos modernos ya conocen TS/NestJS suficientemente)
- ✅ Plugin advisor.ts permanece en `opencode/tools/advisor.ts` (commit `23a7cb7` lo movió allí para arreglar colisión de tool registry — `advisor_consult` registra correctamente)

### Disciplina (de Superpowers)
- ✅ TDD Iron Law con anti-rationalization table en coder (excepción para bugfixes triviales)
- ✅ smart-zone-budget con cap 100K, warning 80K, surgical compaction como tercera vía
- ✅ NO importar repo entero de Superpowers — destilar patrones
- ✅ NO adoptar SessionStart hook tal cual — diseñar propio compatible con orchestrator-delegate-first
- ✅ NO adoptar Visual Companion / brainstorm-server — overengineering
- ✅ Disciplina cultural: ban "You're absolutely right!" + usar "your human partner"

### Operación (de gentle-ai)
- ✅ NO importar repo entero de gentle-ai — destilar patrones, no migrar a Go
- ✅ NO adoptar SDD lineal de 9 fases — son ortogonales a vertical slices, mantener nuestro flujo
- ✅ NO copiar `strict-tdd.md` literal — destilar sus principios (TDD Cycle Evidence, Banned Assertion Patterns, Mock Hygiene cap) e integrarlos a nuestro skill `tdd-discipline` y return envelope
- ✅ NO copiar `judgment-day` literal — generalizar nuestro `security` existente con parámetro `domain`
- ✅ Pre-commit AI gate en TypeScript reusando `advisor_consult` (no bash, no GGA binary)
- ✅ Skill-registry físico generado por comando propio `/skills:scan`

### Pendientes
- ⏳ Migración orchestrator a Opus → confirmar costo en Sprint 2
- ⏳ Adoptar Sandcastle externo o construir AFK propio → Sprint 3 decide
- ⏳ Two-stage review (verifier split): diseñar en Sprint 0.5 (IL10), implementar en Sprint 2 (M3)
- ⏳ Cross-provider advisor (Codex GPT-5.3): GA8 backlog post-Sprint 1

---

## Open questions

- ¿Qué task_budget threshold define "tarea trivial" para mantener orchestrator en Sonnet?
- ¿Activar cross-provider review siempre / solo crítico / opt-in usuario?
- ¿Qué evals añadir para validar que vertical slices son efectivamente vertical y no falsos positivos?
- ¿SessionStart hook custom: opt-in por proyecto o siempre activo?
- ¿Anti-rationalization tables: capturar empíricamente de evals propios reales (preferido) o partir de patrones Superpowers como baseline temporal?
- ¿Profiles switchables (GA5): 3 archivos JSON o feature nativa de OpenCode?
- ¿Bilingüe ES/EN: forzar en TODO el plan o solo en docs públicas + skills?

---

## Next steps

### HOY (~5h) — Quick wins desbloqueantes
- QW1: limpiar README de commands ficticios (15 min)
- QW2: skill `grill-me` con Description Trap (30 min)
- QW3: TDD Iron Law + anti-rationalization en coder (15 min)
- QW4: smart-zone-budget shared (20 min)
- QW5: ✅ ya hecho (advisor.ts confirmado en `tools/`)
- QW6: skill `verification-before-completion` (1h)
- IL1: Description Trap audit (2h, prerrequisito de TODO)
- IL4: disciplina cultural en CONVENTIONS.md (1h)

### Esta semana (~14h) — Sprint 0.5 + Fase 1
- Fase 1: eliminar 3 SKILLs grandes (~30 min)
- Sprint 0.5 restante: IL2 (3h) + IL5 (3h) + IL6 (30min) + IL7 (2h) + IL8 (1h) + IL9 (4h) + IL10 (3h)

### Próxima semana — Sprint 0.5b + start Sprint 1
- Sprint 0.5b: GA1 (2h) + GA2 (2h) + GA3 (4h) + GA4 (2h) = ~10h
- Sprint 1 kickoff: branch `feat/sprint-1-fundamentals`, M1 vertical slices + A11/A12 golden tests

### Después — Sprint 1 → Sprint 3
- Re-baseline evals con golden tests nuevos
- Mergear Sprint 1 atómico
- Iniciar Sprint 2 (architect agent + HITL/AFK + Opus orchestrator)

---

## Referencias

### Vault notes (síntesis investigada)
- `vault://Research/Matt-Pocock-AI-Software-Engineering-Workshop.md`
- `vault://Research/Matt-Pocock-Community-Validation.md`
- `vault://Research/Skills-Repo-vs-Matt-Pocock.md`
- `vault://Research/Skills-Repo-Improvement-Plan-v2.md`
- `vault://Research/Superpowers-vs-Clasing-Skills.md`
- `vault://Research/Gentle-AI-vs-Clasing-Skills.md`

### Research memory (handoffs entre subagentes)
- `mem_modkhttv_at7mz4` — plan v2
- `mem_modjtroj_6obphg` — gap analysis
- `mem_modl8u3x_8bk8rb` — Superpowers comparación
- `mem_modmkklu_rhc45p` — gentle-ai verificación profunda
- `mem_modmilow_epxw7r` — gentle-ai datos duros

### Bibliografía rectora
- Brooks — *The Design of Design* (shared design concept)
- Ousterhout — *A Philosophy of Software Design* (deep modules)
- Pragmatic Programmer — Tracer bullets / vertical slices
- Chroma research — context rot benchmarks empíricos
- Anthropic Advisor Strategy (abr 2026)

### Repos de referencia analizados
- [obra/superpowers](https://github.com/obra/superpowers) — Jesse Vincent, disciplina adversarial
- [Gentleman-Programming/gentle-ai](https://github.com/Gentleman-Programming/gentle-ai) — Alan Buscaglia, operación industrial
- [Gentleman-Programming/engram](https://github.com/Gentleman-Programming/engram) — memoria persistente Go (referencia para Neurox)
- [Gentleman-Programming/gentleman-guardian-angel](https://github.com/Gentleman-Programming/gentleman-guardian-angel) — pre-commit AI gate (referencia para GA3)
