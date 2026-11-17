//! Robin Hood Hashing (Open Addressing)
//!
//! Robin Hood hashing is an open-addressing scheme that reduces *variance* in
//! probe distances by "stealing" slots from rich entries (those sitting close
//! to their ideal position) to give to poor entries (those far from theirs).
//!
//! # Insert algorithm
//! When inserting entry E with current probe distance `d`:
//!   1. Compute target slot idx = (hash(key) + d) % cap.
//!   2. If slot is Empty, place E there with dist=d. Done.
//!   3. If slot holds a key equal to E's key, update value. Done.
//!   4. If slot holds an entry F with dist_F < d ("richer" than us), swap E and
//!      F ("Robin Hood steal"): place E in the slot and continue inserting F
//!      with its own probe distance incremented from its ideal slot.
//!   5. Otherwise (F is at least as poor as E), increment d and go to step 1.
//!
//! # Lookup
//! Probe i=0,1,2,...:
//!   - If Empty → not found.
//!   - If slot.dist < i → not found (early termination; any matching entry would
//!     have displaced this one during insertion).
//!   - If key matches → found.
//!
//! # Delete (backward shift / Robin Hood deletion)
//! Naively marking a tombstone breaks the early-termination invariant. Instead:
//!   1. Find the slot containing the key.
//!   2. Walk forward, shifting each subsequent entry one step back (reducing its
//!      dist by 1) while its dist > 0.
//!   3. Set the last vacated slot to Empty.
//!
//! # Resize
//! When load > 0.70, resize to next power of two >= 2*cap. All Occupied entries
//! are reinserted.

use crate::hasher::{hash_key, next_power_of_two};

/// A slot in the Robin Hood table.
#[derive(Clone, Debug)]
pub enum RhSlot {
    Empty,
    Occupied {
        key: i64,
        val: i64,
        /// Probe distance from the slot this entry hashes to (0 = ideal).
        dist: usize,
    },
}

/// Statistics snapshot.
#[derive(Debug, Clone)]
pub struct Stats {
    pub load_factor: f64,
    pub avg_probe_dist: f64,
    pub max_probe_dist: usize,
    pub probe_count_total: usize,
    pub resize_count: usize,
    pub collision_count: usize,
}

/// Hash table using Robin Hood hashing.
pub struct RobinHood {
    slots: Vec<RhSlot>,
    len: usize,
    capacity: usize,
    insert_ops: usize,
    /// Sum of probe distances for all currently-stored entries (for avg).
    probe_count_total: usize,
    /// Maximum probe distance ever seen during an insert.
    max_probe_dist: usize,
    collision_count: usize,
    resize_count: usize,
}

impl RobinHood {
    /// Create a new RobinHood table. Capacity rounded to next power of two
    /// (minimum 2).
    pub fn new(initial_capacity: usize) -> Self {
        let cap = if initial_capacity <= 1 {
            2
        } else {
            next_power_of_two(initial_capacity)
        };
        Self {
            slots: (0..cap).map(|_| RhSlot::Empty).collect(),
            len: 0,
            capacity: cap,
            insert_ops: 0,
            probe_count_total: 0,
            max_probe_dist: 0,
            collision_count: 0,
            resize_count: 0,
        }
    }

    /// Insert or update. Triggers resize at load > 0.70.
    pub fn insert(&mut self, key: i64, val: i64) {
        if self.load_factor() > 0.70 {
            self.resize();
        }
        self.insert_ops += 1;
        self.insert_internal(key, val);
    }

    /// Core insertion; also used by resize (without updating insert_ops/resize_count).
    fn insert_internal(&mut self, key: i64, val: i64) {
        let home = hash_key(key, self.capacity);
        // The entry we are currently trying to place.
        let mut cur_key = key;
        let mut cur_val = val;
        let mut cur_dist = 0usize;

        loop {
            let idx = (home.wrapping_add(
                // Calculate offset from home based on cur_dist, but we need
                // the actual ideal slot for cur_key after swaps.
                // We track cur_dist as "how many steps from ideal slot we are",
                // so the absolute index is (ideal + cur_dist) % cap.
                // After a swap cur_key's ideal may differ — recompute.
                hash_key(cur_key, self.capacity)
                    .wrapping_add(cur_dist),
            )) % self.capacity;
            // Simpler: compute absolute index directly.
            let abs_idx = (hash_key(cur_key, self.capacity) + cur_dist) % self.capacity;

            // Update max probe distance stat.
            if cur_dist > self.max_probe_dist {
                self.max_probe_dist = cur_dist;
            }

            match &self.slots[abs_idx] {
                RhSlot::Empty => {
                    self.probe_count_total += cur_dist;
                    if cur_dist > 0 {
                        self.collision_count += 1;
                    }
                    self.slots[abs_idx] = RhSlot::Occupied {
                        key: cur_key,
                        val: cur_val,
                        dist: cur_dist,
                    };
                    self.len += 1;
                    return;
                }
                RhSlot::Occupied { key: k, .. } if *k == cur_key => {
                    // Update existing key's value.
                    if let RhSlot::Occupied { val: v, .. } = &mut self.slots[abs_idx] {
                        *v = cur_val;
                    }
                    return;
                }
                RhSlot::Occupied { dist: d, .. } if *d < cur_dist => {
                    // Robin Hood steal: evict the richer entry.
                    self.collision_count += 1;
                    let (evict_key, evict_val, evict_dist) =
                        if let RhSlot::Occupied { key, val, dist } = &self.slots[abs_idx] {
                            (*key, *val, *dist)
                        } else {
                            unreachable!()
                        };
                    self.slots[abs_idx] = RhSlot::Occupied {
                        key: cur_key,
                        val: cur_val,
                        dist: cur_dist,
                    };
                    // Now try to place the evicted entry.
                    cur_key = evict_key;
                    cur_val = evict_val;
                    cur_dist = evict_dist + 1;
                }
                RhSlot::Occupied { .. } => {
                    // Slot occupied by entry at least as poor as us; keep probing.
                    self.collision_count += 1;
                    cur_dist += 1;
                }
            }
            // Suppress unused variable warning for the computed-but-unused idx
            let _ = idx;
        }
    }

    /// Look up a key with early termination.
    pub fn get(&self, key: i64) -> Option<i64> {
        if self.capacity == 0 {
            return None;
        }
        let home = hash_key(key, self.capacity);
        for i in 0..self.capacity {
            let idx = (home + i) % self.capacity;
            match &self.slots[idx] {
                RhSlot::Empty => return None,
                RhSlot::Occupied { dist, .. } if *dist < i => {
                    // Any entry with this key would have dist >= i (it would
                    // have stolen this slot). So the key is not present.
                    return None;
                }
                RhSlot::Occupied { key: k, val: v, .. } if *k == key => return Some(*v),
                RhSlot::Occupied { .. } => continue,
            }
        }
        None
    }

    /// Remove using backward shift to preserve the early-termination invariant.
    pub fn remove(&mut self, key: i64) -> bool {
        if self.capacity == 0 {
            return false;
        }
        let home = hash_key(key, self.capacity);

        // Step 1: find the slot.
        let mut found_idx: Option<usize> = None;
        for i in 0..self.capacity {
            let idx = (home + i) % self.capacity;
            match &self.slots[idx] {
                RhSlot::Empty => return false,
                RhSlot::Occupied { dist, .. } if *dist < i => return false,
                RhSlot::Occupied { key: k, .. } if *k == key => {
                    found_idx = Some(idx);
                    break;
                }
                RhSlot::Occupied { .. } => continue,
            }
        }

        let start = match found_idx {
            Some(i) => i,
            None => return false,
        };

        // Step 2: backward shift — shift subsequent entries left while dist > 0.
        let mut current = start;
        loop {
            let next = (current + 1) % self.capacity;
            match &self.slots[next] {
                RhSlot::Empty => {
                    self.slots[current] = RhSlot::Empty;
                    break;
                }
                RhSlot::Occupied { dist, .. } if *dist == 0 => {
                    // This entry is at its ideal slot; we cannot shift it back.
                    self.slots[current] = RhSlot::Empty;
                    break;
                }
                RhSlot::Occupied { key: k, val: v, dist: d } => {
                    let (k2, v2, d2) = (*k, *v, *d);
                    self.slots[current] = RhSlot::Occupied {
                        key: k2,
                        val: v2,
                        dist: d2 - 1,
                    };
                    current = next;
                }
            }
        }

        self.len -= 1;
        true
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

    pub fn load_factor(&self) -> f64 {
        if self.capacity == 0 {
            return 0.0;
        }
        self.len as f64 / self.capacity as f64
    }

    /// Average probe distance across all stored entries.
    pub fn avg_probe_dist(&self) -> f64 {
        if self.len == 0 {
            return 0.0;
        }
        // Recompute from current slot state for accuracy.
        let total: usize = self.slots.iter().map(|s| {
            if let RhSlot::Occupied { dist, .. } = s { *dist } else { 0 }
        }).sum();
        total as f64 / self.len as f64
    }

    /// Maximum probe distance seen across all currently-stored entries.
    pub fn max_probe_dist(&self) -> usize {
        self.slots.iter().map(|s| {
            if let RhSlot::Occupied { dist, .. } = s { *dist } else { 0 }
        }).max().unwrap_or(0)
    }

    pub fn probe_count_total(&self) -> usize {
        self.probe_count_total
    }

    pub fn collision_count(&self) -> usize {
        self.collision_count
    }

    pub fn resize_count(&self) -> usize {
        self.resize_count
    }

    pub fn stats(&self) -> Stats {
        Stats {
            load_factor: self.load_factor(),
            avg_probe_dist: self.avg_probe_dist(),
            max_probe_dist: self.max_probe_dist(),
            probe_count_total: self.probe_count_total,
            resize_count: self.resize_count,
            collision_count: self.collision_count,
        }
    }

    /// Resize to next power of two >= 2*capacity. Reinserts all Occupied entries.
    fn resize(&mut self) {
        let new_cap = next_power_of_two(self.capacity.saturating_mul(2).max(2));
        let old_slots = std::mem::replace(
            &mut self.slots,
            (0..new_cap).map(|_| RhSlot::Empty).collect(),
        );
        self.capacity = new_cap;
        self.len = 0;
        self.probe_count_total = 0;
        self.max_probe_dist = 0;

        for slot in old_slots {
            if let RhSlot::Occupied { key, val, .. } = slot {
                self.insert_internal(key, val);
                // insert_internal increments self.len; don't double-count.
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
        let mut rh = RobinHood::new(4);
        rh.insert(1, 10);
        rh.insert(2, 20);
        assert_eq!(rh.get(1), Some(10));
        assert_eq!(rh.get(2), Some(20));
        assert_eq!(rh.get(3), None);
        assert!(rh.remove(1));
        assert!(!rh.remove(1));
        assert_eq!(rh.get(1), None);
    }
}
