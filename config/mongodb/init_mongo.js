// Inicialización de MongoDB para Benchmark AntFish
// Colección 'analisis' sin sharding; WiredTiger;
// Índices requeridos por AntFish (init_antfish_db.js):
// I2: { user_id: 1, fecha: -1, _id: -1 }
// No se indexa score_total para evaluar contención en ordenamiento masivo (Q2)
db = db.getSiblingDB('benchmark_db');

db.analisis.drop();
db.createCollection('analisis');

db.analisis.createIndex(
  { "user_id": 1, "fecha": -1, "_id": -1 },
  { name: "idx_analisis_user_fecha_id" }
);
