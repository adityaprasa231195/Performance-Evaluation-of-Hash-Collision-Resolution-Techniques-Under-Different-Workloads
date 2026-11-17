#!/usr/bin/env python3
"""
Paper Generator for Hash Table Collision Resolution Research Paper
Outputs: paper/paper.typ and paper/main.tex
Author: Aditya Kumar Harishankar Prasad
"""

import os
import sys
import pandas as pd
import numpy as np

# Load CSV data
csv_path = "../results/summary_stats.csv"
if not os.path.exists(csv_path):
    csv_path = "results/summary_stats.csv"
df = pd.read_csv(csv_path)

def get_row(impl, size, dist, op):
    sub = df[(df['impl'] == impl) & (df['size'] == size) & (df['distribution'] == dist) & (df['operation'] == op)]
    if len(sub) == 0:
        return None
    return sub.iloc[0]

def fmt_f(val, decimals=2):
    if val is None or pd.isna(val):
        return "N/A"
    return f"{float(val):.{decimals}f}"

def fmt_int(val):
    if val is None or pd.isna(val):
        return "N/A"
    return f"{int(val):,}"

def get_val(impl, size, dist, op, col, decimals=2):
    row = get_row(impl, size, dist, op)
    if row is None:
        return "N/A"
    val = row[col]
    if col in ['median_ns', 'iqr_ns', 'mean_ns', 'min_ns', 'max_ns', 'load_factor']:
        return fmt_f(val, decimals)
    elif col in ['avg_probe']:
        return fmt_f(val, 4)
    elif col in ['collisions', 'max_probe', 'memory_bytes']:
        return fmt_int(val)
    return str(val)

def get_mem_mb(impl, size):
    row = get_row(impl, size, 'random', 'insert')
    if row is None:
        return "N/A"
    bytes_val = row['memory_bytes']
    return fmt_f(bytes_val / (1024*1024), 2)

def get_mem_kb(impl, size):
    row = get_row(impl, size, 'random', 'insert')
    if row is None:
        return "N/A"
    bytes_val = row['memory_bytes']
    return fmt_f(bytes_val / 1024, 1)

print("Helper functions configured successfully.")
