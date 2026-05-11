# Design Tree — skynex-eval

## Resolved decisions

- D1: **Scope** — Evaluar los 12 items testeables del ecosistema (42 test cases), cubriendo quality gates + pipeline + coverage amplia
- D2: **Lenguaje** — Go, integrado en el mismo repo/go.mod que skynex
- D3: **Binario** — Separado (`skynex-eval`), no subcomando del installer
- D4: **Auto-responder multi-turn** — Script fijo por test case (campo `turns:[]` en YAML), fallback "use recommended", max 10 turns
- D5: **LLM-as-judge** — Híbrido: Haiku para gates simples (1-5), Sonnet para planning (7,10,11,12), Opus para pipeline crítico (6,8,9). Flag `--no-llm-judge` disponible.
- D6: **Fixtures** — Todo committed en repo con lockfiles. `_setup.sh` corre `npm ci`. Sin node_modules en git.
- D7: **Arquitectura de ejecución** — `opencode serve --port 4096` arrancado por lifecycle manager, tests vía HTTP POST /session/:id/message, respuestas analizadas por judges

## Open assumptions (validate before PRD)

- A1: `opencode serve` funciona headless con la config actual de skynex (validado en spike ✅)
- A2: Cada sesión nueva es stateless (no arrastra contexto de sesiones previas) — asumir sí, verificar
- A3: El costo real por run completo será ~$3-5 — depende de cache hit rate en producción

## Out of scope (explicit)

- nestjs-patterns / typescript-advanced-types (referencia, no testeable directamente)
- commit / pr / rollback (side effects en git/filesystem)
- Dashboard web de resultados (futuro)
- CI integration (futuro — primero funcionar localmente)
- Performance benchmarking del propio opencode (solo medimos calidad de output)

## Ready for PRD
✅ yes — todas las decisiones resueltas
