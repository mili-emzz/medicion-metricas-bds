// Q1: Unwind, Filter & Grouping (Saturación de CPU)
// Desanida items, filtra price > 50, calcula subtotal y agrupa suma/promedio por país y categoría
db.orders.aggregate([
  { "$unwind": "$items" },
  { "$match": { "items.price": { "$gt": 50 } } },
  {
    "$group": {
      "_id": {
        "country": "$customer.geo.country",
        "category": "$items.category"
      },
      "total_revenue": { "$sum": { "$multiply": ["$items.qty", "$items.price"] } },
      "avg_revenue": { "$avg": { "$multiply": ["$items.qty", "$items.price"] } },
      "count": { "$sum": 1 }
    }
  }
]);

