# Theoretical Notes: Hash Table Collision Resolution

*Hash Table Research Paper — Literature Worker Notes*
*Created: 2026-11-17 | Status: Draft*

---

## 1. Notation and Definitions

| Symbol | Meaning |
|--------|---------|
| $n$ | Number of elements stored in the table |
| $m$ | Number of slots in the hash table |
| $\alpha = n/m$ | **Load factor** ($0 < \alpha < 1$ for open addressing; any $\alpha > 0$ for chaining) |
| $C^+_\alpha$ | Expected probes for a **successful** search at load factor $\alpha$ |
| $C^-_\alpha$ | Expected probes for an **unsuccessful** search (or insertion) at load factor $\alpha$ |
| PSL | Probe Sequence Length — number of slots examined before finding the target or empty |

> [!NOTE]
> All probe-count formulas below assume a **uniform random hash function** (fully random). Real hash functions introduce non-uniformity; see Section 6 on hash function independence requirements.

---

## 2. Expected Probe Counts by Method

### 2.1 Separate Chaining

Under the simple uniform hashing assumption with $n$ elements and $m$ chains:

$$C^+_\alpha = 1 + \frac{\alpha}{2}$$

$$C^-_\alpha = e^{-\alpha} + \alpha \approx 1 + \alpha \quad (\text{for small } \alpha)$$

**Source:** Knuth (1998) §6.4, Theorem C; CLRS (2022) Theorem 11.1.

**Key insight:** Successful search costs $1$ (reaching the chain head) plus $\alpha/2$ (expected comparisons within the chain). The load factor $\alpha$ can exceed 1 freely.

**Memory:** $O(n + m)$ — $m$ pointers for chain heads, $n$ nodes each with a next-pointer. Each node carries metadata overhead (typically 8–16 bytes for a pointer).

---

### 2.2 Linear Probing (Open Addressing)

$$C^+_\alpha \approx \frac{1}{2}\left(1 + \frac{1}{1-\alpha}\right)$$

$$C^-_\alpha \approx \frac{1}{2}\left(1 + \frac{1}{(1-\alpha)^2}\right)$$

**Source:** Knuth (1998) §6.4, Equations (19)–(20) (derived via the "parking problem" / ballot problem analysis).

**Key insight:** As $\alpha \to 1$, unsuccessful probes diverge as $(1-\alpha)^{-2}$ — quadratic blow-up. At $\alpha = 0.75$ (a common default), $C^-_{0.75} \approx 8.5$ probes for an unsuccessful search.

**Primary clustering** is the pathology: runs of occupied slots grow, creating long probe chains. Knuth (1998) §6.4 formally defines and analyses clustering.

**Cache behaviour:** Sequential probe access is **ideal for cache lines** (typically 64 bytes, holding 8–16 int-sized slots). This is why linear probing outperforms theoretically superior methods on modern hardware \cite{richter2015}.

---

### 2.3 Quadratic Probing

Probe sequence: $h(k), h(k)+1^2, h(k)+2^2, \ldots$

Closed-form expected probe counts are harder to derive; the analysis depends on table size (must be a prime for full table coverage). Empirically:

$$C^+_\alpha \approx 1 - \ln(1-\alpha) - \frac{\alpha}{2} \quad \text{(approximation)}$$

$$C^-_\alpha \approx \frac{1}{1-\alpha} - \alpha - \ln(1-\alpha) \quad \text{(approximation)}$$

**Source:** Knuth (1998) §6.4, Exercise 20; also discussed in Sedgewick & Wayne (2011) §3.4.

**Secondary clustering** (not primary): two keys with the same hash follow identical probe sequences, but different initial hashes yield different sequences.

**Memory:** $O(m)$ — in-place, one array of $m$ slots. Load factor must be kept below $0.5$–$0.6$ to avoid failed insertions (table size must be prime for guaranteed full scan).

---

### 2.4 Double Hashing (Open Addressing)

Probe sequence: $h_1(k) + i \cdot h_2(k) \pmod{m}$, $i = 0, 1, 2, \ldots$

This approximates **uniform probing** (independent random probes). Under that model:

$$C^+_\alpha \approx -\frac{1}{\alpha}\ln(1-\alpha)$$

$$C^-_\alpha \approx \frac{1}{1-\alpha}$$

**Source:** Knuth (1998) §6.4, Equations (21)–(22).

**No clustering** (neither primary nor secondary), provided $h_2(k)$ is coprime to $m$. Best asymptotic probe counts among standard open-addressing methods.

**Cache behaviour:** Probe steps $h_2(k)$ are pseudo-random jumps → **poor cache locality**, multiple cache misses per lookup.

---

### 2.5 Robin Hood Hashing

Robin Hood hashing is a variant of linear probing that uses the PSL of each stored element to reduce variance:

**Insertion rule:** When a new element's PSL exceeds the PSL of the element currently in the probe position, displace the existing element (the "rich" one) and continue inserting the displaced element.

Expected probe counts for Robin Hood hashing are asymptotically similar to linear probing:

$$C^+_\alpha \approx \frac{1}{2}\left(1 + \frac{1}{1-\alpha}\right) \quad \text{(same leading term)}$$

but with **dramatically reduced variance**:

$$\text{Var}[\text{PSL}] = O(\ln \ln n) \quad \text{vs.} \quad O\left(\frac{1}{(1-\alpha)^2}\right) \text{ for standard linear probing}$$

**Source:** Celis (1986) PhD thesis §3–4; Celis, Larson & Munro (1985) FOCS.

**Practical consequence:** Maximum PSL grows as $O(\log n)$ rather than $O(n)$; enables **early-termination search** (stop if current PSL exceeds the stored element's PSL — the target cannot be further along).

**Backward-shift deletion** (no tombstones): when deleting slot $i$, shift subsequent elements backward until finding an element with PSL = 0 or an empty slot. This maintains invariants without tombstone accumulation.

---

### 2.6 Brent's Algorithm

A modification of linear probing that at insertion checks whether relocating an existing element can reduce total future probe costs.

**Key result:** Brent (1973) showed that this reduces $C^+_\alpha$ to approximately:

$$C^+_\alpha \approx e^{\sqrt{2 \ln(1/(1-\alpha))}} \cdot \sqrt{\frac{e}{2}} \quad \text{(rough bound)}$$

which grows more slowly than standard linear probing as $\alpha \to 1$.

**Trade-off:** Insertion is more expensive ($O(\alpha)$ overhead) but lookups are faster. Best suited for read-heavy workloads.

**Source:** Brent (1973), Communications of ACM.

---

## 3. Load Factor Behaviour Analysis

```
Load Factor (α) | Linear Probing C⁻ | Double Hashing C⁻ | Chaining C⁻
                |   ½(1+(1-α)⁻²)    |    (1-α)⁻¹        |  1 + α
----------------|-------------------|-------------------|------------
    0.50        |      2.50         |      2.00         |   1.50
    0.70        |      6.72         |      3.33         |   1.70
    0.75        |      8.50         |      4.00         |   1.75
    0.80        |     13.00         |      5.00         |   1.80
    0.90        |     50.50         |     10.00         |   1.90
    0.95        |    200.50         |     20.00         |   1.95
```

**Observations:**
- Chaining is **load-factor agnostic** — $C^-$ grows linearly and gracefully with $\alpha > 1$.
- Linear probing degrades catastrophically near $\alpha = 1$ due to primary clustering.
- Double hashing degrades gracefully but loses cache locality benefit.
- **SwissTable** (Kulukundis 2017; d'Antras 2018; Abseil 2018) maintains $\alpha \leq 0.875$ (7/8) while using SIMD group probing to amortise cache misses across 16-slot metadata scans.

> [!TIP]
> A load factor of **0.5–0.75** is a common practical sweet spot for open addressing, balancing probe count and space utilisation. Robin Hood hashing can operate at higher load factors (up to ~0.9) while keeping probes bounded.

---

## 4. Memory Complexity

| Method | Space (table) | Auxiliary space | Pointer overhead |
|--------|--------------|-----------------|-----------------|
| Separate chaining | $O(m)$ (array of heads) + $O(n)$ (nodes) | — | $n \times$ sizeof(pointer) |
| Linear probing | $O(m)$ | — | None (in-array) |
| Quadratic probing | $O(m)$ | — | None (in-array) |
| Double hashing | $O(m)$ | $O(1)$ secondary hash | None |
| Robin Hood (open addr.) | $O(m)$ | $O(1)$ PSL per slot | Optional 1 byte PSL |
| Cuckoo hashing | $O(m)$ (two tables, 2×) | — | None |
| SwissTable | $O(m)$ (slots) + $O(m/8)$ (control bytes) | — | None |

**Notes:**
- For chaining, each node requires a pointer (8 bytes on 64-bit systems) + possible padding — a 16-byte key-value pair becomes 24–32 bytes.
- Open-addressing methods store keys and values in-place: much better cache density.
- SwissTable uses 1 control byte per slot (7-bit H2 hash + 1 status bit) = $m/8$ extra cache lines for the metadata array — a small constant overhead that enables SIMD group probing.

**Source:** Knuth (1998) §6.4; Kulukundis (2017); Abseil documentation (2018).

---

## 5. Cache Locality Discussion

Modern CPUs have memory hierarchies with large latency gaps:
- L1 cache: ~4 cycles
- L2 cache: ~12 cycles
- L3 cache: ~40 cycles
- Main RAM: ~200 cycles

**Linear probing** accesses consecutive slots, maximising **spatial locality** — a cache-line fetch (64 bytes) pre-loads 8–16 adjacent slots, so subsequent probes in the same run are "free".

**Separate chaining** dereferences a pointer per lookup — each node may be in a different cache line, causing **pointer-chasing cache misses**. At $\alpha = 1$ this means 1 cache miss per element in the chain.

**Double hashing** has probe step $h_2(k)$ which is pseudo-random → consecutive probes are in different cache lines → 1 cache miss per probe.

**SwissTable design** (Kulukundis 2017):
1. Control bytes are densely packed in a separate metadata array → scanning 16 control bytes fits in 1 cache line.
2. SIMD (SSE2 `_mm_cmpeq_epi8`) compares all 16 control bytes in one instruction → usually 0 or 1 full key comparison needed.
3. Full key/value slots are only accessed when the 7-bit H2 fingerprint matches → cache misses on the data array are rare.

**Richter et al. (2015)** empirically confirmed that cache-conscious implementations (linear probing at $\alpha \leq 0.9$, SwissTable-style) outperform theoretically superior double hashing because memory access patterns matter more than probe count at typical dataset sizes (L3-cache-sized tables).

> [!IMPORTANT]
> Cache line alignment: aligning the hash table's slot array to 64-byte boundaries and ensuring slot sizes are powers of 2 avoids split-line reads. This is a critical implementation detail noted in Abseil documentation (2018).

---

## 6. Hash Function Independence Requirements

Uniform hashing is an idealisation. Real hash functions have limited independence:

| Method | Minimum independence needed | Reference |
|--------|----------------------------|-----------|
| Chaining (expected O(1)) | 2-universal | Carter & Wegman (1979) |
| Linear probing (expected O(1)) | 5-independent | Pagh, Pagh & Ružić (2007/2009) |
| Cuckoo hashing (expected O(1) insert) | Fully random OR O(log n)-independent | Pagh & Rodler (2004) |
| Double hashing | 2-universal suffices (empirical) | Thorup (2015) |
| FNV-1a in practice | Non-cryptographic; not formally analysed | Fowler et al. (2019) |

**FNV-1a** (XOR-then-multiply) has no formal independence proof but performs well empirically for hash tables with non-adversarial inputs. It is used in Rust's hashbrown prior to randomised seed mixing.

**SipHash** (not in bib — to add) is used by Rust's default HashMap for DoS-resistance — it provides randomised, keyed hashing based on the SipHash 2-4 construction.

> [!WARNING]
> Using a non-independent hash function with linear probing can degrade worst-case performance to O(n) per operation. Pagh et al. (2007) proved that 4-independence is *insufficient*; 5-independence is required for the expected O(1) guarantee.

---

## 7. Key Implementation Considerations

### 7.1 Resizing / Rehashing
- **Triggered by:** load factor exceeding threshold (e.g., 0.75 for Java HashMap, 0.875 for SwissTable).
- **Cost:** $O(n)$ amortised — rebuild entire table at $2m$ capacity, rehash all elements.
- **Incremental resizing** (Larson 1988): split one bucket per insert, avoiding bulk rehash — useful for real-time systems.

### 7.2 Deletion in Open Addressing
- **Tombstones:** Mark slot as "deleted" (not empty) so probe chains are not broken. Accumulate over time, degrading performance.
- **Backward-shift deletion** (Robin Hood): shift subsequent elements backward after deletion; no tombstones needed; O(1) amortised. Described in Celis (1986) and popularised by Goossaert (2013, blog).

### 7.3 Key/Value Layout
- **Interleaved (AoS):** `[(k1,v1), (k2,v2), ...]` — good spatial locality for paired key-value access.
- **Separate arrays (SoA):** `[k1,k2,...]` and `[v1,v2,...]` — better for key-only scans (e.g., lookups in hash sets).
- **SwissTable:** separates metadata (control bytes) from key-value slots to allow SIMD filtering before touching values.

### 7.4 Load Factor Thresholds (Practical Recommendations)

| Implementation | Default load factor | Notes |
|----------------|--------------------|----|
| Java `HashMap` | 0.75 | Separate chaining; tunable |
| Python `dict` | ~0.667 | Compact open addressing |
| Rust `hashbrown` | 0.875 (7/8) | SwissTable; SIMD probing |
| C++ `std::unordered_map` | 1.0 (by spec) | Separate chaining; often worse |
| Generic linear probing | 0.5–0.75 | Avoids clustering blow-up |
| Robin Hood hashing | up to 0.9 | Low PSL variance compensates |

### 7.5 Integer vs. String Keys
- Integer keys: **multiply-shift** hashing ($h(k) = (k \cdot a) \gg (w - r)$) achieves 2-universality at single-instruction cost (Thorup 2015).
- String keys: **FNV-1a** or **MurmurHash3** or **xxHash** are common non-cryptographic choices; SipHash for security-sensitive contexts.

---

## 8. Summary Table: Method Comparison

| Method | $C^+_\alpha$ (avg probes, succ.) | $C^-_\alpha$ (avg probes, unsucc.) | Cache | Memory | Deletion |
|--------|----------------------------------|-------------------------------------|-------|--------|----------|
| Chaining | $1 + \alpha/2$ | $e^{-\alpha} + \alpha$ | Poor (pointer chase) | $O(n+m)$ + ptr overhead | Simple (node removal) |
| Linear probing | $\frac{1}{2}(1 + \frac{1}{1-\alpha})$ | $\frac{1}{2}(1 + \frac{1}{(1-\alpha)^2})$ | Excellent | $O(m)$ | Tombstone or backward shift |
| Quadratic probing | (approx.) $1 - \ln(1-\alpha) - \frac{\alpha}{2}$ | (approx.) $\frac{1}{1-\alpha} - \alpha - \ln(1-\alpha)$ | Good | $O(m)$ | Tombstone |
| Double hashing | $-\frac{\ln(1-\alpha)}{\alpha}$ | $\frac{1}{1-\alpha}$ | Poor (random jumps) | $O(m)$ | Tombstone |
| Robin Hood | ≈ linear probing (mean) | ≈ linear probing (mean) | Excellent (linear probe) | $O(m)$ + 1 byte PSL | Backward shift (clean) |
| Cuckoo | O(1) worst case | O(1) worst case | Good (2 probes max) | $O(m)$ (2 tables) | Simple |
| SwissTable | ≈ linear (SIMD) | ≈ linear (SIMD) | Excellent (metadata array) | $O(m)$ + $m/8$ ctrl bytes | Tombstone in metadata |

---

## References (Abbreviated)

- Brent (1973): `10.1145/361952.361965`
- Carter & Wegman (1979): `10.1016/0022-0000(79)90044-8`
- Celis (1986): UW Technical Report CS-86-14
- Celis, Larson & Munro (1985): `10.1109/SFCS.1985.48`
- CLRS (2022): MIT Press, ISBN 978-0-262-04630-5
- d'Antras / hashbrown (2018): https://github.com/rust-lang/hashbrown
- Fowler et al. / FNV (2019 IETF draft): https://datatracker.ietf.org/doc/draft-eastlake-fnv/
- Frigo et al. (1999): `10.1109/SFFCS.1999.814600`
- Knuth (1998): Addison-Wesley, §6.4
- Kulukundis / SwissTable CppCon (2017): https://www.youtube.com/watch?v=ncHmEUmJZf4
- Larson (1988): `10.1145/42404.42410`
- Maier, Sanders & Walzer (2019): `10.1007/s00453-019-00572-x`
- Mitzenmacher & Upfal (2017): Cambridge UP, ISBN 978-1-107-15488-9
- Östlin & Pagh (2003): DOI `10.1137/060658400`
- Pagh & Rodler (2004): `10.1016/j.jalgor.2003.12.002`
- Pagh, Pagh & Ružić (2007/2009): `10.1145/1250790.1250839` / `10.1137/070702278`
- Richter, Alvarez & Dittrich (2015): `10.14778/2850583.2850585`
- Sedgewick & Wayne (2011): Addison-Wesley, §3.4
- Thorup (2015): arXiv:1504.06804
- Vitter (2001): `10.1145/384192.384193`
- Wegman & Carter (1981): `10.1016/0022-0000(81)90033-7`
