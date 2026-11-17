#!/usr/bin/env python3
"""
Section IX: Threats to Validity
"""

def get_typst_validity():
    return """
= IX. Threats to Validity

To facilitate objective interpretation of our findings, we discuss potential threats to internal, external, and construct validity.

== A. Internal Validity

Internal validity addresses whether the observed experimental variations are attributable directly to the evaluated collision resolution algorithms rather than experimental artifacts or systematic measurement errors.
- *Hash Function Selection:* All implementations utilized the 64-bit Fowler-Noll-Vo (FNV-1a) hash function. While FNV-1a provides deterministic, reproducible byte-level mixing with minimal CPU instruction overhead, its avalanche properties are inferior to cryptographic constructions (e.g., SipHash-1-3) or hardware-accelerated algorithms (e.g., AES-NI-based AHash). Under distributions with highly structured higher-order bits, hash bias may interact with probing sequences. We mitigated this by evaluating seven distinct key distributions, including adversarial collision-heavy patterns.
- *Timing Precision and System Interference:* Operating system context switches, page faults, CPU frequency scaling (Intel Speed Step / Turbo Boost), and background kernel threads can introduce timing jitter. We mitigated these threats by: (i) executing benchmarks on dedicated hardware, (ii) pre-allocating memory buffers before timing initiation, (iii) running 7 independent trials per condition, and (iv) utilizing non-parametric median and IQR statistics rather than arithmetic means to reject outlier contamination.
- *Compiler Optimizations:* Rust 1.100.0 utilizing LLVM 19 applies sophisticated compiler optimizations (loop unrolling, autovectorization, inlining). Subtle differences in struct layout can cause the compiler to vectorize certain probe loops while leaving others scalar. We minimized compilation bias by enforcing identical release profile flags (`opt-level = 3`, `lto = "fat"`, `codegen-units = 1`) across all benchmark binaries.

== B. External Validity

External validity considers the extent to which our empirical findings generalize to broader software systems and diverse deployment environments.
- *Key and Payload Types:* Our experiments focused exclusively on 64-bit signed integer keys and 64-bit signed integer values (`(i64, i64)`). This 16-byte payload fits cleanly within CPU cache lines. However, real-world systems software frequently stores variable-length strings, polymorphic objects, or large binary blobs. Large payloads expand slot sizes (e.g., 64 or 128 bytes per slot), drastically reducing the number of slots per cache line and diminishing the spatial prefetching advantage of Linear Probing. In such scenarios, Separate Chaining (storing pointers to heap-allocated objects) or indirect open-addressing tables often become more competitive.
- *Single-Threaded vs. Concurrent Execution:* Our benchmarks evaluate single-threaded hash table operations. Concurrent key-value stores (e.g., `crossbeam-skiplist`, `evmap`, or `dashmap`) utilize fine-grained bucket mutexes, read-copy-update (RCU), or lock-free compare-and-swap (CAS) primitives. In concurrent environments, open addressing is significantly more difficult to synchronize than separate chaining, because displaced elements in Robin Hood hashing or contiguous clusters in Linear Probing require multi-slot atomic coordination @maier2019.

== C. Construct Validity

Construct validity assesses whether our experimental metrics accurately capture real-world algorithmic performance.
- *Tombstone Saturation Dynamics:* In our methodology, deletion benchmarks measured the time required to delete pre-inserted keys from a populated table. However, in long-running production server workloads, tables experience millions of interleaved insertions, deletions, and updates ("churn"). In linear and quadratic probing, tombstones accumulate continuously over time, gradually degrading lookup performance until a resize or compaction is forced. A single-phase benchmark may underestimate the long-term degradation of tombstone-based open addressing compared to Robin Hood's backward-shift compaction.
"""
