//! Comprehensive correctness tests for all four hash table implementations.
//! Each implementation is verified against a BTreeMap reference.

use std::collections::BTreeMap;
use hash_table_study::separate_chaining::SeparateChaining;
use hash_table_study::linear_probing::LinearProbing;
use hash_table_study::quadratic_probing::QuadraticProbing;
use hash_table_study::robin_hood::RobinHood;

// ─── Helpers ──────────────────────────────────────────────────────────────────

fn seeded_keys(seed: u64, n: usize) -> Vec<(i64, i64)> {
    // Simple LCG PRNG — reproducible without pulling in rand for tests.
    let mut state = seed;
    let mut out = Vec::with_capacity(n);
    for _ in 0..n {
        state = state.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        let k = (state >> 33) as i64 - (1i64 << 30);
        state = state.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        let v = (state >> 33) as i64;
        out.push((k, v));
    }
    out
}

// ─── Separate Chaining tests ──────────────────────────────────────────────────

#[test]
fn test_sc_empty() {
    let sc = SeparateChaining::new(8);
    assert_eq!(sc.len(), 0);
    assert!(sc.is_empty());
    assert_eq!(sc.get(0), None);
    assert!(!sc.contains_key(42));
}

#[test]
fn test_sc_single() {
    let mut sc = SeparateChaining::new(4);
    sc.insert(99, 42);
    assert_eq!(sc.len(), 1);
    assert_eq!(sc.get(99), Some(42));
    assert!(sc.contains_key(99));
}

#[test]
fn test_sc_multi() {
    let mut sc = SeparateChaining::new(8);
    let mut ref_map = BTreeMap::new();
    for i in 0i64..50 {
        sc.insert(i, i * 2);
        ref_map.insert(i, i * 2);
    }
    assert_eq!(sc.len(), ref_map.len());
    for (k, v) in &ref_map {
        assert_eq!(sc.get(*k), Some(*v), "key={k}");
    }
}

#[test]
fn test_sc_negative_keys() {
    let mut sc = SeparateChaining::new(8);
    sc.insert(-1, 10);
    sc.insert(-100, 20);
    sc.insert(i64::MIN, 30);
    assert_eq!(sc.get(-1), Some(10));
    assert_eq!(sc.get(-100), Some(20));
    assert_eq!(sc.get(i64::MIN), Some(30));
    assert_eq!(sc.get(-2), None);
}

#[test]
fn test_sc_duplicate_update() {
    let mut sc = SeparateChaining::new(4);
    sc.insert(5, 100);
    sc.insert(5, 200);
    sc.insert(5, 300);
    assert_eq!(sc.len(), 1);
    assert_eq!(sc.get(5), Some(300));
}

#[test]
fn test_sc_search_hit() {
    let mut sc = SeparateChaining::new(16);
    for i in 0i64..20 { sc.insert(i, i + 1); }
    assert_eq!(sc.get(0), Some(1));
    assert_eq!(sc.get(19), Some(20));
    assert_eq!(sc.get(10), Some(11));
}

#[test]
fn test_sc_search_miss() {
    let mut sc = SeparateChaining::new(8);
    for i in 0i64..10 { sc.insert(i, i); }
    assert_eq!(sc.get(100), None);
    assert_eq!(sc.get(-1), None);
}

#[test]
fn test_sc_delete_hit() {
    let mut sc = SeparateChaining::new(8);
    sc.insert(7, 77);
    assert!(sc.remove(7));
    assert_eq!(sc.get(7), None);
    assert_eq!(sc.len(), 0);
}

#[test]
fn test_sc_delete_miss() {
    let mut sc = SeparateChaining::new(8);
    sc.insert(1, 1);
    assert!(!sc.remove(999));
    assert_eq!(sc.len(), 1);
}

#[test]
fn test_sc_repeated_insert_delete() {
    let mut sc = SeparateChaining::new(4);
    let mut ref_map = BTreeMap::new();
    for i in 0i64..30 {
        sc.insert(i, i);
        ref_map.insert(i, i);
    }
    for i in (0i64..30).step_by(2) {
        sc.remove(i);
        ref_map.remove(&i);
    }
    assert_eq!(sc.len(), ref_map.len());
    for (k, v) in &ref_map {
        assert_eq!(sc.get(*k), Some(*v));
    }
    // Deleted keys should be gone.
    for i in (0i64..30).step_by(2) {
        assert_eq!(sc.get(i), None);
    }
}

#[test]
fn test_sc_collision_heavy() {
    // Use capacity=1 to force everything into one bucket.
    let mut sc = SeparateChaining::new(1);
    for i in 0i64..10 { sc.insert(i, i * 10); }
    assert_eq!(sc.len(), 10);
    for i in 0i64..10 {
        assert_eq!(sc.get(i), Some(i * 10));
    }
}

#[test]
fn test_sc_high_load() {
    let mut sc = SeparateChaining::new(4);
    let mut ref_map = BTreeMap::new();
    for i in 0i64..200 {
        sc.insert(i, i);
        ref_map.insert(i, i);
    }
    for (k, v) in &ref_map {
        assert_eq!(sc.get(*k), Some(*v));
    }
}

#[test]
fn test_sc_resize() {
    let mut sc = SeparateChaining::new(2);
    let initial_cap = sc.capacity();
    // Insert enough to trigger at least one resize.
    for i in 0i64..100 { sc.insert(i, i); }
    assert!(sc.capacity() > initial_cap, "table should have resized");
    assert!(sc.resize_count() > 0);
    for i in 0i64..100 {
        assert_eq!(sc.get(i), Some(i));
    }
}

#[test]
fn test_sc_load_factor() {
    let mut sc = SeparateChaining::new(16);
    // Before any inserts.
    assert!(sc.load_factor() < 1e-9);
    for i in 0i64..8 { sc.insert(i, i); }
    // Load should stay <= 0.75 (resize kicks in above that).
    assert!(sc.load_factor() <= 0.76, "load={}", sc.load_factor());
}

#[test]
fn test_sc_stats() {
    let mut sc = SeparateChaining::new(4);
    for i in 0i64..20 { sc.insert(i, i); }
    let st = sc.stats();
    assert!(st.load_factor > 0.0);
    assert!(st.max_chain_len >= 1);
    assert!(st.avg_chain_len >= 1.0);
}

// ─── Linear Probing tests ─────────────────────────────────────────────────────

#[test]
fn test_lp_empty() {
    let lp = LinearProbing::new(8);
    assert_eq!(lp.len(), 0);
    assert!(lp.is_empty());
    assert_eq!(lp.get(0), None);
}

#[test]
fn test_lp_single() {
    let mut lp = LinearProbing::new(4);
    lp.insert(99, 42);
    assert_eq!(lp.len(), 1);
    assert_eq!(lp.get(99), Some(42));
    assert!(lp.contains_key(99));
}

#[test]
fn test_lp_multi() {
    let mut lp = LinearProbing::new(8);
    let mut ref_map = BTreeMap::new();
    for i in 0i64..50 {
        lp.insert(i, i * 2);
        ref_map.insert(i, i * 2);
    }
    assert_eq!(lp.len(), ref_map.len());
    for (k, v) in &ref_map {
        assert_eq!(lp.get(*k), Some(*v), "key={k}");
    }
}

#[test]
fn test_lp_negative_keys() {
    let mut lp = LinearProbing::new(8);
    lp.insert(-1, 10);
    lp.insert(-100, 20);
    lp.insert(i64::MIN, 30);
    assert_eq!(lp.get(-1), Some(10));
    assert_eq!(lp.get(-100), Some(20));
    assert_eq!(lp.get(i64::MIN), Some(30));
    assert_eq!(lp.get(-2), None);
}

#[test]
fn test_lp_duplicate_update() {
    let mut lp = LinearProbing::new(8);
    lp.insert(5, 100);
    lp.insert(5, 200);
    lp.insert(5, 300);
    assert_eq!(lp.len(), 1);
    assert_eq!(lp.get(5), Some(300));
}

#[test]
fn test_lp_search_hit() {
    let mut lp = LinearProbing::new(16);
    for i in 0i64..20 { lp.insert(i, i + 1); }
    assert_eq!(lp.get(0), Some(1));
    assert_eq!(lp.get(19), Some(20));
}

#[test]
fn test_lp_search_miss() {
    let mut lp = LinearProbing::new(8);
    for i in 0i64..10 { lp.insert(i, i); }
    assert_eq!(lp.get(100), None);
    assert_eq!(lp.get(-1), None);
}

#[test]
fn test_lp_delete_hit() {
    let mut lp = LinearProbing::new(8);
    lp.insert(7, 77);
    assert!(lp.remove(7));
    assert_eq!(lp.get(7), None);
    assert_eq!(lp.len(), 0);
}

#[test]
fn test_lp_delete_miss() {
    let mut lp = LinearProbing::new(8);
    lp.insert(1, 1);
    assert!(!lp.remove(999));
    assert_eq!(lp.len(), 1);
}

#[test]
fn test_lp_repeated_insert_delete() {
    let mut lp = LinearProbing::new(4);
    let mut ref_map = BTreeMap::new();
    for i in 0i64..30 {
        lp.insert(i, i);
        ref_map.insert(i, i);
    }
    for i in (0i64..30).step_by(2) {
        lp.remove(i);
        ref_map.remove(&i);
    }
    assert_eq!(lp.len(), ref_map.len());
    for (k, v) in &ref_map {
        assert_eq!(lp.get(*k), Some(*v));
    }
    for i in (0i64..30).step_by(2) {
        assert_eq!(lp.get(i), None, "deleted key {i} should be absent");
    }
}

#[test]
fn test_lp_collision_heavy() {
    let mut lp = LinearProbing::new(2);
    for i in 0i64..20 { lp.insert(i, i * 10); }
    assert_eq!(lp.len(), 20);
    for i in 0i64..20 {
        assert_eq!(lp.get(i), Some(i * 10));
    }
}

#[test]
fn test_lp_high_load() {
    let mut lp = LinearProbing::new(4);
    let mut ref_map = BTreeMap::new();
    for i in 0i64..200 {
        lp.insert(i, i);
        ref_map.insert(i, i);
    }
    for (k, v) in &ref_map {
        assert_eq!(lp.get(*k), Some(*v));
    }
}

#[test]
fn test_lp_resize() {
    let mut lp = LinearProbing::new(2);
    let initial_cap = lp.capacity();
    for i in 0i64..100 { lp.insert(i, i); }
    assert!(lp.capacity() > initial_cap);
    assert!(lp.resize_count() > 0);
    for i in 0i64..100 {
        assert_eq!(lp.get(i), Some(i));
    }
}

#[test]
fn test_lp_load_factor() {
    let mut lp = LinearProbing::new(16);
    assert!(lp.load_factor() < 1e-9);
    for i in 0i64..8 { lp.insert(i, i); }
    assert!(lp.load_factor() <= 0.71, "load={}", lp.load_factor());
}

#[test]
fn test_lp_stats() {
    let mut lp = LinearProbing::new(4);
    for i in 0i64..20 { lp.insert(i, i); }
    let st = lp.stats();
    assert!(st.load_factor > 0.0);
    assert!(st.avg_probe_count >= 1.0);
}

// ─── Quadratic Probing tests ──────────────────────────────────────────────────

#[test]
fn test_qp_empty() {
    let qp = QuadraticProbing::new(8);
    assert_eq!(qp.len(), 0);
    assert!(qp.is_empty());
    assert_eq!(qp.get(0), None);
}

#[test]
fn test_qp_single() {
    let mut qp = QuadraticProbing::new(4);
    qp.insert(99, 42);
    assert_eq!(qp.len(), 1);
    assert_eq!(qp.get(99), Some(42));
    assert!(qp.contains_key(99));
}

#[test]
fn test_qp_multi() {
    let mut qp = QuadraticProbing::new(8);
    let mut ref_map = BTreeMap::new();
    for i in 0i64..50 {
        qp.insert(i, i * 2);
        ref_map.insert(i, i * 2);
    }
    assert_eq!(qp.len(), ref_map.len());
    for (k, v) in &ref_map {
        assert_eq!(qp.get(*k), Some(*v), "key={k}");
    }
}

#[test]
fn test_qp_negative_keys() {
    let mut qp = QuadraticProbing::new(8);
    qp.insert(-1, 10);
    qp.insert(-100, 20);
    qp.insert(i64::MIN, 30);
    assert_eq!(qp.get(-1), Some(10));
    assert_eq!(qp.get(-100), Some(20));
    assert_eq!(qp.get(i64::MIN), Some(30));
    assert_eq!(qp.get(-2), None);
}

#[test]
fn test_qp_duplicate_update() {
    let mut qp = QuadraticProbing::new(8);
    qp.insert(5, 100);
    qp.insert(5, 200);
    qp.insert(5, 300);
    assert_eq!(qp.len(), 1);
    assert_eq!(qp.get(5), Some(300));
}

#[test]
fn test_qp_search_hit() {
    let mut qp = QuadraticProbing::new(16);
    for i in 0i64..20 { qp.insert(i, i + 1); }
    assert_eq!(qp.get(0), Some(1));
    assert_eq!(qp.get(19), Some(20));
}

#[test]
fn test_qp_search_miss() {
    let mut qp = QuadraticProbing::new(8);
    for i in 0i64..10 { qp.insert(i, i); }
    assert_eq!(qp.get(100), None);
    assert_eq!(qp.get(-1), None);
}

#[test]
fn test_qp_delete_hit() {
    let mut qp = QuadraticProbing::new(8);
    qp.insert(7, 77);
    assert!(qp.remove(7));
    assert_eq!(qp.get(7), None);
    assert_eq!(qp.len(), 0);
}

#[test]
fn test_qp_delete_miss() {
    let mut qp = QuadraticProbing::new(8);
    qp.insert(1, 1);
    assert!(!qp.remove(999));
    assert_eq!(qp.len(), 1);
}

#[test]
fn test_qp_repeated_insert_delete() {
    let mut qp = QuadraticProbing::new(4);
    let mut ref_map = BTreeMap::new();
    for i in 0i64..30 {
        qp.insert(i, i);
        ref_map.insert(i, i);
    }
    for i in (0i64..30).step_by(2) {
        qp.remove(i);
        ref_map.remove(&i);
    }
    assert_eq!(qp.len(), ref_map.len());
    for (k, v) in &ref_map {
        assert_eq!(qp.get(*k), Some(*v));
    }
    for i in (0i64..30).step_by(2) {
        assert_eq!(qp.get(i), None, "deleted key {i} should be absent");
    }
}

#[test]
fn test_qp_collision_heavy() {
    let mut qp = QuadraticProbing::new(2);
    for i in 0i64..20 { qp.insert(i, i * 10); }
    assert_eq!(qp.len(), 20);
    for i in 0i64..20 {
        assert_eq!(qp.get(i), Some(i * 10));
    }
}

#[test]
fn test_qp_high_load() {
    let mut qp = QuadraticProbing::new(4);
    let mut ref_map = BTreeMap::new();
    for i in 0i64..200 {
        qp.insert(i, i);
        ref_map.insert(i, i);
    }
    for (k, v) in &ref_map {
        assert_eq!(qp.get(*k), Some(*v));
    }
}

#[test]
fn test_qp_resize() {
    let mut qp = QuadraticProbing::new(2);
    let initial_cap = qp.capacity();
    for i in 0i64..100 { qp.insert(i, i); }
    assert!(qp.capacity() > initial_cap);
    assert!(qp.resize_count() > 0);
    for i in 0i64..100 {
        assert_eq!(qp.get(i), Some(i));
    }
}

#[test]
fn test_qp_load_factor() {
    let mut qp = QuadraticProbing::new(16);
    assert!(qp.load_factor() < 1e-9);
    for i in 0i64..5 { qp.insert(i, i); }
    assert!(qp.load_factor() <= 0.51, "load={}", qp.load_factor());
}

#[test]
fn test_qp_stats() {
    let mut qp = QuadraticProbing::new(4);
    for i in 0i64..20 { qp.insert(i, i); }
    let st = qp.stats();
    assert!(st.load_factor > 0.0);
    assert!(st.avg_probe_count >= 1.0);
}

// ─── Robin Hood tests ─────────────────────────────────────────────────────────

#[test]
fn test_rh_empty() {
    let rh = RobinHood::new(8);
    assert_eq!(rh.len(), 0);
    assert!(rh.is_empty());
    assert_eq!(rh.get(0), None);
}

#[test]
fn test_rh_single() {
    let mut rh = RobinHood::new(4);
    rh.insert(99, 42);
    assert_eq!(rh.len(), 1);
    assert_eq!(rh.get(99), Some(42));
    assert!(rh.contains_key(99));
}

#[test]
fn test_rh_multi() {
    let mut rh = RobinHood::new(8);
    let mut ref_map = BTreeMap::new();
    for i in 0i64..50 {
        rh.insert(i, i * 2);
        ref_map.insert(i, i * 2);
    }
    assert_eq!(rh.len(), ref_map.len());
    for (k, v) in &ref_map {
        assert_eq!(rh.get(*k), Some(*v), "key={k}");
    }
}

#[test]
fn test_rh_negative_keys() {
    let mut rh = RobinHood::new(8);
    rh.insert(-1, 10);
    rh.insert(-100, 20);
    rh.insert(i64::MIN, 30);
    assert_eq!(rh.get(-1), Some(10));
    assert_eq!(rh.get(-100), Some(20));
    assert_eq!(rh.get(i64::MIN), Some(30));
    assert_eq!(rh.get(-2), None);
}

#[test]
fn test_rh_duplicate_update() {
    let mut rh = RobinHood::new(8);
    rh.insert(5, 100);
    rh.insert(5, 200);
    rh.insert(5, 300);
    assert_eq!(rh.len(), 1);
    assert_eq!(rh.get(5), Some(300));
}

#[test]
fn test_rh_search_hit() {
    let mut rh = RobinHood::new(16);
    for i in 0i64..20 { rh.insert(i, i + 1); }
    assert_eq!(rh.get(0), Some(1));
    assert_eq!(rh.get(19), Some(20));
}

#[test]
fn test_rh_search_miss() {
    let mut rh = RobinHood::new(8);
    for i in 0i64..10 { rh.insert(i, i); }
    assert_eq!(rh.get(100), None);
    assert_eq!(rh.get(-1), None);
}

#[test]
fn test_rh_delete_hit() {
    let mut rh = RobinHood::new(8);
    rh.insert(7, 77);
    assert!(rh.remove(7));
    assert_eq!(rh.get(7), None);
    assert_eq!(rh.len(), 0);
}

#[test]
fn test_rh_delete_miss() {
    let mut rh = RobinHood::new(8);
    rh.insert(1, 1);
    assert!(!rh.remove(999));
    assert_eq!(rh.len(), 1);
}

#[test]
fn test_rh_repeated_insert_delete() {
    let mut rh = RobinHood::new(4);
    let mut ref_map = BTreeMap::new();
    for i in 0i64..30 {
        rh.insert(i, i);
        ref_map.insert(i, i);
    }
    for i in (0i64..30).step_by(2) {
        rh.remove(i);
        ref_map.remove(&i);
    }
    assert_eq!(rh.len(), ref_map.len());
    for (k, v) in &ref_map {
        assert_eq!(rh.get(*k), Some(*v));
    }
    for i in (0i64..30).step_by(2) {
        assert_eq!(rh.get(i), None, "deleted key {i} should be absent");
    }
}

#[test]
fn test_rh_collision_heavy() {
    let mut rh = RobinHood::new(2);
    for i in 0i64..20 { rh.insert(i, i * 10); }
    assert_eq!(rh.len(), 20);
    for i in 0i64..20 {
        assert_eq!(rh.get(i), Some(i * 10));
    }
}

#[test]
fn test_rh_high_load() {
    let mut rh = RobinHood::new(4);
    let mut ref_map = BTreeMap::new();
    for i in 0i64..200 {
        rh.insert(i, i);
        ref_map.insert(i, i);
    }
    for (k, v) in &ref_map {
        assert_eq!(rh.get(*k), Some(*v));
    }
}

#[test]
fn test_rh_resize() {
    let mut rh = RobinHood::new(2);
    let initial_cap = rh.capacity();
    for i in 0i64..100 { rh.insert(i, i); }
    assert!(rh.capacity() > initial_cap);
    assert!(rh.resize_count() > 0);
    for i in 0i64..100 {
        assert_eq!(rh.get(i), Some(i));
    }
}

#[test]
fn test_rh_load_factor() {
    let mut rh = RobinHood::new(16);
    assert!(rh.load_factor() < 1e-9);
    for i in 0i64..8 { rh.insert(i, i); }
    assert!(rh.load_factor() <= 0.71, "load={}", rh.load_factor());
}

#[test]
fn test_rh_stats() {
    let mut rh = RobinHood::new(4);
    for i in 0i64..20 { rh.insert(i, i); }
    let st = rh.stats();
    assert!(st.load_factor > 0.0);
}

// ─── Cross-implementation agreement test ──────────────────────────────────────

#[test]
fn test_all_agree() {
    let pairs = seeded_keys(42, 1000);

    let mut ref_map = BTreeMap::new();
    let mut sc = SeparateChaining::new(16);
    let mut lp = LinearProbing::new(16);
    let mut qp = QuadraticProbing::new(16);
    let mut rh = RobinHood::new(16);

    for (k, v) in &pairs {
        ref_map.insert(*k, *v);
        sc.insert(*k, *v);
        lp.insert(*k, *v);
        qp.insert(*k, *v);
        rh.insert(*k, *v);
    }

    // All must agree with the reference BTreeMap for every key inserted.
    for k in ref_map.keys() {
        let expected = ref_map[k];
        assert_eq!(sc.get(*k), Some(expected), "SC miss key={k}");
        assert_eq!(lp.get(*k), Some(expected), "LP miss key={k}");
        assert_eq!(qp.get(*k), Some(expected), "QP miss key={k}");
        assert_eq!(rh.get(*k), Some(expected), "RH miss key={k}");
    }

    // Counts must match.
    assert_eq!(sc.len(), ref_map.len());
    assert_eq!(lp.len(), ref_map.len());
    assert_eq!(qp.len(), ref_map.len());
    assert_eq!(rh.len(), ref_map.len());
}
