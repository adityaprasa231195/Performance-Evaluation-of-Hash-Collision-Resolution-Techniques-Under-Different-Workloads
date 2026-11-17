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
        fontsize=7, bold=False, zorder=3, labelcolor=None):
    edgecolor = edgecolor or C["gray"]
    labelcolor = labelcolor or C["text"]
    r = FancyBboxPatch((x - w/2, y - h/2), w, h,
                        boxstyle="round,pad=0.02",
                        facecolor=facecolor, edgecolor=edgecolor,
                        linewidth=1.0, zorder=zorder)
    ax.add_patch(r)
    weight = "bold" if bold else "normal"
    ax.text(x, y, label, ha="center", va="center",
            fontsize=fontsize, color=labelcolor, weight=weight, zorder=zorder+1,
            wrap=True)


def new_diagram_fig(w_in=3.5, h_in=2.4, title=None):
    fig, ax = plt.subplots(figsize=(w_in, h_in))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    if title:
        ax.set_title(title, fontsize=9, pad=4)
    return fig, ax


# ─── Diagram 1: General Hash Table ───────────────────────────────────────────
def fig_diagram_hash_structure():
    fig, ax = new_diagram_fig(3.5, 2.5, "Hash Table: Key → Hash Function → Bucket")

    # Keys on left
    keys = ['"apple"', '"banana"', '"cherry"']
    key_y = [0.78, 0.60, 0.42]
    for k, y in zip(keys, key_y):
        box(ax, 0.13, y, 0.20, 0.10, k, facecolor="#eef4ff",
            edgecolor=C["blue"], fontsize=6)

    # Hash function box (center-left)
    box(ax, 0.42, 0.60, 0.20, 0.30, "hash(k)\nmod N",
        facecolor=C["blue"], edgecolor=C["blue"],
        labelcolor="white", fontsize=7, bold=True)

    # Arrow keys → hash
    for y in key_y:
        draw_arrow(ax, 0.24, y, 0.32, 0.60)

    # Bucket array (right)
    bucket_x = 0.72
    bucket_w = 0.18
    bucket_h = 0.095
    indices = list(range(5))
    bucket_top = 0.85
    for i in indices:
        by = bucket_top - i * (bucket_h + 0.025)
        fc = "#fff3cd" if i in (1, 3) else "white"
        ec = C["orange"] if i in (1, 3) else C["gray"]
        box(ax, bucket_x, by, bucket_w, bucket_h, f"[{i}]",
            facecolor=fc, edgecolor=ec, fontsize=6)

    # Arrows hash → buckets
    draw_arrow(ax, 0.52, 0.72, bucket_x - bucket_w/2, 0.85 - 0.0*(bucket_h+0.025))
    draw_arrow(ax, 0.52, 0.60, bucket_x - bucket_w/2, 0.85 - 1*(bucket_h+0.025))
    draw_arrow(ax, 0.52, 0.48, bucket_x - bucket_w/2, 0.85 - 3*(bucket_h+0.025))

    # Collision note
    ax.text(0.72, 0.85 - 1.5*(bucket_h+0.025), "← collision",
            ha="left", va="center", fontsize=6, color=C["orange"],
            style="italic")

    # Linked list hint from bucket[1]
    lx = bucket_x + bucket_w/2
    ly = 0.85 - 1*(bucket_h+0.025)
    ax.text(lx + 0.02, ly, "→ [k₁|v₁] → [k₂|v₂]",
            ha="left", va="center", fontsize=5.5, color=C["green"])

    # Labels
    ax.text(0.13, 0.90, "Keys", ha="center", fontsize=7, weight="bold")
    ax.text(0.72, 0.09, "Bucket Array (N slots)", ha="center", fontsize=6.5, color=C["gray"])

    savefig(fig, "fig_diagram_hash_structure")


# ─── Diagram 2: Separate Chaining ────────────────────────────────────────────
def fig_diagram_separate_chaining():
    fig, ax = new_diagram_fig(3.5, 2.6, "Separate Chaining: Insert & Lookup")

    n_buckets = 5
    bx, bw, bh = 0.18, 0.16, 0.10
    top_y = 0.84
    gap = 0.145

    chains = {
        0: [("k=0","v=0")],
        1: [("k=5","v=A"), ("k=10","v=B")],  # collision at bucket 1
        2: [],
        3: [("k=8","v=C")],
        4: [],
    }

    for i in range(n_buckets):
        by = top_y - i * gap
        fc = "#eef4ff" if chains[i] else "#f5f5f5"
        box(ax, bx, by, bw, bh, f"[{i}]",
            facecolor=fc, edgecolor=C["blue"], fontsize=6.5)

        prev_x = bx + bw/2
        for j, (k, v) in enumerate(chains[i]):
            nx = prev_x + 0.17
            ny = by
            fc2 = "#fff3cd" if i == 1 else "#efffef"
            box(ax, nx, ny, 0.16, bh, f"{k}\n{v}",
                facecolor=fc2, edgecolor=C["orange"] if i==1 else C["green"],
                fontsize=5.5)
            draw_arrow(ax, prev_x, ny, nx - 0.08, ny)
            prev_x = nx + 0.08

        # NULL at end
        nx = prev_x + 0.10
        if chains[i]:
            ax.text(nx, top_y - i*gap, "NULL", ha="center", va="center",
                    fontsize=5.5, color=C["gray"])

    # Lookup path annotation
    ax.annotate("lookup(k=10):\nbucket 1 → scan chain",
                xy=(0.26, top_y - 1*gap + 0.01),
                xytext=(0.03, top_y - 1*gap + 0.14),
                arrowprops=dict(arrowstyle="->", color=C["red"], lw=0.9),
                fontsize=5.5, color=C["red"])

    ax.text(0.18, 0.08, "O(1) avg insert · O(1+α) avg lookup · α = load factor",
            ha="center", fontsize=6, color=C["gray"])

    savefig(fig, "fig_diagram_separate_chaining")


# ─── Diagram 3: Linear Probing ───────────────────────────────────────────────
def fig_diagram_linear_probing():
    fig, ax = new_diagram_fig(3.5, 2.5, "Linear Probing: Collision & Tombstone")

    n = 8
    slot_w = 1.0 / (n + 1)
    slot_h = 0.18
    slot_y = 0.60

    contents = ["—", "k=1\nv=A", "k=9\nv=B", "[del]", "k=4\nv=C", "—", "—", "—"]
    colors   = ["#f5f5f5", "#eef4ff", "#fff3cd", "#ffdddd", "#efffef", "#f5f5f5","#f5f5f5","#f5f5f5"]
    edges    = [C["gray"], C["blue"], C["orange"], C["red"], C["green"],C["gray"],C["gray"],C["gray"]]

    xs = [(i + 1) * slot_w for i in range(n)]
    for i, (x, label, fc, ec) in enumerate(zip(xs, contents, colors, edges)):
        r = plt.Rectangle((x - slot_w*0.45, slot_y - slot_h/2), slot_w*0.9, slot_h,
                           facecolor=fc, edgecolor=ec, linewidth=1.0, zorder=3)
        ax.add_patch(r)
        ax.text(x, slot_y, label, ha="center", va="center", fontsize=5.5, zorder=4)
        ax.text(x, slot_y - slot_h/2 - 0.06, str(i), ha="center", fontsize=6,
                color=C["gray"])

    # Probe sequence for new key hash(k)=1 (slot 1 occupied)
    probe_y = slot_y + slot_h/2 + 0.12
    for step, idx in enumerate([1, 2, 3]):
        px = xs[idx]
        ax.annotate("", xy=(px, slot_y + slot_h/2),
                    xytext=(px, probe_y),
                    arrowprops=dict(arrowstyle="->",
                                   color=C["red"] if idx<3 else C["green"], lw=1.0))
        label = f"h+{step}" if step > 0 else "h(k)"
        ax.text(px, probe_y + 0.06, label, ha="center", fontsize=5.5, color=C["red"])

    ax.text(xs[3], probe_y + 0.06, "insert\nhere", ha="center", fontsize=5,
            color=C["green"])

    # Tombstone note
    ax.annotate("tombstone\n(deleted)", xy=(xs[3], slot_y),
                xytext=(xs[3] - 0.08, slot_y - 0.25),
                arrowprops=dict(arrowstyle="->", color=C["red"], lw=0.8),
                fontsize=5.5, color=C["red"], ha="center")

    ax.text(0.5, 0.05, "Probe: h(k), h(k)+1, h(k)+2, … (mod N)   Primary clustering risk",
            ha="center", fontsize=5.5, color=C["gray"])
    ax.text(0.5, 0.92, "Slot index →", ha="center", fontsize=6, color=C["gray"])

    savefig(fig, "fig_diagram_linear_probing")


# ─── Diagram 4: Quadratic Probing ────────────────────────────────────────────
def fig_diagram_quadratic_probing():
    fig, ax = new_diagram_fig(3.5, 2.5, "Quadratic Probing: h(k) + i²")

    n = 9
    slot_w = 1.0 / (n + 1)
    slot_h = 0.18
    slot_y = 0.58

    base = 2  # h(k) = 2
    probes = [base, (base+1)%n, (base+4)%n, (base+9)%n]  # h+0,h+1²,h+2²,h+3²
    contents = ["—"] * n
    for i, p in enumerate(probes[1:], 1):
        contents[p] = f"try {i}"
    contents[base] = "occupied"

    colors = []
    for i in range(n):
        if i == base: colors.append("#fff3cd")
        elif i in probes[1:]: colors.append("#eef4ff")
        else: colors.append("#f5f5f5")

    xs = [(i + 1) * slot_w for i in range(n)]
    for i, (x, label, fc) in enumerate(zip(xs, contents, colors)):
        r = plt.Rectangle((x - slot_w*0.45, slot_y - slot_h/2), slot_w*0.9, slot_h,
                           facecolor=fc,
                           edgecolor=C["orange"] if label=="occupied" else C["gray"],
                           linewidth=1.0, zorder=3)
        ax.add_patch(r)
        ax.text(x, slot_y, label, ha="center", va="center", fontsize=5.0, zorder=4)
        ax.text(x, slot_y - slot_h/2 - 0.06, str(i), ha="center", fontsize=6, color=C["gray"])

    # Probe arcs above
    arc_base_y = slot_y + slot_h/2 + 0.04
    offsets_labels = [(1, "h+1²"), (4, "h+2²"), (9, "h+3²")]
    for off, lbl in offsets_labels:
        dest = (base + off) % n
        # draw curved arrow
        x0 = xs[base]
        x1 = xs[dest]
        mid_x = (x0 + x1) / 2
        arc_h = 0.12 + 0.02 * off
        style = f"arc3,rad={-0.4 - 0.05*off}"
        ax.annotate("", xy=(x1, slot_y + slot_h/2),
                    xytext=(x0, slot_y + slot_h/2),
                    arrowprops=dict(arrowstyle="->",
                                   connectionstyle=style,
                                   color=C["blue"], lw=0.9))
        ax.text(mid_x, arc_base_y + arc_h, lbl, ha="center", fontsize=5.5,
                color=C["blue"])

    ax.text(xs[base], arc_base_y + 0.02, "h(k)", ha="center", fontsize=6,
            color=C["orange"], weight="bold")
    ax.text(0.5, 0.05, "Probe: h(k)+1, h(k)+4, h(k)+9, …   Reduces primary clustering",
            ha="center", fontsize=5.5, color=C["gray"])

    savefig(fig, "fig_diagram_quadratic_probing")


# ─── Diagram 5: Robin Hood Hashing ───────────────────────────────────────────
def fig_diagram_robin_hood():
    fig, ax = new_diagram_fig(3.5, 2.6, "Robin Hood Hashing: Displacement & Stealing")

    n = 7
    slot_w = 1.0 / (n + 1)
    slot_h = 0.17
    slot_y = 0.63

    # (key_label, displacement)
    slots = [
        ("—",    0,  "#f5f5f5", C["gray"]),
        ("k=A",  0,  "#eef4ff", C["blue"]),
        ("k=B",  1,  "#efffef", C["green"]),
        ("k=C",  2,  "#fff3cd", C["orange"]),  # displaced 2
        ("—",    0,  "#f5f5f5", C["gray"]),
        ("—",    0,  "#f5f5f5", C["gray"]),
        ("—",    0,  "#f5f5f5", C["gray"]),
    ]
    xs = [(i + 1) * slot_w for i in range(n)]

    for i, (x, (label, disp, fc, ec)) in enumerate(zip(xs, slots)):
        r = plt.Rectangle((x - slot_w*0.45, slot_y - slot_h/2), slot_w*0.9, slot_h,
                           facecolor=fc, edgecolor=ec, linewidth=1.0, zorder=3)
        ax.add_patch(r)
        ax.text(x, slot_y + 0.015, label, ha="center", va="center", fontsize=6, zorder=4)
        ax.text(x, slot_y - 0.030, f"d={disp}", ha="center", va="center",
                fontsize=5.0, color=C["gray"], zorder=4)
        ax.text(x, slot_y - slot_h/2 - 0.06, str(i), ha="center", fontsize=6,
                color=C["gray"])

    # Incoming entry with d=3 trying to insert at slot 3
    incoming_x = xs[3]
    incoming_y = slot_y + slot_h/2 + 0.22
    box(ax, incoming_x, incoming_y, 0.17, 0.11, "new: k=X\nd=3 → steal!",
        facecolor="#ffe0e0", edgecolor=C["red"], fontsize=5.5)
    draw_arrow(ax, incoming_x, incoming_y - 0.06, incoming_x, slot_y + slot_h/2 + 0.01)

    ax.annotate("d(X)=3 > d(C)=2\n→ evict C, insert X\nC probes forward",
                xy=(xs[4], slot_y + slot_h/2),
                xytext=(xs[5], slot_y + slot_h/2 + 0.18),
                fontsize=5.0, color=C["red"], ha="center",
                arrowprops=dict(arrowstyle="->", color=C["red"], lw=0.7))

    ax.text(0.5, 0.06, "Invariant: d(slot[i]) ≤ d(slot[i+1])   Equalises probe lengths",
            ha="center", fontsize=5.5, color=C["gray"])

    savefig(fig, "fig_diagram_robin_hood")


# ─── Diagram 6: Benchmark Workflow ───────────────────────────────────────────
def fig_diagram_benchmark_workflow():
    fig, ax = new_diagram_fig(3.5, 2.8, "Benchmark Workflow")

    steps = [
        ("Dataset\nCreation",    0.50, 0.87),
        ("Table Init\n(capacity)", 0.50, 0.73),
        ("Timed Ops\n(insert/lookup/delete)", 0.50, 0.57),
        ("Collect Stats\n(ns, probes, memory)", 0.50, 0.41),
        ("Write CSV\n(raw_experiments.csv)", 0.50, 0.25),
        ("Analysis &\nPlots", 0.50, 0.11),
    ]
    colors_box = [C["blue"], C["blue"], C["orange"], C["green"], C["green"], C["red"]]

    for i, ((label, x, y), fc) in enumerate(zip(steps, colors_box)):
        box(ax, x, y, 0.42, 0.095, label, facecolor=fc,
            edgecolor=fc, labelcolor="white", fontsize=6.5, bold=(i == 0))
        if i < len(steps) - 1:
            draw_arrow(ax, x, y - 0.048, steps[i+1][1], steps[i+1][2] + 0.048)

    # Side annotations
    ax.text(0.78, 0.57, "loop × sizes\n× load factors\n× distributions",
            ha="left", va="center", fontsize=5.5, color=C["orange"])
    ax.text(0.78, 0.25, "summary_stats.csv\naggregation",
            ha="left", va="center", fontsize=5.5, color=C["green"])

    savefig(fig, "fig_diagram_benchmark_workflow")


# ─── Diagram 7: Experiment Flowchart ─────────────────────────────────────────
def fig_diagram_experiment_flowchart():
    fig, ax = new_diagram_fig(3.5, 2.6, "Overall Research Workflow")

    nodes = [
        ("Literature\nReview",   0.14, 0.50, C["blue"]),
        ("Implementation\n(Rust)", 0.30, 0.50, C["blue"]),
        ("Unit\nTests",          0.46, 0.76, C["green"]),
        ("Benchmark\nSuite",     0.46, 0.50, C["orange"]),
        ("Statistical\nAnalysis", 0.62, 0.50, C["orange"]),
        ("Plots &\nDiagrams",    0.78, 0.76, C["red"]),
        ("Paper\n(LaTeX)",       0.78, 0.50, C["red"]),
        ("Submission",           0.78, 0.24, C["gray"]),
    ]

    for label, x, y, fc in nodes:
        box(ax, x, y, 0.14, 0.14, label, facecolor=fc,
            edgecolor=fc, labelcolor="white", fontsize=5.5)

    # Arrows
    edges = [
        (0, 1), (1, 2), (1, 3), (2, 3), (3, 4), (4, 5), (4, 6), (5, 6), (6, 7)
    ]
    for a, b in edges:
        x0, y0 = nodes[a][1], nodes[a][2]
        x1, y1 = nodes[b][1], nodes[b][2]
        draw_arrow(ax, x0 + 0.07*(1 if x1>x0 else -1),
                   y0 + 0.07*(1 if y1>y0 else (-1 if y1<y0 else 0)),
                   x1 - 0.07*(1 if x1>x0 else -1),
                   y1 - 0.07*(1 if y1>y0 else (-1 if y1<y0 else 0)))

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
