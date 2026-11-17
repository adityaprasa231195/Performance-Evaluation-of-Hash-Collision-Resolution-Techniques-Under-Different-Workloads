#!/usr/bin/env python3
"""
Section V: Experimental Methodology
"""

def get_typst_methodology():
    return """
= V. Experimental Methodology

To ensure absolute reproducibility and empirical rigor, our benchmark methodology strictly controls hardware interference, enforces statistical sampling standards, and evaluates diverse workload distributions.

== A. Hardware and Execution Platform

All experiments were conducted on a dedicated bare-metal Linux workstation running CachyOS Linux (x86_64 architecture). The system specifications, verified via `/proc/cpuinfo` and `lscpu`, are as follows:
- *Processor:* 12th Gen Intel Core i7-12700F (Alder Lake microarchitecture) featuring 12 physical cores (8 Golden Cove Performance-cores and 4 Gracemont Efficient-cores) supporting 20 simultaneous execution threads.
- *Microarchitectural Cache Hierarchy:*
  - *L1 Data Cache:* 48 KiB per P-core (512 KiB total across instances), 12-way associative, 64-byte cache lines.
  - *L1 Instruction Cache:* 32 KiB per P-core (512 KiB total).
  - *L2 Unified Cache:* 1.25 MiB per P-core, 2.0 MiB per E-core cluster (12 MiB total), 10-way associative.
  - *L3 Shared Cache:* 25 MiB Intel Smart Cache shared across all cores, 16-way associative.
- *Main Memory:* 32 GiB DDR4 RAM in dual-channel configuration.
- *Toolchain and Compilation Flags:* `rustc 1.100.0` (channel: stable, release profile). Cargo release configuration specifies:
  ```toml
  [profile.release]
  opt-level = 3
  lto = "fat"
  codegen-units = 1
  panic = "abort"
  ```
  This ensures the LLVM compiler applies complete cross-crate Link-Time Optimization (LTO), aggressive function inlining, autovectorization, and dead-code elimination.

== B. Workload Characteristics and Synthetic Key Distributions

To thoroughly evaluate algorithmic behavior under diverse entropy conditions, we generate seven distinct synthetic key distributions ($K = upright("i64")$):
+ *Uniform Random (`random`):* Keys sampled uniformly from the entire 64-bit signed integer domain ($[-2^63, 2^63 - 1]$) via a deterministic pseudorandom number generator (`rand::rngs::StdRng`). This models general-purpose hash table workloads under high entropy.
+ *Sequential (`sequential`):* Monotonically increasing contiguous integers ($0, 1, 2, dots, N - 1$). Common in auto-incrementing database primary keys and streaming event IDs.
+ *Reverse Sequential (`reverse_sequential`):* Monotonically decreasing contiguous integers ($N - 1, N - 2, dots, 0$). Models descending priority queues and reverse chronological streams.
+ *Clustered (`clustered`):* Keys generated in dense periodic clusters ($k = upright("base") + delta$ where $delta in [0, 64]$ and cluster bases are spaced across the integer range). Tests resilience against spatial locality burst collisions.
+ *Collision-Heavy (`collision_heavy`):* Keys generated with fixed low-order bit patterns designed to produce identical bucket hash prefixes, deliberately forcing extreme collision rates -> stress resolution mechanics.
+ *Duplicate-Heavy (`duplicate_heavy`):* Workloads composed of $N$ insertions sampled from a very small universe of only 10 distinct keys ($k in [0, 9]$). Evaluates update-in-place efficiency, early membership hit detection, and absence of redundant table resizing.
+ *Small Range (`small_range`):* Keys uniformly distributed across a narrow bounded range ($k in [0, 1000]$), evaluating behavior when key cardinality is substantially smaller than table capacity.

== C. Experimental Design and Measurement Protocol

The experimental test matrix evaluates:
$ 4 " Impls" times 5 " Scales" times 7 " Dists" times 4 " Ops" $
Scale sizes span five orders of magnitude: $N in {10^3, 10^4, 10^5, 5 times 10^5, 10^6}$ elements. For each combination, seven independent trials ($T = 7$) are executed, yielding a total of:
$ 4 times 5 times 7 times 4 times 7 = 3920 " measurements" $
These are summarized into 560 aggregate rows in `results/summary_stats.csv`.

*Measurement Isolation:* For each trial, the benchmark harness pre-allocates datasets in memory before initiating timing -> prevent memory allocation or data generation overhead from contaminating measurements. Timing is performed using monotonic hardware cycle clocks via `std::time::Instant`. To eliminate CPU thermal throttling artifacts, warm-up runs precede each measurement phase.

== D. Performance Metrics and Statistical Rigor

In alignment with empirical algorithmics standards @sedgewick2011, we report both non-parametric and parametric statistics:
- *Median Latency (ns/op):* Robust indicator of central tendency unaffected by transient operating system interrupts.
- *Interquartile Range (IQR, ns/op):* Measure of statistical dispersion ($"IQR" = Q_3 - Q_1$).
- *Probe Sequence Length (PSL):* Average and maximum probe steps traversed during dictionary operations.
- *Collision Count:* Total number of times an insertion encountered a non-empty bucket upon primary hash dispatch.
- *Effective Load Factor ($alpha$):* Exact table density at benchmark completion ($alpha = N / M$).
- *Memory Footprint (Bytes / MiB):* Total heap allocation occupied by bucket structures, slot arrays, and metadata.
"""
