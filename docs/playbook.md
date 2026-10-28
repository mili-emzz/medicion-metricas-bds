      | Medici(cid:243)n |     |                    | de      | mØtricas | en           | bases           | documentales |       |     |
|       |                  |     | Contenci(cid:243)n | de      | CPU      | y memoria    | en agregaciones |              | JSON: |     |
|       |                  |     |                    | MongoDB | frente   | a PostgreSQL |                 | JSONB        |       |     |
Objetivo
Medirlatencia,rendimientoyhuelladerecursosalejecutaragregacionesJSONanidadasbajol(cid:237)mites
estrictosdeCPU(CFSthrottling)ymemoriaconDockercgroupsv2,comparandounmotordocumental
| con un motor | relacional |     | que   | almacena | documentos | en JSONB. |     |     |     |     |
| ------------ | ---------- | --- | ----- | -------- | ---------- | --------- | --- | --- | --- | --- |
| 1. Preguntas |            |     | sobre | las      | mØtricas   |           |     |     |     |     |
M1 (cid:190)C(cid:243)mo cambian la latencia P95 y P99 de las agregaciones sobre documentos anidados cuando se
| limita | de forma | estricta |     | la CPU | y la memoria? |     |     |     |     |     |
| ------ | -------- | -------- | --- | ------ | ------------- | --- | --- | --- | --- | --- |
M2 (cid:190)QuØ motor usa de forma mÆs e(cid:28)ciente los bu(cid:27)ers de ordenamiento y agrupamiento antes de volcar
| a disco | temporal | o   | fallar | por falta | de memoria | (OOM)? |     |     |     |     |
| ------- | -------- | --- | ------ | --------- | ---------- | ------ | --- | --- | --- | --- |
M3 (cid:190)CuÆl es la huella de CPU y memoria por cada 1000 documentos procesados en el motor documental
| frente     | al motor | con      | JSONB? |         |                 |     |     |                    |     |     |
| ---------- | -------- | -------- | ------ | ------- | --------------- | --- | --- | ------------------ | --- | --- |
| 2. Motores |          | objetivo |        |         |                 |     |     |                    |     |     |
| Motor      |          | Modelo   | de     | datos / | versi(cid:243)n |     |     | Indexaci(cid:243)n |     |     |
MongoDB Colecci(cid:243)n orders sin sharding; WiredTiger; ˝ndice simple en timestamp y order_id
latest-stable
PostgreSQL Tabla orders (id UUID PRIMARY KEY, data PK en id; B-Tree sobre timestamp extra(cid:237)do
|                   |     | JSONB); | latest-stable |     |         |           |      | del JSONB |                |     |
| ----------------- | --- | ------- | ------------- | --- | ------- | --------- | ---- | --------- | -------------- | --- |
| 3. Per(cid:28)les |     | de      | recursos      |     | (Docker | / cgroups |      | v2)       |                |     |
| ID                |     |         | Nombre        |     |         |           | CPUs | Memoria   | mem_swappiness |     |
PROFILE_A_BASELINE Sin contenci(cid:243)n (Baseline) 4,0 4096m 0
| PROFILE_B_MEDIUM |     |     | Contenci(cid:243)n |     | media |     | 2,0 | 2048m |     | 0   |
| ---------------- | --- | --- | ------------------ | --- | ----- | --- | --- | ----- | --- | --- |
PROFILE_C_SEVERE Contenci(cid:243)n severa (throttling activo) 1,0 1024m 0
| 4. Especi(cid:28)caci(cid:243)n |     |     |     | del dataset |     |     |     |     |     |     |
| ------------------------------- | --- | --- | --- | ----------- | --- | --- | --- | --- | --- | --- |
|                                 |     |     | •   |             | •   |     |     | •   |     |     |
Registros: 500000 formato JSON 3 niveles de anidamiento promedio 3 (cid:237)tems por registro.
Atributos:
1

IT2iD BasesdeDatosenlaNube
(cid:136)
order_id (UUID), timestamp (ISO-8601)
(cid:136)
customer (objeto: id, tier, segment, geo[country, state, city, zip, coordinates])
(cid:136)
items (arreglo de objetos: sku, category, brand, qty, price, tax_pct, discounts)
(cid:136)
payment (objeto: method, status, transaction_id, gateway_latency_ms, totals)
(cid:136)
metadata (objeto: channel, user_agent, session_id, flags)
5. Cargas de trabajo (consultas)
5.1. Q1 (cid:22) Unwind, Filter & Grouping (saturaci(cid:243)n de CPU)
Desanidar el arreglo de (cid:237)tems, (cid:28)ltrar price >50, calcular subtotal (qty * price) y agrupar suma-
toria y promedio por pa(cid:237)s y categor(cid:237)a.
MongoDB (pipeline).
[
{ "$unwind": "$items" },
{ "$match": { "items.price": { "$gt": 50 } } },
{
"$group": {
"_id": {
"country": "$customer.geo.country",
"category": "$items.category"
},
"total_revenue": { "$sum": { "$multiply": ["$items.qty", "$items.price"] } },
"avg_revenue": { "$avg": { "$multiply": ["$items.qty", "$items.price"] } },
"count": { "$sum": 1 }
}
}
]
PostgreSQL.
SELECT data->’customer’->’geo’->>’country’ AS country,
item->>’category’ AS category,
SUM((item->>’qty’)::numeric * (item->>’price’)::numeric) AS total_revenue,
AVG((item->>’qty’)::numeric * (item->>’price’)::numeric) AS avg_revenue,
COUNT(*) AS count
FROM orders, jsonb_array_elements(data->’items’) AS item
WHERE (item->>’price’)::numeric > 50
GROUP BY 1, 2;
5.2. Q2 (cid:22) Massive Sort & Top-K (estrØs de bu(cid:27)er)
Filtrar (cid:243)rdenes completadas en un rango de fechas, ordenar descendente por payment.final_total
y obtener el Top-1000 sin (cid:237)ndices previos en el total.
Variantes de estrØs de memoria.
MongoDB: allowDiskUse: false / allowDiskUse: true
PostgreSQL: SET work_mem = ’4MB’ / SET work_mem = ’64MB’
MongoDB (pipeline).
[
{ "$match": {
"payment.status": "completed",
"timestamp": { "$gte": "2026-01-01T00:00:00Z" }
} },
{ "$sort": { "payment.final_total": -1 } },
2

| IT2iD         |      |                |     |     |                        |     |     | BasesdeDatosenlaNube |     |
| ------------- | ---- | -------------- | --- | --- | ---------------------- | --- | --- | -------------------- | --- |
| { "$limit":   | 1000 | },             |     |     |                        |     |     |                      |     |
| { "$project": | {    |                |     |     |                        |     |     |                      |     |
| "order_id":   | 1,   | "customer.id": |     | 1,  | "payment.final_total": |     | 1   |                      |     |
} }
]
PostgreSQL.
| SELECT data->>’order_id’                   |     |     | AS order_id, |              |     |                |     |     |     |
| ------------------------------------------ | --- | --- | ------------ | ------------ | --- | -------------- | --- | --- | --- |
| data->’customer’->>’id’                    |     |     | AS           | customer_id, |     |                |     |     |     |
| (data->’payment’->>’final_total’)::numeric |     |     |              |              |     | AS final_total |     |     |     |
FROM orders
| WHERE data->’payment’->>’status’                    |     |     |     | = ’completed’ |                |            |     |     |     |
| --------------------------------------------------- | --- | --- | --- | ------------- | -------------- | ---------- | --- | --- | --- |
| AND (data->>’timestamp’)::timestamptz               |     |     |     |               | >= ’2026-01-01 | 00:00:00Z’ |     |     |     |
| ORDER BY (data->’payment’->>’final_total’)::numeric |     |     |     |               |                | DESC       |     |     |     |
LIMIT 1000;
| 6. Protocolo    |           | de                | ejecuci(cid:243)n |           |                             |     |     |     |     |
| --------------- | --------- | ----------------- | ----------------- | --------- | --------------------------- | --- | --- | --- | --- |
| Concurrencia:   |           | 1, 10,            | 50                | clientes. |                             |     |     |     |     |
| Repeticiones    |           | por escenario:    |                   | 3.        |                             |     |     |     |     |
| Ciclo de        | vida:     |                   |                   |           |                             |     |     |     |     |
| (cid:136) Flush | de cachØ: | sync;             |                   | echo      | 3 >/proc/sys/vm/drop_caches |     |     |     |     |
| (cid:136)       |           | •                 |                   |           | •                           |     |     |     |     |
| Warmup:         | 60s       | medici(cid:243)n: |                   | 300s      | cooldown:                   | 60s |     |     |     |
Mediciones totales: 36 celdas de la matriz (2 motores × 3 per(cid:28)les × 2 queries × 3 concurrencias);
| cada celda            | × 3 | repeticiones. |        |     |     |     |     |     |     |
| --------------------- | --- | ------------- | ------ | --- | --- | --- | --- | --- | --- |
| 7. Telemetr(cid:237)a |     |               | y KPIs |     |     |     |     |     |     |
Stack.
| cAdvisor:      | mØtricas |                  | de contenedor |     | (cgroups   | v2).   |        |     |     |
| -------------- | -------- | ---------------- | ------------- | --- | ---------- | ------ | ------ | --- | --- |
| Node Exporter: |          | mØtricas         |               | de  | host (I/O, | disco, | swap). |     |     |
| Prometheus:    |          | scrape_interval: |               |     | 1s.        |        |        |     |     |
Indicadores.
| KPI                                       |     |     |     |     |     |     |     | Unidad    | Tipo            |
| ----------------------------------------- | --- | --- | --- | --- | --- | --- | --- | --------- | --------------- |
| throughput_qps                            |     |     |     |     |     |     |     | queries/s | Performance     |
| latency_p50_ms                            |     |     |     |     |     |     |     | ms        | Performance     |
| latency_p95_ms                            |     |     |     |     |     |     |     | ms        | Performance     |
| latency_p99_ms                            |     |     |     |     |     |     |     | ms        | Performance     |
| container_cpu_cfs_throttled_seconds_total |     |     |     |     |     |     |     | s         | OS / Contention |
| container_memory_rss_bytes                |     |     |     |     |     |     |     | bytes     | OS / Memory     |
disk_spill_detected
|            |     |     |     |     |     |     |     | boolean | Engine / Internal |
| ---------- | --- | --- | --- | --- | --- | --- | --- | ------- | ----------------- |
| oom_killed |     |     |     |     |     |     |     | boolean | Stability         |
3

IT2iD BasesdeDatosenlaNube
8. Entregables
8.1. Repositorio de c(cid:243)digo
docker-compose.yml con per(cid:28)les de recursos parametrizados
synthetic_data_generator.py (dataset 500k)
benchmark_runner (scripts k6 o Python multiproceso)
queries/ (agregaciones MongoDB y SQL PostgreSQL)
run_benchmarks.sh (automatizaci(cid:243)n de la matriz de mediciones)
8.2. Esquema CSV de mediciones
timestamp_epoch, engine, profile, query_id, concurrency, run_number,
throughput_qps, latency_p50_ms, latency_p95_ms, latency_p99_ms,
cpu_throttled_seconds, max_rss_mb, disk_spill, status
8.3. Secciones del reporte de mØtricas
1. Especi(cid:28)caciones del host y del entorno Docker
2. MØtodo de medici(cid:243)n y veri(cid:28)caci(cid:243)n del baseline
3. Resultados consolidados (throughput, P95/P99, tiempo de throttling)
4. AnÆlisis grÆ(cid:28)co (P99 vs concurrencia, throttling vs QPS, curva RSS)
5. Planes de ejecuci(cid:243)n (explain executionStats frente a EXPLAIN ANALYZE BUFFERS)
6. Interpretaci(cid:243)n: l(cid:237)mites de memoria, volcado a disco y throttling de cgroups
7. Recomendaciones tØcnicas para despliegues documentales en la nube
Actividaddemedici(cid:243)n•BasesdeDatosenlaNube•IT2iD•2026.
4
