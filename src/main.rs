use hash_table_study::separate_chaining::SeparateChaining;
use hash_table_study::linear_probing::LinearProbing;
use hash_table_study::quadratic_probing::QuadraticProbing;
use hash_table_study::robin_hood::RobinHood;

fn main() {
    // Sample data: 20 keys including negatives and duplicates.
    let samples: &[(i64, i64)] = &[
        (1, 100),
        (2, 200),
        (-3, 300),
        (4, 400),
        (-5, 500),
        (6, 600),
        (7, 700),
        (8, 800),
        (9, 900),
        (10, 1000),
        // duplicates — should update value
        (1, 111),
        (2, 222),
        (-3, 333),
        // more unique keys
        (11, 1100),
        (12, 1200),
        (-13, 1300),
        (100, 10000),
        (-100, 20000),
        (0, 0),
        (i64::MAX, 42),
    ];

    println!("=== Separate Chaining ===");
    let mut sc = SeparateChaining::new(8);
    for &(k, v) in samples { sc.insert(k, v); }
    let st = sc.stats();
    println!("  len={}, capacity={}", sc.len(), sc.capacity());
    println!("  load_factor={:.3}, collisions={}", st.load_factor, st.collisions);
    println!("  avg_chain={:.3}, max_chain={}, resizes={}", st.avg_chain_len, st.max_chain_len, st.resize_count);
    println!("  get(1)={:?}, get(-3)={:?}, get(99)={:?}", sc.get(1), sc.get(-3), sc.get(99));

    println!("\n=== Linear Probing ===");
    let mut lp = LinearProbing::new(8);
    for &(k, v) in samples { lp.insert(k, v); }
    let st = lp.stats();
    println!("  len={}, capacity={}", lp.len(), lp.capacity());
    println!("  load_factor={:.3}, collisions={}", st.load_factor, st.collisions);
    println!("  avg_probe={:.3}, max_probe_run={}, tombstones={}", st.avg_probe_count, st.max_probe_run, st.tombstones);
    println!("  resizes={}", st.resize_count);
    println!("  get(1)={:?}, get(-3)={:?}, get(99)={:?}", lp.get(1), lp.get(-3), lp.get(99));

    println!("\n=== Quadratic Probing ===");
    let mut qp = QuadraticProbing::new(8);
    for &(k, v) in samples { qp.insert(k, v); }
    let st = qp.stats();
    println!("  len={}, capacity={}", qp.len(), qp.capacity());
    println!("  load_factor={:.3}, collisions={}", st.load_factor, st.collisions);
    println!("  avg_probe={:.3}, tombstones={}", st.avg_probe_count, st.tombstones);
    println!("  resizes={}", st.resize_count);
    println!("  get(1)={:?}, get(-3)={:?}, get(99)={:?}", qp.get(1), qp.get(-3), qp.get(99));

    println!("\n=== Robin Hood Hashing ===");
    let mut rh = RobinHood::new(8);
    for &(k, v) in samples { rh.insert(k, v); }
    let st = rh.stats();
    println!("  len={}, capacity={}", rh.len(), rh.capacity());
    println!("  load_factor={:.3}", st.load_factor);
    println!("  avg_probe_dist={:.3}, max_probe_dist={}", st.avg_probe_dist, st.max_probe_dist);
    println!("  probe_total={}, resizes={}", st.probe_count_total, st.resize_count);
    println!("  get(1)={:?}, get(-3)={:?}, get(99)={:?}", rh.get(1), rh.get(-3), rh.get(99));
}
