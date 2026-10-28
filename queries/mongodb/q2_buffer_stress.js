// Q2: Massive Sort & Top-K (Estrés de Búfer/Memoria) — Dominio: AntFish
// Colección: analisis (init_antfish_db.js)
//
// Lógica: Filtra registros de análisis a partir de 2026-01-01 y ordena
// descendente por score_total (campo NO indexado), extrayendo el Top-1000.
// Esto fuerza un sort stage sin índice de apoyo, estresando el búfer de
// ordenamiento tanto en memoria como en disco.
//
// Variantes de estrés de memoria (parametrizable en benchmark_runner.py):
//   allowDiskUse: false → falla con OOM si el sort supera el límite de 100MB en memoria
//   allowDiskUse: true  → permite volcado a disco temporal (disk_spill detectable)
//
// Índice disponible: { user_id, fecha, _id } — NO cubre score_total → sort sin índice
db.analisis.aggregate([
  {
    "$match": {
      "fecha": { "$gte": ISODate("2026-01-01T00:00:00Z") }
    }
  },
  { "$sort": { "score_total": -1 } },
  { "$limit": 1000 },
  {
    "$project": {
      "_id":              0,
      "user_id":          1,
      "dominio_principal":1,
      "score_total":      1,
      "nivel_riesgo":     1,
      "tipo_entrada":     1,
      "fecha":            1
    }
  }
], { allowDiskUse: false }); // Parametrizable: false | true


