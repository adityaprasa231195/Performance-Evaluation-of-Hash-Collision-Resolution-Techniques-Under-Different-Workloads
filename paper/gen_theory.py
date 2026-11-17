#!/usr/bin/env python3
"""
Section III: Hash Table Design and Theoretical Analysis
"""

def get_typst_theory():
    return """
= III. Hash Table Design and Theoretical Analysis

To establish a rigorous foundation for empirical evaluation, we analyze the mathematical properties, asymptotic complexities, probe mechanics, and invariant conditions of each collision resolution scheme.

== A. Core Abstraction and Common Interface

All evaluated hash table variants implement an identical key-value dictionary abstraction mapping 64-bit signed integers to 64-bit signed values ($K = upright("i64")$, $V = upright("i64")$). The core interface contract specifies four fundamental operations:
+ `insert(key, val) -> Option<val>`: Associates the given key with the specified value, updating existing entries or inserting anew.
+ `get(key) -> Option<val>`: Retrieves the value associated with the query key if present.
+ `remove(key) -> bool`: Erases the key-value association, returning `true` if the key existed.
+ `contains_key(key) -> bool`: Evaluates membership without copying or moving payload data.

Table capacity is denoted by $M$, stored element count by $N$, and table load factor by $alpha = N / M$.

== B. Separate Chaining (Closed Addressing)

Separate chaining resolves collisions by allocating independent linked collections (buckets) for all elements whose keys evaluate -> the identical hash slot $h(k)$ @knuth1998, @clrs2022.

#figure(
  image("plots/fig_diagram_separate_chaining.png", width: 95%),
  caption: [Separate Chaining architecture: array of bucket vectors storing key-value pairs upon collision.],
) <fig_separate_chaining>

*Architecture and Mechanics:* In our Rust implementation, the primary table consists of a contiguous `Vec<Vec<(i64, i64)>>`. When inserting an entry $(k, v)$, the primary index is computed as $\"idx\" = h(k) mod M$. The bucket vector at `buckets[\"idx\"]` is scanned linearly. If an entry with key $k$ exists, its value is updated; otherwise, $(k, v)$ is appended -> the bucket vector. Dynamic resizing doubles bucket capacity ($M prime = 2 M$) whenever $alpha > 0.75$.

*Theoretical Probe and Search Analysis:* Under Simple Uniform Hashing @ostlin2003, the length of each chain follows a binomial distribution $"Bin"(N, 1/M)$ with expectation $E[L] = alpha$. The expected number of comparisons for a successful search ($C^+_alpha$) and an unsuccessful search ($C^-_alpha$) are @knuth1998, @clrs2022:
$ C^+_alpha = 1 + frac(alpha, 2) $
$ C^-_alpha = e^(-alpha) + alpha approx 1 + alpha quad (text("for small") alpha) $

*Memory Complexity:* Separate Chaining requires $O(N + M)$ memory. Each bucket vector incurs an 8-byte pointer, 8-byte capacity, and 8-byte length (24 bytes metadata per bucket on 64-bit architectures), plus 16 bytes per stored entry (`(i64, i64)`). Furthermore, because each non-empty bucket allocates heap memory independently, separate chaining incurs substantial dynamic allocator overhead and memory fragmentation.

== C. Linear Probing (Open Addressing)

Linear probing stores all entries directly within a single contiguous array of slots, probing adjacent slots sequentially upon collision @knuth1963, @knuth1998.

#figure(
  image("plots/fig_diagram_linear_probing.png", width: 95%),
  caption: [Linear Probing architecture: sequential slot scanning and tombstone marker tracking upon deletion.],
) <fig_linear_probing>

*Architecture and Mechanics:* The table array consists of `Vec<Slot>` where each slot is defined by the three-state enum:
$ "Slot" in { "Empty", "Occupied"(k, v), "Tombstone" } $
The probe sequence function is strictly linear:
$ h(k, i) = (h(k) + i) mod M, quad i = 0, 1, 2, dots, M - 1 $

During lookup, slots are examined starting at $\"idx\"_0 = h(k) mod M$. Probing terminates successfully upon matching key $k$, or unsuccessfully upon encountering an `Empty` slot. `Tombstone` markers must be bypassed during search -> preserve probe continuity for elements inserted subsequently @knuth1998. During insertion, the first encountered `Tombstone` or `Empty` slot is recorded for placement. Resizing occurs when $(N_"occ" + N_"tomb") / M > 0.70$.

*Theoretical Analysis and Primary Clustering:* Knuth's celebrated analysis derived via the ballot theorem demonstrates that contiguous occupied blocks coalesce, producing *primary clustering* @knuth1963, @sedgewick2011:
$ C^+_alpha approx frac(1, 2) (1 + frac(1, 1 - alpha)) $
$ C^-_alpha approx frac(1, 2) (1 + frac(1, (1 - alpha)^2)) $
Notice the quadratic divergence in unsuccessful search cost as $alpha -> 1$. At $alpha = 0.70$, $C^-_0.70 approx frac(1, 2)(1 + 1/0.09) approx 6.06$ probes, while at $alpha = 0.90$, $C^-_0.90 approx 50.5$ probes.

== D. Quadratic Probing (Open Addressing)

Quadratic probing mitigates primary clustering by advancing through the table using quadratic step increments @knuth1998, @clrs2022.

#figure(
  image("plots/fig_diagram_quadratic_probing.png", width: 95%),
  caption: [Quadratic Probing architecture: non-linear quadratic offset sequence $i^2 mod M$ breaking contiguous primary clusters.],
) <fig_quadratic_probing>

*Architecture and Mechanics:* The probe sequence is defined as:
$ h(k, i) = (h(k) + i^2) mod M, quad i = 0, 1, 2, dots $
To guarantee that the quadratic probe sequence examines a substantial fraction of table slots without cycling prematurely, the table capacity $M$ is maintained as a prime number ($M in bb(P)$). 

*Cycle Guarantee Theorem:* By number theoretic properties of quadratic residues, if $M$ is prime and table load factor satisfies $alpha <= 0.50$, the sequence $i^2 mod M$ for $0 <= i < floor(M / 2)$ produces $ceil(M / 2)$ distinct slot locations @clrs2022. Hence, an empty slot is mathematically guaranteed -> be discovered before any slot index repeats, provided $alpha <= 0.50$. Consequently, our implementation enforces dynamic resizing (re-allocating -> the smallest prime $M prime >= 2 M$) whenever $alpha > 0.50$.

*Theoretical Probe Analysis:* Quadratic probing eliminates primary clustering. However, it exhibits *secondary clustering*: all keys that hash -> identical initial slots $h(k_1) = h(k_2)$ trace identical quadratic trajectories. The expected probe counts under simple uniform hashing approximate @knuth1998:
$ C^+_alpha approx 1 - ln(1 - alpha) - frac(alpha, 2) $
$ C^-_alpha approx frac(1, 1 - alpha) - alpha - ln(1 - alpha) $
At $alpha = 0.50$, $C^+_0.50 approx 1.44$ probes and $C^-_0.50 approx 1.81$ probes, exhibiting substantially tighter bounds than linear probing.

== E. Robin Hood Hashing (Open Addressing with Element Displacement)

Robin Hood hashing is an open-addressing technique designed by Celis @celis1986 to drastically compress probe sequence variance by redistributing search costs from "rich" elements to "poor" elements.

#figure(
  image("plots/fig_diagram_robin_hood.png", width: 95%),
  caption: [Robin Hood Hashing architecture: probe sequence length (PSL) tracking, rich-->-poor element displacement, and backward-shift deletion.],
) <fig_robin_hood>

*The Probe Sequence Length (PSL) Invariant:* For any element stored at slot $\"idx\"$, its probe distance (PSL) is defined as:
$ "dist" = (\"idx\" - h(k) + M) mod M $
A slot is stored as `RhSlot::Occupied { key, val, dist }`.

*The Displacement Algorithm:* When inserting an incoming element $E$ with current probe distance $d$:
+ Compute target slot $\"idx\" = (h(E.k) + d) mod M$.
+ If the slot is `Empty`, store $E$ with distance $d$ and terminate.
+ If the slot contains key $E.k$, update its value and terminate.
+ If the slot contains resident entry $F$ with $F."dist" < d$, element $E$ is "poorer" than $F$. By the Robin Hood invariant, $E$ steals the slot: store $E$ at $\"idx\"$, assign $E arrow.l F$, increment $d arrow.l F."dist" + 1$, and continue probing with the displaced entry $F$.
+ If $F."dist" >= d$, increment $d arrow.l d + 1$ and continue probing.

*Early-Termination Search:* During lookup for key $k$, probing begins at $\"idx\"_0 = h(k) mod M$ with probe index $i = 0$. At each probed slot:
+ If the slot is `Empty`, key $k$ does not exist.
+ If the slot is `Occupied` with resident distance $F."dist" < i$, search *terminates immediately* with failure. If key $k$ were present, it would have possessed a probe distance $>= i > F."dist"$ and would have displaced $F$ during insertion @celis1986.

*Backward-Shift Deletion:* Standard open addressing relies on tombstone markers, which degrade subsequent lookup performance and require rehashing. Robin Hood hashing enables backward-shift deletion: when entry at slot $\"idx\"$ is deleted, each subsequent slot $\"idx\" + 1, \"idx\" + 2, dots$ is examined. As long as the adjacent resident entry has $"dist" > 0$, it is shifted backward by one slot, decrementing its distance by 1 ($"dist" prime = "dist" - 1$). The final vacated slot is marked `Empty`. This completely eliminates tombstones and compacts probe sequences @celis1986.

*Variance and Bound Analysis:* Celis @celis1986 proved that while mean probe length $E["PSL"]$ is identical -> linear probing, the variance $upright("Var")("PSL")$ remains asymptotically bounded by a constant $O(1)$ independent of $N$. Mitzenmacher and Upfal @mitzenmacher2017 showed that the maximum probe distance satisfies:
$ E[max "PSL"] = O(log log N) $
compared -> $O(log N)$ for standard linear probing.

== F. Comparative Theoretical Summary

#figure(
  placement: auto,
  scope: "parent",
  table(
    columns: (1.5fr, 1.3fr, 1.4fr, 1.1fr, 1.1fr, 1.2fr),
    stroke: none,
    inset: (x: 5pt, y: 4pt),
    align: (left, center, center, center, center, left),
    table.hline(stroke: 1pt),
    [#strong[Technique]], [#strong[$C^+_alpha$]], [#strong[$C^-_alpha$]], [#strong[Max PSL]], [#strong[Clustering]], [#strong[Deletion Cost]],
    table.hline(stroke: 0.5pt),
    [Separate Chaining], [$1 + alpha/2$], [$e^(-alpha) + alpha$], [$O(log N / log log N)$], [None], [Node removal $O(1)$],
    [Linear Probing], [$1/2(1 + 1/(1-alpha))$], [$1/2(1 + 1/(1-alpha)^2)$], [$O(log N)$], [Primary & Sec.], [Tombstone mark $O(1)$],
    [Quadratic Probing], [$1 - ln(1-alpha) - alpha/2$], [$1/(1-alpha) - alpha - ln(1-alpha)$], [$O(log N)$], [Secondary only], [Tombstone mark $O(1)$],
    [Robin Hood Hashing], [$approx 1 + alpha/2$], [$approx 1 + alpha/2$], [$O(log log N)$], [Primary (mitigated)], [Backward shift $O("PSL")$],
    table.hline(stroke: 1pt),
  ),
  caption: [Theoretical comparison of collision resolution techniques under Simple Uniform Hashing Assumption (SUHA).],
) <tbl_theoretical_summary>
"""
