import os
import sys
import pandas as pd
import numpy as np

# Load CSV data
csv_path = "../results/summary_stats.csv"
if not os.path.exists(csv_path):
    csv_path = "results/summary_stats.csv"
df = pd.read_csv(csv_path)

print(f"Loaded {len(df)} rows from {csv_path}")

# Helper functions to query exact data
def get_val(impl, size, dist, op, col):
    sub = df[(df['impl'] == impl) & (df['size'] == size) & (df['distribution'] == dist) & (df['operation'] == op)]
    if len(sub) == 0:
        return "N/A"
    val = sub[col].values[0]
    if isinstance(val, float):
        if col in ['median_ns', 'iqr_ns', 'mean_ns', 'min_ns', 'max_ns', 'load_factor']:
            return f"{val:.2f}"
        elif col in ['avg_probe']:
            return f"{val:.4f}"
    return str(val)

def get_mem_mb(impl, size):
    sub = df[(df['impl'] == impl) & (df['size'] == size) & (df['distribution'] == 'random') & (df['operation'] == 'insert')]
    if len(sub) == 0:
        return "N/A"
    bytes_val = sub['memory_bytes'].values[0]
    return f"{bytes_val / (1024*1024):.2f}"

def get_mem_kb(impl, size):
    sub = df[(df['impl'] == impl) & (df['size'] == size) & (df['distribution'] == 'random') & (df['operation'] == 'insert')]
    if len(sub) == 0:
        return "N/A"
    bytes_val = sub['memory_bytes'].values[0]
    return f"{bytes_val / 1024:.1f}"

print("Sanity check - LinearProbing 100k random insert median:", get_val('LinearProbing', 100000, 'random', 'insert', 'median_ns'))
print("Sanity check - RobinHood 100k random insert median:", get_val('RobinHood', 100000, 'random', 'insert', 'median_ns'))
