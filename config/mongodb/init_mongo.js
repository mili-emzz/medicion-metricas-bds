// Inicialización de MongoDB para Benchmark
// Colección orders sin sharding; WiredTiger; Índice simple en timestamp y order_id
db = db.getSiblingDB('benchmark_db');

db.orders.drop();
db.createCollection('orders');

// Índices requeridos por el Playbook (Sección 2)
db.orders.createIndex({ "timestamp": 1 }, { name: "idx_orders_timestamp" });
db.orders.createIndex({ "order_id": 1 }, { name: "idx_orders_order_id" });

