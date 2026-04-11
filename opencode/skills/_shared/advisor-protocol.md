# Advisor Protocol — Strategic escalation to a senior model

> **REGLA FUNDAMENTAL**: El advisor es un tool de escalacion estrategica, no de ejecucion.
> Llama al advisor cuando necesites orientacion de alto nivel, no para tareas mecanicas.
> El advisor PIENSA sobre tu contexto y devuelve un plan corto — nunca ejecuta tools ni escribe codigo.

## Cuando llamar al advisor

Llama al tool `advisor_consult` en estos 4 momentos:

| Trigger | Descripcion | Ejemplo |
|---------|-------------|---------|
| **Antes de trabajo sustantivo** | Despues de orientacion (leer archivos, entender contexto), ANTES de escribir codigo o comprometerte con un approach | "He leido el codebase, voy a implementar X. Advisor: es el approach correcto?" |
| **Cuando creas que terminaste** | Hacer el deliverable durable primero (escribir archivo, guardar resultado), LUEGO consultar | "Termine la implementacion, esta en file.ts. Advisor: algo que se me escape?" |
| **Cuando estes atascado** | Si llevas 2+ intentos sin progreso claro | "Intente A y B, ambos fallan por X. Advisor: que estoy missing?" |
| **Antes de cambiar de approach** | Antes de pivotar a una estrategia fundamentalmente diferente | "El approach actual no funciona, estoy considerando pivotar a Y. Advisor: vale la pena?" |

## Frecuencia

- **Tasks complejas**: minimo una vez antes de commit a un approach y una vez antes de declarar done.
- **Tasks cortas/reactivas**: una llamada puede ser suficiente, o ninguna si es trivialmente simple.
- **NO llamar para**: formatting, renames simples, fixes obvios, operaciones mecanicas.

## Limite de uso

- **Maximo 3 llamadas por sesion**. Si alcanzas el limite, continua con tu mejor criterio.
- **Circuit breaker**: si haces 2 llamadas consecutivas sin progreso entre ellas, pide input al usuario en vez de seguir consultando.

## Como llamar

Pasa una pregunta especifica en el argumento `question`:
- Incluye que estas haciendo y por que
- Incluye que has intentado y que fallo
- Incluye que estas considerando hacer ahora
- Se concreto — "que hago?" es una mala pregunta; "el approach A falla por X, deberia intentar B o C?" es buena

El advisor recibe automaticamente tu historial completo de sesion. No necesitas repetir todo — enfocate en la pregunta.

## Como tratar el consejo

> Dale al consejo peso serio — viene de un modelo mas capaz.

- Si sigues un paso y falla empiricamente, adapta.
- Si tienes evidencia de primera mano que contradice el consejo, adapta.
- Si hay conflicto entre tus hallazgos y el consejo, haz una **reconcile call**: "Encontre X, tu sugieres Y — que constraint rompe el tie?"

## Jerarquia advisor vs otros agentes

| Dimension | Quien decide |
|-----------|-------------|
| **QUE hacer** (estrategia, approach, prioridades) | Advisor gana |
| **COMO hacerlo** (implementacion, patrones, code structure) | Tech-planner / coder gana |
| **Conflicto en el QUE** | Advisor tiene prioridad — seguir su orientacion |
| **Conflicto en el COMO** | El agente ejecutor tiene prioridad — conoce el contexto local |

## Fallback

Si el advisor no esta disponible (error, timeout, limite alcanzado):
- **NO te bloquees**. Continua con tu mejor criterio.
- **NO reintentes** mas de 1 vez.
- Documenta en tu output que el advisor no estaba disponible.

## Integracion con Neurox

- **Al recibir consejo valioso**: considera guardar la decision en Neurox con `neurox_save(observation_type="decision")` para que futuras sesiones se beneficien.
- **Antes de consultar**: si Neurox tiene decisiones previas relevantes, mencionalo en tu pregunta al advisor para evitar re-litigar decisiones ya tomadas.
