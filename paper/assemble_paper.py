#!/usr/bin/env python3
"""
Assemble and compile the complete hash table research paper in Typst.
Outputs: paper/paper.typ and paper/research_paper_hash_tables.pdf
Author: Aditya Kumar Harishankar Prasad
"""

import os
import sys

from gen_intro import get_typst_intro
from gen_related import get_typst_related
from gen_theory import get_typst_theory
from gen_impl import get_typst_impl
from gen_methodology import get_typst_methodology
from gen_results import get_typst_results
from gen_discussion import get_typst_discussion
from gen_selection import get_typst_selection
from gen_validity import get_typst_validity
from gen_conclusion import get_typst_conclusion
from gen_appendices import get_typst_appendices

header = """#set page(
  paper: "us-letter",
  margin: (top: 2cm, bottom: 2.2cm, left: 1.8cm, right: 1.8cm),
  header: context {
    if counter(page).get().first() > 1 [
      #text(size: 8.5pt, fill: luma(80), font: "Liberation Sans")[
        Performance Evaluation of Hash Collision Resolution Techniques Under Different Workloads $dot$ A. K. H. Prasad
        #h(1fr)
        #counter(page).display()
      ]
    ]
  },
  footer: context {
    if counter(page).get().first() == 1 [
      #align(center)[
        #text(size: 8pt, fill: luma(100), font: "Liberation Sans")[
          Preprint submitted to Research Repository $dot$ November 2026
        ]
      ]
    ]
  }
)

#set text(
  font: "Liberation Serif",
  size: 9.5pt,
  fill: black,
  lang: "en"
)

#set par(
  justify: true,
  leading: 0.54em,
  first-line-indent: 1.2em
)

#show heading: it => block(breakable: false)[
  #set text(font: "Liberation Sans", weight: "bold", fill: black)
  #if it.level == 1 {
    v(1.2em, weak: true)
    text(size: 11pt)[#it.body]
    v(0.4em, weak: true)
  } else if it.level == 2 {
    v(0.9em, weak: true)
    text(size: 10pt)[#it.body]
    v(0.3em, weak: true)
  } else {
    v(0.7em, weak: true)
    text(size: 9.5pt)[#it.body]
    v(0.25em, weak: true)
  }
]

#show figure.caption: it => [
  #set text(size: 8.3pt, font: "Liberation Sans", fill: black)
  #it
]

#show raw: set text(font: "Liberation Mono", size: 7.0pt, fill: black)
#show raw.where(block: true): it => block(
  fill: luma(252),
  stroke: 0.5pt + luma(180),
  inset: 4.5pt,
  radius: 2pt,
  width: 100%,
  it
)

// Title Block (Title and Author only, strictly no affiliation or institution)
#align(center)[
  #v(0.5em)
  #text(size: 16pt, weight: "bold", font: "Liberation Sans")[
    Performance Evaluation of Hash Collision Resolution\ Techniques Under Different Workloads
  ]
  #v(0.6em)
  #text(size: 11.5pt, weight: "medium", font: "Liberation Sans")[
    Aditya Kumar Harishankar Prasad
  ]
  #v(0.8em)
]

// Abstract and Keywords Block
#rect(
  width: 100%,
  fill: white,
  stroke: 0.5pt + luma(180),
  inset: 9pt,
  radius: 2pt
)[
  #text(weight: "bold", font: "Liberation Sans", size: 9pt)[Abstract—]
  Hash tables represent fundamental building blocks across computer systems, underpinning database indexing, language runtimes, in-memory caches, and network routing pipelines. While classical theoretical models evaluate hash tables under idealized Simple Uniform Hashing Assumptions with constant amortized time ($O(1)$), physical execution on modern multi-core superscalar processors diverges dramatically due to cache hierarchy latencies, hardware prefetching, store-buffer pressure, and distributional entropy. This paper presents an exhaustive, reproducible comparative performance evaluation of four canonical collision resolution techniques implemented from first principles in Rust (`rustc 1.100.0`): Separate Chaining (vector-of-vectors), Linear Probing (tombstone-based open addressing), Quadratic Probing (prime-capacity cycle-guaranteed open addressing), and Robin Hood Hashing (probe-distance displacement with backward-shift deletion). We evaluate concrete 64-bit signed integer keys (`i64`) across five input scales ($10^3$ to $10^6$ elements) and seven synthetic key distributions (uniform random, sequential, reverse sequential, clustered, collision-heavy, duplicate-heavy, and small-range), executing 3,920 benchmark measurements across 7 independent trials per condition. The empirical data reveals that Linear Probing achieves the highest lookup hit throughput (12.29 ns at $N = 10^5$) propelled by hardware cache line prefetching, but suffers severe primary clustering with maximum probe sequence lengths expanding up to 47–51 slots. In stark contrast, Robin Hood hashing dramatically compresses probe sequence variance, restricting maximum probe sequence length to $<= 12$ across all scales and workloads, albeit incurring a 2.14$times$ insertion latency tax (64.59 ns at $N = 10^5$) due to element displacement store traffic. Separate Chaining exhibits predictable search behavior but incurs up to 1.39$times$ higher memory footprint and severe pointer chasing stalls beyond L3 cache boundaries (102.44 ns insertion at $N = 10^6$). Quadratic Probing successfully eliminates primary clustering while maintaining the lowest memory footprint across scales (4.58 MiB at $N = 10^5$). We synthesize these empirical and architectural observations into an actionable selection taxonomy for systems software engineering in Rust.

  #v(0.4em)
  #text(weight: "bold", font: "Liberation Sans", size: 8.5pt)[Keywords:]
  #text(size: 8.5pt)[hash tables, collision resolution, separate chaining, linear probing, quadratic probing, Robin Hood hashing, Rust, performance evaluation]
]

#v(0.8em)

#show: columns.with(2, gutter: 14pt)
"""

bib_block = """
= XI. References

#bibliography("references.bib")
"""

full_typst = (
    header + "\n" +
    get_typst_intro() + "\n" +
    get_typst_related() + "\n" +
    get_typst_theory() + "\n" +
    get_typst_impl() + "\n" +
    get_typst_methodology() + "\n" +
    get_typst_results() + "\n" +
    get_typst_discussion() + "\n" +
    get_typst_selection() + "\n" +
    get_typst_validity() + "\n" +
    get_typst_conclusion() + "\n" +
    bib_block + "\n" +
    get_typst_appendices()
)

out_typ_path = "paper.typ"
with open(out_typ_path, "w") as f:
    f.write(full_typst)

print(f"Wrote {len(full_typst)} characters to {out_typ_path}")

