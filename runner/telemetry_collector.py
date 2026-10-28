import time
import urllib.request
import urllib.parse
import json
from typing import Dict, Any, Optional

class TelemetryCollector:
    """
    Recolector de métricas de contenedor y host consultando la API HTTP de Prometheus.
    Captura CFS throttling, RSS Memory, Spill a disco y OOM kills.
    """

    def __init__(self, prometheus_url: str = "http://localhost:9090"):
        self.prometheus_url = prometheus_url.rstrip("/")

    def query(self, promql: str) -> Optional[float]:
        """Ejecuta una consulta instantánea a Prometheus y devuelve el primer valor float."""
        try:
            url = f"{self.prometheus_url}/api/v1/query?{urllib.parse.urlencode({'query': promql})}"
            req = urllib.request.Request(url, headers={"User-Agent": "BenchmarkRunner/1.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("status") == "success":
                    results = data.get("data", {}).get("result", [])
                    if results:
                        return float(results[0]["value"][1])
        except Exception as e:
            # En modo offline o si Prometheus no está disponible de inmediato
            pass
        return None

    def query_range_max(self, promql: str, start_epoch: float, end_epoch: float, step: int = 1) -> Optional[float]:
        """Consulta el valor máximo en un rango de tiempo."""
        try:
            params = {
                "query": promql,
                "start": str(start_epoch),
                "end": str(end_epoch),
                "step": str(step)
            }
            url = f"{self.prometheus_url}/api/v1/query_range?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(url, headers={"User-Agent": "BenchmarkRunner/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("status") == "success":
                    results = data.get("data", {}).get("result", [])
                    if results:
                        values = [float(val[1]) for val in results[0]["values"]]
                        return max(values) if values else None
        except Exception:
            pass
        return None

    def get_container_name(self, engine: str) -> str:
        return "benchmark_mongodb" if engine.lower() == "mongodb" else "benchmark_postgresql"

    def get_cfs_throttled_seconds(self, engine: str) -> float:
        """Obtiene container_cpu_cfs_throttled_seconds_total."""
        container = self.get_container_name(engine)
        val = self.query(f'container_cpu_cfs_throttled_seconds_total{{name="{container}"}}')
        return round(val, 4) if val is not None else 0.0

    def get_max_rss_mb(self, engine: str, start_epoch: float, end_epoch: float) -> float:
        """Obtiene el pico de container_memory_rss_bytes en MB durante el intervalo de medición."""
        container = self.get_container_name(engine)
        query = f'container_memory_rss_bytes{{name="{container}"}}'
        max_bytes = self.query_range_max(query, start_epoch, end_epoch, step=1)
        if max_bytes is None:
            # Fallback a consulta instantánea
            curr = self.query(query)
            max_bytes = curr if curr is not None else 0.0
        return round(max_bytes / (1024 * 1024), 2)

    def check_oom_event(self, engine: str) -> bool:
        """Verifica si el contenedor sufrió un OOM event."""
        container = self.get_container_name(engine)
        val = self.query(f'container_oom_events_total{{name="{container}"}}')
        return bool(val and val > 0)

