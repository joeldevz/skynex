# PRD — skynex-eval: Agent Evaluation Suite

## 1. Executive Summary & Systems Context

**Problem:** Los skills y agentes de Skynex se modifican sin evidencia de si mejoran o empeoran. El skill `grill-me` no se activa correctamente (33% pass rate medido), pero sin un sistema de medición, cualquier fix es fe.

**Solution:** Un binario CLI (`skynex-eval`) que ejecuta 42 test cases automatizados contra `opencode serve`, aplica judges deterministas + LLM-as-judge, captura métricas de tokens/costo/latencia, y genera diff reports comparando baseline vs cambios.

**Ecosystem Impact:** Desbloquea iteración segura de TODOS los skills y agentes. Sin esto, el roadmap de "agregar diagnose, context-md, caveman, etc." está bloqueado por riesgo de regresión.

---

## 2. Multidimensional Success Metrics (KPIs)

| Dimensión | KPI | Target |
|-----------|-----|--------|
| **Performance** | Tiempo de un run completo (42 cases) | < 20 minutos |
| **Performance** | False positive rate de judges | < 5% |
| **Performance** | False negative rate de judges | < 10% |
| **UX** | Tiempo setup-to-first-run para un nuevo dev | < 5 minutos |
| **UX** | Agregar un nuevo test case (solo YAML + fixture) | < 10 minutos |
| **Safety** | Cost cap: kill switch automático | $10/run max |
| **Safety** | No run modifica el filesystem fuera de /eval/results/ | 100% |
| **Cost** | Costo promedio por run completo | ≤ $5 USD |
| **Cost** | Binario compila en CI | < 2 min |

---

## 3. User Experience & Functionality

### User Personas

| Persona | Descripción |
|---------|-------------|
| **Skill Developer** (tú) | Modifica skills/prompts y necesita saber si mejoró |
| **Contributor** | PRs externos que tocan skills, necesitan validar antes de merge |
| **CI Bot** | Ejecución automática por PR |

### User Stories

| ID | User Story | Acceptance Criteria | SP | Rationale |
|----|-----------|--------------------|----|-----------|
| US-1 | As a skill developer, I want to capture a baseline of current agent behavior so I have a reference point | `skynex-eval baseline --suite all` produces `results/baseline-{date}.json` with all 42 case scores | 5 | Lifecycle + runner + judges full integration |
| US-2 | As a skill developer, I want to compare current vs baseline so I know if my change improved things | `skynex-eval compare --baseline X` outputs pass/fail delta, score delta, cost delta per item | 5 | Diff logic + reporter |
| US-3 | As a skill developer, I want to run a single test case quickly to iterate | `skynex-eval run --case grill_positive_feature` runs 1 case in < 60s | 3 | Runner isolation + case loader |
| US-4 | As a skill developer, I want auto-responder for multi-turn tests (grill-me) so tests are fully automated | Multi-turn cases define `turns:[]` in YAML; runner sends responses automatically | 5 | Multi-turn harness new |
| US-5 | As a CI bot, I want a cost cap that aborts the run if it exceeds budget | `--cost-cap 5` aborts if accumulated cost > $5 | 2 | Simple counter check |
| US-6 | As a skill developer, I want the eval suite to detect regressions clearly | Diff report shows ❌ for items that went pass→fail, with exact case + judge detail | 3 | Reporter formatting |
| US-7 | As a contributor, I want to add a new test case by writing only YAML + fixture | YAML schema documented; fixture in `eval/fixtures/`; no Go code needed | 3 | Case loader design |
| US-8 | As a skill developer, I want LLM-as-judge for qualitative checks | Judge calls appropriate model (Haiku/Sonnet/Opus per item) with rubric from YAML | 5 | LLM judge integration |
| US-9 | As a skill developer, I want to skip LLM judge for fast iteration | `--no-llm-judge` runs only deterministic checks | 1 | Flag handling |
| US-10 | As a skill developer, I want N reruns for non-deterministic items | Config per item in spec; median/min aggregation | 3 | Runner loop + aggregation |

**Total: 35 SP (Fibonacci)**

### Non-Goals

- Dashboard web (futuro)
- CI pipeline config (futuro — manual run primero)
- Coverage de nestjs-patterns / typescript-advanced-types (no testeables)
- Performance benchmarking de opencode itself
- Testear side-effect commands (commit, pr, rollback)

---

## 4. Technical Specifications

### Architecture

```
┌─────────────────────────────────────────────┐
│             skynex-eval binary               │
├─────────────────────────────────────────────┤
│  cmd/skynex-eval/main.go                    │
│    ├── baseline (captures current state)    │
│    ├── compare (diff against baseline)      │
│    ├── run (single case/suite)              │
│    ├── list (show available cases)          │
│    └── report (HTML from JSON)              │
├─────────────────────────────────────────────┤
│  internal/eval/                             │
│    ├── lifecycle/     → manage opencode     │
│    ├── client/        → HTTP to server      │
│    ├── runner/        → execute cases       │
│    ├── cases/         → YAML loader         │
│    ├── judges/        → deterministic + LLM │
│    ├── metrics/       → token/cost/timing   │
│    └── reporter/      → JSON + diff         │
├─────────────────────────────────────────────┤
│  eval/                                      │
│    ├── cases/         → 42 YAML files       │
│    ├── fixtures/      → 25 directories      │
│    └── results/       → gitignored outputs  │
└─────────────────────────────────────────────┘
         ↕ HTTP (port 4096)
┌─────────────────────────────────────────────┐
│           opencode serve                     │
│  (started/stopped by lifecycle manager)     │
└─────────────────────────────────────────────┘
```

### Test Case YAML Schema

```yaml
id: grill_positive_feature
item: grill-me
type: positive                    # positive | negative
agent: orchestrator               # which agent receives the prompt
input: "I want to add a notification system to the app"

# Multi-turn (optional)
turns:
  - answer: "use recommended"
  - answer: "in-app only, no push notifications"
  - answer: "use recommended"
max_turns: 10

# Fixtures (optional)
fixture: grill/with_context       # relative to eval/fixtures/
setup_cmd: ""                     # command to run in fixture dir before test

# Deterministic judges
checks:
  - name: question_count_per_message
    type: regex_count_max_per_msg
    pattern: '\?'
    value: 2
  - name: contains_recommended
    type: contains_any
    patterns: ["recomiendo", "sugiero", "recommend", "suggested"]
  - name: no_code_blocks
    type: not_contains_pattern
    pattern: '```\w+'
  - name: skill_loaded
    type: tool_called
    tool: "mcp_Skill"
  - name: design_tree_created
    type: file_written
    pattern: "*design*tree*"

# LLM judge (optional)
llm_judge:
  enabled: true
  model: "anthropic/claude-haiku-4-5"    # per-item default
  rubric: |
    Rate 0-10:
    1. Question quality (0.3): discriminating vs open-ended
    2. Tree traversal (0.3): depends on previous answers
    3. Pacing (0.2): right depth (3-7 questions)
    4. Recommendation quality (0.2): concrete and justified
  pass_threshold: 7

# Reruns
n_runs: 2
aggregation: min                  # min | median | mean

# Metrics to capture
metrics:
  - tokens_total
  - tokens_output
  - duration_ms
  - tool_calls_count
  - cost_usd
```

### Integration Points

| System | Protocol | Purpose |
|--------|----------|---------|
| opencode serve | HTTP REST :4096 | Session mgmt + message API |
| Anthropic API | via opencode | LLM-as-judge calls |
| Filesystem | direct | Fixtures, results, fixtures setup |
| Neurox | via opencode MCP | Context for tests that need it |

### Security & Privacy

- API keys: reusa los configurados en opencode (no nuevas credenciales)
- Results: gitignored por defecto (contienen prompts/responses)
- Cost cap: hard kill switch, nunca excede presupuesto
- Fixtures: no contienen datos reales, solo código sintético

### Phased Rollout

| Phase | Scope | SP | Estimated |
|-------|-------|----|----|
| **MVP (Fase 1)** | Lifecycle + client + runner + deterministic judges + 17 cases (items 1-5) | 13 | 10h |
| **Pipeline (Fase 2)** | LLM judge + multi-turn + 11 cases (items 6-8) | 12 | 8h |
| **Coverage (Fase 3)** | Remaining 14 cases (items 9-12) + diff reporter | 10 | 6h |

---

## 5. Technical Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| OpenCode API changes between versions | Breaks client | Pin opencode version; version-check in lifecycle |
| LLM non-determinism gives flaky results | False regressions | N reruns with aggregation; tolerance band (±1 point) |
| Cost exceeds budget in CI | Unexpected bills | Hard `--cost-cap` kill switch; estimate before run |
| Fixtures drift from reality | False passes | GROUND_TRUTH.json reviewed on fixture changes |
| `opencode serve` hangs or crashes | Suite stuck | Timeout per case (120s default); lifecycle watchdog |
| Multi-turn auto-responder doesn't match agent questions | Test meaningless | Fallback to "use recommended"; max turns kill switch |

---

## Ready for PLAN.md
✅ All decisions resolved, PRD approved pending user confirmation.
