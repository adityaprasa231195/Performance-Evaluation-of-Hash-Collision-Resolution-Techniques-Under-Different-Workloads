# Performance Evaluation of Hash Collision Resolution Techniques Under Different Workloads

**Author & Contact Information:**
- **Author:** Aditya Kumar Harishankar Prasad
- **Email:** adityaprasa231195@gmail.com
- **GitHub Repository:** [https://github.com/adityaprasa231195/Performance-Evaluation-of-Hash-Collision-Resolution-Techniques-Under-Different-Workloads](https://github.com/adityaprasa231195/Performance-Evaluation-of-Hash-Collision-Resolution-Techniques-Under-Different-Workloads)
- **Primary Artifacts:** 21-page IEEE two-column research paper (`paper/main.pdf`), complete Rust implementation source code, automated test suite (70 tests), raw empirical benchmark data (3,920 runs), and 17 publication-quality vector figures.
- **License:** MIT License (Software) & Creative Commons Attribution 4.0 International (Data & Manuscript)

---

## 1. Research Overview & Abstract

Hash tables are fundamental components of modern computing infrastructure, serving as core primitives in databases, compiler symbol tables, runtime environments, in-memory caches, and distributed stream processors. Although asymptotic time complexity models under the Simple Uniform Hashing Assumption (SUHA) predict $O(1)$ average-case performance across standard collision resolution techniques, empirical execution times on modern superscalar processor architectures are heavily dominated by CPU cache hierarchies, memory access patterns, hardware prefetching, and allocation overheads.

This research package provides a comprehensive, rigorous, and fully reproducible empirical evaluation comparing the four primary hash collision resolution paradigms:
1. **Separate Chaining (SC):** Closed addressing using a vector-of-buckets with dynamically allocated node vectors (`Vec<Vec<(i64, i64)>>`).
2. **Linear Probing (LP):** Open addressing using a contiguous flat table with stride $c=1$, power-of-two capacity bitmask indexing, and tombstone-based lazy deletion.
3. **Quadratic Probing (QP):** Open addressing with triangular quadratic displacement ($h(k, i) = (h(k) + i^2) \pmod M$) over prime-capacity tables ensuring complete cycle coverage up to load factor $\alpha \le 0.50$.
4. **Robin Hood Hashing (RH):** Open addressing incorporating probe sequence length (PSL) displacement tracking, "rich-from-poor" element swapping, backward-shift deletion without tombstones, and early-termination search.

All data structures are engineered ground-up in idiomatic, safe Rust without using standard-library hash maps. A deterministic 64-bit FNV-1a hash function with an explicit seed is utilized across all implementations to eliminate hash variance and isolate collision resolution characteristics.

---

## 2. Key Empirical Findings

From 3,920 controlled benchmark executions across five data scales ($N = 10^3, 10^4, 5\times 10^4, 10^5, 10^6$), seven synthetic key distributions, and four primary operations:

1. **Hardware Cache Locality Dominance:**  
   At scales residing within the CPU L3 cache boundary ($N \le 10^5$), **Linear Probing** achieves the fastest successful lookup latency (12.29 ns at $N = 10^5$), substantially outperforming closed addressing due to contiguous spatial memory locality that maximizes CPU L1/L2 prefetcher hit rates.
2. **Primary Clustering Pathology in Linear Probing:**  
   Under heavy load and clustered key distributions, Linear Probing exhibits severe primary clustering, with maximum probe sequence lengths expanding up to 47–51 slots, leading to latency degradation during unsuccessful lookups and insertion cycles.
3. **Variance Compression in Robin Hood Hashing:**  
   Robin Hood hashing strictly equalizes probe distribution, bounding the maximum probe sequence length to $\le 12$ across all scales, load factors, and adversarial distributions. This yields exceptionally stable query performance and deterministic worst-case bounds, albeit at a $2.14\times$ insertion latency overhead ($64.59$ ns vs. $30.13$ ns for LP at $N = 10^5$) driven by displacement-induced memory write traffic.
4. **Pointer Indirection Penalty in Separate Chaining:**  
   Separate Chaining incurs significant allocation and pointer indirection overhead, consuming $1.39\times$ more memory than open addressing ($11.08$ MiB vs. $8.00$ MiB at $N = 10^5$). When data size exceeds the 25 MB L3 cache at $N = 10^6$, Separate Chaining insertion degrades to $102.44$ ns due to repeated DRAM line fills and allocator lock contention.
5. **Quadratic Probing as a Memory-Efficient Tradeoff:**  
   Quadratic Probing completely suppresses primary clustering while achieving the lowest physical memory footprint across all tested configurations ($4.58$ MiB at $N = 10^5$), demonstrating robust performance under uniform and sequential workloads.

---

## 3. Package Structure & File Manifest

```
├── README.md                         # Comprehensive project documentation & reproduction guide
├── LICENSE                           # MIT License
├── Cargo.toml / Cargo.lock           # Rust package configuration & pinned dependencies
├── references.bib                    # 24 verified academic BibTeX citations
│
├── 01_Reference_Papers/              # Literature inventory (literature_inventory.csv)
├── 02_Technical_Documentation/       # Hardware and OS architectural specifications
├── 03_Research_Notes/                # SUHA derivations, probe expectations & cache notes
│
├── src/                              # Complete Rust implementation source code
│   ├── lib.rs                        # Module exports and common interface
│   ├── main.rs                       # Interactive demonstration program
│   ├── hasher.rs                     # Deterministic FNV-1a hasher & capacity management
│   ├── separate_chaining.rs          # Separate Chaining implementation
│   ├── linear_probing.rs             # Linear Probing with tombstones
│   ├── quadratic_probing.rs          # Quadratic Probing with prime cycle guarantees
│   ├── robin_hood.rs                 # Robin Hood Hashing with backward-shift deletion
│   └── bin/
│       ├── experiment.rs             # Automated benchmark harness (3,920 runs)
│       └── stats_analysis.rs         # Statistical analysis engine (median, IQR, probe metrics)
│
├── tests/
│   └── correctness.rs                # 61 integration tests (+ 9 unit tests) against BTreeMap
│
├── benches/
│   └── benchmarks.rs                 # Criterion microbenchmarking harness
│
├── results/                          # Complete empirical dataset
│   ├── hardware_info.txt             # CPU cache, clock, and architecture specifications
│   ├── experiment_output.txt         # Raw console logs of benchmark execution
│   ├── raw_experiments.csv           # 3,920 individual trial records
│   └── summary_stats.csv             # 560 aggregated statistical records
│
├── plots/                            # 17 Vector figures & generation script
│   ├── plot_generation.py            # Python script for generating PDF, SVG, and PNG figures
│   ├── fig_diagram_*.pdf/.svg/.png   # 7 Algorithmic and workflow diagrams
│   └── fig1..10_*.pdf/.svg/.png      # 10 Empirical performance and probe distribution plots
│
└── paper/                            # Research manuscript sources & compiled PDF
    ├── main.pdf                      # Final 21-page IEEE two-column research paper
    ├── research_paper_hash_tables.pdf# Archival duplicate of the compiled paper
    ├── main.tex                      # IEEEtran LaTeX source code
    ├── paper.typ                     # Typst source code
    └── assemble_paper.py             # Paper generation and validation pipeline
```

---

## 4. Hardware and Environment Specifications

All empirical data were captured on a dedicated, quiet bare-metal workstation under thermal stabilization:
- **Processor:** Intel Core i7-12700F (12 physical cores, 20 execution threads; 8 Performance cores @ 4.90 GHz max boost, 4 Efficient cores @ 3.60 GHz)
- **Memory Hierarchy:** 
  - L1 Data Cache: 32 KB per core (8-way set associative)
  - L2 Unified Cache: 1.25 MB per P-core / 2 MB per E-cluster
  - L3 Unified Cache: 25 MB shared LLC
  - System RAM: 32 GB DDR4-3200 dual-channel
- **Operating System:** Linux x86_64 (CachyOS, kernel 6.13.0, CPU governor set to `performance`)
- **Compiler:** Rust toolchain `rustc 1.100.0` with compiler flags `-C opt-level=3 -C lto=thin -C target-cpu=native`

---

## 5. Verification & Reproduction Instructions

### Step 1: Automated Correctness Tests
To execute all 70 correctness unit and integration tests against standard reference implementations:
```bash
cargo test
```
*Expected result:* 70 tests passed (9 in `src/`, 61 in `tests/correctness.rs`), 0 failures.

### Step 2: Reproducing Benchmark Experiments
To run the full empirical battery of 3,920 trials across all scales, distributions, and operations:
```bash
cargo run --release --bin experiment
```
Measurements are written directly to `results/raw_experiments.csv`.

### Step 3: Statistical Aggregation
To calculate medians, interquartile ranges, probe sequence statistics, and collision metrics:
```bash
cargo run --release --bin stats_analysis
```
Summary statistics are compiled into `results/summary_stats.csv`.

### Step 4: Re-generating Figures & Diagrams
To generate all 17 vector plots in PDF, SVG, and 300 DPI PNG:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install matplotlib pandas numpy scipy
python plots/plot_generation.py --csv results/summary_stats.csv
```

### Step 5: Compiling Research Manuscript
To compile the 21-page IEEE two-column paper from source:
- **Using Typst (recommended):**
  ```bash
  typst compile paper/paper.typ paper/main.pdf
  ```
- **Using LaTeX (IEEEtran):**
  ```bash
  cd paper && pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
  ```

---

## 6. How to Cite This Research

If you use this dataset, implementation, or manuscript in your research, please cite:

```bibtex
@article{prasad2026hashperformance,
  author    = {Aditya Kumar Harishankar Prasad},
  title     = {Performance Evaluation of Hash Collision Resolution Techniques Under Different Workloads},
  year      = {2026},
  journal   = {Zenodo Research Repository},
  doi       = {10.5281/zenodo.XXXXXXX},
  url       = {https://github.com/adityaprasa231195/Performance-Evaluation-of-Hash-Collision-Resolution-Techniques-Under-Different-Workloads},
  note      = {Comprehensive empirical study, Rust implementations, and reproduction dataset}
}
```
