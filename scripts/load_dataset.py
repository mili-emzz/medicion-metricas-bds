#!/usr/bin/env python3
"""
load_dataset.py
Carga masiva por lotes (bulk insert) del dataset generado en MongoDB y PostgreSQL.
Crea los esquemas e índices estipulados en la Sección 2 del Playbook.
"""

import os
import sys
import json
import time
import argparse
from typing import List, Dict, Any

def load_to_mongo(file_path: str, uri: str = "mongodb://localhost:27017/", batch_size: int = 5000):
    from pymongo import MongoClient
    print(f"[*] Conectando a MongoDB en {uri}...")
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    db = client["benchmark_db"]
    collection = db["orders"]

    print("[*] Recreando colección e índices en MongoDB...")
    collection.drop()
    collection.create_index([("timestamp", 1)], name="idx_orders_timestamp")
    collection.create_index([("order_id", 1)], name="idx_orders_order_id")

    print(f"[*] Insertando registros desde {file_path} en MongoDB (lotes de {batch_size})...")
    start_time = time.time()
    batch = []
    total_inserted = 0

    with open(file_path, "r", encoding="utf-8") as f:
        # Detectar si es array JSON o JSON lines
        first_char = f.read(1)
        f.seek(0)
        if first_char == "[":
            records = json.load(f)
            for i in range(0, len(records), batch_size):
                chunk = records[i:i + batch_size]
                collection.insert_many(chunk, ordered=False)
                total_inserted += len(chunk)
                print(f"    -> {total_inserted} registros insertados en MongoDB...", end="\r")
        else:
            for line in f:
                line = line.strip()
                if not line or line in ["[", "]", ","]:
                    continue
                if line.endswith(","):
                    line = line[:-1]
                batch.append(json.loads(line))
                if len(batch) >= batch_size:
                    collection.insert_many(batch, ordered=False)
                    total_inserted += len(batch)
                    batch = []
                    print(f"    -> {total_inserted} registros insertados en MongoDB...", end="\r")
            if batch:
                collection.insert_many(batch, ordered=False)
                total_inserted += len(batch)

    elapsed = time.time() - start_time
    print(f"\n[+] MongoDB: {total_inserted} registros cargados en {elapsed:.2f}s ({total_inserted/elapsed:.1f} rec/s).")
    client.close()

def load_to_postgres(file_path: str, host: str = "localhost", port: int = 5432, batch_size: int = 5000):
    try:
        import psycopg2
        from psycopg2.extras import execute_values
    except ImportError:
        import psycopg
        execute_values = None

    print(f"[*] Conectando a PostgreSQL en {host}:{port}...")
    conn = psycopg2.connect(host=host, port=port, dbname="benchmark_db", user="postgres", password="postgres")
    conn.autocommit = False
    cur = conn.cursor()

    print("[*] Recreando tabla orders e índice JSONB en PostgreSQL...")
    cur.execute("DROP TABLE IF EXISTS orders CASCADE;")
    cur.execute("CREATE TABLE orders (id UUID PRIMARY KEY, data JSONB NOT NULL);")
    cur.execute("CREATE INDEX idx_orders_timestamp ON orders (((data->>'timestamp')::timestamptz));")
    conn.commit()

    print(f"[*] Insertando registros desde {file_path} en PostgreSQL...")
    start_time = time.time()
    batch = []
    total_inserted = 0

    insert_sql = "INSERT INTO orders (id, data) VALUES %s;"

    with open(file_path, "r", encoding="utf-8") as f:
        first_char = f.read(1)
        f.seek(0)
        if first_char == "[":
            records = json.load(f)
            for i in range(0, len(records), batch_size):
                chunk = [(r["order_id"], json.dumps(r)) for r in records[i:i + batch_size]]
                execute_values(cur, insert_sql, chunk)
                conn.commit()
                total_inserted += len(chunk)
                print(f"    -> {total_inserted} registros insertados en PostgreSQL...", end="\r")
        else:
            for line in f:
                line = line.strip()
                if not line or line in ["[", "]", ","]:
                    continue
                if line.endswith(","):
                    line = line[:-1]
                rec = json.loads(line)
                batch.append((rec["order_id"], json.dumps(rec)))
                if len(batch) >= batch_size:
                    execute_values(cur, insert_sql, batch)
                    conn.commit()
                    total_inserted += len(batch)
                    batch = []
                    print(f"    -> {total_inserted} registros insertados en PostgreSQL...", end="\r")
            if batch:
                execute_values(cur, insert_sql, batch)
                conn.commit()
                total_inserted += len(batch)

    elapsed = time.time() - start_time
    print(f"\n[+] PostgreSQL: {total_inserted} registros cargados en {elapsed:.2f}s ({total_inserted/elapsed:.1f} rec/s).")
    cur.close()
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Carga masiva de datos sintéticos a MongoDB y PostgreSQL")
    parser.add_argument("--file", "-f", type=str, default="./data/dataset.json", help="Ruta del archivo de dataset")
    parser.add_argument("--engine", "-e", type=str, default="both", choices=["both", "mongodb", "postgresql"])
    parser.add_argument("--batch-size", "-b", type=int, default=5000, help="Tamaño de lote")

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"[-] Error: Archivo de datos no encontrado en {args.file}")
        print("    Genérelo primero ejecutando: python synthetic_data_generator.py")
        sys.exit(1)

    if args.engine in ["both", "mongodb"]:
        load_to_mongo(args.file, batch_size=args.batch_size)

    if args.engine in ["both", "postgresql"]:
        load_to_postgres(args.file, batch_size=args.batch_size)

if __name__ == "__main__":
    main()

