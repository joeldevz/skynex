# Agent Evaluation Framework

Fixtures declarativos para revisar el comportamiento de agentes. No se ejecutan
modelos ni APIs al modificar esta configuracion.

## Golden Tests (12 fixtures conservados)

| Test | Agente | Qué valida |
|------|--------|------------|
| 01-planner-reads-conventions | planner | Lee CONVENTIONS.md antes de preguntar |
| 02-planner-uses-template | planner | Usa template PLAN-crud para tareas CRUD |
| 05-coder-reads-before-writing | coder | Lee código existente antes de escribir |
| 06-coder-runs-verification | coder | Corre tsc/build/test antes de reportar éxito |
| 08-test-follows-existing-patterns | coder | Sigue patrones de tests existentes |
| 10–16 | orchestrator (historico) | Recuperacion, riesgo, identidad y evidencia del workflow |

`coder` tiene su definicion en `agents/`. Los fixtures 01–02 usan el nombre
historico `planner`; el agente de planificacion actual se llama `tech-planner`.
Los fixtures 10–16 conservan el nombre historico `orchestrator`, cuya definicion
esta archivada fuera del bundle activo. Son referencias de contratos anteriores,
no instrucciones para invocar un agente disponible ni un alias para otro agente.
Los cuatro fixtures del flujo retirado fueron eliminados; no se renumeran los restantes.

## Cómo correr

```bash
# Todos los golden tests
./evals/run-evals.sh

# Un test específico
./evals/run-evals.sh golden/01-planner-reads-conventions.yaml

# Solo tests de un agente
./evals/run-evals.sh --agent planner
```

## Formato de test YAML

```yaml
id: unique-id
name: "Nombre legible"
description: |
  Qué valida este test.
agent: coder

prompt: |
  Lo que se le envía al agente.

setup:
  files:
    - path: relativo/al/tmpdir
      content: |
        contenido del archivo

checks:
  must_read:           # Archivos que DEBE leer
    - CONVENTIONS.md
  must_read_any:       # Al menos uno de estos
    - file-a.ts
    - file-b.ts
  must_not:            # Cosas que NO debe hacer
    - "Write code directly"
  must_run_any:        # Comandos que debe ejecutar
    - "npx tsc --noEmit"
  reads_before_writes: # true = las lecturas deben ocurrir antes que las escrituras
  must_delegate_to:    # Subagente al que debe delegar
  expect_in_output:    # Strings que deben aparecer en la respuesta
    - "review"

timeout: 120000
```

## Evaluación

Los tests son **declarativos** — definen expectativas sobre el comportamiento del agente.
La evaluación hoy es manual (leer el output y verificar contra los checks).

Roadmap:
- [ ] Runner automático que parsea los YAML y ejecuta con opencode CLI
- [ ] Evaluadores que comparan tool calls contra los checks
- [ ] Resultados en JSON para tracking de regresión
- [ ] CI integration

## Cuándo agregar tests

- Cuando cambias el prompt de un agente
- Cuando agregas una capacidad a un agente disponible
- Cuando un agente se comporta mal y quieres evitar regresión
