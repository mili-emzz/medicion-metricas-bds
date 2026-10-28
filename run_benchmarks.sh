#!/bin/bash
# run_benchmarks.sh
# Orquestador del Benchmark MongoDB vs PostgreSQL JSONB bajo contención de recursos (cgroups v2)
# Cumple estrictamente con la Sección 6 del Playbook y las Reglas de AGENTS.md

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RESULTS_CSV="./results/benchmark_results.csv"
PROFILES_ENV="./config/profiles.env"

# Cargar variables de perfiles
if [ -f "$PROFILES_ENV" ]; then
    source "$PROFILES_ENV"
fi

ENGINES=("MongoDB" "PostgreSQL")
PROFILES=("PROFILE_A_BASELINE" "PROFILE_B_MEDIUM" "PROFILE_C_SEVERE")
QUERIES=("Q1" "Q2")
CONCURRENCIES=(1 10 50)
RUNS_PER_CELL=3

# Función para aplicar perfil de recursos cgroups v2
apply_resource_profile() {
    local profile=$1
    echo "[*] Aplicando límites cgroups v2 para: $profile"
    case $profile in
        "PROFILE_A_BASELINE")
            export BENCHMARK_CPUS=${PROFILE_A_CPUS:-4.0}
            export BENCHMARK_MEMORY=${PROFILE_A_MEMORY:-4096m}
            export BENCHMARK_MEM_SWAP=${PROFILE_A_MEM_SWAP:-4096m}
            ;;
        "PROFILE_B_MEDIUM")
            export BENCHMARK_CPUS=${PROFILE_B_CPUS:-2.0}
            export BENCHMARK_MEMORY=${PROFILE_B_MEMORY:-2048m}
            export BENCHMARK_MEM_SWAP=${PROFILE_B_MEM_SWAP:-2048m}
            ;;
        "PROFILE_C_SEVERE")
            export BENCHMARK_CPUS=${PROFILE_C_CPUS:-1.0}
            export BENCHMARK_MEMORY=${PROFILE_C_MEMORY:-1024m}
            export BENCHMARK_MEM_SWAP=${PROFILE_C_MEM_SWAP:-1024m}
            ;;
    esac

    # Reiniciar servicios con nuevos límites
    docker compose up -d --remove-orphans
    echo "[+] Contenedores ajustados a cpus=$BENCHMARK_CPUS, memory=$BENCHMARK_MEMORY, swap=$BENCHMARK_MEM_SWAP"
    sleep 5
}

# Paso 1: Flush de caché del host requerido por protocolo
flush_host_cache() {
    echo "[*] Ejecutando flush de caché de host (drop_caches)..."
    sync || true
    if [ "$(id -u)" -eq 0 ]; then
        echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true
    else
        sudo sync && sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches' 2>/dev/null || true
    fi
}

# Modo de ejecución (completo o piloto)
MODE=${1:-"all"}

if [ "$MODE" == "--pilot" ]; then
    echo "=========================================================="
    echo " MODO PILOTO: Ejecutando 1 celda de prueba y verificación "
    echo "=========================================================="
    apply_resource_profile "PROFILE_A_BASELINE"
    flush_host_cache
    python3 benchmark_runner.py \
        --engine "MongoDB" \
        --profile "PROFILE_A_BASELINE" \
        --query "Q1" \
        --concurrency 1 \
        --run-number 1 \
        --warmup 10 \
        --duration 30 \
        --cooldown 5
    echo "[+] Prueba piloto completada. Revise ./results/benchmark_results.csv"
    exit 0
fi

echo "=========================================================="
echo " INICIANDO MATRIZ DE BENCHMARK COMPLETA (36 celdas × 3)   "
echo "=========================================================="

total_cells=36
cell_counter=0

for engine in "${ENGINES[@]}"; do
    for profile in "${PROFILES[@]}"; do
        apply_resource_profile "$profile"

        for query in "${QUERIES[@]}"; do
            for concurrency in "${CONCURRENCIES[@]}"; do
                cell_counter=$((cell_counter + 1))
                echo ""
                echo ">>> Celda $cell_counter / $total_cells: Motor=$engine | Perfil=$profile | Query=$query | Concurrencia=$concurrency <<<"

                for run in $(seq 1 $RUNS_PER_CELL); do
                    echo "--- Corrida $run de $RUNS_PER_CELL ---"
                    
                    # 1. Flush de caché de host
                    flush_host_cache

                    # 2, 3 & 4. Warmup (60s), Medición (300s), Cooldown (60s)
                    python3 benchmark_runner.py \
                        --engine "$engine" \
                        --profile "$profile" \
                        --query "$query" \
                        --concurrency "$concurrency" \
                        --run-number "$run" \
                        --warmup 60 \
                        --duration 300 \
                        --cooldown 60
                done
            done
        done
    done
done

echo ""
echo "=========================================================="
echo "[+] MATRIZ DE BENCHMARK COMPLETADA EXITOSAMENTE."
echo "    Resultados consolidados en: $RESULTS_CSV"
echo "=========================================================="

