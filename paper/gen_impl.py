#!/usr/bin/env python3
"""
Section IV: Rust Implementation and Benchmark Architecture
"""

def get_typst_impl():
    return """
= IV. Rust Implementation and Benchmark Architecture

To guarantee reproducible, high-performance evaluation, all four collision resolution algorithms and supporting test harnesses were implemented from first principles in Rust (`rustc 1.100.0`, edition 2021).

#figure(
  image("plots/fig_diagram_benchmark_workflow.png", width: 95%),
  caption: [Benchmark execution workflow illustrating deterministic key generation, pre-population, timed multi-trial execution, and statistical metrics aggregation.],
) <fig_benchmark_workflow>

== A. Language and Type Safety Guarantees

Rust was selected as the implementation vehicle due to its unique combination of memory safety without garbage collection, predictable memory layouts, and zero-cost abstractions @antras2018. In C and C++, manual memory management often introduces undefined behavior (use-after-free, dangling pointers, data races), while in Java or Go, the presence of an asynchronous garbage collector introduces unpredictable latency spikes and object metadata bloat. Rust's strict compile-time borrow checker guarantees exclusive mutability (`&mut self`) during dictionary modifications and shared immutability (`&self`) during concurrent queries, compiling directly to optimized native machine code via the LLVM compiler backend.

== B. Deterministic Hash Infrastructure

A critical requirement in empirical collision studies is isolating the performance of collision resolution mechanics from hash function variation. Standard library hash tables frequently incorporate randomized keys (such as SipHash-1-3 or AHash) to prevent Denial-of-Service (DoS) hash collision attacks @antras2018. However, non-deterministic random seeds introduce run-to-run variance that obscures algorithmic comparison.

To enforce absolute reproducibility across runs and machine architectures, we implement the 64-bit Fowler-Noll-Vo (FNV-1a) hash function @fowler2019. The FNV-1a algorithm processes the 8 raw bytes of each 64-bit signed integer key (`i64`) in strict little-endian order (`key.to_le_bytes()`):
$ h_0 = "FNV_OFFSET_BASIS" = 14695981039346656037 $
$ h_(j+1) = (h_j xor b_j) times "FNV_PRIME" mod 2^64 $
where $upright("FNV_PRIME") = 1099511628211$. The slot index is computed as:
$ "idx" = (h_8 " as usize") mod M $

For quadratic probing, table resizing requires prime capacities. We implement an optimized trial-division primality tester (`next_prime(n)`) that checks odd integers skipping multiples of 2 and 3, ensuring rapid table allocation up -> millions of entries. For linear probing, separate chaining, and Robin Hood hashing, power-of-two sizing is maintained via bitwise operations (`next_power_of_two()`).

== C. Collision Resolution Implementations

Each hash table variant is encapsulated within a distinct Rust module with zero external crate dependencies:

+ *`SeparateChaining`:* Stores entries in a contiguous `Vec<Vec<(i64, i64)>>`. When table load factor $alpha = N / M > 0.75$, bucket capacity is doubled, and all key-value pairs are rehashed into the new bucket array.
+ *`LinearProbing`:* Stored as `Vec<Slot>` where `Slot` is a 24-byte enum (`Empty`, `Occupied(i64, i64)`, `Tombstone`). Load factor threshold is enforced at $0.70$ based on total non-empty slots ($(N_"occ" + N_"tomb") / M$).
+ *`QuadraticProbing`:* Stored as `Vec<Slot>` with prime capacity $M$. Threshold is set strictly -> $alpha <= 0.50$, resizing -> the smallest prime $M prime >= 2 M$ -> guarantee cycle coverage.
+ *`RobinHood`:* Stored as `Vec<RhSlot>` where `RhSlot` is either `Empty` or `Occupied { key: i64, val: i64, dist: usize }` (32 bytes per slot on 64-bit systems). Load threshold is enforced at $alpha <= 0.70$.

#figure(
  image("plots/fig_diagram_experiment_flowchart.png", width: 95%),
  caption: [Experimental measurement flowchart detailing dataset synthesis, warm-up iterations, hardware performance counter sampling, and multi-trial statistics generation.],
) <fig_experiment_flowchart>

== D. Deletion Strategies

Deletion mechanics represent one of the starkest differentiators between open-addressing schemes:
- *Chaining Removal:* Separate Chaining scans the target bucket and performs `Vec::swap_remove`, achieving $O(1)$ removal without maintaining bucket order.
- *Lazy Tombstone Deletion:* Linear and Quadratic Probing replace the target entry with a `Slot::Tombstone` marker. While achieving immediate $O(1)$ execution, tombstones remain in the table, extending subsequent probe sequences until cleared during a table resize.
- *Backward-Shift Compaction:* Robin Hood hashing executes backward-shift deletion @celis1986. Subsequent entries are shifted one slot backward until an entry with $"dist" = 0$ or an `Empty` slot is encountered. This preserves probe sequence continuity, guarantees zero tombstone accumulation, and maintains the early-termination search invariant.

== E. Benchmark Suite and Harness Architecture

The benchmarking infrastructure consists of two complementary harnesses:
+ *Criterion 0.5 Benchmark Harness:* Utilized for high-precision micro-benchmarking with outlier rejection, warm-up phases, and Welch's t-test validation (`benches/benchmarks.rs`).
+ *Custom High-Throughput Multi-Trial Runner:* Implemented in `src/bin/experiment.rs` and `src/bin/stats_analysis.rs`. To accurately measure per-operation latency across large scales ($N = 10^6$), the runner executes full batch operations, measures total elapsed time via `std::time::Instant`, and divides by $N$ to yield nanoseconds per operation. Each experimental condition is executed across 7 independent trials, recording median, interquartile range (IQR), mean, standard deviation, minimum, maximum, collision counts, average PSL, maximum PSL, effective load factor, and memory consumption.
"""
