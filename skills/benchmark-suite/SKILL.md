---
name: benchmark-suite
description: Procedimientos y comandos para orquestar, monitorear y analizar el benchmark comparativo entre MongoDB y PostgreSQL JSONB bajo contención de recursos (Docker cgroups v2).
---

# Benchmark Suite: MongoDB vs PostgreSQL (JSONB)

Esta skill documenta el ciclo de vida y los comandos para la suite de evaluación de métricas y contención de recursos.

## 1. Generación de Datos Sintéticos

Para generar el dataset de 500,000 registros (modular y en streaming):
```bash
python synthetic_data_generator.py --records 500000 --output ./data/dataset.json --schema ecommerce
```

## 2. Inicialización del Entorno Docker y Telemetría

Levantar contenedores con perfil de contención (`PROFILE_A_BASELINE`, `PROFILE_B_MEDIUM`, `PROFILE_C_SEVERE`):
```bash
# Ejemplo con Baseline
export BENCHMARK_CPUS=4.0
export BENCHMARK_MEMORY=4096m
export BENCHMARK_MEM_SWAP=4096m
docker compose up -d
```

Servicios levantados:
- MongoDB en `:27017`
- PostgreSQL en `:5432`
- Prometheus en `:9090`
- cAdvisor en `:8080`
- Node Exporter en `:9100`

## 3. Carga Masiva de Datos

```bash
python scripts/load_dataset.py --file ./data/dataset.json --engine both
```

## 4. Ejecución de Pruebas

### Celda Piloto (Verificación rápida):
```bash
# En Bash
./run_benchmarks.sh --pilot

# O en PowerShell
.\scripts\run_benchmarks.ps1 -Pilot
```

### Celda Individual:
```bash
python benchmark_runner.py \
  --engine MongoDB \
  --profile PROFILE_A_BASELINE \
  --query Q1 \
  --concurrency 10 \
  --run-number 1 \
  --warmup 60 \
  --duration 300 \
  --cooldown 60
```

### Matriz Completa (36 celdas × 3 repeticiones):
```bash
./run_benchmarks.sh
```

## 5. Inspección de Resultados y Telemetría
El resultado se acumula en `./results/benchmark_results.csv` con el esquema inmutable:
`timestamp_epoch,engine,profile,query_id,concurrency,run_number,throughput_qps,latency_p50_ms,latency_p95_ms,latency_p99_ms,cpu_throttled_seconds,max_rss_mb,disk_spill,status`

