import time
from typing import Dict, Any, Tuple

class MongoClientExecutor:
    """Cliente de ejecución para consultas de MongoDB en la colección 'analisis' (Q1 y Q2)."""

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
        """
        Ejecuta Q1 (Unwind, Filter & Grouping sobre 'analisis') y devuelve latencia en ms.
        Desanida 'urls_extraidas', filtra score_total >= 50 y agrupa por tipo_entrada,
        nivel_riesgo y dominio calculando promedios.
        """
        pipeline = [
            { "$unwind": "$urls_extraidas" },
            {
                "$match": {
                    "score_total": { "$gte": 50 }
                }
            },
            {
                "$group": {
                    "_id": {
                        "tipo_entrada": "$tipo_entrada",
                        "nivel_riesgo": "$nivel_riesgo",
                        "dominio": "$urls_extraidas.dominio"
                    },
                    "total_amenazas": { "$sum": 1 },
                    "promedio_score": { "$avg": "$score_total" },
                    "promedio_puntos_apis": { "$avg": "$puntos_por_capa.apis" },
                    "promedio_puntos_url": { "$avg": "$puntos_por_capa.url" },
                    "promedio_puntos_texto": { "$avg": "$puntos_por_capa.texto" }
                }
            }
        ]
        start = time.perf_counter()
        list(self._db.analisis.aggregate(pipeline))
        return (time.perf_counter() - start) * 1000.0

    def execute_q2(self, allow_disk_use: bool = False) -> Tuple[float, bool]:
        """
        Ejecuta Q2 (Massive Sort & Top-K sobre 'analisis') con flag allowDiskUse.
        Filtra por fecha y ordena por score_total desc (campo sin índice) extrayendo Top-1000.
        Devuelve (latencia_ms, disk_spill_detected).
        """
        pipeline = [
            {
                "$match": {
                    "fecha": { "$gte": "2026-01-01T00:00:00Z" }
                }
            },
            { "$sort": { "score_total": -1 } },
            { "$limit": 1000 },
            {
                "$project": {
                    "_id": 0,
                    "user_id": 1,
                    "dominio_principal": 1,
                    "score_total": 1,
                    "nivel_riesgo": 1,
                    "tipo_entrada": 1,
                    "fecha": 1
                }
            }
        ]
        start = time.perf_counter()
        spill_detected = False
        try:
            list(self._db.analisis.aggregate(pipeline, allowDiskUse=allow_disk_use))
            latency = (time.perf_counter() - start) * 1000.0
            if allow_disk_use:
                spill_detected = True
            return latency, spill_detected
        except Exception as e:
            err_msg = str(e).lower()
            if "sort exceeded memory limit" in err_msg or "allowdiskuse" in err_msg:
                return (time.perf_counter() - start) * 1000.0, True
            raise e
