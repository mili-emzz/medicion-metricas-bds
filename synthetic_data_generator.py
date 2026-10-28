#!/usr/bin/env python3
"""
synthetic_data_generator.py
Generador de datos sintéticos parametrizable para benchmark de agregaciones JSON.
Cumple con la Sección 4 y 8.1 del Playbook y la Regla 2 de AGENTS.md.
"""

import sys
import argparse
from data_generator.generator import DatasetGenerator, SCHEMA_REGISTRY

def main():
    parser = argparse.ArgumentParser(
        description="Generador sintético de datasets anidados para benchmark MongoDB vs PostgreSQL"
    )
    parser.add_argument(
        "--records", "-n",
        type=int,
        default=500000,
        help="Cantidad total de registros a generar (default: 500000)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="./data/dataset.json",
        help="Ruta del archivo de salida (.json o .jsonl) (default: ./data/dataset.json)"
    )
    parser.add_argument(
        "--batch-size", "-b",
        type=int,
        default=10000,
        help="Tamaño de lote para escritura en streaming (default: 10000)"
    )
    parser.add_argument(
        "--schema", "-s",
        type=str,
        choices=list(SCHEMA_REGISTRY.keys()),
        default="ecommerce",
        help="Nombre del esquema a instanciar (default: ecommerce)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Semilla aleatoria para reproducibilidad (default: 42)"
    )

    args = parser.parse_args()

    schema_cls = SCHEMA_REGISTRY[args.schema]
    schema_instance = schema_cls(seed=args.seed)

    generator = DatasetGenerator(schema=schema_instance)
    generator.generate_to_file(
        output_path=args.output,
        total_records=args.records,
        batch_size=args.batch_size
    )

if __name__ == "__main__":
    main()

