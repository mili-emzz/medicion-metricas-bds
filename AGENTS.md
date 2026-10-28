# Instrucciones Generales para el Agente

Este documento define las reglas de operación, restricciones y flujos de trabajo obligatorios para la ejecución del benchmark comparativo entre MongoDB y PostgreSQL (JSONB) bajo contención de recursos.

## 1. Directiva de Estado Inicial
Antes de ejecutar cualquier modificación en el código o iniciar pruebas, el agente **DEBE** leer el archivo JSON de contexto general del proyecto. Este archivo contiene el estado actual de avance y define qué pasos del plan y de la matriz de ejecución ya han sido completados. No asumas un estado inicial sin verificar este archivo.

## 2. Misión y Nota Crucial sobre el Dominio
*   **Propósito:** Automatizar, ejecutar y documentar un benchmark para medir latencia, QPS y huella de recursos bajo contención estricta (Docker cgroups v2).
*   **⚠️ AVISO SOBRE EL DOMINIO:** El dataset referenciado de 500,000 registros y el esquema documentado (`orders`, `customer`, `items`, etc.) son **EJEMPLOS ILUSTRATIVOS**. El dominio final de datos está sujeto a cambios. 
*   **Regla de diseño:** El agente debe construir los generadores (`synthetic_data_generator.py`) y el marco de consultas (`queries/`) de forma altamente modular y parametrizable, listos para adaptarse al dominio definitivo.

## 3. Stack Tecnológico y Monitoreo
El entorno debe construirse estrictamente sobre el siguiente stack:
*   **Contenedores:** Docker utilizando los límites de `cgroups v2`.
*   **Ejecución de carga:** `k6` o scripts multiproceso en `Python` (orquestados por `benchmark_runner`).
*   **Telemetría y Métricas:**
    *   **Prometheus:** Configurado con `scrape_interval: 1s`.
    *   **cAdvisor:** Obligatorio para capturar métricas del contenedor (`container_cpu_cfs_throttled_seconds_total`, `container_memory_rss_bytes`).
    *   **Node Exporter:** Para monitorear I/O de disco y estado del host.

## 4. Perfiles de Recursos (cgroups v2)
El archivo `docker-compose.yml` debe definir de forma parametrizada tres niveles de contención inmutables:
*   `PROFILE_A_BASELINE` (Sin contención): `4.0` CPUs, `4096m` Memoria, `mem_swappiness: 0`.
*   `PROFILE_B_MEDIUM` (Contención media): `2.0` CPUs, `2048m` Memoria, `mem_swappiness: 0`.
*   `PROFILE_C_SEVERE` (Contención severa): `1.0` CPUs, `1024m` Memoria, `mem_swappiness: 0`. *(Nota: Este perfil está diseñado intencionalmente para forzar el throttling CFS).*

## 5. Cargas de Trabajo (Workloads)
Independientemente del dominio final de datos, los patrones lógicos de las pruebas son fijos:
*   **Q1 (Saturación de CPU):** Operaciones equivalentes a desanidar arreglos (`$unwind` en Mongo / `jsonb_array_elements` en Postgres), filtrado condicional y agrupación multidimensional para agregaciones (suma, promedio).
*   **Q2 (Estrés de Memoria / Búfer):** Filtrado por rangos y ordenamiento masivo sobre campos no indexados para extraer un Top-K (ej. `LIMIT 1000`).
*   **Variantes obligatorias para Q2:**
    *   MongoDB: Ejecutar alternando `allowDiskUse: false` y `allowDiskUse: true`.
    *   PostgreSQL: Ejecutar alternando `work_mem = '4MB'` y `work_mem = '64MB'`.

## 6. Protocolo de Ejecución y Ciclo de Vida
El script `run_benchmarks.sh` es el orquestador principal y debe cumplir a rajatabla el siguiente ciclo:
*   **Tamaño de la Matriz:** 36 celdas únicas (2 motores × 3 perfiles × 2 consultas × 3 niveles de concurrencia: 1, 10, 50).
*   **Repeticiones:** Cada celda de la matriz debe ejecutarse **3 veces** consecutivas.
*   **Ciclo obligatorio por cada ejecución:**
    1.  **Flush de Caché (Host):** Ejecutar `sync; echo 3 > /proc/sys/vm/drop_caches`.
    2.  **Warmup:** 60 segundos de calentamiento.
    3.  **Medición:** 300 segundos de prueba activa recolectando telemetría.
    4.  **Cooldown:** 60 segundos de reposo de las bases de datos.

## 7. Esquema CSV de Mediciones (Inmutable)
Cada ejecución generará exactamente una (1) fila en el CSV de resultados.
*   **Regla de Oro:** **NO INVENTAR NI RENOMBRAR COLUMNAS.** El estudio posterior depende de que el esquema sea idéntico.
*   **Columnas exactas requeridas:**
    `timestamp_epoch, engine, profile, query_id, concurrency, run_number, throughput_qps, latency_p50_ms, latency_p95_ms, latency_p99_ms, cpu_throttled_seconds, max_rss_mb, disk_spill, status`
*   **Restricción del campo 'status':** Solo puede contener uno de estos cuatro valores: `ok`, `spill`, `oom` (Out Of Memory) o `error`. Todo evento de "disk_spill" o "oom_killed" debe quedar reflejado aquí cruzando datos con la telemetría.