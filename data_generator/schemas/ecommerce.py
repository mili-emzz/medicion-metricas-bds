import uuid
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
from data_generator.base import BaseDatasetSchema

class EcommerceOrderSchema(BaseDatasetSchema):
    """
    Esquema ilustrativo de comercio electrónico según Especificación 4 del Playbook:
    - 3 niveles de anidamiento promedio.
    - ~3 ítems por registro.
    - Tipos estructurados: UUID, ISO-8601, listas de objetos y diccionarios anidados.
    """

    COUNTRIES = ["MX", "US", "ES", "BR", "CO", "AR", "CL", "DE", "FR", "CA"]
    CATEGORIES = ["electronics", "appliances", "apparel", "home", "books", "beauty", "sports", "gaming"]
    BRANDS = ["Sony", "Samsung", "Apple", "LG", "Nike", "Adidas", "Philips", "Lenovo", "Xiaomi", "Bosch"]
    TIERS = ["standard", "silver", "gold", "vip"]
    PAYMENT_METHODS = ["credit_card", "debit_card", "paypal", "crypto", "wire_transfer"]
    PAYMENT_STATUSES = ["completed", "completed", "completed", "pending", "failed", "refunded"] # Mayor probabilidad a completed
    CHANNELS = ["web", "mobile_ios", "mobile_android", "pos_terminal", "api_b2b"]

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.start_date = datetime(2025, 6, 1, tzinfo=timezone.utc)
        self.end_date = datetime(2026, 6, 1, tzinfo=timezone.utc)
        self.delta_seconds = int((self.end_date - self.start_date).total_seconds())

    def get_collection_name(self) -> str:
        return "orders"

    def generate_record(self) -> Dict[str, Any]:
        order_id = str(uuid.UUID(int=self.rng.getrandbits(128)))
        record_time = self.start_date + timedelta(seconds=self.rng.randint(0, self.delta_seconds))
        timestamp_iso = record_time.isoformat()

        # Nivel 1 & 2: Customer y Geo
        country = self.rng.choice(self.COUNTRIES)
        customer = {
            "id": f"cust_{self.rng.randint(10000, 99999)}",
            "tier": self.rng.choice(self.TIERS),
            "segment": f"segment_{self.rng.choice(['retail', 'wholesale', 'direct', 'smb'])}",
            "geo": {
                "country": country,
                "state": f"state_{self.rng.randint(1, 20)}",
                "city": f"city_{self.rng.randint(1, 50)}",
                "zip": f"{self.rng.randint(10000, 99999)}",
                "coordinates": [
                    round(self.rng.uniform(-90.0, 90.0), 4),
                    round(self.rng.uniform(-180.0, 180.0), 4)
                ]
            }
        }

        # Nivel 1 & 2: Items (Promedio 3 ítems con variación 1..5)
        num_items = self.rng.choices([1, 2, 3, 4, 5], weights=[0.1, 0.25, 0.4, 0.15, 0.1])[0]
        items: List[Dict[str, Any]] = []
        subtotal = 0.0

        for i in range(num_items):
            qty = self.rng.randint(1, 4)
            # Rango de precios: algunos <= 50, otros > 50 para evaluar el filtro de Q1
            price = round(self.rng.uniform(15.0, 350.0), 2)
            item_subtotal = round(qty * price, 2)
            subtotal += item_subtotal

            items.append({
                "sku": f"SKU-{self.rng.choice(self.CATEGORIES)[:3].upper()}-{self.rng.randint(100, 999)}",
                "category": self.rng.choice(self.CATEGORIES),
                "brand": self.rng.choice(self.BRANDS),
                "qty": qty,
                "price": price,
                "tax_pct": 16.0,
                "discounts": round(self.rng.uniform(0.0, 10.0), 2)
            })

        subtotal = round(subtotal, 2)
        tax = round(subtotal * 0.16, 2)
        discount = round(self.rng.uniform(0.0, min(subtotal * 0.1, 20.0)), 2)
        final_total = round(subtotal + tax - discount, 2)

        # Nivel 1 & 2: Payment y Totales
        payment = {
            "method": self.rng.choice(self.PAYMENT_METHODS),
            "status": self.rng.choice(self.PAYMENT_STATUSES),
            "transaction_id": f"tx_{uuid.UUID(int=self.rng.getrandbits(128)).hex[:16]}",
            "gateway_latency_ms": self.rng.randint(80, 1200),
            "totals": {
                "subtotal": subtotal,
                "tax": tax,
                "discount": discount
            },
            "final_total": final_total
        }

        # Nivel 1: Metadata
        metadata = {
            "channel": self.rng.choice(self.CHANNELS),
            "user_agent": f"Mozilla/5.0 (ClientPlatform; Session/{self.rng.randint(100, 999)})",
            "session_id": f"sess_{uuid.UUID(int=self.rng.getrandbits(128)).hex[:12]}",
            "flags": {
                "is_gift": self.rng.random() < 0.1,
                "express_delivery": self.rng.random() < 0.25,
                "fraud_reviewed": self.rng.random() < 0.05
            }
        }

        return {
            "order_id": order_id,
            "timestamp": timestamp_iso,
            "customer": customer,
            "items": items,
            "payment": payment,
            "metadata": metadata
        }

