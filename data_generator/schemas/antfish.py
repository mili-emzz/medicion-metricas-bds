import uuid
import random
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from data_generator.base import BaseDatasetSchema

class AntFishAnalisisSchema(BaseDatasetSchema):
    """
    Esquema para la colección/tabla 'analisis' del dominio AntFish.
    Cumple con el validador JSON Schema + $expr de init_antfish_db.js (ADR #52, #53, #59, #69):
      - score_total [0, 100]
      - nivel_riesgo en ['bajo', 'medio', 'alto', 'critico'] coherente con score_total
      - puntos_por_capa: apis (0-60), url (0-30), texto (0-20)
      - tipo_entrada en ['sms', 'url']
      - SMS requiere mensaje_hash hex-64; URL requiere mensaje_hash = None (null)
      - urls_extraidas (max 2 elementos) con { url, dominio }
      - recomendaciones (1 a 3 elementos)
      - motivo_cortocircuito coherente con score
    """

    DOMINIOS_COMUNES = [
        "banco-seguro.com", "login-actualizacion.net", "verificacion-cuenta.xyz",
        "soporte-tecnico-urgente.org", "premio-ganador-sorteo.info", "portal-clientes-auth.co",
        "google.com", "github.com", "microsoft.com", "paypal-security-alert.me",
        "redireccion-bancaria.top", "secure-auth-token.biz", "envio-paquete-rastreo.online",
        "factura-pendiente-pago.site", "actualiza-datos-app.cloud"
    ]

    MARCAS = ["Santander", "BBVA", "MercadoLibre", "Netflix", "Amazon", "Apple", "WhatsApp"]

    RECOMENDACIONES_POOL = [
        "No abrir enlaces sospechosos",
        "Verificar directamente con la entidad emisora",
        "Bloquear el remitente del mensaje",
        "Cambiar credenciales comprometidas",
        "Reportar el incidente al equipo de seguridad"
    ]

    FUENTES_POOL = ["Google Web Risk", "VirusTotal", "PhishTank", "Heurística Interna"]

    def __init__(self, start_date: datetime = None, end_date: datetime = None):
        self.start_date = start_date or datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        self.end_date = end_date or datetime(2026, 10, 28, 0, 0, 0, tzinfo=timezone.utc)
        self.total_seconds = int((self.end_date - self.start_date).total_seconds())

    def get_collection_name(self) -> str:
        return "analisis"

    def generate_record(self) -> Dict[str, Any]:
        tipo_entrada = random.choices(["sms", "url"], weights=[0.4, 0.6])[0]
        dominio_principal = random.choice(self.DOMINIOS_COMUNES)

        # Regla de cortocircuito o score normal
        cortocircuito_chance = random.random()
        if cortocircuito_chance < 0.05:
            motivo_cortocircuito = "lista_negra"
            score_total = random.randint(95, 100)
        elif cortocircuito_chance < 0.15:
            motivo_cortocircuito = "suplantacion_marca"
            score_total = random.randint(80, 100)
        else:
            motivo_cortocircuito = None
            score_total = random.randint(0, 100)

        # nivel_riesgo estricto según validador de AntFish:
        # < 20 bajo, < 50 medio, < 80 alto, >= 80 critico
        if score_total < 20:
            nivel_riesgo = "bajo"
        elif score_total < 50:
            nivel_riesgo = "medio"
        elif score_total < 80:
            nivel_riesgo = "alto"
        else:
            nivel_riesgo = "critico"

        # puntos_por_capa coherentes con límites: apis (0-60), url (0-30), texto (0-20)
        p_apis = min(60, int(score_total * 0.55) + random.randint(0, 5))
        p_url = min(30, int(score_total * 0.28) + random.randint(0, 3))
        p_texto = min(20, max(0, score_total - p_apis - p_url))
        puntos_por_capa = {
            "apis": p_apis,
            "url": p_url,
            "texto": p_texto
        }

        # Regla D4 / ADR #69: SMS requiere hash hex-64; URL requiere null
        if tipo_entrada == "sms":
            raw_text = f"Mensaje sospechoso {random.randint(1000, 9999999)}"
            mensaje_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
        else:
            mensaje_hash = None

        # urls_extraidas (maxItems: 2)
        num_urls = random.randint(1, 2)
        urls_extraidas = []
        for _ in range(num_urls):
            dom = random.choice(self.DOMINIOS_COMUNES)
            urls_extraidas.append({
                "url": f"https://{dom}/path/{uuid.uuid4().hex[:8]}",
                "dominio": dom
            })

        # recomendaciones (minItems: 1, maxItems: 3)
        num_recs = random.randint(1, 3)
        recomendaciones = random.sample(self.RECOMENDACIONES_POOL, num_recs)

        # hallazgos
        hallazgos = []
        if score_total >= 50:
            hallazgos.append(f"Detección de patrones maliciosos en {dominio_principal}")
        if motivo_cortocircuito:
            hallazgos.append(f"Activación de regla directa: {motivo_cortocircuito}")

        # fuentes consultadas
        fuentes = random.sample(self.FUENTES_POOL, random.randint(1, 3))

        # fecha dentro del rango temporal (ISO 8601 con UTC)
        rand_offset = random.randint(0, self.total_seconds)
        fecha_dt = self.start_date + timedelta(seconds=rand_offset)
        fecha_iso = fecha_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        record = {
            "analisis_id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "tipo_entrada": tipo_entrada,
            "mensaje_hash": mensaje_hash,
            "dominio_principal": dominio_principal,
            "score_total": score_total,
            "nivel_riesgo": nivel_riesgo,
            "motivo_cortocircuito": motivo_cortocircuito,
            "analisis_parcial": False,
            "puntos_por_capa": puntos_por_capa,
            "urls_extraidas": urls_extraidas,
            "hallazgos": hallazgos,
            "recomendaciones": recomendaciones,
            "fuentes_consultadas": fuentes,
            "fecha": fecha_iso
        }

        return record

