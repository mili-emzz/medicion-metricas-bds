// Q2: Massive Sort & Top-K (Estrés de Búfer)
// Filtra completadas desde 2026-01-01, ordena descendente por final_total y extrae Top-1000
// Nota: Ejecutar alternando allowDiskUse: false y allowDiskUse: true
db.orders.aggregate([
  { 
    "$match": {
      "payment.status": "completed",
      "timestamp": { "$gte": "2026-01-01T00:00:00Z" }
    } 
  },
  { "$sort": { "payment.final_total": -1 } },
  { "$limit": 1000 },
  { 
    "$project": {
      "_id": 0,
      "order_id": 1,
      "customer.id": 1,
      "payment.final_total": 1
    } 
  }
], { allowDiskUse: false }); // Parametrizable: true | false

