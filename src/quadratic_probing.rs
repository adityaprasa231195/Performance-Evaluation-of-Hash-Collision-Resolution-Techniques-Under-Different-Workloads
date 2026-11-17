//! Quadratic Probing Hash Table (Open Addressing)
//!
//! Like linear probing but the probe offset is quadratic in the step count:
//!   idx(i) = (hash(key) + i²) % capacity
//!
//! # Why prime capacity?
//! With a prime capacity m and i ∈ 0 .. ⌊m/2⌋, the positions
//! h, h+1, h+4, h+9, ... (mod m) are all distinct. Proof sketch:
//!   Suppose (h + i²) ≡ (h + j²) (mod m) with 0 ≤ i < j ≤ ⌊m/2⌋.
//!   Then m | (j²−i²) = (j−i)(j+i).
//!   Since m is prime and 0 < j−i < m and 0 < j+i < m, neither factor is
//!   divisible by m — contradiction. So all positions are distinct, guaranteeing
//!   that any insertion with load < 0.5 will find an empty slot.
//!
//! This is why we keep load factor below 0.50 and resize aggressively.
//!
//! # Tombstones
//! Like linear probing, deleted slots become Tombstone. The search skips them
//! but Empty still stops the search.
//!
//! # Resize policy
//! When occupied / capacity > 0.50, resize to next_prime(2 * capacity).

use crate::hasher::{hash_key, next_prime};

/// A single slot in the quadratic-probing table (reusing the same shape as LP).
#[derive(Clone, Debug)]
pub enum Slot {
    Empty,
    Occupied(i64, i64), // (key, value)
    Tombstone,
}

/// Statistics snapshot.
#[derive(Debug, Clone)]
pub struct Stats {
    pub collisions: usize,
    pub tombstones: usize,
    pub load_factor: f64,
    pub avg_probe_count: f64,
    pub max_probe_count: usize,
    pub resize_count: usize,
}

/// Hash table using quadratic probing.
pub struct QuadraticProbing {
    slots: Vec<Slot>,
    len: usize,
    capacity: usize, // Always prime.
    insert_ops: usize,
    collision_count: usize,
    tombstone_count: usize,
    probe_count_total: usize,
    max_probe_count: usize,
    resize_count: usize,
}

impl QuadraticProbing {
    /// Create a new QuadraticProbing table.
    /// Capacity is rounded up to the next prime >= initial_capacity (minimum 2).
    pub fn new(initial_capacity: usize) -> Self {
        let cap = next_prime(initial_capacity.max(2));
        Self {
            slots: (0..cap).map(|_| Slot::Empty).collect(),
            len: 0,
            capacity: cap,
            insert_ops: 0,
            collision_count: 0,
            tombstone_count: 0,
            probe_count_total: 0,
            max_probe_count: 0,
            resize_count: 0,
        }
    }

    /// Insert or update. Triggers resize at load > 0.50.
    pub fn insert(&mut self, key: i64, val: i64) {
        if self.load_factor() > 0.50 {
            self.resize();
        }

        self.insert_ops += 1;
        let start = hash_key(key, self.capacity);
        let mut first_tombstone: Option<usize> = None;
        let mut probes = 0usize;

        // With prime capacity we only need to probe capacity/2 steps to cover
        // all distinct positions (see module-level proof). But we scan up to
        // capacity steps for safety (handles tombstone-heavy states).
        for i in 0..self.capacity {
            // Quadratic offset: i² (wrapping to avoid overflow on large i).
            let offset = i.wrapping_mul(i);
            let idx = (start + offset) % self.capacity;
            probes += 1;

            match &self.slots[idx] {
                Slot::Empty => {
                    let insert_at = first_tombstone.unwrap_or(idx);
                    if i > 0 {
                        self.collision_count += 1;
                    }
                    if first_tombstone.is_some() && insert_at != idx {
                        self.tombstone_count -= 1;
                    }
                    self.slots[insert_at] = Slot::Occupied(key, val);
                    self.len += 1;
                    break;
                }
                Slot::Tombstone => {
                    if first_tombstone.is_none() {
                        first_tombstone = Some(idx);
                    }
                    if i > 0 {
                        self.collision_count += 1;
                    }
                }
                Slot::Occupied(k, _) if *k == key => {
                    // Update in place.
                    if let Slot::Occupied(_, v) = &mut self.slots[idx] {
                        *v = val;
                    }
                    break;
                }
                Slot::Occupied(_, _) => {
                    if i > 0 || first_tombstone.is_some() {
                        self.collision_count += 1;
                    }
                }
            }
        }

        self.probe_count_total += probes;
        if probes > self.max_probe_count {
            self.max_probe_count = probes;
        }
    }

    /// Look up key; skips tombstones, stops at Empty.
    pub fn get(&self, key: i64) -> Option<i64> {
        if self.capacity == 0 {
            return None;
        }
        let start = hash_key(key, self.capacity);
        for i in 0..self.capacity {
            let offset = i.wrapping_mul(i);
            let idx = (start + offset) % self.capacity;
            match &self.slots[idx] {
                Slot::Empty => return None,
                Slot::Tombstone => continue,
                Slot::Occupied(k, v) if *k == key => return Some(*v),
                Slot::Occupied(_, _) => continue,
            }
        }
        None
    }

    /// Remove key; marks slot Tombstone. Returns true if key was present.
    pub fn remove(&mut self, key: i64) -> bool {
        if self.capacity == 0 {
            return false;
        }
        let start = hash_key(key, self.capacity);
        for i in 0..self.capacity {
            let offset = i.wrapping_mul(i);
            let idx = (start + offset) % self.capacity;
            match &self.slots[idx] {
                Slot::Empty => return false,
                Slot::Tombstone => continue,
                Slot::Occupied(k, _) if *k == key => {
                    self.slots[idx] = Slot::Tombstone;
                    self.len -= 1;
                    self.tombstone_count += 1;
                    return true;
                }
                Slot::Occupied(_, _) => continue,
            }
        }
        false
    }

    pub fn contains_key(&self, key: i64) -> bool {
        self.get(key).is_some()
    }

    pub fn len(&self) -> usize {
        self.len
    }

    pub fn is_empty(&self) -> bool {
        self.len == 0
    }

    pub fn capacity(&self) -> usize {
        self.capacity
    }

    /// Load factor = occupied / capacity.
    pub fn load_factor(&self) -> f64 {
        if self.capacity == 0 {
            return 0.0;
        }
        self.len as f64 / self.capacity as f64
    }

    pub fn collision_count(&self) -> usize {
        self.collision_count
    }

    pub fn tombstone_count(&self) -> usize {
        self.tombstone_count
    }

    pub fn avg_probe_count(&self) -> f64 {
        if self.insert_ops == 0 {
            return 0.0;
        }
        self.probe_count_total as f64 / self.insert_ops as f64
    }

    pub fn max_probe_count(&self) -> usize {
        self.max_probe_count
    }

    pub fn resize_count(&self) -> usize {
        self.resize_count
    }

    pub fn stats(&self) -> Stats {
        Stats {
            collisions: self.collision_count,
            tombstones: self.tombstone_count,
            load_factor: self.load_factor(),
            avg_probe_count: self.avg_probe_count(),
            max_probe_count: self.max_probe_count,
            resize_count: self.resize_count,
        }
    }

    /// Resize to next_prime(2 * capacity). Only Occupied slots are rehashed.
    fn resize(&mut self) {
        let new_cap = next_prime(self.capacity.saturating_mul(2).max(2));
        let old_slots = std::mem::replace(
            &mut self.slots,
            (0..new_cap).map(|_| Slot::Empty).collect(),
        );
        self.capacity = new_cap;
        self.len = 0;
        self.tombstone_count = 0;

        for slot in old_slots {
            if let Slot::Occupied(k, v) = slot {
                let start = hash_key(k, self.capacity);
                for i in 0..self.capacity {
                    let offset = i.wrapping_mul(i);
                    let idx = (start + offset) % self.capacity;
                    if let Slot::Empty = &self.slots[idx] {
                        self.slots[idx] = Slot::Occupied(k, v);
                        self.len += 1;
                        break;
                    }
                }
            }
        }
        self.resize_count += 1;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn smoke_test() {
        let mut qp = QuadraticProbing::new(4);
        qp.insert(1, 10);
        qp.insert(2, 20);
        assert_eq!(qp.get(1), Some(10));
        assert_eq!(qp.get(2), Some(20));
        assert_eq!(qp.get(3), None);
        assert!(qp.remove(1));
        assert!(!qp.remove(1));
        assert_eq!(qp.get(1), None);
    }
}
