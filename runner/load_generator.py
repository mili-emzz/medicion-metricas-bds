import time
import math
import concurrent.futures
from typing import List, Dict, Any, Tuple
from runner.client_mongo import MongoClientExecutor
from runner.client_postgres import PostgresClientExecutor

def worker_task(
    engine: str,
    query_id: str,
    variant_param: Any,
    stop_event: Any,
    latencies: List[float],
    spill_flags: List[bool],
    error_flags: List[bool]
):
    """Tarea ejecutada por cada worker concurrente en el ciclo de carga."""
    client = None
    try:
        if engine.lower() == "mongodb":
            client = MongoClientExecutor()
            client.connect()
            while not stop_event.is_set():
                try:
                    if query_id == "Q1":
                        lat = client.execute_q1()
                        latencies.append(lat)
                    else:
                        allow_disk = bool(variant_param)
                        lat, spill = client.execute_q2(allow_disk_use=allow_disk)
                        latencies.append(lat)
                        if spill:
                            spill_flags.append(True)
                except Exception as ex:
                    error_flags.append(True)
                    time.sleep(0.1)
        else:
            client = PostgresClientExecutor()
            client.connect()
            while not stop_event.is_set():
                try:
                    if query_id == "Q1":
                        lat = client.execute_q1()
                        latencies.append(lat)
                    else:
                        work_mem = str(variant_param or "4MB")
                        lat, spill = client.execute_q2(work_mem=work_mem)
                        latencies.append(lat)
                        if spill:
                            spill_flags.append(True)
                except Exception as ex:
                    error_flags.append(True)
                    time.sleep(0.1)
    finally:
        if client:
            client.close()

def calculate_percentiles(values: List[float]) -> Tuple[float, float, float]:
    """Calcula P50, P95 y P99 de una lista de latencias en ms."""
    if not values:
        return 0.0, 0.0, 0.0
    sorted_v = sorted(values)
    n = len(sorted_v)

    def p(k: float) -> float:
        idx = min(math.ceil((k / 100.0) * n) - 1, n - 1)
        return round(sorted_v[max(0, idx)], 2)

    return p(50), p(95), p(99)

