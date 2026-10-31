import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

os.makedirs("./reports/figures", exist_ok=True)
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

df = pd.read_csv("./results/benchmark_results.csv")
# Excluir la fila 0 (corrida piloto previa)
df_clean = df.iloc[1:].copy()

# Normalizar nombres de perfiles
profile_map = {
    'PROFILE_A_BASELINE': 'Baseline (4 CPU / 4GB)',
    'PROFILE_B_MEDIUM': 'Medium (2 CPU / 2GB)',
    'PROFILE_C_SEVERE': 'Severe (1 CPU / 1GB)'
}
df_clean['profile_label'] = df_clean['profile'].map(profile_map)

# Agrupar por motor, query, perfil y concurrencia (promedio de las 3 repeticiones)
grouped = df_clean.groupby(['engine', 'query_id', 'profile', 'profile_label', 'concurrency']).agg({
    'throughput_qps': 'mean',
    'latency_p50_ms': 'mean',
    'latency_p95_ms': 'mean',
    'latency_p99_ms': 'mean'
}).reset_index()

# -------------------------------------------------------------
# GRÁFICA 1: Latencia P99 vs Concurrencia (Q1 y Q2)
# -------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

profiles = ['PROFILE_A_BASELINE', 'PROFILE_B_MEDIUM', 'PROFILE_C_SEVERE']
colors_mongo = {'PROFILE_A_BASELINE': '#13aa52', 'PROFILE_B_MEDIUM': '#00684a', 'PROFILE_C_SEVERE': '#001e2b'}
colors_pg = {'PROFILE_A_BASELINE': '#336791', 'PROFILE_B_MEDIUM': '#1f425f', 'PROFILE_C_SEVERE': '#0b1d28'}

# Subplot Q1 (CPU Saturation)
for prof in profiles:
    lbl = profile_map[prof].split(' ')[0]
    # Mongo Q1
    m_data = grouped[(grouped['engine'] == 'MongoDB') & (grouped['query_id'] == 'Q1') & (grouped['profile'] == prof)]
    if not m_data.empty:
        ax1.plot(m_data['concurrency'], m_data['latency_p99_ms'] / 1000.0, marker='o', linewidth=2.2,
                 color=colors_mongo[prof], label=f'MongoDB ({lbl})')
    # Postgres Q1
    p_data = grouped[(grouped['engine'] == 'PostgreSQL') & (grouped['query_id'] == 'Q1') & (grouped['profile'] == prof)]
    if not p_data.empty:
        # Reemplazar ceros de error por valor de corte para visualización
        lat_s = p_data['latency_p99_ms'].apply(lambda x: x / 1000.0 if x > 0 else 500.0)
        ax1.plot(p_data['concurrency'], lat_s, marker='s', linestyle='--', linewidth=2.2,
                 color=colors_pg[prof], label=f'Postgres ({lbl})')

ax1.set_title("Q1 (CPU / Unwind): Latencia P99 vs Concurrencia", fontsize=14, fontweight='bold', pad=12)
ax1.set_xlabel("Nivel de Concurrencia (Clientes)", fontsize=12)
ax1.set_ylabel("Latencia P99 (Segundos)", fontsize=12)
ax1.set_yscale('log')
ax1.set_xticks([1, 10, 50])
ax1.legend(loc='upper left', frameon=True, fontsize=9)
ax1.grid(True, which="both", ls="--", alpha=0.5)

# Subplot Q2 (Buffer Stress / Sort)
for prof in profiles:
    lbl = profile_map[prof].split(' ')[0]
    # Mongo Q2
    m_data = grouped[(grouped['engine'] == 'MongoDB') & (grouped['query_id'] == 'Q2') & (grouped['profile'] == prof)]
    if not m_data.empty:
        ax2.plot(m_data['concurrency'], m_data['latency_p99_ms'] / 1000.0, marker='o', linewidth=2.2,
                 color=colors_mongo[prof], label=f'MongoDB ({lbl})')
    # Postgres Q2
    p_data = grouped[(grouped['engine'] == 'PostgreSQL') & (grouped['query_id'] == 'Q2') & (grouped['profile'] == prof)]
    if not p_data.empty:
        ax2.plot(p_data['concurrency'], p_data['latency_p99_ms'] / 1000.0, marker='s', linestyle='--', linewidth=2.2,
                 color=colors_pg[prof], label=f'Postgres ({lbl})')

ax2.set_title("Q2 (Buffer / Sort): Latencia P99 vs Concurrencia", fontsize=14, fontweight='bold', pad=12)
ax2.set_xlabel("Nivel de Concurrencia (Clientes)", fontsize=12)
ax2.set_ylabel("Latencia P99 (Segundos)", fontsize=12)
ax2.set_yscale('log')
ax2.set_xticks([1, 10, 50])
ax2.legend(loc='upper left', frameon=True, fontsize=9)
ax2.grid(True, which="both", ls="--", alpha=0.5)

plt.tight_layout()
plt.savefig("./reports/figures/p99_vs_concurrency.png", dpi=300)
plt.close()
print("[+] Generada: reports/figures/p99_vs_concurrency.png")

# -------------------------------------------------------------
# GRÁFICA 2: Throughput (QPS) Comparativo
# -------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# QPS en Q1
labels = ['C=1\nBase', 'C=1\nMed', 'C=1\nSev', 'C=10\nBase', 'C=10\nMed', 'C=10\nSev', 'C=50\nBase', 'C=50\nMed', 'C=50\nSev']
x = np.arange(len(labels))
width = 0.35

mongo_q1_vals = []
pg_q1_vals = []
for c in [1, 10, 50]:
    for p in profiles:
        m_val = grouped[(grouped['engine'] == 'MongoDB') & (grouped['query_id'] == 'Q1') & (grouped['concurrency'] == c) & (grouped['profile'] == p)]['throughput_qps'].values
        p_val = grouped[(grouped['engine'] == 'PostgreSQL') & (grouped['query_id'] == 'Q1') & (grouped['concurrency'] == c) & (grouped['profile'] == p)]['throughput_qps'].values
        mongo_q1_vals.append(m_val[0] if len(m_val) > 0 else 0)
        pg_q1_vals.append(p_val[0] if len(p_val) > 0 else 0)

ax1.bar(x - width/2, mongo_q1_vals, width, label='MongoDB', color='#13aa52')
ax1.bar(x + width/2, pg_q1_vals, width, label='PostgreSQL JSONB', color='#336791')
ax1.set_title("Throughput Q1 (Consultas/segundo)", fontsize=13, fontweight='bold')
ax1.set_ylabel("QPS", fontsize=11)
ax1.set_xticks(x)
ax1.set_xticklabels(labels, fontsize=9)
ax1.legend()
ax1.grid(True, axis='y', ls='--', alpha=0.6)

# QPS en Q2
mongo_q2_vals = []
pg_q2_vals = []
for c in [1, 10, 50]:
    for p in profiles:
        m_val = grouped[(grouped['engine'] == 'MongoDB') & (grouped['query_id'] == 'Q2') & (grouped['concurrency'] == c) & (grouped['profile'] == p)]['throughput_qps'].values
        p_val = grouped[(grouped['engine'] == 'PostgreSQL') & (grouped['query_id'] == 'Q2') & (grouped['concurrency'] == c) & (grouped['profile'] == p)]['throughput_qps'].values
        mongo_q2_vals.append(m_val[0] if len(m_val) > 0 else 0)
        pg_q2_vals.append(p_val[0] if len(p_val) > 0 else 0)

ax2.bar(x - width/2, mongo_q2_vals, width, label='MongoDB', color='#13aa52')
ax2.bar(x + width/2, pg_q2_vals, width, label='PostgreSQL JSONB', color='#336791')
ax2.set_title("Throughput Q2 (Consultas/segundo)", fontsize=13, fontweight='bold')
ax2.set_ylabel("QPS", fontsize=11)
ax2.set_xticks(x)
ax2.set_xticklabels(labels, fontsize=9)
ax2.legend()
ax2.grid(True, axis='y', ls='--', alpha=0.6)

plt.tight_layout()
plt.savefig("./reports/figures/throughput_qps_comparison.png", dpi=300)
plt.close()
print("[+] Generada: reports/figures/throughput_qps_comparison.png")

# -------------------------------------------------------------
# GRÁFICA 3: Impacto de la Contención (Degradación Baseline vs Severe)
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 5))

# Factor de aumento de latencia P50 (Severe / Baseline) para Concurrencia 1
engines = ['MongoDB', 'PostgreSQL']
scenarios = ['Q1 (CPU / Unwind)', 'Q2 (Buffer / Sort)']

mongo_deg_q1 = (grouped[(grouped['engine'] == 'MongoDB') & (grouped['query_id'] == 'Q1') & (grouped['concurrency'] == 1) & (grouped['profile'] == 'PROFILE_C_SEVERE')]['latency_p50_ms'].values[0] /
                grouped[(grouped['engine'] == 'MongoDB') & (grouped['query_id'] == 'Q1') & (grouped['concurrency'] == 1) & (grouped['profile'] == 'PROFILE_A_BASELINE')]['latency_p50_ms'].values[0])

pg_deg_q1 = (grouped[(grouped['engine'] == 'PostgreSQL') & (grouped['query_id'] == 'Q1') & (grouped['concurrency'] == 1) & (grouped['profile'] == 'PROFILE_C_SEVERE')]['latency_p50_ms'].values[0] /
             grouped[(grouped['engine'] == 'PostgreSQL') & (grouped['query_id'] == 'Q1') & (grouped['concurrency'] == 1) & (grouped['profile'] == 'PROFILE_A_BASELINE')]['latency_p50_ms'].values[0])

mongo_deg_q2 = (grouped[(grouped['engine'] == 'MongoDB') & (grouped['query_id'] == 'Q2') & (grouped['concurrency'] == 1) & (grouped['profile'] == 'PROFILE_C_SEVERE')]['latency_p50_ms'].values[0] /
                grouped[(grouped['engine'] == 'MongoDB') & (grouped['query_id'] == 'Q2') & (grouped['concurrency'] == 1) & (grouped['profile'] == 'PROFILE_A_BASELINE')]['latency_p50_ms'].values[0])

pg_deg_q2 = (grouped[(grouped['engine'] == 'PostgreSQL') & (grouped['query_id'] == 'Q2') & (grouped['concurrency'] == 1) & (grouped['profile'] == 'PROFILE_C_SEVERE')]['latency_p50_ms'].values[0] /
             grouped[(grouped['engine'] == 'PostgreSQL') & (grouped['query_id'] == 'Q2') & (grouped['concurrency'] == 1) & (grouped['profile'] == 'PROFILE_A_BASELINE')]['latency_p50_ms'].values[0])

x = np.arange(len(scenarios))
width = 0.35

ax.bar(x - width/2, [mongo_deg_q1, mongo_deg_q2], width, label='MongoDB', color='#13aa52')
ax.bar(x + width/2, [pg_deg_q1, pg_deg_q2], width, label='PostgreSQL JSONB', color='#336791')

ax.set_title("Multiplicador de Latencia P50 bajo Contención Severa vs Baseline (C=1)", fontsize=13, fontweight='bold', pad=12)
ax.set_ylabel("Factor de Aumento (x veces más lento)", fontsize=11)
ax.set_xticks(x)
ax.set_xticklabels(scenarios, fontsize=11)
ax.axhline(1.0, color='gray', linestyle=':', label='Baseline (1.0x)')
ax.legend()
ax.grid(True, axis='y', ls='--', alpha=0.6)

plt.tight_layout()
plt.savefig("./reports/figures/latency_degradation_factor.png", dpi=300)
plt.close()
print("[+] Generada: reports/figures/latency_degradation_factor.png")

