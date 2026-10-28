-- Q1: Unwind, Filter & Grouping (Saturación de CPU) — Dominio: AntFish
-- Tabla: analisis (data JSONB)
--
-- Lógica: Desanida el arreglo JSONB 'urls_extraidas' de cada fila mediante
-- jsonb_array_elements(), filtra score_total >= 50 (nivel alto/crítico) y
-- agrupa por tipo_entrada, nivel_riesgo y dominio calculando conteos y
-- promedios. Operación equivalente a Q1 MongoDB.
--
-- Índice disponible: B-Tree sobre (data->>'fecha') — NO cubre score_total → full scan
-- Variante de memoria: controlada externamente con SET work_mem = '4MB' | '64MB'
SELECT
    data->>'tipo_entrada'                         AS tipo_entrada,
    data->>'nivel_riesgo'                         AS nivel_riesgo,
    url_obj->>'dominio'                           AS dominio,
    COUNT(*)                                      AS total_amenazas,
    AVG((data->>'score_total')::numeric)          AS promedio_score,
    AVG((data->'puntos_por_capa'->>'apis')::numeric)   AS promedio_puntos_apis,
    AVG((data->'puntos_por_capa'->>'url')::numeric)    AS promedio_puntos_url,
    AVG((data->'puntos_por_capa'->>'texto')::numeric)  AS promedio_puntos_texto
FROM analisis,
     jsonb_array_elements(data->'urls_extraidas') AS url_obj
WHERE (data->>'score_total')::numeric >= 50
GROUP BY 1, 2, 3;


