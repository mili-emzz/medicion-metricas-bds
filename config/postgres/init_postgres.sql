-- Inicialización de PostgreSQL para Benchmark JSONB
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

DROP TABLE IF EXISTS orders CASCADE;

CREATE TABLE orders (
    id UUID PRIMARY KEY,
    data JSONB NOT NULL
);

-- Índice B-Tree sobre timestamp extraído de JSONB especificado en el Playbook (Sección 2)
CREATE INDEX IF NOT EXISTS idx_orders_timestamp 
ON orders (((data->>'timestamp')::timestamptz));

