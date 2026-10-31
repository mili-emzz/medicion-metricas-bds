-- Q2: Massive Sort & Top-K (Estrés de Búfer/Memoria) — Dominio: AntFish
-- Tabla: analisis (data JSONB)
--
-- Lógica: Filtra registros de análisis a partir de 2026-01-01 y ordena
-- descendente por score_total (NO indexado), extrayendo el Top-1000.
-- Fuerza un sort stage en memoria o con volcado a disco según work_mem.
--
-- Variantes de estrés de memoria (inyectadas por benchmark_runner.py antes de ejecutar):
--   SET work_mem = '4MB';   → fuerza disk spill (temp_bytes > 0 en pg_stat_statements)
--   SET work_mem = '64MB';  → permite sort en memoria
--
-- Índice disponible: B-Tree sobre (data->>'fecha') — NO cubre score_total → sort sin índice
SELECT
    data->>'user_id'          AS user_id,
    data->>'dominio_principal' AS dominio_principal,
    (data->>'score_total')::numeric AS score_total,
    data->>'nivel_riesgo'     AS nivel_riesgo,
    data->>'tipo_entrada'     AS tipo_entrada,
    data->>'fecha'            AS fecha
FROM analisis
WHERE (data->>'fecha') >= '2026-01-01T00:00:00Z'
ORDER BY (data->>'score_total')::numeric DESC
LIMIT 1000;


