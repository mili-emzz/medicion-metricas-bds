import time
from typing import Dict, Any, Tuple

class PostgresClientExecutor:
    """Cliente de ejecución para consultas de PostgreSQL JSONB en la tabla 'analisis' (Q1 y Q2)."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        dbname: str = "benchmark_db",
        user: str = "postgres",
        password: str = "postgres"
    ):
        self.conn_params = {
            "host": host,
            "port": port,
            "dbname": dbname,
            "user": user,
            "password": password
        }
        self._conn = None

    def connect(self):
        try:
            import psycopg2
            self._conn = psycopg2.connect(**self.conn_params)
            self._conn.autocommit = True
        except ImportError:
            try:
                import psycopg
                self._conn = psycopg.connect(**self.conn_params, autocommit=True)
            except ImportError:
                raise RuntimeError("psycopg2 o psycopg no están instalados. Ejecute: pip install psycopg2-binary")

    def close(self):
        if self._conn:
            self._conn.close()

    def execute_q1(self) -> float:
        """
        Ejecuta Q1 (Unwind, Filter & Grouping sobre 'analisis') y devuelve latencia en ms.
        Usa jsonb_array_elements para desanidar 'urls_extraidas', filtra score_total >= 50
        y agrupa multidimensionalmente.
        """
        sql = """
        SELECT
            data->>'tipo_entrada'                         AS tipo_entrada,
            data->>'nivel_riesgo'                         AS nivel_riesgo,
            url_obj->>'dominio'                           AS dominio,
            COUNT(*)                                      AS total_amenazas,
            AVG((data->>'score_total')::numeric)          AS promedio_score,
            AVG((data->'puntos_por_capa'->>'apis')::numeric)   AS promedio_puntos_apis,
            AVG((data->'puntos_por_capa'->>'url')::numeric)    AS promedio_puntos_url,
            AVG((data->'puntos_por_capa'->>'texto')::numeric)  AS promedio_puntos_texto
        FROM analisis,
             jsonb_array_elements(data->'urls_extraidas') AS url_obj
        WHERE (data->>'score_total')::numeric >= 50
        GROUP BY 1, 2, 3;
        """
        cur = self._conn.cursor()
        start = time.perf_counter()
        cur.execute(sql)
        cur.fetchall()
        cur.close()
        return (time.perf_counter() - start) * 1000.0

    def execute_q2(self, work_mem: str = "4MB") -> Tuple[float, bool]:
        """
        Ejecuta Q2 (Massive Sort & Top-K sobre 'analisis') con ajuste dinámico de work_mem.
        Filtra por fecha y ordena por score_total desc (campo sin índice) extrayendo Top-1000.
        Devuelve (latencia_ms, disk_spill_detected).
        """
        cur = self._conn.cursor()
        cur.execute(f"SET work_mem = '{work_mem}';")

        cur.execute("SELECT temp_bytes FROM pg_stat_database WHERE datname = 'benchmark_db';")
        temp_before = cur.fetchone()[0] or 0

        sql = """
        SELECT
            data->>'user_id'          AS user_id,
            data->>'dominio_principal' AS dominio_principal,
            (data->>'score_total')::numeric AS score_total,
            data->>'nivel_riesgo'     AS nivel_riesgo,
            data->>'tipo_entrada'     AS tipo_entrada,
            (data->>'fecha')::timestamptz AS fecha
        FROM analisis
        WHERE (data->>'fecha')::timestamptz >= '2026-01-01 00:00:00Z'
        ORDER BY (data->>'score_total')::numeric DESC
        LIMIT 1000;
        """
        start = time.perf_counter()
        cur.execute(sql)
        cur.fetchall()
        latency = (time.perf_counter() - start) * 1000.0

        cur.execute("SELECT temp_bytes FROM pg_stat_database WHERE datname = 'benchmark_db';")
        temp_after = cur.fetchone()[0] or 0
        cur.close()

        spill_detected = (temp_after > temp_before)
        return latency, spill_detected
