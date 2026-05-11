# Skynex Evaluation Specification

**Generado:** 2026-04-30
**Scope:** 12 items × ~3 test cases = **42 test cases** total
**Arquitectura:** Tests via `opencode serve` HTTP API + judges deterministas + LLM-as-judge opcional

## Convenciones globales
- `RESPONSE_TEXT` = texto concatenado del response del agente
- `TOOL_CALLS[]` = invocaciones de tools desde message parts
- `FILES_WRITTEN[]` = paths de archivos vía write/edit tool calls
- `SUBAGENT_CALLS[]` = task tool calls con subagent_type
- LLM-judge model: `anthropic/claude-opus-4-7`, temp 0.0
- N=3 reruns para items no-determinísticos; score final = mediana

## Items y test cases

| # | Item | Tipo | Test cases | N runs | Aggregation |
|---|------|------|------------|--------|-------------|
| 1 | grill-me | skill | 5 | 2 | min |
| 2 | verification-before-completion | skill | 3 | 2 | min |
| 3 | tdd-discipline | skill | 3 | 2 | min |
| 4 | skill-validator | subagent | 3 | 2 | min |
| 5 | verifier | subagent | 3 | 2 | min |
| 6 | orchestrator | primary | 4 | 5 | median |
| 7 | prd | skill | 3 | 3 | median |
| 8 | security | subagent | 4 | 3 | median |
| 9 | adversarial-review | skill | 3 | 3 | median |
| 10 | product-planner | subagent | 3 | 3 | median |
| 11 | tech-planner | subagent | 4 | 3 | median |
| 12 | test-reviewer | subagent | 4 | 3 | median |

**Total: 42 test cases**

## Schema común por test run

```json
{
  "case_id": "grill_positive_feature",
  "item": "grill-me",
  "n_run": 1,
  "status": "pass | fail",
  "deterministic_score": 0.85,
  "llm_score": 7.5,
  "final_score": "computed",
  "tokens_in": 12000,
  "tokens_out": 850,
  "tokens_cached": 51000,
  "cost_usd": 0.06,
  "duration_ms": 14200,
  "tool_calls_count": 3,
  "subagent_calls": ["tech-planner", "coder"],
  "files_written": ["design-tree.md"],
  "judge_findings": {
    "passed": ["question_count_per_message", "..."],
    "failed": ["contains_recommended_answer"],
    "warnings": []
  }
}
```

## Baseline + Diff strategy

- Frozen reference build → `baseline.json`
- Cada PR run → `current.json`
- Diff report flags:
  - **Regressions:** item pasó de pass → fail
  - **Score drops:** > 1 punto
  - **Cost increases:** > 20% (warn, no auto-fail)

## Fixtures layout

```
eval/fixtures/
├── grill/{empty,with_context}/
├── vbc/{passing_tests,no_tests,failing_tests}/
├── tdd/{ts_vitest,ts_vitest_existing_parser,trivial}/
├── skv/{tdd_violation,clean,docs_only}/
├── verifier/{working_math,broken_math,no_tests}/
├── orch/{ts_project,ts_project_failing,jwt_starter}/
├── prd/{with_design_tree,empty}/
├── sec/{sqli,xss,safe,secrets}/      # cada uno con GROUND_TRUTH.json
├── adv/{weak_tests,adr_questionable,refactor_diff}/
├── pp/{with_prd,empty}/
├── tp/{ts_minimal,ts_with_utils,ts_complex,nestjs}/
└── tr/{weak,missing_edges,coupled,clean}/  # cada uno con GROUND_TRUTH.json
```

## Detalles por item

(Documento completo con specs A-G por item: ver EVAL-SPEC-DETAIL.md)

Cada item documenta:
- A) **Specification** — 5-10 comportamientos esperados concretos
- B) **Test cases** — ID, input prompt, type, expected behavior
- C) **Deterministic judges** — regex/count/contains checks programáticos
- D) **LLM-as-judge rubric** — rúbrica para evaluación cualitativa
- E) **Metrics** — números a capturar
- F) **Risks** — falsos positivos/negativos, mitigación
- G) **Fixtures** — archivos pre-existentes necesarios
