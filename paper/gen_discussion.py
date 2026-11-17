#!/usr/bin/env python3
"""
Section VII: Comparative Discussion and Architectural Insights
"""

def get_typst_discussion():
    return """
= VII. Comparative Discussion and Architectural Insights

The empirical findings presented in Section VI reveal profound microarchitectural interactions that explain the divergence between theoretical RAM model operation counts and physical wall-clock execution times.

== A. Microarchitectural Realities: Contiguity vs. Indirection (RQ6)

Modern superscalar x86_64 processors, such as the Intel Golden Cove architecture evaluated here, incorporate aggressive spatial prefetchers (the Data Prefetcher and Spatial Memory Streaming Prefetcher) designed to detect regular linear address strides @fowler2019, @richter2015. 

*The Contiguity Dividend of Linear Probing:* In our implementation, each `Slot` in Linear Probing occupies 24 bytes. Consequently, a single 64-byte L1 data cache line accommodates $64 / 24 approx 2.67$ table slots. When a collision occurs, probing index $\"idx\" + 1$ or $\"idx\" + 2$ almost certainly targets the exact same cache line already loaded into L1. If probing extends further, the hardware spatial prefetcher detects the sequential stride and prefetches adjacent cache lines into the L2 and L1 caches before instruction execution reaches them. This spatial locality explains why Linear Probing consistently achieves the highest lookup hit throughput ({12.29} ns at $N = 10^5$), despite having higher collision rates and longer average probe sequences than Separate Chaining or Robin Hood.

*The Indirection Penalty of Separate Chaining:* In stark contrast, Separate Chaining suffers from double indirection and memory fragmentation @vitter2001. Traversing a bucket requires:
+ Indexing into the primary table array `buckets[\"idx\"]` to retrieve the 24-byte `Vec` header (pointer, capacity, length).
+ Dereferencing the heap pointer -> access the dynamically allocated buffer storing the `(i64, i64)` tuples.
+ Scanning entries within the bucket.

Even if the primary bucket array resides in cache, the secondary heap buffer allocated by the global memory allocator (`mimalloc` or system `malloc`) frequently resides in a disparate, un-cached memory page. At large scales ($N = 10^6$), each lookup in Separate Chaining triggers a Translation Lookaside Buffer (TLB) lookup and an L3/DRAM access, incurring a 60–100 nanosecond penalty. This architectural reality explains why Separate Chaining's insertion latency escalates -> 102.44 ns at $N = 10^6$, whereas Linear Probing remains at 44.84 ns.

*Non-Linear Striding in Quadratic Probing:* Quadratic Probing provides an illuminating intermediate case. By stepping with quadratic increments $i^2 mod M$, the distance between successive probes expands rapidly ($Delta = 1, 3, 5, 7, 9, dots$ slots, corresponding -> $24, 72, 120, 168, dots$ bytes). After the initial probe, every subsequent quadratic probe straddles multiple cache lines, effectively defeating spatial hardware prefetchers. While QP eliminates primary clustering in algorithmic theory, its non-linear memory access pattern incurs a microarchitectural penalty, resulting in lookup hit latencies ({15.01} ns at $N = 10^5$) slightly higher than Linear Probing ({12.29} ns).

== B. The Cost of Variance Reduction: Robin Hood Displacement vs. Determinism

Our empirical data provides the first precise quantitative measurement of the "Robin Hood tax" in Rust systems programming:
- *Insertion Overhead:* At $N = 10^5$, Robin Hood insertion requires {64.59} ns per operation, compared to {30.18} ns for Linear Probing—a 114% overhead. This penalty arises directly from element displacement: when an inserted element displaces a "richer" resident, the CPU must write to the current slot, copy the resident into registers, increment probe distance counters, and continue a chain of write operations down the table. In a superscalar CPU, write operations allocate entries in the CPU Store Buffer; cascading displacements fill store buffers, causing pipeline stalls.
- *Lookup Determinism and SLA Guarantees:* In return for this insertion tax, Robin Hood delivers unmatched search determinism. Maximum probe length is restricted -> $<= 12$ across all scales, and lookup miss terminates in {19.91} ns (beating Linear Probing's {20.92} ns). For mission-critical systems, web proxies, and financial matching engines operating under strict Service Level Agreements (SLAs), tail latency (99th and 99.9th percentile response time) is far more critical than average throughput. Robin Hood hashing completely eliminates the catastrophic 40-->-50 probe outlier clusters that plague standard linear probing.

== C. Tombstones vs. Shifted Compaction in Deletion

Our evaluation quantitatively contrasts the two prevailing deletion paradigms:
- *Tombstone Invalidation:* Linear and Quadratic Probing mark deleted slots as `Tombstone` in $O(1)$ time ({13.78} ns and {15.56} ns at $N = 10^5$). However, tombstones are "ghost entries": they must be inspected during lookups, artificially elongating probe sequences and degrading search performance over long-running workloads with high churn. Furthermore, tombstones consume table capacity, forcing premature table resizes even when effective occupancy ($N / M$) is low.
- *Backward-Shift Compaction:* Robin Hood hashing incurs {18.57} ns at $N = 10^5$ to execute backward-shift compaction. Because maximum PSL is tightly bounded, backward-shift compaction rarely moves more than 2–4 elements. In exchange for ~4.8 ns of deletion overhead, Robin Hood guarantees zero tombstone accumulation, preserves table capacity, and maintains optimal search chain compaction without requiring full table rehashing.

== D. Algorithmic Trade-off Spectrum

Table 5 synthesizes the multidimensional trade-off spectrum across the four collision resolution paradigms.

#figure(
  table(
    columns: (1.5fr, 1.2fr, 1.2fr, 1.2fr, 1.2fr),
    stroke: none,
    align: (left, center, center, center, center),
    table.hline(stroke: 1pt),
    [#strong[Criterion]], [#strong[Chaining]], [#strong[Linear]], [#strong[Quadratic]], [#strong[Robin Hood]],
    table.hline(stroke: 0.5pt),
    [Lookup Hit Speed], [Moderate], [Fastest], [Fast], [Fast],
    [Lookup Miss Speed], [Fastest], [Moderate], [Moderate], [Fast],
    [Insertion Speed], [Slow], [Fastest], [Fast], [Moderate],
    [Tail Latency (99.9%)], [Poor], [Catastrophic], [Moderate], [Optimal],
    [Memory Efficiency], [Poor (Heap)], [Good], [Optimal], [Moderate],
    [Churn Resilience], [Optimal], [Poor (Tomb.)], [Poor (Tomb.)], [Optimal (Shift)],
    [SIMD Vectorizability], [None], [High], [Low], [High],
    table.hline(stroke: 1pt),
  ),
  caption: [Multidimensional engineering trade-off matrix for hash collision resolution techniques.],
) <tbl_tradeoff_spectrum>
"""
