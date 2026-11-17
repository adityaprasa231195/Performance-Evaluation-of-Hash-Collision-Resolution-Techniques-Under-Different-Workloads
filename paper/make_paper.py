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
    if pd.isna(val):
        return "N/A"
    return f"{float(val):.{decimals}f}"

def fmt_int(val):
    if pd.isna(val):
        return "N/A"
    return f"{int(val):,}"

print("Script template ready.")
