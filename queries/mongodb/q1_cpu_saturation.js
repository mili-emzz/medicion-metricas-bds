// Q1: Unwind, Filter & Grouping (Saturación de CPU) — Dominio: AntFish
// Colección: analisis (init_antfish_db.js)
//
// Lógica: Desanida el arreglo 'urls_extraidas' de cada documento de análisis,
// filtra los registros con score_total >= 50 (nivel alto/crítico),
// y agrupa por tipo_entrada, nivel_riesgo y dominio para calcular conteos
// y promedios de score y puntos por capa APIs. Esta operación es CPU-intensiva
// porque fuerza el desanidado de hasta 2 URLs por documento en 500k registros.
//
// Campo anidado: urls_extraidas (array, maxItems: 2) → { url: string, dominio: string }
// Índice disponible: { user_id, fecha, _id } — NO cubre score_total → full collection scan
db.analisis.aggregate([
  { "$unwind": "$urls_extraidas" },
  {
    "$match": {
      "score_total": { "$gte": 50 }
    }
  },
  {
    "$group": {
      "_id": {
        "tipo_entrada":  "$tipo_entrada",
        "nivel_riesgo":  "$nivel_riesgo",
        "dominio":       "$urls_extraidas.dominio"
      },
      "total_amenazas":       { "$sum": 1 },
      "promedio_score":       { "$avg": "$score_total" },
      "promedio_puntos_apis": { "$avg": "$puntos_por_capa.apis" },
      "promedio_puntos_url":  { "$avg": "$puntos_por_capa.url" },
      "promedio_puntos_texto":{ "$avg": "$puntos_por_capa.texto" }
    }
  }
]);


