#!/usr/bin/env python3
"""
Paper Generator for Hash Table Collision Resolution Research Paper
Author: Aditya Kumar Harishankar Prasad
"""

import os
import sys
import pandas as pd
import numpy as np

# Load benchmark statistics
csv_path = "../results/summary_stats.csv"
if not os.path.exists(csv_path):
    csv_path = "results/summary_stats.csv"
df = pd.read_csv(csv_path)

print(f"Loaded {len(df)} summary rows from {csv_path}")

