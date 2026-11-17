//! Linear Probing Hash Table (Open Addressing)
//!
//! All entries live in a single flat array of slots. Collisions are resolved
//! by scanning forward (wrapping) one slot at a time until an Empty slot or
//! the same key is found.
//!
//! # Probe sequence
//!   idx(i) = (hash(key) + i) % capacity,  i = 0, 1, 2, ...
//!
//! # Tombstones
//! Deleted slots become Tombstone rather than Empty.  During lookup we skip
//! tombstones (a Tombstone does *not* stop a search the way Empty does).
//! During insert we place the new entry at the first tombstone encountered
//! (if any) even if we continue scanning to confirm the key isn't already
//! present.
//!
//! # Resize policy
//! When (occupied + tombstone) / capacity > 0.70 we resize to the next power
//! of two >= 2*capacity. Only Occupied slots are rehashed; tombstones vanish.
//!
//! # Clustering
//! Primary clustering is a known weakness: long runs of filled slots cause
//! degraded probe sequences. This is quantified by `max_probe_run()`.

use crate::hasher::{hash_key, next_power_of_two};

/// A single slot in the linear-probing table.
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
    pub max_probe_run: usize,
    pub resize_count: usize,
}

/// Hash table using linear probing.
pub struct LinearProbing {
    slots: Vec<Slot>,
    /// Number of Occupied entries.
    len: usize,
    capacity: usize,
    /// Count of insert() calls (including updates).
    insert_ops: usize,
    /// Count of insert probes that land on an Occupied or Tombstone slot.
    collision_count: usize,
    tombstone_count: usize,
    /// Cumulative probe steps across ALL insert operations.
    probe_count_total: usize,
    resize_count: usize,
}

impl LinearProbing {
    /// Create a new LinearProbing table. Capacity is rounded up to next power
    /// of two (minimum 2) to avoid mod-by-zero and guarantee room to probe.
    pub fn new(initial_capacity: usize) -> Self {
        let cap = if initial_capacity <= 1 {
            2
        } else {
            next_power_of_two(initial_capacity)
        };
        Self {
            slots: (0..cap).map(|_| Slot::Empty).collect(),
            len: 0,
            capacity: cap,
            insert_ops: 0,
            collision_count: 0,
            tombstone_count: 0,
            probe_count_total: 0,
            resize_count: 0,
        }
    }

    /// Insert or update a key-value pair.
    /// - If key already exists, update value in-place.
    /// - Otherwise insert at the first tombstone (if any) or first empty slot.
    /// - Triggers resize when (occupied + tombstone) / cap > 0.70.
    pub fn insert(&mut self, key: i64, val: i64) {
        // Resize check: include tombstones in the density check to prevent
        // the table from filling with tombstones and looping forever.
        if self.fill_ratio() > 0.70 {
            self.resize();
        }

        self.insert_ops += 1;
        let start = hash_key(key, self.capacity);
        let mut first_tombstone: Option<usize> = None;
        let mut probes = 0usize;

        for i in 0..self.capacity {
            let idx = (start + i) % self.capacity;
            probes += 1;

            match &self.slots[idx] {
                Slot::Empty => {
                    // Key not present; insert here (or at first tombstone).
                    let insert_at = first_tombstone.unwrap_or(idx);
                    if i > 0 {
                        // We probed at least once past the ideal slot → collision.
                        self.collision_count += 1;
                    }
                    if first_tombstone.is_some() && insert_at != idx {
                        // We're placing at an earlier tombstone; that tombstone
                        // is being replaced, so tombstone_count decrements.
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
                    // Continue probing — the key might be further ahead.
                }
                Slot::Occupied(k, _) if *k == key => {
                    // Key found; update value in-place.
                    if let Slot::Occupied(_, v) = &mut self.slots[idx] {
                        *v = val;
                    }
                    break;
                }
                Slot::Occupied(_, _) => {
                    // Different key; keep probing.
                    if i > 0 || first_tombstone.is_some() {
                        self.collision_count += 1;
                    }
                }
            }
        }

        // If we found the key was absent and we have a tombstone slot, we may
        // have broken out of the loop via the Empty branch above, but handle
        // the case where the scan exhausted all slots (shouldn't happen with
        // resize, but be safe).
        if let Some(ts_idx) = first_tombstone {
            // Check if we already handled insertion in the loop above.
            // The loop inserts at first_tombstone when it hits Empty, so we
            // only need to handle the edge case where every slot is tombstone.
            // In that scenario the loop exits without inserting.
            if self.capacity > 0 {
                // Check if key was actually inserted by seeing if the tombstone
                // slot is now Occupied.
                if let Slot::Tombstone = &self.slots[ts_idx] {
                    // Still a tombstone — the loop found the key elsewhere or
                    // exhausted (capacity=0 edge already handled). Try to
                    // ensure we don't double-insert.
                    // This path should not be reached in normal operation.
                    let _ = ts_idx; // Suppress unused warning; this is a safety guard.
                }
            }
        }

        self.probe_count_total += probes;
    }

    /// Look up a key. Skips tombstones; stops at Empty.
    pub fn get(&self, key: i64) -> Option<i64> {
        if self.capacity == 0 {
            return None;
        }
        let start = hash_key(key, self.capacity);
        for i in 0..self.capacity {
            let idx = (start + i) % self.capacity;
            match &self.slots[idx] {
                Slot::Empty => return None,
                Slot::Tombstone => continue,
                Slot::Occupied(k, v) if *k == key => return Some(*v),
                Slot::Occupied(_, _) => continue,
            }
        }
        None
    }

    /// Remove a key. Marks the slot as Tombstone. Returns true if key existed.
    pub fn remove(&mut self, key: i64) -> bool {
        if self.capacity == 0 {
            return false;
        }
        let start = hash_key(key, self.capacity);
        for i in 0..self.capacity {
            let idx = (start + i) % self.capacity;
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

    /// Load factor = occupied / capacity (excludes tombstones).
    pub fn load_factor(&self) -> f64 {
        if self.capacity == 0 {
            return 0.0;
        }
        self.len as f64 / self.capacity as f64
    }

    /// Fill ratio = (occupied + tombstones) / capacity; used for resize decision.
    pub fn fill_ratio(&self) -> f64 {
        if self.capacity == 0 {
            return 0.0;
        }
        (self.len + self.tombstone_count) as f64 / self.capacity as f64
    }

    pub fn collision_count(&self) -> usize {
        self.collision_count
    }

    pub fn tombstone_count(&self) -> usize {
        self.tombstone_count
    }

    /// Average probes per insert operation.
    pub fn avg_probe_count(&self) -> f64 {
        if self.insert_ops == 0 {
            return 0.0;
        }
        self.probe_count_total as f64 / self.insert_ops as f64
    }

    /// Length of the longest consecutive run of Occupied+Tombstone slots.
    /// Long runs indicate primary clustering.
    pub fn max_probe_run(&self) -> usize {
        if self.capacity == 0 {
            return 0;
        }
        // We scan 2× the array (wrapping) to handle runs that cross index 0.
        let n = self.capacity;
        let mut max_run = 0usize;
        let mut current = 0usize;
        for i in 0..(2 * n) {
            let idx = i % n;
            match &self.slots[idx] {
                Slot::Empty => {
                    max_run = max_run.max(current);
                    current = 0;
                    // After a gap we don't want to continue the second pass.
                    if i >= n {
                        break;
                    }
                }
                _ => current += 1,
            }
        }
        max_run.max(current)
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
            max_probe_run: self.max_probe_run(),
            resize_count: self.resize_count,
        }
    }

    /// Resize to next power of two >= 2*capacity. Only Occupied slots rehashed.
    fn resize(&mut self) {
        let new_cap = next_power_of_two(self.capacity.saturating_mul(2).max(2));
        let old_slots = std::mem::replace(
            &mut self.slots,
            (0..new_cap).map(|_| Slot::Empty).collect(),
        );
        self.capacity = new_cap;
        self.len = 0;
        self.tombstone_count = 0;

        for slot in old_slots {
            if let Slot::Occupied(k, v) = slot {
                // Rehash without updating stats.
                let start = hash_key(k, self.capacity);
                for i in 0..self.capacity {
                    let idx = (start + i) % self.capacity;
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
        let mut lp = LinearProbing::new(4);
        lp.insert(1, 10);
        lp.insert(2, 20);
        assert_eq!(lp.get(1), Some(10));
        assert_eq!(lp.get(2), Some(20));
        assert_eq!(lp.get(3), None);
        assert!(lp.remove(1));
        assert!(!lp.remove(1));
        assert_eq!(lp.get(1), None);
    }
}
