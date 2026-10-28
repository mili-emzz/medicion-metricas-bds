#!/usr/bin/env python3
"""
benchmark_runner.py
Orquestador de ejecución de carga concurrente y telemetría de contenedor.
Cumple con las Secciones 6, 7 y 8.2 del Playbook y las Reglas de AGENTS.md.
"""

import os
import sys
import time
import argparse
import threading
from typing import List
from runner.load_generator import worker_task, calculate_percentiles
from runner.telemetry_collector import TelemetryCollector

CSV_HEADER = "timestamp_epoch,engine,profile,query_id,concurrency,run_number,throughput_qps,latency_p50_ms,latency_p95_ms,latency_p99_ms,cpu_throttled_seconds,max_rss_mb,disk_spill,status\n"

def ensure_csv_exists(csv_path: str):
    os.makedirs(os.path.dirname(os.path.abspath(csv_path)), exist_ok=True)
    if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write(CSV_HEADER)

def main():
    parser = argparse.ArgumentParser(description="Runner de Benchmark y Medición de Métricas")
    parser.add_argument("--engine", type=str, required=True, choices=["mongodb", "postgresql", "MongoDB", "PostgreSQL"])
    parser.add_argument("--profile", type=str, required=True, choices=["PROFILE_A_BASELINE", "PROFILE_B_MEDIUM", "PROFILE_C_SEVERE"])
    parser.add_argument("--query", type=str, required=True, choices=["Q1", "Q2", "Q1_CPU_Saturation", "Q2_Buffer_Stress"])
    parser.add_argument("--concurrency", type=int, required=True, choices=[1, 10, 50])
    parser.add_argument("--run-number", type=int, required=True, help="Número de corrida (1, 2 o 3)")
    parser.add_argument("--warmup", type=int, default=60, help="Duración del warmup en segundos (default: 60)")
    parser.add_argument("--duration", type=int, default=300, help="Duración de medición en segundos (default: 300)")
    parser.add_argument("--cooldown", type=int, default=60, help="Duración del cooldown en segundos (default: 60)")
    parser.add_argument("--variant", type=str, default="", help="Variante de búfer: allowDiskUse (true/false) o work_mem (4MB/64MB)")
    parser.add_argument("--csv-path", type=str, default="./results/benchmark_results.csv", help="Ruta del CSV inmutable")
    parser.add_argument("--prom-url", type=str, default="http://localhost:9090", help="URL de Prometheus")

    args = parser.parse_args()

    engine_norm = "MongoDB" if args.engine.lower() == "mongodb" else "PostgreSQL"
    query_id_norm = "Q1" if "1" in args.query else "Q2"

    variant_param = None
    if query_id_norm == "Q2":
        if engine_norm == "MongoDB":
            variant_param = (args.variant.lower() == "true") if args.variant else False
        else:
            variant_param = args.variant if args.variant else "4MB"

    print("=" * 70)
    print(f"[*] INICIANDO CELDA DE BENCHMARK")
    print(f"    Motor:        {engine_norm}")
    print(f"    Perfil:       {args.profile}")
    print(f"    Query:        {query_id_norm} (Variante: {variant_param})")
    print(f"    Concurrencia: {args.concurrency} clientes")
    print(f"    Repetición:   {args.run_number} de 3")
    print(f"    Ciclo:        Warmup={args.warmup}s | Medición={args.duration}s | Cooldown={args.cooldown}s")
    print("=" * 70)

    telemetry = TelemetryCollector(prometheus_url=args.prom_url)

    # 1. Warmup
    if args.warmup > 0:
        print(f"\n[1/3] Iniciando Warmup ({args.warmup}s)...")
        stop_warmup = threading.Event()
        warm_threads = []
        dummy_latencies, dummy_spill, dummy_errors = [], [], []

        for _ in range(args.concurrency):
            t = threading.Thread(
                target=worker_task,
                args=(engine_norm, query_id_norm, variant_param, stop_warmup, dummy_latencies, dummy_spill, dummy_errors)
            )
            t.daemon = True
            t.start()
            warm_threads.append(t)

        time.sleep(args.warmup)
        stop_warmup.set()
        for t in warm_threads:
            t.join(timeout=5)
        print(f"[+] Warmup finalizado.")

    # 2. Medición activa
    print(f"\n[2/3] Iniciando Medición activa ({args.duration}s)...")
    start_throttled = telemetry.get_cfs_throttled_seconds(engine_norm)
    start_epoch = time.time()
    measurement_latencies: List[float] = []
    spill_flags: List[bool] = []
    error_flags: List[bool] = []

    stop_measurement = threading.Event()
    threads = []
    for _ in range(args.concurrency):
        t = threading.Thread(
            target=worker_task,
            args=(engine_norm, query_id_norm, variant_param, stop_measurement, measurement_latencies, spill_flags, error_flags)
        )
        t.daemon = True
        t.start()
        threads.append(t)

    # Monitoreo de progreso
    time_limit = start_epoch + args.duration
    while time.time() < time_limit:
        remaining = int(time_limit - time.time())
        current_count = len(measurement_latencies)
        print(f"    -> Tiempo restante: {remaining}s | Consultas ejecutadas: {current_count}...", end="\r")
        time.sleep(1)

    stop_measurement.set()
    for t in threads:
        t.join(timeout=10)

    end_epoch = time.time()
    actual_duration = max(end_epoch - start_epoch, 1.0)
    end_throttled = telemetry.get_cfs_throttled_seconds(engine_norm)

    print(f"\n[+] Medición finalizada. Total de consultas: {len(measurement_latencies)}")

    # 3. Cooldown
    if args.cooldown > 0:
        print(f"\n[3/3] Iniciando Cooldown ({args.cooldown}s)...")
        time.sleep(args.cooldown)
        print(f"[+] Cooldown finalizado.")

    # 4. Cálculo de Métricas y Telemetría
    throughput_qps = round(len(measurement_latencies) / actual_duration, 2)
    p50, p95, p99 = calculate_percentiles(measurement_latencies)
    cpu_throttled = max(0.0, round(end_throttled - start_throttled, 4))
    max_rss_mb = telemetry.get_max_rss_mb(engine_norm, start_epoch, end_epoch)
    disk_spill = (len(spill_flags) > 0)

    # Determinación de status: 'ok', 'spill', 'oom', 'error'
    oom_killed = telemetry.check_oom_event(engine_norm)
    if oom_killed:
        status = "oom"
    elif len(error_flags) > 0 and len(measurement_latencies) == 0:
        status = "error"
    elif disk_spill:
        status = "spill"
    else:
        status = "ok"

    # 5. Persistencia en CSV inmutable
    ensure_csv_exists(args.csv_path)
    csv_row = (
        f"{int(start_epoch)},{engine_norm},{args.profile},{query_id_norm},"
        f"{args.concurrency},{args.run_number},{throughput_qps},{p50},{p95},{p99},"
        f"{cpu_throttled},{max_rss_mb},{str(disk_spill).lower()},{status}\n"
    )

    with open(args.csv_path, "a", encoding="utf-8") as f:
        f.write(csv_row)

    print("\n" + "=" * 70)
    print(f"[*] RESULTADO REGISTRADO EN CSV:")
    print(f"    Throughput (QPS):      {throughput_qps}")
    print(f"    Latencia P50 / P95 / P99: {p50} ms / {p95} ms / {p99} ms")
    print(f"    CFS Throttled Seconds: {cpu_throttled} s")
    print(f"    Max RSS:               {max_rss_mb} MB")
    print(f"    Disk Spill Detected:   {disk_spill}")
    print(f"    Status:                {status}")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()

