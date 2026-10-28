|     | Medici(cid:243)n | de mØtricas         | en bases | documentales            |     |
| --- | ---------------- | ------------------- | -------- | ----------------------- | --- |
|     | MongoDB          | frente a PostgreSQL | JSONB    | bajo contenci(cid:243)n |     |
Ingenier(cid:237)aenTecnolog(cid:237)asdelaInformaci(cid:243)neInnovaci(cid:243)nDigital
IT2iD
|     |     | UniversidadPolitØcnicadeChiapas |     | • IT2iD |     |
| --- | --- | ------------------------------- | --- | ------- | --- |
2026
| IT2iD | UniversidadPolitØcnicadeChiapas |     | • IT2iD | | 2026 |     | 1/13 |
| --------------------------------------- | --- | ------- | ------ | --- | ---- |

|          |              |     |     | Recorrido de la sesi(cid:243)n |     |
| -------- | ------------ | --- | --- | ------------------------------ | --- |
| Pregunta | gu(cid:237)a |     |     |                                |     |
(cid:190)QuØ hay que medir, c(cid:243)mo se ejecuta y quØ evidencia entregar para que un estudio posterior (y
| un revisor) | puedan reproducir | y cuestionar | el resultado? |          |     |
| ----------- | ----------------- | ------------ | ------------- | -------- | --- |
|             | QuØ               | C(cid:243)mo | Ejemplo       | QuØ      |     |
|             | medimos           | secorre      | decelda       | entregar |     |
Al salir
Entender la matriz Mongo/Postgres × per(cid:28)les × Q1/Q2 × concurrencia, y el CSV/reporte que
| alimenta | un estudio.                     |         |        |     |      |
| -------- | ------------------------------- | ------- | ------ | --- | ---- |
| IT2iD |  | UniversidadPolitØcnicadeChiapas | • IT2iD | | 2026 |     | 2/13 |

|     |     |     |     | QuØ | van a | hacer (en | una frase) |     |
| --- | --- | --- | --- | --- | ----- | --------- | ---------- | --- |
Actividad
|          | MongoDB |              | PostgreSQL | JSONB |             |              |      |     |
| -------- | ------- | ------------ | ---------- | ----- | ----------- | ------------ | ---- | --- |
| Comparar |         | (documentos) | y          |       | al ejecutar | agregaciones | JSON |     |
anidadas, con l(cid:237)mites estrictos de CPU y memoria (Docker cgroups v2).
Dataset: 500000 (cid:243)rdenes con ∼3 niveles de anidamiento.
| Dos   | cargas: Q1                        | (unwind + | group) y Q2 (sort | + Top-K). |     |     |     |     |
| ----- | --------------------------------- | --------- | ----------------- | --------- | --- | --- | --- | --- |
| Tres  | per(cid:28)les: baseline          | / media   | / severa.         |           |     |     |     |     |
| Tres  | concurrencias:                    | 1, 10,    | 50.               |           |     |     |     |     |
| No es | (cid:16)probar si arranca(cid:17) |           |                   |           |     |     |     |     |
|       |                                   | mØtricas  | numeradas         |           |     |     |     |     |
Cada corrida produce (latencia, QPS, throttling, RSS, spill, OOM) en un
CSV homogØneo.
| IT2iD | | UniversidadPolitØcnicadeChiapas |     | • IT2iD | 2026 |     |     |     |     | 3/13 |
| ------- | ------------------------------- | --- | -------------- | --- | --- | --- | --- | ---- |

|     |     |     | Preguntas | que responden | las mØtricas |     |
| --- | --- | --- | --------- | ------------- | ------------ | --- |
M1 (cid:190)C(cid:243)mo cambian P95/P99 al limitar CPU y memoria?
M2 (cid:190)QuØ motor gestiona mejor bu(cid:27)ers antes de spill o OOM?
M3
(cid:190)CuÆl es la huella de CPU/memoria por cada 1000 documentos?
| Para el equipo                          |             |               | Para el                 | estudio          |                |      |
| --------------------------------------- | ----------- | ------------- | ----------------------- | ---------------- | -------------- | ---- |
|                                         |             |               | Son las                 | mismas preguntas | que un revisor |      |
| Gu(cid:237)an quØ celdas                | priorizar y | quØ contraste |                         |                  |                |      |
| reportar.                               |             |               | pedirÆ justi(cid:28)car | con datos.       |                |      |
| IT2iD | UniversidadPolitØcnicadeChiapas |             | • IT2iD       | | 2026                  |                  |                | 4/13 |

|     | Per(cid:28)les | de recursos | (ejemplo | operativo) |
| --- | -------------- | ----------- | -------- | ---------- |
QuØ anotar siempre
profile, l(cid:237)mites Docker reales, versi(cid:243)n del motor y si hubo spill/OOM. Sin eso, la celda no
sirve para el estudio.
| IT2iD | UniversidadPolitØcnicadeChiapas | • IT2iD | 2026 |     |     | 5/13 |
| --------------------------------------- | -------------- | --- | --- | ---- |

|     |     |     |     | Ejemplo | Q1: saturaci(cid:243)n | de CPU |
| --- | --- | --- | --- | ------- | ---------------------- | ------ |
Desanidar items, (cid:28)ltrar price > 50, agrupar por pa(cid:237)s y categor(cid:237)a.
| MongoDB    | (idea)                          |            |                       | PostgreSQL           | (idea)      |      |
| ---------- | ------------------------------- | ---------- | --------------------- | -------------------- | ----------- | ---- |
| $unwind    | items                           |            |                       | jsonb_array_elements |             |      |
| $match     | price > 50                      |            |                       | + WHERE              | price > 50  |      |
| $group     | by country,                     |            |                       | + GROUP              | BY country, |      |
|            | category                        |            |                       |                      | category    |      |
| MØtrica    | a mirar                         |            |                       |                      |             |      |
| Throughput | y P95/P99;                      | en severa, | tiempo CFS throttled. |                      |             |      |
| IT2iD |    | UniversidadPolitØcnicadeChiapas |            | • IT2iD |             | 2026                 |             | 6/13 |

|                      |              |                           |     | Ejemplo   | Q2: estrØs | de bu(cid:27)er | (Top-K) |
| -------------------- | ------------ | ------------------------- | --- | --------- | ---------- | --------------- | ------- |
| Filtrar completadas, |              | ordenar por final_total,  |     | Top-1000. |            |                 |         |
| Mongo:               | allowDiskUse | false/true.               |     |           |            |                 |         |
| Postgres:            | work_mem     | 4MB / 64MB.               |     |           |            |                 |         |
| Ejemplo              | de lectura   | ((cid:28)cticio, formato) |     |           |            |                 |         |
Per(cid:28)l C, concurrencia 50, allowDiskUse:false ⇒ spill o fallo.
| Misma celda | con disco | permitido ⇒ | termina, pero | baja QPS. |     |     |     |
| ----------- | --------- | ----------- | ------------- | --------- | --- | --- | --- |
| Para el     | revisor   |             |               |           |     |     |     |
ambas
| Hay que | reportar                        | variantes: | sin spill y con | spill (o OOM). |     |     |      |
| ------- | ------------------------------- | ---------- | --------------- | -------------- | --- | --- | ---- |
| IT2iD | | UniversidadPolitØcnicadeChiapas |            | • IT2iD         | | 2026         |     |     | 7/13 |

Una celda de la matriz (quØ es (cid:16)una medici(cid:243)n(cid:17))
|     | Motor | Per(cid:28)l | Query Concurrencia |     |
| --- | ----- | ------------ | ------------------ | --- |
×3repeticiones
| Matriz: 2×3×2×3 | = 36 celdas; | cada una | × 3 repeticiones. |     |
| --------------- | ------------ | -------- | ----------------- | --- |
Ciclo: (cid:29)ush cachØ → warmup 60s → medici(cid:243)n 300s → cooldown 60s.
| Producto m(cid:237)nimo por | celda |     |     |     |
| --------------------------- | ----- | --- | --- | --- |
Una (cid:28)la CSV por repetici(cid:243)n + nota de estado (ok/spill/oom/error).
| IT2iD | UniversidadPolitØcnicadeChiapas |     | • IT2iD | 2026 |     | 8/13 |
| --------------------------------------- | --- | -------------- | --- | ---- |

|     | Ejemplo | de (cid:28)la CSV | (formato | esperado) |
| --- | ------- | ----------------- | -------- | --------- |
Sincolumnasinventadasnirenombradas:elestudioposteriorconcatenatodoslosCSV.
| IT2iD | UniversidadPolitØcnicadeChiapas | • IT2iD | 2026 |     |     | 9/13 |
| --------------------------------------- | -------------- | --- | --- | ---- |

|                  |               |     |           | QuØ         | van a entregar   |     |
| ---------------- | ------------- | --- | --------- | ----------- | ---------------- | --- |
| C(cid:243)digo / | scripts       |     | Evidencia |             |                  |     |
| docker-compose   | parametrizado |     | CSV con   | el esquema  | (cid:28)jo       |     |
| generador        | 500k          |     | Capturas  | o logs de   | spill/OOM        |     |
| runner           | (k6 o Python) |     | Reporte   | de mØtricas | (7 secciones del |     |
playbook)
| queries/ | Mongo + SQL |     |     |     |     |     |
| -------- | ----------- | --- | --- | --- | --- | --- |
run_benchmarks.sh
| Criterio de | utilidad |     |     |     |     |     |
| ----------- | -------- | --- | --- | --- | --- | --- |
Si otro equipo no puede reejecutar o un revisor no puede cuestionar P99/throttling con sus
| datos, la                               | entrega estÆ incompleta. |                |     |     |     |       |
| --------------------------------------- | ------------------------ | -------------- | --- | --- | --- | ----- |
| IT2iD | UniversidadPolitØcnicadeChiapas |                          | • IT2iD | 2026 |     |     |     | 10/13 |

|     |     |     | QuØ preguntarÆ | un revisor | (antic(cid:237)pense) |     |
| --- | --- | --- | -------------- | ---------- | --------------------- | --- |
1. (cid:190)El baseline es comparable (mismo dataset, mismas queries)?
| 2. (cid:190)Las  | latencias son | P50/P95/P99           | o solo promedios? |     |     |     |
| ---------------- | ------------- | --------------------- | ----------------- | --- | --- | --- |
| 3. (cid:190)Hubo | throttling    | CFS? (cid:190)CuÆntos | segundos?         |     |     |     |
4. (cid:190)Spill a disco o OOM? (cid:190)En quØ per(cid:28)l y concurrencia?
5. (cid:190)CuÆntas repeticiones y c(cid:243)mo se resume (media / mediana)?
| 6. (cid:190)El plan | de ejecuci(cid:243)n | respalda | el cuello de botella? |     |     |     |
| ------------------- | -------------------- | -------- | --------------------- | --- | --- | --- |
| Su reporte          | debe contestarlas    | con      | tablas/(cid:28)guras  |     |     |     |
No con opiniones: con (cid:28)las del CSV y un plan explain / EXPLAIN ANALYZE.
| IT2iD | | UniversidadPolitØcnicadeChiapas |     | • IT2iD | 2026 |     |     | 11/13 |
| ------- | ------------------------------- | --- | -------------- | --- | --- | ----- |

|     |     | Secciones | del reporte | (checklist) |
| --- | --- | --------- | ----------- | ----------- |
Puente
El PDF playbook.pdf es la especi(cid:28)caci(cid:243)n; estas diapos (cid:28)jan el contrato de entrega.
| IT2iD | UniversidadPolitØcnicadeChiapas | • IT2iD | 2026 |     |     | 12/13 |
| --------------------------------------- | -------------- | --- | --- | ----- |

Cierre
| Miden bajo | contenci(cid:243)n, | no solo | (cid:16)en mÆquina libre(cid:17). |     |
| ---------- | ------------------- | ------- | --------------------------------- | --- |
Cada celda → (cid:28)las CSV + estado + (si aplica) spill/OOM.
El entregable alimenta un estudio y resiste preguntas de revisor.
| Siguiente | paso en laboratorio |     |     |     |
| --------- | ------------------- | --- | --- | --- |
Levantar per(cid:28)les A/B/C, correr una celda piloto (1 motor × 1 query × 1 concurrencia) y
| validar el CSV                          | antes de | la matriz completa. |                |       |
| --------------------------------------- | -------- | ------------------- | -------------- | ----- |
| IT2iD | UniversidadPolitØcnicadeChiapas |          |                     | • IT2iD | 2026 | 13/13 |
