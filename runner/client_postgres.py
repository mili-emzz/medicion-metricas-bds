import time
from typing import Dict, Any, Tuple

class PostgresClientExecutor:
    """Cliente de ejecución para consultas de PostgreSQL JSONB (Q1 y Q2)."""

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
        """Ejecuta Q1 (Unwind, Filter & Grouping) y devuelve latencia en ms."""
        sql = """
        SELECT data->'customer'->'geo'->>'country' AS country,
               item->>'category' AS category,
               SUM((item->>'qty')::numeric * (item->>'price')::numeric) AS total_revenue,
               AVG((item->>'qty')::numeric * (item->>'price')::numeric) AS avg_revenue,
               COUNT(*) AS count
        FROM orders, jsonb_array_elements(data->'items') AS item
        WHERE (item->>'price')::numeric > 50
        GROUP BY 1, 2;
        """
        cur = self._conn.cursor()
        start = time.perf_counter()
        cur.execute(sql)
        cur.fetchall()
        cur.close()
        return (time.perf_counter() - start) * 1000.0

    def execute_q2(self, work_mem: str = "4MB") -> Tuple[float, bool]:
        """
        Ejecuta Q2 (Massive Sort & Top-K) con configuración de work_mem.
        Devuelve (latencia_ms, disk_spill_detected).
        """
        cur = self._conn.cursor()
        cur.execute(f"SET work_mem = '{work_mem}';")
        
        # Consulta para registrar temp_bytes antes
        cur.execute("SELECT temp_bytes FROM pg_stat_database WHERE datname = 'benchmark_db';")
        temp_before = cur.fetchone()[0] or 0

        sql = """
        SELECT data->>'order_id' AS order_id,
               data->'customer'->>'id' AS customer_id,
               (data->'payment'->>'final_total')::numeric AS final_total
        FROM orders
        WHERE data->'payment'->>'status' = 'completed'
          AND (data->>'timestamp')::timestamptz >= '2026-01-01 00:00:00Z'
        ORDER BY (data->'payment'->>'final_total')::numeric DESC
        LIMIT 1000;
        """
        start = time.perf_counter()
        cur.execute(sql)
        cur.fetchall()
        latency = (time.perf_counter() - start) * 1000.0

        # Verificar si hubo incremento de temp_bytes (disk spill a archivos temporales de ordenamiento)
        cur.execute("SELECT temp_bytes FROM pg_stat_database WHERE datname = 'benchmark_db';")
        temp_after = cur.fetchone()[0] or 0
        cur.close()

        spill_detected = (temp_after > temp_before)
        return latency, spill_detected

