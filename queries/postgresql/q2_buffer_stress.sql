-- Q2: Massive Sort & Top-K (Estrés de Búfer)
-- Filtra completadas desde 2026-01-01, ordena descendente por final_total y extrae Top-1000
-- Variantes de estrés de memoria: SET work_mem = '4MB' / SET work_mem = '64MB'
SELECT 
    data->>'order_id' AS order_id,
    data->'customer'->>'id' AS customer_id,
    (data->'payment'->>'final_total')::numeric AS final_total
FROM orders
WHERE data->'payment'->>'status' = 'completed'
  AND (data->>'timestamp')::timestamptz >= '2026-01-01 00:00:00Z'
ORDER BY (data->'payment'->>'final_total')::numeric DESC
LIMIT 1000;

