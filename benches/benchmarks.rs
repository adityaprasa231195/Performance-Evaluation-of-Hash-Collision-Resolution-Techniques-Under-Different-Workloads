use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion};
use rand::{Rng, SeedableRng};
use rand::rngs::StdRng;
use hash_table_study::separate_chaining::SeparateChaining;
use hash_table_study::linear_probing::LinearProbing;
use hash_table_study::quadratic_probing::QuadraticProbing;
use hash_table_study::robin_hood::RobinHood;

const SEED: u64 = 42;
const SIZES: &[usize] = &[1_000, 10_000, 100_000, 500_000];

fn gen_keys(size: usize) -> Vec<i64> {
    let mut rng = StdRng::seed_from_u64(SEED);
    (0..size).map(|_| rng.gen::<i64>()).collect()
}

// ─── Separate Chaining ────────────────────────────────────────────────────────

fn bench_insert_sc(c: &mut Criterion) {
    let mut group = c.benchmark_group("insert_sc");
    for &size in SIZES {
        let keys = gen_keys(size);
        group.bench_with_input(BenchmarkId::from_parameter(size), &size, |b, _| {
            b.iter(|| {
                let mut sc = SeparateChaining::new(size);
                for &k in &keys {
                    sc.insert(black_box(k), black_box(k));
                }
                black_box(sc.len())
            });
        });
    }
    group.finish();
}

fn bench_lookup_hit_sc(c: &mut Criterion) {
    let mut group = c.benchmark_group("lookup_hit_sc");
    for &size in SIZES {
        let keys = gen_keys(size);
        let mut sc = SeparateChaining::new(size);
        for &k in &keys { sc.insert(k, k); }
        group.bench_with_input(BenchmarkId::from_parameter(size), &size, |b, _| {
            b.iter(|| {
                let mut sum = 0i64;
                for &k in &keys {
                    sum = sum.wrapping_add(sc.get(black_box(k)).unwrap_or(0));
                }
                black_box(sum)
            });
        });
    }
    group.finish();
}

fn bench_lookup_miss_sc(c: &mut Criterion) {
    let mut group = c.benchmark_group("lookup_miss_sc");
    for &size in SIZES {
        let keys = gen_keys(size);
        let miss_keys: Vec<i64> = gen_keys(size).into_iter().map(|k| k.wrapping_add(1)).collect();
        let mut sc = SeparateChaining::new(size);
        for &k in &keys { sc.insert(k, k); }
        group.bench_with_input(BenchmarkId::from_parameter(size), &size, |b, _| {
            b.iter(|| {
                let mut found = 0usize;
                for &k in &miss_keys {
                    if sc.get(black_box(k)).is_some() { found += 1; }
                }
                black_box(found)
            });
        });
    }
    group.finish();
}

fn bench_delete_sc(c: &mut Criterion) {
    let mut group = c.benchmark_group("delete_sc");
    for &size in SIZES {
        let keys = gen_keys(size);
        group.bench_with_input(BenchmarkId::from_parameter(size), &size, |b, _| {
            b.iter(|| {
                let mut sc = SeparateChaining::new(size);
                for &k in &keys { sc.insert(k, k); }
                for &k in &keys { sc.remove(black_box(k)); }
                black_box(sc.len())
            });
        });
    }
    group.finish();
}

// ─── Linear Probing ───────────────────────────────────────────────────────────

fn bench_insert_lp(c: &mut Criterion) {
    let mut group = c.benchmark_group("insert_lp");
    for &size in SIZES {
        let keys = gen_keys(size);
        group.bench_with_input(BenchmarkId::from_parameter(size), &size, |b, _| {
            b.iter(|| {
                let mut lp = LinearProbing::new(size);
                for &k in &keys { lp.insert(black_box(k), black_box(k)); }
                black_box(lp.len())
            });
        });
    }
    group.finish();
}

fn bench_lookup_hit_lp(c: &mut Criterion) {
    let mut group = c.benchmark_group("lookup_hit_lp");
    for &size in SIZES {
        let keys = gen_keys(size);
        let mut lp = LinearProbing::new(size);
        for &k in &keys { lp.insert(k, k); }
        group.bench_with_input(BenchmarkId::from_parameter(size), &size, |b, _| {
            b.iter(|| {
                let mut sum = 0i64;
                for &k in &keys { sum = sum.wrapping_add(lp.get(black_box(k)).unwrap_or(0)); }
                black_box(sum)
            });
        });
    }
    group.finish();
}

fn bench_lookup_miss_lp(c: &mut Criterion) {
    let mut group = c.benchmark_group("lookup_miss_lp");
    for &size in SIZES {
        let keys = gen_keys(size);
        let miss_keys: Vec<i64> = gen_keys(size).into_iter().map(|k| k.wrapping_add(1)).collect();
        let mut lp = LinearProbing::new(size);
        for &k in &keys { lp.insert(k, k); }
        group.bench_with_input(BenchmarkId::from_parameter(size), &size, |b, _| {
            b.iter(|| {
                let mut found = 0usize;
                for &k in &miss_keys { if lp.get(black_box(k)).is_some() { found += 1; } }
                black_box(found)
            });
        });
    }
    group.finish();
}

fn bench_delete_lp(c: &mut Criterion) {
    let mut group = c.benchmark_group("delete_lp");
    for &size in SIZES {
        let keys = gen_keys(size);
        group.bench_with_input(BenchmarkId::from_parameter(size), &size, |b, _| {
            b.iter(|| {
                let mut lp = LinearProbing::new(size);
                for &k in &keys { lp.insert(k, k); }
                for &k in &keys { lp.remove(black_box(k)); }
                black_box(lp.len())
            });
        });
    }
    group.finish();
}

// ─── Quadratic Probing ────────────────────────────────────────────────────────

fn bench_insert_qp(c: &mut Criterion) {
    let mut group = c.benchmark_group("insert_qp");
    for &size in SIZES {
        let keys = gen_keys(size);
        group.bench_with_input(BenchmarkId::from_parameter(size), &size, |b, _| {
            b.iter(|| {
                let mut qp = QuadraticProbing::new(size);
                for &k in &keys { qp.insert(black_box(k), black_box(k)); }
                black_box(qp.len())
            });
        });
    }
    group.finish();
}

fn bench_lookup_hit_qp(c: &mut Criterion) {
    let mut group = c.benchmark_group("lookup_hit_qp");
    for &size in SIZES {
        let keys = gen_keys(size);
        let mut qp = QuadraticProbing::new(size);
        for &k in &keys { qp.insert(k, k); }
        group.bench_with_input(BenchmarkId::from_parameter(size), &size, |b, _| {
            b.iter(|| {
                let mut sum = 0i64;
                for &k in &keys { sum = sum.wrapping_add(qp.get(black_box(k)).unwrap_or(0)); }
                black_box(sum)
            });
        });
    }
    group.finish();
}

fn bench_lookup_miss_qp(c: &mut Criterion) {
    let mut group = c.benchmark_group("lookup_miss_qp");
    for &size in SIZES {
        let keys = gen_keys(size);
        let miss_keys: Vec<i64> = gen_keys(size).into_iter().map(|k| k.wrapping_add(1)).collect();
        let mut qp = QuadraticProbing::new(size);
        for &k in &keys { qp.insert(k, k); }
        group.bench_with_input(BenchmarkId::from_parameter(size), &size, |b, _| {
            b.iter(|| {
                let mut found = 0usize;
                for &k in &miss_keys { if qp.get(black_box(k)).is_some() { found += 1; } }
                black_box(found)
            });
        });
    }
    group.finish();
}

fn bench_delete_qp(c: &mut Criterion) {
    let mut group = c.benchmark_group("delete_qp");
    for &size in SIZES {
        let keys = gen_keys(size);
        group.bench_with_input(BenchmarkId::from_parameter(size), &size, |b, _| {
            b.iter(|| {
                let mut qp = QuadraticProbing::new(size);
                for &k in &keys { qp.insert(k, k); }
                for &k in &keys { qp.remove(black_box(k)); }
                black_box(qp.len())
            });
        });
    }
    group.finish();
}

// ─── Robin Hood ───────────────────────────────────────────────────────────────

fn bench_insert_rh(c: &mut Criterion) {
    let mut group = c.benchmark_group("insert_rh");
    for &size in SIZES {
        let keys = gen_keys(size);
        group.bench_with_input(BenchmarkId::from_parameter(size), &size, |b, _| {
            b.iter(|| {
                let mut rh = RobinHood::new(size);
                for &k in &keys { rh.insert(black_box(k), black_box(k)); }
                black_box(rh.len())
            });
        });
    }
    group.finish();
}

fn bench_lookup_hit_rh(c: &mut Criterion) {
    let mut group = c.benchmark_group("lookup_hit_rh");
    for &size in SIZES {
        let keys = gen_keys(size);
        let mut rh = RobinHood::new(size);
        for &k in &keys { rh.insert(k, k); }
        group.bench_with_input(BenchmarkId::from_parameter(size), &size, |b, _| {
            b.iter(|| {
                let mut sum = 0i64;
                for &k in &keys { sum = sum.wrapping_add(rh.get(black_box(k)).unwrap_or(0)); }
                black_box(sum)
            });
        });
    }
    group.finish();
}

fn bench_lookup_miss_rh(c: &mut Criterion) {
    let mut group = c.benchmark_group("lookup_miss_rh");
    for &size in SIZES {
        let keys = gen_keys(size);
        let miss_keys: Vec<i64> = gen_keys(size).into_iter().map(|k| k.wrapping_add(1)).collect();
        let mut rh = RobinHood::new(size);
        for &k in &keys { rh.insert(k, k); }
        group.bench_with_input(BenchmarkId::from_parameter(size), &size, |b, _| {
            b.iter(|| {
                let mut found = 0usize;
                for &k in &miss_keys { if rh.get(black_box(k)).is_some() { found += 1; } }
                black_box(found)
            });
        });
    }
    group.finish();
}

fn bench_delete_rh(c: &mut Criterion) {
    let mut group = c.benchmark_group("delete_rh");
    for &size in SIZES {
        let keys = gen_keys(size);
        group.bench_with_input(BenchmarkId::from_parameter(size), &size, |b, _| {
            b.iter(|| {
                let mut rh = RobinHood::new(size);
                for &k in &keys { rh.insert(k, k); }
                for &k in &keys { rh.remove(black_box(k)); }
                black_box(rh.len())
            });
        });
    }
    group.finish();
}

// ─── Criterion groups ─────────────────────────────────────────────────────────

criterion_group!(
    benches_sc,
    bench_insert_sc,
    bench_lookup_hit_sc,
    bench_lookup_miss_sc,
    bench_delete_sc
);

criterion_group!(
    benches_lp,
    bench_insert_lp,
    bench_lookup_hit_lp,
    bench_lookup_miss_lp,
    bench_delete_lp
);

criterion_group!(
    benches_qp,
    bench_insert_qp,
    bench_lookup_hit_qp,
    bench_lookup_miss_qp,
    bench_delete_qp
);

criterion_group!(
    benches_rh,
    bench_insert_rh,
    bench_lookup_hit_rh,
    bench_lookup_miss_rh,
    bench_delete_rh
);

criterion_main!(benches_sc, benches_lp, benches_qp, benches_rh);
