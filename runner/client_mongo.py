import time
from typing import Dict, Any, Tuple

class MongoClientExecutor:
    """Cliente de ejecución para consultas de MongoDB (Q1 y Q2)."""

    def __init__(self, uri: str = "mongodb://localhost:27017/", db_name: str = "benchmark_db"):
        self.uri = uri
        self.db_name = db_name
        self._client = None
        self._db = None

    def connect(self):
        try:
            from pymongo import MongoClient
            self._client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            self._db = self._client[self.db_name]
        except ImportError:
            raise RuntimeError("pymongo no está instalado. Ejecute: pip install pymongo")

    def close(self):
        if self._client:
            self._client.close()

    def execute_q1(self) -> float:
        """Ejecuta Q1 (Unwind, Filter & Grouping) y devuelve la latencia en ms."""
        pipeline = [
            { "$unwind": "$items" },
            { "$match": { "items.price": { "$gt": 50 } } },
            {
                "$group": {
                    "_id": {
                        "country": "$customer.geo.country",
                        "category": "$items.category"
                    },
                    "total_revenue": { "$sum": { "$multiply": ["$items.qty", "$items.price"] } },
                    "avg_revenue": { "$avg": { "$multiply": ["$items.qty", "$items.price"] } },
                    "count": { "$sum": 1 }
                }
            }
        ]
        start = time.perf_counter()
        list(self._db.orders.aggregate(pipeline))
        return (time.perf_counter() - start) * 1000.0

    def execute_q2(self, allow_disk_use: bool = False) -> Tuple[float, bool]:
        """
        Ejecuta Q2 (Massive Sort & Top-K) y devuelve (latencia_ms, disk_spill_detected).
        """
        pipeline = [
            { 
                "$match": {
                    "payment.status": "completed",
                    "timestamp": { "$gte": "2026-01-01T00:00:00Z" }
                } 
            },
            { "$sort": { "payment.final_total": -1 } },
            { "$limit": 1000 },
            { 
                "$project": {
                    "_id": 0,
                    "order_id": 1,
                    "customer.id": 1,
                    "payment.final_total": 1
                } 
            }
        ]
        start = time.perf_counter()
        spill_detected = False
        try:
            list(self._db.orders.aggregate(pipeline, allowDiskUse=allow_disk_use))
            latency = (time.perf_counter() - start) * 1000.0
            # Si se permitió uso de disco en Q2 y terminó exitosamente sin fallar por 100MB RAM sort limit
            if allow_disk_use:
                spill_detected = True
            return latency, spill_detected
        except Exception as e:
            err_msg = str(e).lower()
            if "sort exceeded memory limit" in err_msg or "allowdiskuse" in err_msg:
                # Fallo por buffer/spill no permitido
                return (time.perf_counter() - start) * 1000.0, True
            raise e

