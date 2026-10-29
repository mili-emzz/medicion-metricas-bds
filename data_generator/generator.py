import os
import json
import time
from typing import Optional, Type
from data_generator.base import BaseDatasetSchema
from data_generator.schemas.ecommerce import EcommerceOrderSchema
from data_generator.schemas.antfish import AntFishAnalisisSchema

SCHEMA_REGISTRY = {
    "antfish": AntFishAnalisisSchema,
    "ecommerce": EcommerceOrderSchema,
    "default": AntFishAnalisisSchema
}

def register_schema(name: str, schema_cls: Type[BaseDatasetSchema]):
    SCHEMA_REGISTRY[name] = schema_cls

class DatasetGenerator:
    """
    Motor modular de generación de datasets sintéticos por lotes (streaming),
    garantizando baja huella de memoria durante la generación de 500,000 registros.
    """

    def __init__(self, schema: Optional[BaseDatasetSchema] = None):
        self.schema = schema or AntFishAnalisisSchema()

    def generate_to_file(self, output_path: str, total_records: int = 500000, batch_size: int = 10000):
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        print(f"[*] Iniciando generación de {total_records} registros con esquema '{self.schema.__class__.__name__}'...")
        start_time = time.time()

        is_json_array = output_path.endswith(".json")
        first_record = True

        with open(output_path, "w", encoding="utf-8") as f:
            if is_json_array:
                f.write("[\n")

            records_written = 0
            while records_written < total_records:
                current_batch_size = min(batch_size, total_records - records_written)
                batch_buffer = []

                for _ in range(current_batch_size):
                    record = self.schema.generate_record()
                    record_json = json.dumps(record, ensure_ascii=False)

                    if is_json_array:
                        if not first_record:
                            batch_buffer.append(",\n" + record_json)
                        else:
                            batch_buffer.append(record_json)
                            first_record = False
                    else:
                        batch_buffer.append(record_json + "\n")

                f.writelines(batch_buffer)
                records_written += current_batch_size
                elapsed = time.time() - start_time
                qps = records_written / elapsed if elapsed > 0 else 0
                print(f"    -> {records_written}/{total_records} registros generados ({qps:.1f} rec/s)...", end="\r")

            if is_json_array:
                f.write("\n]\n")

        total_elapsed = time.time() - start_time
        print(f"\n[+] Generación completa en {total_elapsed:.2f}s. Guardado en: {output_path}")
        return output_path
