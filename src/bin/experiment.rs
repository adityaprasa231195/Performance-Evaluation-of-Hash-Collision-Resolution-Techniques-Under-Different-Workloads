use std::hint::black_box;
use std::io::Write;
use std::time::Instant;
use rand::rngs::StdRng;
use rand::{Rng, SeedableRng};

use hash_table_study::linear_probing::{LinearProbing, Slot as LpSlot};
use hash_table_study::quadratic_probing::{QuadraticProbing, Slot as QpSlot};
use hash_table_study::robin_hood::{RobinHood, RhSlot};
use hash_table_study::separate_chaining::SeparateChaining;

const SIZES: &[usize] = &[1_000, 10_000, 100_000, 500_000, 1_000_000];
const DISTRIBUTIONS: &[&str] = &[
    "random",
    "sequential",
    "reverse_sequential",
    "clustered",
    "duplicate_heavy",
    "small_range",
    "collision_heavy",
];
const IMPLS: &[&str] = &[
    "SeparateChaining",
    "LinearProbing",
    "QuadraticProbing",
    "RobinHood",
];
const NUM_TRIALS: usize = 7;

fn generate_dataset(dist: &str, size: usize) -> (Vec<i64>, Vec<i64>) {
    let mut rng = StdRng::seed_from_u64(42);
    let keys: Vec<i64> = match dist {
        "random" => (0..size).map(|_| rng.gen::<i64>()).collect(),
        "sequential" => (0..size as i64).collect(),
        "reverse_sequential" => (0..size as i64).rev().collect(),
        "clustered" => {
            let mut k = Vec::with_capacity(size);
            let num_clusters = (size + 99) / 100;
            for _ in 0..num_clusters {
                let base = (rng.gen::<u64>() % (i64::MAX as u64 / 2)) as i64;
                for j in 0..100 {
                    if k.len() < size {
                        k.push(base + j as i64);
                    }
                }
            }
            k
        }
        "duplicate_heavy" => {
            let unique: Vec<i64> = (0..100).map(|_| rng.gen::<i64>()).collect();
            (0..size).map(|_| unique[rng.gen_range(0..100)]).collect()
        }
        "small_range" => (0..size).map(|_| rng.gen_range(0..1000i64)).collect(),
        "collision_heavy" => {
            // Multiples of 16 produce substantial bucket clustering under FNV-1a
            (0..size as i64).map(|i| i * 16).collect()
        }
        _ => panic!("Unknown distribution: {}", dist),
    };

    let miss_keys: Vec<i64> = match dist {
        "duplicate_heavy" => {
            let mut miss_rng = StdRng::seed_from_u64(9999);
            (0..size).map(|_| miss_rng.gen_range(i64::MIN..-10_000_000)).collect()
        }
        "small_range" => {
            (0..size).map(|i| 10_000 + (i % 1000) as i64).collect()
        }
        "collision_heavy" => {
            (0..size as i64).map(|i| i * 16 + 1).collect()
        }
        "sequential" | "reverse_sequential" => {
            (0..size as i64).map(|i| -(i + 1)).collect()
        }
        _ => {
            let offset = (i64::MAX / 2) + 1_000_000;
            keys.iter().map(|&k| k.wrapping_add(offset)).collect()
        }
    };

    (keys, miss_keys)
}

struct RunStats {
    collisions: usize,
    avg_probe: f64,
    max_probe: usize,
    load_factor: f64,
    memory_bytes: usize,
}

struct OpResult {
    total_ns: u128,
    per_op_ns: f64,
    stats: RunStats,
}

fn bench_sc(size: usize, keys: &[i64], miss_keys: &[i64]) -> (OpResult, OpResult, OpResult, OpResult) {
    let mut table = SeparateChaining::new(size);

    // 1. Insert
    let t0 = Instant::now();
    for &k in keys {
        table.insert(black_box(k), black_box(k));
    }
    let ins_ns = t0.elapsed().as_nanos();
    let stats = RunStats {
        collisions: table.collision_count(),
        avg_probe: table.avg_chain_len(),
        max_probe: table.max_chain_len(),
        load_factor: table.load_factor(),
        memory_bytes: table.capacity() * std::mem::size_of::<Vec<(i64, i64)>>()
            + table.len() * std::mem::size_of::<(i64, i64)>(),
    };
    let ins_res = OpResult {
        total_ns: ins_ns,
        per_op_ns: ins_ns as f64 / size as f64,
        stats,
    };

    // 2. Lookup Hit
    let t0 = Instant::now();
    let mut hits = 0usize;
    for &k in keys {
        if black_box(table.get(black_box(k))).is_some() {
            hits += 1;
        }
    }
    black_box(hits);
    let hit_ns = t0.elapsed().as_nanos();
    let hit_res = OpResult {
        total_ns: hit_ns,
        per_op_ns: hit_ns as f64 / size as f64,
        stats: RunStats {
            collisions: table.collision_count(),
            avg_probe: table.avg_chain_len(),
            max_probe: table.max_chain_len(),
            load_factor: table.load_factor(),
            memory_bytes: ins_res.stats.memory_bytes,
        },
    };

    // 3. Lookup Miss
    let t0 = Instant::now();
    let mut misses = 0usize;
    for &k in miss_keys {
        if black_box(table.get(black_box(k))).is_none() {
            misses += 1;
        }
    }
    black_box(misses);
    let miss_ns = t0.elapsed().as_nanos();
    let miss_res = OpResult {
        total_ns: miss_ns,
        per_op_ns: miss_ns as f64 / size as f64,
        stats: RunStats {
            collisions: table.collision_count(),
            avg_probe: table.avg_chain_len(),
            max_probe: table.max_chain_len(),
            load_factor: table.load_factor(),
            memory_bytes: ins_res.stats.memory_bytes,
        },
    };

    // 4. Delete
    let t0 = Instant::now();
    let mut dels = 0usize;
    for &k in keys {
        if black_box(table.remove(black_box(k))) {
            dels += 1;
        }
    }
    black_box(dels);
    let del_ns = t0.elapsed().as_nanos();
    let del_res = OpResult {
        total_ns: del_ns,
        per_op_ns: del_ns as f64 / size as f64,
        stats: RunStats {
            collisions: table.collision_count(),
            avg_probe: table.avg_chain_len(),
            max_probe: table.max_chain_len(),
            load_factor: table.load_factor(),
            memory_bytes: ins_res.stats.memory_bytes,
        },
    };

    (ins_res, hit_res, miss_res, del_res)
}

fn bench_lp(size: usize, keys: &[i64], miss_keys: &[i64]) -> (OpResult, OpResult, OpResult, OpResult) {
    let mut table = LinearProbing::new(size);

    // 1. Insert
    let t0 = Instant::now();
    for &k in keys {
        table.insert(black_box(k), black_box(k));
    }
    let ins_ns = t0.elapsed().as_nanos();
    let stats = RunStats {
        collisions: table.collision_count(),
        avg_probe: table.avg_probe_count(),
        max_probe: table.max_probe_run(),
        load_factor: table.load_factor(),
        memory_bytes: table.capacity() * std::mem::size_of::<LpSlot>(),
    };
    let ins_res = OpResult {
        total_ns: ins_ns,
        per_op_ns: ins_ns as f64 / size as f64,
        stats,
    };

    // 2. Lookup Hit
    let t0 = Instant::now();
    let mut hits = 0usize;
    for &k in keys {
        if black_box(table.get(black_box(k))).is_some() {
            hits += 1;
        }
    }
    black_box(hits);
    let hit_ns = t0.elapsed().as_nanos();
    let hit_res = OpResult {
        total_ns: hit_ns,
        per_op_ns: hit_ns as f64 / size as f64,
        stats: RunStats {
            collisions: table.collision_count(),
            avg_probe: table.avg_probe_count(),
            max_probe: table.max_probe_run(),
            load_factor: table.load_factor(),
            memory_bytes: ins_res.stats.memory_bytes,
        },
    };

    // 3. Lookup Miss
    let t0 = Instant::now();
    let mut misses = 0usize;
    for &k in miss_keys {
        if black_box(table.get(black_box(k))).is_none() {
            misses += 1;
        }
    }
    black_box(misses);
    let miss_ns = t0.elapsed().as_nanos();
    let miss_res = OpResult {
        total_ns: miss_ns,
        per_op_ns: miss_ns as f64 / size as f64,
        stats: RunStats {
            collisions: table.collision_count(),
            avg_probe: table.avg_probe_count(),
            max_probe: table.max_probe_run(),
            load_factor: table.load_factor(),
            memory_bytes: ins_res.stats.memory_bytes,
        },
    };

    // 4. Delete
    let t0 = Instant::now();
    let mut dels = 0usize;
    for &k in keys {
        if black_box(table.remove(black_box(k))) {
            dels += 1;
        }
    }
    black_box(dels);
    let del_ns = t0.elapsed().as_nanos();
    let del_res = OpResult {
        total_ns: del_ns,
        per_op_ns: del_ns as f64 / size as f64,
        stats: RunStats {
            collisions: table.collision_count(),
            avg_probe: table.avg_probe_count(),
            max_probe: table.max_probe_run(),
            load_factor: table.load_factor(),
            memory_bytes: ins_res.stats.memory_bytes,
        },
    };

    (ins_res, hit_res, miss_res, del_res)
}

fn bench_qp(size: usize, keys: &[i64], miss_keys: &[i64]) -> (OpResult, OpResult, OpResult, OpResult) {
    let mut table = QuadraticProbing::new(size);

    // 1. Insert
    let t0 = Instant::now();
    for &k in keys {
        table.insert(black_box(k), black_box(k));
    }
    let ins_ns = t0.elapsed().as_nanos();
    let stats = RunStats {
        collisions: table.collision_count(),
        avg_probe: table.avg_probe_count(),
        max_probe: table.max_probe_count(),
        load_factor: table.load_factor(),
        memory_bytes: table.capacity() * std::mem::size_of::<QpSlot>(),
    };
    let ins_res = OpResult {
        total_ns: ins_ns,
        per_op_ns: ins_ns as f64 / size as f64,
        stats,
    };

    // 2. Lookup Hit
    let t0 = Instant::now();
    let mut hits = 0usize;
    for &k in keys {
        if black_box(table.get(black_box(k))).is_some() {
            hits += 1;
        }
    }
    black_box(hits);
    let hit_ns = t0.elapsed().as_nanos();
    let hit_res = OpResult {
        total_ns: hit_ns,
        per_op_ns: hit_ns as f64 / size as f64,
        stats: RunStats {
            collisions: table.collision_count(),
            avg_probe: table.avg_probe_count(),
            max_probe: table.max_probe_count(),
            load_factor: table.load_factor(),
            memory_bytes: ins_res.stats.memory_bytes,
        },
    };

    // 3. Lookup Miss
    let t0 = Instant::now();
    let mut misses = 0usize;
    for &k in miss_keys {
        if black_box(table.get(black_box(k))).is_none() {
            misses += 1;
        }
    }
    black_box(misses);
    let miss_ns = t0.elapsed().as_nanos();
    let miss_res = OpResult {
        total_ns: miss_ns,
        per_op_ns: miss_ns as f64 / size as f64,
        stats: RunStats {
            collisions: table.collision_count(),
            avg_probe: table.avg_probe_count(),
            max_probe: table.max_probe_count(),
            load_factor: table.load_factor(),
            memory_bytes: ins_res.stats.memory_bytes,
        },
    };

    // 4. Delete
    let t0 = Instant::now();
    let mut dels = 0usize;
    for &k in keys {
        if black_box(table.remove(black_box(k))) {
            dels += 1;
        }
    }
    black_box(dels);
    let del_ns = t0.elapsed().as_nanos();
    let del_res = OpResult {
        total_ns: del_ns,
        per_op_ns: del_ns as f64 / size as f64,
        stats: RunStats {
            collisions: table.collision_count(),
            avg_probe: table.avg_probe_count(),
            max_probe: table.max_probe_count(),
            load_factor: table.load_factor(),
            memory_bytes: ins_res.stats.memory_bytes,
        },
    };

    (ins_res, hit_res, miss_res, del_res)
}

fn bench_rh(size: usize, keys: &[i64], miss_keys: &[i64]) -> (OpResult, OpResult, OpResult, OpResult) {
    let mut table = RobinHood::new(size);

    // 1. Insert
    let t0 = Instant::now();
    for &k in keys {
        table.insert(black_box(k), black_box(k));
    }
    let ins_ns = t0.elapsed().as_nanos();
    let stats = RunStats {
        collisions: table.collision_count(),
        avg_probe: 1.0 + table.avg_probe_dist(),
        max_probe: 1 + table.max_probe_dist(),
        load_factor: table.load_factor(),
        memory_bytes: table.capacity() * std::mem::size_of::<RhSlot>(),
    };
    let ins_res = OpResult {
        total_ns: ins_ns,
        per_op_ns: ins_ns as f64 / size as f64,
        stats,
    };

    // 2. Lookup Hit
    let t0 = Instant::now();
    let mut hits = 0usize;
    for &k in keys {
        if black_box(table.get(black_box(k))).is_some() {
            hits += 1;
        }
    }
    black_box(hits);
    let hit_ns = t0.elapsed().as_nanos();
    let hit_res = OpResult {
        total_ns: hit_ns,
        per_op_ns: hit_ns as f64 / size as f64,
        stats: RunStats {
            collisions: table.collision_count(),
            avg_probe: 1.0 + table.avg_probe_dist(),
            max_probe: 1 + table.max_probe_dist(),
            load_factor: table.load_factor(),
            memory_bytes: ins_res.stats.memory_bytes,
        },
    };

    // 3. Lookup Miss
    let t0 = Instant::now();
    let mut misses = 0usize;
    for &k in miss_keys {
        if black_box(table.get(black_box(k))).is_none() {
            misses += 1;
        }
    }
    black_box(misses);
    let miss_ns = t0.elapsed().as_nanos();
    let miss_res = OpResult {
        total_ns: miss_ns,
        per_op_ns: miss_ns as f64 / size as f64,
        stats: RunStats {
            collisions: table.collision_count(),
            avg_probe: 1.0 + table.avg_probe_dist(),
            max_probe: 1 + table.max_probe_dist(),
            load_factor: table.load_factor(),
            memory_bytes: ins_res.stats.memory_bytes,
        },
    };

    // 4. Delete
    let t0 = Instant::now();
    let mut dels = 0usize;
    for &k in keys {
        if black_box(table.remove(black_box(k))) {
            dels += 1;
        }
    }
    black_box(dels);
    let del_ns = t0.elapsed().as_nanos();
    let del_res = OpResult {
        total_ns: del_ns,
        per_op_ns: del_ns as f64 / size as f64,
        stats: RunStats {
            collisions: table.collision_count(),
            avg_probe: 1.0 + table.avg_probe_dist(),
            max_probe: 1 + table.max_probe_dist(),
            load_factor: table.load_factor(),
            memory_bytes: ins_res.stats.memory_bytes,
        },
    };

    (ins_res, hit_res, miss_res, del_res)
}

fn main() {
    println!("============================================================");
    println!(" Hash Table Collision Resolution Benchmark Runner");
    println!("============================================================");

    std::fs::create_dir_all("results").expect("Failed to create results dir");
    let mut csv_file = std::fs::File::create("results/raw_experiments.csv")
        .expect("Failed to create raw_experiments.csv");

    // CSV Header as required:
    // impl,size,distribution,operation,trial,time_ns,collisions,avg_probe,max_probe,load_factor,memory_bytes
    writeln!(
        csv_file,
        "impl,size,distribution,operation,trial,time_ns,collisions,avg_probe,max_probe,load_factor,memory_bytes"
    )
    .expect("Failed to write CSV header");

    let total_benchmarks = SIZES.len() * DISTRIBUTIONS.len() * IMPLS.len() * NUM_TRIALS;
    let mut completed = 0;
    let global_start = Instant::now();

    for &size in SIZES {
        println!("\n>>> Running benchmarks for table size N = {} <<<", size);
        for &dist in DISTRIBUTIONS {
            print!("  Generating dataset: distribution = {:18} ... ", dist);
            std::io::stdout().flush().unwrap();
            let gen_start = Instant::now();
            let (keys, miss_keys) = generate_dataset(dist, size);
            println!("done ({:.2?})", gen_start.elapsed());

            for &imp in IMPLS {
                for trial in 1..=NUM_TRIALS {
                    completed += 1;
                    let (ins, hit, miss, del) = match imp {
                        "SeparateChaining" => bench_sc(size, &keys, &miss_keys),
                        "LinearProbing" => bench_lp(size, &keys, &miss_keys),
                        "QuadraticProbing" => bench_qp(size, &keys, &miss_keys),
                        "RobinHood" => bench_rh(size, &keys, &miss_keys),
                        _ => unreachable!(),
                    };

                    let ops = [
                        ("insert", &ins),
                        ("lookup_hit", &hit),
                        ("lookup_miss", &miss),
                        ("delete", &del),
                    ];

                    for (op_name, res) in &ops {
                        writeln!(
                            csv_file,
                            "{},{},{},{},{},{:.2},{},{:.4},{},{:.4},{}",
                            imp,
                            size,
                            dist,
                            op_name,
                            trial,
                            res.per_op_ns,
                            res.stats.collisions,
                            res.stats.avg_probe,
                            res.stats.max_probe,
                            res.stats.load_factor,
                            res.stats.memory_bytes
                        )
                        .expect("Failed to write CSV row");
                    }

                    if trial == 1 {
                        println!(
                            "    [{:3}/{:3}] {:16} N={:<7} | ins: {:6.1} ns/op (tot {:9} ns) | hit: {:5.1} ns/op | miss: {:5.1} ns/op | del: {:5.1} ns/op | coll: {:7} | avg_prb: {:5.2} | max_prb: {:3} | α: {:.2} | mem: {:7} B",
                            completed,
                            total_benchmarks,
                            imp,
                            size,
                            ins.per_op_ns,
                            ins.total_ns,
                            hit.per_op_ns,
                            miss.per_op_ns,
                            del.per_op_ns,
                            ins.stats.collisions,
                            ins.stats.avg_probe,
                            ins.stats.max_probe,
                            ins.stats.load_factor,
                            ins.stats.memory_bytes
                        );
                    }
                }
            }
        }
    }

    csv_file.flush().unwrap();
    println!("\n============================================================");
    println!(
        " All experiments finished in {:.2?}. Raw data written to results/raw_experiments.csv",
        global_start.elapsed()
    );
    println!(" Total CSV rows written: {}", total_benchmarks * 4);
    println!("============================================================");
}
