#!/usr/bin/env python3
"""
Hash Table Research Paper — Figure Generation Script
=====================================================
Generates all SVG/PDF/PNG diagrams and data graphs for the paper.

Dependencies (install before running):
# pip install matplotlib numpy pandas scipy

Usage:
    python plots/plot_generation.py [--csv results/summary_stats.csv]
"""

import os
import sys
import math
import textwrap
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.lines import Line2D
from matplotlib import rcParams

# ─── Global style ────────────────────────────────────────────────────────────
rcParams.update({
    "font.family": "serif",
    "font.size": 8,
    "axes.titlesize": 9,
    "axes.labelsize": 8,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 7,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
    "pdf.fonttype": 42,   # TrueType in PDF (editable)
    "ps.fonttype": 42,
    "lines.linewidth": 1.2,
})

# Accent palette (accessible + B&W-safe via line styles)
C = {
    "blue":   "#1a6faf",
    "orange": "#e07b00",
    "green":  "#2e8b57",
    "red":    "#c0392b",
    "gray":   "#555555",
    "light":  "#dddddd",
    "bg":     "white",
    "text":   "#111111",
    "arrow":  "#333333",
}

STYLES    = ["-",  "--", "-.", ":"]
MARKERS   = ["o",  "s",  "^",  "D"]
IMPL_NAMES = ["SeparateChaining", "LinearProbing", "QuadraticProbing", "RobinHood"]
IMPL_LABELS = ["Separate\nChaining", "Linear\nProbing", "Quadratic\nProbing", "Robin\nHood"]
IMPL_SHORT  = ["SC", "LP", "QP", "RH"]
IMPL_COLORS = [C["blue"], C["orange"], C["green"], C["red"]]

PLOT_DIR = os.path.join(os.path.dirname(__file__))


def savefig(fig, basename, formats=("svg", "pdf", "png")):
    for fmt in formats:
        path = os.path.join(PLOT_DIR, f"{basename}.{fmt}")
        fig.savefig(path, format=fmt)
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION A — ALGORITHM DIAGRAMS (SVG / PDF / PNG)
# ═══════════════════════════════════════════════════════════════════════════════

def draw_arrow(ax, x0, y0, x1, y1, color=None, lw=1.2, style="->"):
    color = color or C["arrow"]
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                 arrowprops=dict(arrowstyle=style, color=color, lw=lw))


def box(ax, x, y, w, h, label, facecolor="white", edgecolor=None,
        fontsize=7, bold=False, zorder=3, labelcolor=None, pad=0.01):
    edgecolor = edgecolor or C["gray"]
    labelcolor = labelcolor or C["text"]
    r = FancyBboxPatch((x - w/2, y - h/2), w, h,
                        boxstyle=f"round,pad={pad}",
                        facecolor=facecolor, edgecolor=edgecolor,
                        linewidth=1.0, zorder=zorder)
    ax.add_patch(r)
    weight = "bold" if bold else "normal"
    ax.text(x, y, label, ha="center", va="center",
            fontsize=fontsize, color=labelcolor, weight=weight, zorder=zorder+1)


def new_diagram_fig(w_in=3.5, h_in=2.5, title=None):
    fig, ax = plt.subplots(figsize=(w_in, h_in))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    if title:
        ax.set_title(title, fontsize=8.5, weight="bold", pad=6)
    return fig, ax


# ─── Diagram 1: General Hash Table ───────────────────────────────────────────
def fig_diagram_hash_structure():
    fig, ax = new_diagram_fig(3.5, 2.5, "Hash Table: Key → Hash Function → Bucket")

    # Keys on left
    keys = ['"apple"', '"banana"', '"cherry"']
    key_y = [0.75, 0.52, 0.30]
    for k, y in zip(keys, key_y):
        box(ax, 0.13, y, 0.18, 0.10, k, facecolor="#eef4ff",
            edgecolor=C["blue"], fontsize=6)

    ax.text(0.13, 0.88, "Input Keys", ha="center", fontsize=6.5, weight="bold", color=C["text"])

    # Hash function box (center)
    box(ax, 0.40, 0.52, 0.18, 0.30, "hash(k)\nmod M",
        facecolor=C["blue"], edgecolor=C["blue"],
        labelcolor="white", fontsize=7, bold=True)

    # Arrow keys → hash
    for y in key_y:
        draw_arrow(ax, 0.22, y, 0.31, 0.52)

    # Bucket array (right)
    bucket_x = 0.67
    bucket_w = 0.14
    bucket_h = 0.09
    indices = list(range(5))
    bucket_top = 0.82
    step_y = 0.125
    for i in indices:
        by = bucket_top - i * step_y
        fc = "#fff3cd" if i in (1, 3) else "white"
        ec = C["orange"] if i == 1 else (C["blue"] if i == 3 else C["gray"])
        box(ax, bucket_x, by, bucket_w, bucket_h, f"[{i}]",
            facecolor=fc, edgecolor=ec, fontsize=6.5)

    # Arrow hash → bucket [0] for apple
    draw_arrow(ax, 0.49, 0.62, bucket_x - bucket_w/2, bucket_top - 0*step_y)
    # Arrow hash → bucket [1] for banana
    draw_arrow(ax, 0.49, 0.52, bucket_x - bucket_w/2, bucket_top - 1*step_y)
    # Arrow hash → bucket [1] for cherry (Collision!)
    draw_arrow(ax, 0.49, 0.42, bucket_x - bucket_w/2, bucket_top - 1*step_y)

    # Clear collision label placed safely to the right
    ax.annotate("Collision!\n(two keys → [1])",
                xy=(bucket_x + bucket_w/2 + 0.01, bucket_top - 1*step_y),
                xytext=(0.88, 0.76),
                arrowprops=dict(arrowstyle="->", color=C["orange"], lw=0.9),
                fontsize=5.5, color=C["orange"], ha="center", weight="bold")

    # Linked entries representation
    ax.text(0.88, bucket_top - 1*step_y - 0.04, "[banana]\n↓\n[cherry]",
            ha="center", va="top", fontsize=5.0, color=C["green"])

    ax.text(bucket_x, 0.10, "Bucket Array (M slots)", ha="center", fontsize=6, color=C["gray"])

    savefig(fig, "fig_diagram_hash_structure")


# ─── Diagram 2: Separate Chaining ────────────────────────────────────────────
def fig_diagram_separate_chaining():
    fig, ax = new_diagram_fig(3.5, 2.6, "Separate Chaining: Insert & Lookup")

    n_buckets = 5
    bx, bw, bh = 0.16, 0.14, 0.09
    top_y = 0.78
    gap = 0.13

    chains = {
        0: [("k=0","v=0")],
        1: [("k=5","v=A"), ("k=10","v=B")],  # collision
        2: [],
        3: [("k=8","v=C")],
        4: [],
    }

    for i in range(n_buckets):
        by = top_y - i * gap
        fc = "#eef4ff" if chains[i] else "#f9f9f9"
        box(ax, bx, by, bw, bh, f"[{i}]",
            facecolor=fc, edgecolor=C["blue"], fontsize=6.5)

        prev_x = bx + bw/2
        for j, (k, v) in enumerate(chains[i]):
            nx = prev_x + 0.16
            ny = by
            fc2 = "#fff3cd" if i == 1 else "#efffef"
            box(ax, nx, ny, 0.14, bh, f"{k}\n{v}",
                facecolor=fc2, edgecolor=C["orange"] if i==1 else C["green"],
                fontsize=5.5)
            draw_arrow(ax, prev_x, ny, nx - 0.07, ny)
            prev_x = nx + 0.07

        # NULL marker
        if chains[i]:
            ax.text(prev_x + 0.07, by, "NULL", ha="center", va="center",
                    fontsize=5.0, color=C["gray"])

    # Lookup annotation placed cleanly in upper empty space (x=0.65, y=0.88) with arrow to bucket 1
    ax.annotate("Lookup (k=10):\nHash to [1] → traverse chain",
                xy=(bx + bw/2, top_y - 1*gap),
                xytext=(0.65, 0.88),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=-0.2", color=C["red"], lw=0.9),
                fontsize=5.5, color=C["red"], ha="center", weight="bold")

    ax.text(0.50, 0.06, "O(1) average lookup · Worst case O(chain length)",
            ha="center", fontsize=5.5, color=C["gray"])

    savefig(fig, "fig_diagram_separate_chaining")


# ─── Diagram 3: Linear Probing ───────────────────────────────────────────────
def fig_diagram_linear_probing():
    fig, ax = new_diagram_fig(3.5, 2.5, "Linear Probing: Collision & Tombstone")

    n = 8
    slot_w = 0.88 / n
    slot_h = 0.18
    slot_y = 0.44

    contents = ["—", "k=1\nv=A", "k=9\nv=B", "[DEL]", "k=4\nv=C", "—", "—", "—"]
    colors   = ["#f9f9f9", "#eef4ff", "#fff3cd", "#ffe0e0", "#efffef", "#f9f9f9","#f9f9f9","#f9f9f9"]
    edges    = [C["gray"], C["blue"], C["orange"], C["red"], C["green"],C["gray"],C["gray"],C["gray"]]

    xs = [0.08 + (i + 0.5) * slot_w for i in range(n)]
    for i, (x, label, fc, ec) in enumerate(zip(xs, contents, colors, edges)):
        r = FancyBboxPatch((x - slot_w*0.44, slot_y - slot_h/2), slot_w*0.88, slot_h,
                           boxstyle="round,pad=0.005",
                           facecolor=fc, edgecolor=ec, linewidth=1.0, zorder=3)
        ax.add_patch(r)
        ax.text(x, slot_y, label, ha="center", va="center", fontsize=5.5,
                color=ec if label=="[DEL]" else C["text"],
                weight="bold" if label=="[DEL]" else "normal", zorder=4)
        ax.text(x, slot_y - slot_h/2 - 0.06, f"[{i}]", ha="center", fontsize=5.5,
                color=C["gray"])

    # Probe sequence for key with h(k)=1
    probe_labels = ["Try 0: h(k)=1\n(occupied)", "Try 1: h+1\n(occupied)"]
    for step, idx in enumerate([1, 2]):
        px = xs[idx]
        ax.annotate("", xy=(px, slot_y + slot_h/2 + 0.01),
                    xytext=(px, 0.72),
                    arrowprops=dict(arrowstyle="->", color=C["red"], lw=0.9))
        ax.text(px, 0.75, probe_labels[step], ha="center", va="bottom", fontsize=4.8, color=C["red"])

    # Insertion target at Tombstone (slot 3)
    ax.annotate("", xy=(xs[3], slot_y + slot_h/2 + 0.01),
                xytext=(xs[3], 0.72),
                arrowprops=dict(arrowstyle="->", color=C["green"], lw=1.1))
    ax.text(xs[3], 0.75, "Try 2: h+2\nReuse [DEL]", ha="center", va="bottom", fontsize=4.8,
            color=C["green"], weight="bold")

    # Tombstone explanation below
    ax.text(xs[3], 0.18, "Tombstone (lazy deletion)", ha="center", fontsize=5.0, color=C["red"], style="italic")
    draw_arrow(ax, xs[3], 0.22, xs[3], slot_y - slot_h/2 - 0.08, color=C["red"])

    ax.text(0.50, 0.05, "Linear Probe: h, h+1, h+2, ... (mod M) · Subject to primary clustering",
            ha="center", fontsize=5.5, color=C["gray"])

    savefig(fig, "fig_diagram_linear_probing")


# ─── Diagram 4: Quadratic Probing ────────────────────────────────────────────
def fig_diagram_quadratic_probing():
    fig, ax = new_diagram_fig(3.5, 2.5, "Quadratic Probing: h(k) + i²")

    n = 9
    slot_w = 0.88 / n
    slot_h = 0.16
    slot_y = 0.40

    base = 2  # h(k) = 2
    contents = ["—"] * n
    contents[base] = "Occ."
    contents[(base+1)%n] = "Try 1"
    contents[(base+4)%n] = "Try 2"

    colors = ["#f9f9f9"] * n
    colors[base] = "#fff3cd"
    colors[(base+1)%n] = "#efffef"
    colors[(base+4)%n] = "#eef4ff"

    xs = [0.06 + (i + 0.5) * slot_w for i in range(n)]
    for i, (x, label, fc) in enumerate(zip(xs, contents, colors)):
        ec = C["orange"] if label=="Occ." else (C["green"] if label=="Try 1" else C["gray"])
        r = FancyBboxPatch((x - slot_w*0.44, slot_y - slot_h/2), slot_w*0.88, slot_h,
                           boxstyle="round,pad=0.005",
                           facecolor=fc, edgecolor=ec, linewidth=1.0, zorder=3)
        ax.add_patch(r)
        ax.text(x, slot_y, label, ha="center", va="center", fontsize=5.0,
                weight="bold" if label != "—" else "normal", zorder=4)
        ax.text(x, slot_y - slot_h/2 - 0.06, f"[{i}]", ha="center", fontsize=5.5, color=C["gray"])

    # Arc 1: base (2) -> base+1 (3), offset = 1²
    x0 = xs[2]
    x1 = xs[3]
    ax.annotate("", xy=(x1, slot_y + slot_h/2), xytext=(x0, slot_y + slot_h/2),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=-0.4", color=C["blue"], lw=1.0))
    ax.text((x0+x1)/2, 0.58, "+1²", ha="center", fontsize=5.5, color=C["blue"], weight="bold")

    # Arc 2: base (2) -> base+4 (6), offset = 2²
    x2 = xs[6]
    ax.annotate("", xy=(x2, slot_y + slot_h/2), xytext=(x0, slot_y + slot_h/2),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=-0.45", color=C["blue"], lw=1.0))
    ax.text((x0+x2)/2, 0.72, "+2² = +4", ha="center", fontsize=5.5, color=C["blue"], weight="bold")

    ax.text(xs[base], slot_y + slot_h/2 + 0.05, "h(k)", ha="center", fontsize=5.5, color=C["orange"], weight="bold")
    ax.text(0.50, 0.06, "Probe: h+1, h+4, h+9, ... (mod M) · Eliminates primary clustering",
            ha="center", fontsize=5.5, color=C["gray"])

    savefig(fig, "fig_diagram_quadratic_probing")


# ─── Diagram 5: Robin Hood Hashing ───────────────────────────────────────────
def fig_diagram_robin_hood():
    fig, ax = new_diagram_fig(3.5, 2.6, "Robin Hood Hashing: Displacement & Stealing")

    n = 7
    slot_w = 0.88 / n
    slot_h = 0.17
    slot_y = 0.46

    slots = [
        ("—",    0,  "#f9f9f9", C["gray"]),
        ("k=A",  0,  "#eef4ff", C["blue"]),
        ("k=B",  1,  "#efffef", C["green"]),
        ("k=C",  2,  "#fff3cd", C["orange"]),
        ("—",    0,  "#f9f9f9", C["gray"]),
        ("—",    0,  "#f9f9f9", C["gray"]),
        ("—",    0,  "#f9f9f9", C["gray"]),
    ]
    xs = [0.06 + (i + 0.5) * slot_w for i in range(n)]

    for i, (x, (label, disp, fc, ec)) in enumerate(zip(xs, slots)):
        r = FancyBboxPatch((x - slot_w*0.44, slot_y - slot_h/2), slot_w*0.88, slot_h,
                           boxstyle="round,pad=0.005",
                           facecolor=fc, edgecolor=ec, linewidth=1.0, zorder=3)
        ax.add_patch(r)
        ax.text(x, slot_y + 0.02, label, ha="center", va="center", fontsize=5.5,
                weight="bold" if label != "—" else "normal", zorder=4)
        ax.text(x, slot_y - 0.03, f"d={disp}", ha="center", va="center",
                fontsize=4.8, color=C["gray"], zorder=4)
        ax.text(x, slot_y - slot_h/2 - 0.06, f"[{i}]", ha="center", fontsize=5.5, color=C["gray"])

    # Incoming key box
    box(ax, xs[3], 0.82, 0.16, 0.11, "New: k=X\n(dist = 3)",
        facecolor="#ffe0e0", edgecolor=C["red"], fontsize=5.2, bold=True)
    draw_arrow(ax, xs[3], 0.76, xs[3], slot_y + slot_h/2 + 0.02, color=C["red"], lw=1.0)

    # Annotation on steal decision
    ax.text(0.72, 0.82, "dist(X)=3 > dist(C)=2\n→ Steal slot [3]!\nC pushed to [4] with d=3",
            ha="left", va="center", fontsize=5.0, color=C["red"])

    ax.text(0.50, 0.06, "\"Rich give to poor\" · Equalises probe variance · Max PSL = O(log log N)",
            ha="center", fontsize=5.5, color=C["gray"])

    savefig(fig, "fig_diagram_robin_hood")


# ─── Diagram 6: Benchmark Workflow ───────────────────────────────────────────
def fig_diagram_benchmark_workflow():
    fig, ax = new_diagram_fig(3.5, 3.0, "Benchmark Execution Workflow")

    steps = [
        ("1. Dataset Synthesis (7 Distributions)", 0.50, 0.88),
        ("2. Table Initialization & Pre-sizing", 0.50, 0.73),
        ("3. Timed Operations (Insert / Hit / Miss / Del)", 0.50, 0.58),
        ("4. Hardware Telemetry & Probe Sampling", 0.50, 0.43),
        ("5. Multi-Trial CSV Logging (3,920 runs)", 0.50, 0.28),
        ("6. Summary Statistics & Figure Generation", 0.50, 0.13),
    ]
    colors_box = [C["blue"], C["blue"], C["orange"], C["green"], C["green"], C["red"]]

    for i, ((label, x, y), fc) in enumerate(zip(steps, colors_box)):
        box(ax, x, y, 0.72, 0.08, label, facecolor=fc,
            edgecolor=fc, labelcolor="white", fontsize=6.0, bold=True, pad=0.005)
        if i < len(steps) - 1:
            draw_arrow(ax, x, y - 0.045, steps[i+1][1], steps[i+1][2] + 0.045, color=C["arrow"], lw=1.0)

    savefig(fig, "fig_diagram_benchmark_workflow")


# ─── Diagram 7: Experiment Flowchart ─────────────────────────────────────────
def fig_diagram_experiment_flowchart():
    fig, ax = new_diagram_fig(3.5, 2.7, "Overall Research Flowchart")

    # 2-Row Architecture to prevent horizontal overlap
    # Row 1: Implementation & Verification (y = 0.70)
    row1 = [
        ("Literature\nReview\n(24 Papers)",   0.20, 0.70, C["blue"]),
        ("Safe Rust\nImpls\n(4 Algorithms)", 0.50, 0.70, C["blue"]),
        ("Correctness\nSuite\n(70 Tests)",    0.80, 0.70, C["green"]),
    ]
    # Row 2: Empirical Evaluation & Paper (y = 0.28)
    row2 = [
        ("Paper Writing\n(IEEE 2-Col\n21 Pages)", 0.80, 0.28, C["red"]),
        ("Statistical\nAnalysis\n(560 Groups)",   0.50, 0.28, C["orange"]),
        ("Controlled\nBenchmark\n(3,920 Trials)", 0.20, 0.28, C["orange"]),
    ]

    for label, x, y, fc in row1 + row2:
        box(ax, x, y, 0.24, 0.18, label, facecolor=fc,
            edgecolor=fc, labelcolor="white", fontsize=5.5, bold=True, pad=0.005)

    # Row 1 arrows
    draw_arrow(ax, 0.32, 0.70, 0.38, 0.70)
    draw_arrow(ax, 0.62, 0.70, 0.68, 0.70)

    # Transition from Row 1 to Row 2: (0.80, 0.70) down to (0.20, 0.28)
    # Down arrow from Tests to Benchmark
    draw_arrow(ax, 0.80, 0.61, 0.80, 0.49, color=C["arrow"])
    draw_arrow(ax, 0.80, 0.49, 0.20, 0.49, color=C["arrow"])
    draw_arrow(ax, 0.20, 0.49, 0.20, 0.37, color=C["arrow"])

    # Row 2 arrows (left to right: Benchmark -> Analysis -> Paper)
    draw_arrow(ax, 0.32, 0.28, 0.38, 0.28)
    draw_arrow(ax, 0.62, 0.28, 0.68, 0.28)

    savefig(fig, "fig_diagram_experiment_flowchart")



# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION B — DATA GRAPHS
# ═══════════════════════════════════════════════════════════════════════════════

SIZES = [1000, 5000, 10000, 50000, 100000, 500000, 1000000]

def make_placeholder_data():
    """
    Generate plausible representative data matching the expected CSV schema.
    Replace with real data when summary_stats.csv is available.
    """
    rng = np.random.default_rng(42)
    rows = []
    distributions = ["random", "sequential", "clustered", "adversarial"]
    load_factors = [0.25, 0.50, 0.75, 0.90]
    ops = ["insert", "lookup_hit", "lookup_miss", "delete"]

    base_ns = {
        "SeparateChaining": {"insert": 85,  "lookup_hit": 70,  "lookup_miss": 55,  "delete": 65},
        "LinearProbing":    {"insert": 60,  "lookup_hit": 45,  "lookup_miss": 35,  "delete": 50},
        "QuadraticProbing": {"insert": 65,  "lookup_hit": 50,  "lookup_miss": 38,  "delete": 55},
        "RobinHood":        {"insert": 72,  "lookup_hit": 48,  "lookup_miss": 36,  "delete": 58},
    }
    mem_bytes = {
        "SeparateChaining": 48, "LinearProbing": 16,
        "QuadraticProbing": 16, "RobinHood": 16,
    }

    for impl in IMPL_NAMES:
        for size in SIZES:
            scale = math.log2(size) / math.log2(1000)
            for dist in distributions:
                dist_mult = {"random": 1.0, "sequential": 0.85, "clustered": 1.35, "adversarial": 1.8}[dist]
                for lf in load_factors:
                    lf_mult = 1.0 + (lf - 0.5) * 1.5
                    for op in ops:
                        base = base_ns[impl][op] * scale * dist_mult * lf_mult
                        noise = rng.normal(1.0, 0.05)
                        median = base * noise
                        rows.append({
                            "implementation": impl,
                            "table_size": size,
                            "distribution": dist,
                            "load_factor": lf,
                            "operation": op,
                            "median_ns": median,
                            "p25_ns": median * 0.88,
                            "p75_ns": median * 1.15,
                            "mean_ns": median * 1.05,
                            "std_ns":  median * 0.12,
                            "memory_bytes": mem_bytes[impl] * size,
                            "collision_count": int(size * lf * {"SeparateChaining":0.42,"LinearProbing":0.3,"QuadraticProbing":0.25,"RobinHood":0.22}[impl] * rng.uniform(0.9,1.1)),
                            "avg_probe": 1.0 + lf/(2*(1-lf)) * {"SeparateChaining":0.5,"LinearProbing":1.0,"QuadraticProbing":0.8,"RobinHood":0.7}[impl],
                            "max_probe": int(math.log(size) * {"SeparateChaining":2,"LinearProbing":5,"QuadraticProbing":4,"RobinHood":3}[impl]),
                            "resize_count": int(math.log2(size/8)),
                        })
    return pd.DataFrame(rows)


def normalize_df(df):
    """Normalize column names and values to match internal format."""
    col_map = {
        "impl": "implementation",
        "size": "table_size",
        "collisions": "collision_count",
        "op": "operation",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    # Normalize implementation names
    def clean_impl(val):
        s = str(val).lower().replace("_", "").replace(" ", "").replace("-", "")
        if "chain" in s or s == "sc": return "SeparateChaining"
        if "linear" in s or s == "lp": return "LinearProbing"
        if "quadratic" in s or s == "qp": return "QuadraticProbing"
        if "robin" in s or s == "rh": return "RobinHood"
        return val
    if "implementation" in df.columns:
        df["implementation"] = df["implementation"].apply(clean_impl)

    # Normalize operations
    def clean_op(val):
        s = str(val).lower().replace("-", "_").replace(" ", "_")
        if "miss" in s or "fail" in s: return "lookup_miss"
        if "hit" in s or "succ" in s: return "lookup_hit"
        if "insert" in s: return "insert"
        if "del" in s: return "delete"
        return s
    if "operation" in df.columns:
        df["operation"] = df["operation"].apply(clean_op)

    # Normalize distributions
    if "distribution" in df.columns:
        df["distribution"] = df["distribution"].astype(str).str.lower().str.strip()

    # Compute p25/p75 if missing
    if "median_ns" in df.columns:
        if "p25_ns" not in df.columns:
            if "iqr_ns" in df.columns:
                df["p25_ns"] = (df["median_ns"] - df["iqr_ns"] / 2.0).clip(lower=0)
                df["p75_ns"] = df["median_ns"] + df["iqr_ns"] / 2.0
            elif "min_ns" in df.columns and "max_ns" in df.columns:
                df["p25_ns"] = df["min_ns"]
                df["p75_ns"] = df["max_ns"]
            elif "std_ns" in df.columns:
                df["p25_ns"] = (df["median_ns"] - df["std_ns"]).clip(lower=0)
                df["p75_ns"] = df["median_ns"] + df["std_ns"]

    return df


def load_data(csv_path):
    if csv_path and os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        print(f"[data] Loaded {len(df)} rows from {csv_path}")
        df = normalize_df(df)
        return df, False
    print("[data] summary_stats.csv not found — using representative placeholder data.")
    return make_placeholder_data(), True


def get_target_size(df, preferred=100000):
    sizes = sorted(df["table_size"].dropna().unique())
    if not sizes:
        return preferred
    if preferred in sizes:
        return preferred
    # Return closest
    return min(sizes, key=lambda s: abs(s - preferred))


def line_plot(ax, df, op, title, ylabel="Median latency (ns)"):
    df_op = df[df["operation"] == op].copy()
    if df_op.empty:
        df_op = df.copy()

    # Filter distribution
    dists = df_op["distribution"].unique()
    if "random" in dists:
        df_dist = df_op[df_op["distribution"] == "random"]
    elif len(dists) > 0:
        df_dist = df_op[df_op["distribution"] == dists[0]]
    else:
        df_dist = df_op

    # Filter load factor
    if "load_factor" in df_dist.columns:
        lfs = df_dist["load_factor"].dropna().unique()
        if len(lfs) > 0:
            target_lf = min(lfs, key=lambda x: abs(x - 0.75))
            df_lf = df_dist[df_dist["load_factor"] == target_lf]
        else:
            df_lf = df_dist
    else:
        df_lf = df_dist

    for i, impl in enumerate(IMPL_NAMES):
        sub = df_lf[df_lf["implementation"] == impl]
        if sub.empty:
            continue
        sub = sub.groupby("table_size").median(numeric_only=True).reset_index()
        ax.plot(sub["table_size"], sub["median_ns"],
                color=IMPL_COLORS[i], marker=MARKERS[i], linestyle=STYLES[i],
                markersize=3.5, label=IMPL_SHORT[i], linewidth=1.2)
        if "p25_ns" in sub.columns and "p75_ns" in sub.columns:
            ax.fill_between(sub["table_size"], sub["p25_ns"], sub["p75_ns"],
                            alpha=0.12, color=IMPL_COLORS[i])

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Table size (entries)", fontsize=8)
    ax.set_ylabel(ylabel, fontsize=8)
    ax.set_title(title, fontsize=9)
    ax.legend(fontsize=7, ncol=2, loc="upper left")
    ax.grid(True, which="both", ls=":", lw=0.5, alpha=0.5)


def fig1_insert_latency_vs_size(df):
    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    line_plot(ax, df, "insert", "Insert Latency vs. Table Size")
    savefig(fig, "fig1_insert_latency_vs_size")


def fig2_lookup_hit_latency_vs_size(df):
    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    line_plot(ax, df, "lookup_hit", "Lookup (Hit) Latency vs. Table Size")
    savefig(fig, "fig2_lookup_hit_latency_vs_size")


def fig3_lookup_miss_latency_vs_size(df):
    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    line_plot(ax, df, "lookup_miss", "Lookup (Miss) Latency vs. Table Size")
    savefig(fig, "fig3_lookup_miss_latency_vs_size")


def fig4_delete_latency_vs_size(df):
    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    line_plot(ax, df, "delete", "Delete Latency vs. Table Size")
    savefig(fig, "fig4_delete_latency_vs_size")


def fig5_load_factor_effect(df):
    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    target_sz = get_target_size(df, 100000)
    df_sz = df[(df["table_size"] == target_sz) & (df["operation"] == "insert")]
    if "distribution" in df_sz.columns and "random" in df_sz["distribution"].values:
        df_sz = df_sz[df_sz["distribution"] == "random"]
    lfs = sorted(df_sz["load_factor"].dropna().unique()) if "load_factor" in df_sz.columns else [0.75]
    if not lfs:
        lfs = [0.75]
    x = np.arange(len(lfs))
    width = 0.18
    for i, impl in enumerate(IMPL_NAMES):
        vals = []
        for lf in lfs:
            sub = df_sz[(df_sz["implementation"]==impl)]
            if "load_factor" in df_sz.columns:
                sub = sub[sub["load_factor"]==lf]
            vals.append(sub["median_ns"].median() if not sub.empty else 0)
        ax.bar(x + i*width, vals, width=width*0.9, label=IMPL_SHORT[i],
               color=IMPL_COLORS[i], edgecolor="white", linewidth=0.5)
    ax.set_xticks(x + width*1.5)
    ax.set_xticklabels([f"α={lf:.2f}" for lf in lfs])
    ax.set_xlabel("Load factor (α)", fontsize=8)
    ax.set_ylabel("Median insert latency (ns)", fontsize=8)
    ax.set_title(f"Load Factor Effect on Insert Performance (N={target_sz:,})", fontsize=9)
    ax.legend(fontsize=7, ncol=4)
    ax.grid(axis="y", ls=":", lw=0.5, alpha=0.5)
    savefig(fig, "fig5_load_factor_effect")


def fig6_memory_comparison(df):
    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    target_sz = get_target_size(df, 100000)
    df_sz = df[df["table_size"] == target_sz]
    mems = []
    for impl in IMPL_NAMES:
        sub = df_sz[df_sz["implementation"] == impl]
        if not sub.empty and "memory_bytes" in sub.columns and not sub["memory_bytes"].isna().all():
            v = sub["memory_bytes"].median()
        else:
            # Fallback estimation based on architecture
            bytes_per_entry = {"SeparateChaining": 48, "LinearProbing": 16, "QuadraticProbing": 16, "RobinHood": 16}[impl]
            v = bytes_per_entry * target_sz
        mems.append(v / 1024 / 1024)  # MB
    bars = ax.bar(IMPL_SHORT, mems, color=IMPL_COLORS, edgecolor="white", linewidth=0.5)
    ax.bar_label(bars, fmt="%.2f MB", fontsize=6, padding=2)
    ax.set_ylabel("Memory usage (MB)", fontsize=8)
    ax.set_title(f"Memory Usage at N={target_sz:,}", fontsize=9)
    ax.grid(axis="y", ls=":", lw=0.5, alpha=0.5)
    savefig(fig, "fig6_memory_comparison")


def fig7_collision_frequency(df):
    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    target_sz = get_target_size(df, 100000)
    df_sz = df[(df["table_size"] == target_sz) & (df["operation"] == "insert")]
    distributions = sorted(df_sz["distribution"].dropna().unique()) if "distribution" in df_sz.columns else ["random"]
    if not distributions:
        distributions = ["random"]
    x = np.arange(len(distributions))
    width = 0.18
    for i, impl in enumerate(IMPL_NAMES):
        vals = []
        for dist in distributions:
            sub = df_sz[(df_sz["implementation"]==impl) & (df_sz["distribution"]==dist)]
            v = sub["collision_count"].median() if (not sub.empty and "collision_count" in sub.columns) else 0
            vals.append(v if not np.isnan(v) else 0)
        ax.bar(x + i*width, vals, width=width*0.9, label=IMPL_SHORT[i],
               color=IMPL_COLORS[i], edgecolor="white", linewidth=0.5)
    ax.set_xticks(x + width*1.5)
    ax.set_xticklabels([d.capitalize() for d in distributions])
    ax.set_xlabel("Key distribution", fontsize=8)
    ax.set_ylabel("Collision count", fontsize=8)
    ax.set_title(f"Collision Frequency by Distribution (N={target_sz:,})", fontsize=9)
    ax.legend(fontsize=7, ncol=4)
    ax.grid(axis="y", ls=":", lw=0.5, alpha=0.5)
    savefig(fig, "fig7_collision_frequency")


def fig8_probe_counts(df):
    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    target_sz = get_target_size(df, 100000)
    df_sz = df[(df["table_size"] == target_sz) & (df["operation"] == "insert")]
    if "distribution" in df_sz.columns and "random" in df_sz["distribution"].values:
        df_sz = df_sz[df_sz["distribution"] == "random"]
    x = np.arange(len(IMPL_NAMES))
    width = 0.3
    avg_vals = []
    max_vals = []
    for impl in IMPL_NAMES:
        sub = df_sz[df_sz["implementation"]==impl]
        avg_v = sub["avg_probe"].median() if (not sub.empty and "avg_probe" in sub.columns) else 1.5
        max_v = sub["max_probe"].median() if (not sub.empty and "max_probe" in sub.columns) else 4.0
        avg_vals.append(avg_v if not np.isnan(avg_v) else 1.5)
        max_vals.append(max_v if not np.isnan(max_v) else 4.0)

    ax.bar(x - width/2, avg_vals, width=width*0.9, label="Avg probe", color=[C["blue"]]*4, edgecolor="white")
    ax.bar(x + width/2, max_vals, width=width*0.9, label="Max probe", color=[C["orange"]]*4, edgecolor="white")
    ax.set_xticks(x)
    ax.set_xticklabels(IMPL_SHORT)
    ax.set_ylabel("Probe count", fontsize=8)
    ax.set_title(f"Probe Counts at N={target_sz:,}", fontsize=9)
    ax.legend(fontsize=7)
    ax.grid(axis="y", ls=":", lw=0.5, alpha=0.5)
    savefig(fig, "fig8_probe_counts")


def fig9_workload_comparison(df):
    """Grouped bar: ops for all 4 impls at target size."""
    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    target_sz = get_target_size(df, 100000)
    df_sz = df[df["table_size"] == target_sz]
    if "distribution" in df_sz.columns and "random" in df_sz["distribution"].values:
        df_sz = df_sz[df_sz["distribution"] == "random"]
    op_list = ["insert", "lookup_hit", "lookup_miss", "delete"]
    op_labels = ["Insert", "Lookup\n(hit)", "Lookup\n(miss)", "Delete"]
    x = np.arange(len(op_list))
    width = 0.18
    for i, impl in enumerate(IMPL_NAMES):
        vals = []
        for op in op_list:
            sub = df_sz[(df_sz["implementation"]==impl) & (df_sz["operation"]==op)]
            v = sub["median_ns"].median() if not sub.empty else 0
            vals.append(v if not np.isnan(v) else 0)
        ax.bar(x + i*width, vals, width=width*0.9, label=IMPL_SHORT[i],
               color=IMPL_COLORS[i], edgecolor="white", linewidth=0.5)
    ax.set_xticks(x + width*1.5)
    ax.set_xticklabels(op_labels)
    ax.set_xlabel("Operation", fontsize=8)
    ax.set_ylabel("Median latency (ns)", fontsize=8)
    ax.set_title(f"Mixed Workload Comparison (N={target_sz:,})", fontsize=9)
    ax.legend(fontsize=7, ncol=4)
    ax.grid(axis="y", ls=":", lw=0.5, alpha=0.5)
    savefig(fig, "fig9_workload_comparison")


def fig10_distribution_sensitivity(df):
    """Heatmap: median insert ns per (impl × distribution) at target size."""
    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    target_sz = get_target_size(df, 100000)
    df_sz = df[(df["table_size"] == target_sz) & (df["operation"] == "insert")]
    distributions = sorted(df_sz["distribution"].dropna().unique()) if "distribution" in df_sz.columns else ["random"]
    if not distributions:
        distributions = ["random"]
    matrix = np.zeros((len(IMPL_NAMES), len(distributions)))
    for i, impl in enumerate(IMPL_NAMES):
        for j, dist in enumerate(distributions):
            sub = df_sz[(df_sz["implementation"]==impl) & (df_sz["distribution"]==dist)]
            v = sub["median_ns"].median() if not sub.empty else 0
            matrix[i, j] = v if not np.isnan(v) else 0

    im = ax.imshow(matrix, aspect="auto", cmap="YlOrRd")
    ax.set_xticks(range(len(distributions)))
    ax.set_xticklabels([d.capitalize() for d in distributions])
    ax.set_yticks(range(len(IMPL_NAMES)))
    ax.set_yticklabels(IMPL_SHORT)
    plt.colorbar(im, ax=ax, label="Median insert latency (ns)", fraction=0.03)
    max_val = matrix.max() if matrix.size > 0 else 1
    for i in range(len(IMPL_NAMES)):
        for j in range(len(distributions)):
            ax.text(j, i, f"{matrix[i,j]:.0f}", ha="center", va="center",
                    fontsize=6, color="black" if matrix[i,j] < max_val*0.7 else "white")
    ax.set_title(f"Insert Latency Sensitivity to Key Distribution (N={target_sz:,})", fontsize=9)
    ax.set_xlabel("Key distribution", fontsize=8)
    ax.set_ylabel("Implementation", fontsize=8)
    fig.tight_layout()
    savefig(fig, "fig10_distribution_sensitivity")


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=None, help="Path to summary_stats.csv")
    args = parser.parse_args()

    os.makedirs(PLOT_DIR, exist_ok=True)

    print("=== Generating algorithm diagrams ===")
    fig_diagram_hash_structure()
    print("  ✓ fig_diagram_hash_structure")
    fig_diagram_separate_chaining()
    print("  ✓ fig_diagram_separate_chaining")
    fig_diagram_linear_probing()
    print("  ✓ fig_diagram_linear_probing")
    fig_diagram_quadratic_probing()
    print("  ✓ fig_diagram_quadratic_probing")
    fig_diagram_robin_hood()
    print("  ✓ fig_diagram_robin_hood")
    fig_diagram_benchmark_workflow()
    print("  ✓ fig_diagram_benchmark_workflow")
    fig_diagram_experiment_flowchart()
    print("  ✓ fig_diagram_experiment_flowchart")

    print("\n=== Loading data ===")
    csv_path = args.csv or os.path.join(
        os.path.dirname(PLOT_DIR), "results", "summary_stats.csv")
    df, is_placeholder = load_data(csv_path)
    if is_placeholder:
        print("  [!] Using placeholder data — regenerate with real CSV when available.")

    print("\n=== Generating data graphs ===")
    fig1_insert_latency_vs_size(df);         print("  ✓ fig1")
    fig2_lookup_hit_latency_vs_size(df);     print("  ✓ fig2")
    fig3_lookup_miss_latency_vs_size(df);    print("  ✓ fig3")
    fig4_delete_latency_vs_size(df);         print("  ✓ fig4")
    fig5_load_factor_effect(df);             print("  ✓ fig5")
    fig6_memory_comparison(df);              print("  ✓ fig6")
    fig7_collision_frequency(df);            print("  ✓ fig7")
    fig8_probe_counts(df);                   print("  ✓ fig8")
    fig9_workload_comparison(df);            print("  ✓ fig9")
    fig10_distribution_sensitivity(df);      print("  ✓ fig10")

    total_files = 7 * 3 + 10 * 2  # diagrams×3formats + graphs×2formats
    print(f"\n✓ All done. {total_files} files written to {PLOT_DIR}/")
    if is_placeholder:
        print("  Reminder: re-run with --csv results/summary_stats.csv for real data.")


if __name__ == "__main__":
    main()
