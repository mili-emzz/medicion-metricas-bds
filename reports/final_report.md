# Reporte de Métricas: MongoDB frente a PostgreSQL JSONB bajo Contención

**Institución:** Universidad Politécnica de Chiapas (UP)  
**Programa:** Ingeniería en Tecnologías de la Información e Innovación Digital (IT2iD)  
**Materia:** Bases de Datos en la Nube (2026)  
**Actividad:** Medición de métricas en bases documentales bajo contención estricta (cgroups v2)  

---

## 1. Especificaciones del Host y del Entorno Docker
- **Sistema Operativo Host:** 
- **Procesador (CPU):** 
- **Memoria RAM Total Host:** 
- **Versión de Docker & Docker Compose:** 
- **Configuración cgroups:** cgroups v2 (`/sys/fs/cgroup`)
- **Versiones de Motores:**
  - MongoDB: `mongo:latest` (WiredTiger Storage Engine)
  - PostgreSQL: `postgres:16` (JSONB)
- **Perfiles de Recursos Asignados:**
  - `PROFILE_A_BASELINE`: 4.0 CPUs, 4096 MB RAM, mem_swappiness: 0.
  - `PROFILE_B_MEDIUM`: 2.0 CPUs, 2048 MB RAM, mem_swappiness: 0.
  - `PROFILE_C_SEVERE`: 1.0 CPUs, 1024 MB RAM, mem_swappiness: 0 (Throttling activo).

---

## 2. Método de Medición y Verificación del Baseline
- **Dataset:** 500,000 documentos sintéticos (~3 niveles de anidamiento, ~3 ítems por registro).
- **Protocolo por Celda (36 celdas × 3 repeticiones = 108 corridas):**
  1. Flush de caché del kernel: `sync; echo 3 > /proc/sys/vm/drop_caches`
  2. Warmup: 60 segundos.
  3. Medición activa: 300 segundos recolectando métricas cada 1s desde cAdvisor y Prometheus.
  4. Cooldown: 60 segundos.
- **Herramientas de Telemetría:**
  - Prometheus (`scrape_interval: 1s`)
  - cAdvisor (`container_cpu_cfs_throttled_seconds_total`, `container_memory_rss_bytes`)
  - Node Exporter

---

## 3. Resultados Consolidados
*Tabla generada a partir de `results/benchmark_results.csv`.*

| Motor | Perfil | Query | Concurrencia | QPS Promedio | Latencia P50 (ms) | Latencia P95 (ms) | Latencia P99 (ms) | Throttling (s) | Max RSS (MB) | Disk Spill | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| MongoDB | Baseline | Q1 | 1 | | | | | | | | |
| MongoDB | Baseline | Q1 | 10 | | | | | | | | |
| MongoDB | Baseline | Q1 | 50 | | | | | | | | |
| PostgreSQL | Baseline | Q1 | 1 | | | | | | | | |
| PostgreSQL | Baseline | Q1 | 10 | | | | | | | | |
| PostgreSQL | Baseline | Q1 | 50 | | | | | | | | |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

---

## 4. Análisis Gráfico
- **4.1. Latencia P99 vs Concurrencia (1, 10, 50):**  
  *Impacto de la saturación de conexiones y contención sobre la cola de peticiones.*
- **4.2. CFS Throttling vs Throughput (QPS):**  
  *Pérdida de rendimiento en PROFILE_C_SEVERE ante la penalización del scheduler de Linux.*
- **4.3. Curva de Memoria RSS y Volcado:**  
  *Evolución del consumo de memoria en Q2 con y sin derrame a disco.*

---

## 5. Planes de Ejecución
- **MongoDB (`explain("executionStats")`):**
  - Análisis de `COLLSCAN` vs `IXSCAN`.
  - Etapas de pipeline: `$unwind` memory buffer y `$sort` con `allowDiskUse`.
- **PostgreSQL (`EXPLAIN (ANALYZE, BUFFERS)`):**
  - Desanidamiento con `jsonb_array_elements`.
  - Operaciones `Sort Method: external merge Disk` vs `quicksort Memory` según `work_mem`.

---

## 6. Interpretación Técnica
- **Límites de memoria y OOM Killer:**
- **Volcado a disco (Disk Spill):**
- **Efecto del Throttling CFS de cgroups v2 en consultas CPU-bound:**

---

## 7. Recomendaciones Técnicas para Despliegues en la Nube
- **Dimensionamiento de vCPU y memoria para cargas JSONB / NoSQL:**
- **Sintonización de buffers (`work_mem`, WiredTiger Cache):**
- **Mitigación de "noisy neighbors" y estrangulamiento de CPU en entornos multi-tenant:**

