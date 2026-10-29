-- Inicialización de PostgreSQL para Benchmark AntFish JSONB
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

DROP TABLE IF EXISTS analisis CASCADE;

CREATE TABLE analisis (
    id UUID PRIMARY KEY,
    data JSONB NOT NULL
);

-- Índice B-Tree sobre campo temporal extraído de JSONB
CREATE INDEX IF NOT EXISTS idx_analisis_fecha 
ON analisis (((data->>'fecha')::timestamptz));
