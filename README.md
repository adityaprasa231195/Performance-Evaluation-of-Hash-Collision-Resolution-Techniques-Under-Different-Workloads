# Performance Evaluation of Hash Collision Resolution Techniques Under Different Workloads

**Author:** Aditya Kumar Harishankar Prasad  
**Language & Toolchain:** Rust (rustc 1.100.0, edition 2021)  
**Host Hardware:** Intel Core i7-12700F (12 cores / 20 threads), 32 GB RAM, Linux x86_64 (CachyOS)  
**Research Paper:** IEEE Two-Column Format, 21 pages (`paper/main.pdf` and `paper/research_paper_hash_tables.pdf`)

---

## 1. Executive Summary

This repository contains a complete, academically rigorous, and fully reproducible empirical computer science research study comparing four fundamental hash collision resolution strategies:
1. **Separate Chaining (SC):** Vector-of-vectors (`Vec<Vec<(i64, i64)>>`) closed addressing.
2. **Linear Probing (LP):** Contiguous flat array with tombstone-based lazy deletion.
3. **Quadratic Probing (QP):** Prime-capacity triangular quadratic offsets ($h(k, i) = (h(k) + i^2) \pmod M$) guaranteeing complete cycle coverage.
4. **Robin Hood Hashing (RH):** Contiguous open addressing with probe sequence length (PSL) displacement tracking, "rich-from-poor" element swapping, backward-shift deletion without tombstones, and early-termination search.

All implementations operate on 64-bit signed integer key-value pairs (`(i64, i64)`), share a deterministic 64-bit FNV-1a hash function with an explicit seed, and do **not** rely on standard library hash tables for collision resolution.

The research includes:
- **70 automated correctness tests** verifying identical semantics against standard `BTreeMap`.
- **3,920 raw benchmark executions** across 5 scales ($10^3$ to $10^6$), 7 synthetic key distributions, 4 operations (insert, lookup hit, lookup miss, delete), and 7 independent repetitions.
- **560 aggregated statistical summary rows** (medians, interquartile ranges, means, extrema, probe counts, collision counts, load factors, memory footprints).
- **17 publication-quality vector figures** (7 algorithmic architecture diagrams + 10 empirical data graphs).
- **21-page IEEE two-column research paper** compiled to PDF via Typst and provided in LaTeX (`main.tex`).

---

## 2. Repository Structure

```
/home/aditta/Downloads/hash table/
├── Cargo.toml                    # Cargo manifest (dependencies: criterion, rand)
├── Cargo.lock                    # Dependency lockfile
├── README.md                     # This documentation file
├── references.bib                # 24 verified academic BibTeX citations
│
├── 01_Reference_Papers/          # Literature review inventory and downloads
│   └── literature_inventory.csv  # 24 entries with DOIs, venues, methodology, and review status
├── 02_Technical_Documentation/   # Technical architecture and compiler specifications
├── 03_Research_Notes/            # Analytical formulations and SUHA derivations
│   └── theoretical_notes.md      # Expected probe counts, cache analysis, and complexity tables
│
├── src/                          # Rust implementation source code
│   ├── lib.rs                    # Library module exports
│   ├── main.rs                   # Interactive demonstration binary
│   ├── hasher.rs                 # Deterministic FNV-1a hasher & prime/pow2 capacity helpers
│   ├── separate_chaining.rs      # Separate Chaining implementation
│   ├── linear_probing.rs         # Linear Probing implementation
│   ├── quadratic_probing.rs      # Quadratic Probing implementation
│   ├── robin_hood.rs             # Robin Hood Hashing implementation
│   └── bin/
│       ├── experiment.rs         # Benchmark runner (3,920 runs across 7 distributions)
│       └── stats_analysis.rs     # Statistical aggregator (median, IQR, probe statistics)
│
├── tests/
│   └── correctness.rs            # 61 integration tests (+ 9 unit tests in src/) against BTreeMap
│
├── benches/
│   └── benchmarks.rs             # Criterion microbenchmarks
│
├── results/                      # Empirical benchmark measurements
│   ├── hardware_info.txt         # CPU, cache hierarchy, memory, and kernel specifications
│   ├── experiment_output.txt     # Complete console logs of benchmark execution
│   ├── raw_experiments.csv       # 3,920 raw trial rows
│   └── summary_stats.csv         # 560 statistical summary rows
│
├── plots/                        # Diagrams and data visualization
│   ├── plot_generation.py        # Python script for generating SVG, PDF, and PNG figures
│   ├── fig_diagram_*.svg/.pdf    # 7 Algorithmic and experimental workflow diagrams
│   └── fig1..10_*.svg/.pdf       # 10 Empirical data plots
│
└── paper/                        # Final research paper manuscript
    ├── main.pdf                  # 21-page IEEE two-column compiled paper
    ├── research_paper_hash_tables.pdf # Archive copy of the compiled paper
    ├── main.tex                  # LaTeX IEEEtran conference source
    ├── paper.typ                 # Typst source code
    └── assemble_paper.py         # Paper generator and validator
```

---

## 3. Build & Correctness Verification

### Prerequisites
- Rust stable toolchain (`rustc >= 1.80.0`, tested on `1.100.0`)
- Cargo
- Python 3 with `matplotlib`, `pandas`, `numpy`, `scipy` (installed in `.venv`)
- `typst` (optional, for recompiling the paper PDF)

### Compile the Library and Binaries
```bash
cargo build --release
```

### Run Correctness Tests
```bash
cargo test
```
**Expected Result:** 70 passed tests (9 unit tests in `src/` + 61 comprehensive tests in `tests/correctness.rs`). Zero failures.

---

## 4. Reproducing the Benchmarks

To re-run the complete benchmark battery and re-generate the raw measurement CSV files:

```bash
# 1. Execute the 3,920 benchmark trials across all scales, distributions, and operations
cargo run --release --bin experiment

# 2. Compute median, IQR, probe metrics, and summary tables
cargo run --release --bin stats_analysis

# 3. Optional: Run Criterion microbenchmarks
cargo bench
```

All raw measurements will be updated in `results/raw_experiments.csv`, and statistical summaries in `results/summary_stats.csv`.

---

## 5. Re-generating Figures and Diagrams

To re-generate all 17 vector diagrams and empirical data plots:

```bash
# Using the local virtual environment:
.venv/bin/python plots/plot_generation.py --csv results/summary_stats.csv
```

Outputs will be saved in `plots/` in SVG, PDF, and 300 DPI PNG formats.

---

## 6. Compiling the Research Paper

The research paper is written in both **Typst** and **LaTeX (IEEEtran)**.

To compile the Typst version to PDF:
```bash
cd paper
typst compile paper.typ main.pdf
```

To compile the LaTeX version (requires `pdflatex` or `tectonic` and IEEEtran):
```bash
cd paper
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

---

## 7. Key Empirical Findings

1. **Hardware Cache Locality Dominance:**  
   At scales fitting within L3 cache ($N \le 10^5$), **Linear Probing** achieves the lowest lookup latency (12.29 ns), directly benefiting from CPU spatial hardware prefetchers scanning contiguous array slots.
2. **Primary Clustering in Linear Probing:**  
   Despite superior mean latency, Linear Probing suffers severe primary clustering, with maximum probe sequence lengths expanding up to 47–51 slots under clustered and random workloads.
3. **Variance Compression in Robin Hood Hashing:**  
   Robin Hood hashing restricts the maximum probe length to $\le 12$ across all scales and workloads, providing deterministic worst-case query times. However, this comes at an insertion latency penalty ($64.59$ ns at $N=10^5$) due to element displacement store traffic.
4. **Pointer Chasing Penalty in Separate Chaining:**  
   Separate Chaining degrades significantly once memory usage exceeds CPU cache sizes ($102.44$ ns insertion at $N=10^6$), requiring $1.39\times$ more memory than open addressing due to heap allocation metadata.
5. **Quadratic Probing as an Optimal Compromise:**  
   Quadratic Probing completely eliminates primary clustering while maintaining the lowest physical memory footprint across all tested scales ($4.58$ MiB at $N=10^5$).
