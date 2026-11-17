//! Separate Chaining Hash Table
//!
//! Each bucket is an independent linked list (here represented as a Vec).
//! Collisions are resolved by appending to the existing bucket's list.
//!
//! # Complexity (expected, uniform hashing)
//! - Insert: O(1) amortised
//! - Lookup: O(1 + α) where α = load factor = n/m
//! - Delete: O(1 + α)
//! - Space:  O(n + m) — m buckets + n entries
//!
//! # Resize policy
//! When load factor exceeds 0.75 we resize to the next power of two >= 2*cap.
//! This keeps α below 0.75, ensuring O(1) expected chain length.

use crate::hasher::{hash_key, next_power_of_two};

/// Statistics snapshot for SeparateChaining.
#[derive(Debug, Clone)]
pub struct Stats {
    pub collisions: usize,
    pub avg_chain_len: f64,
    pub max_chain_len: usize,
    pub load_factor: f64,
    pub resize_count: usize,
}

/// Hash table using separate chaining collision resolution.
pub struct SeparateChaining {
    /// The array of buckets; each bucket is a vec of (key, value) pairs.
    buckets: Vec<Vec<(i64, i64)>>,
    /// Number of key-value pairs stored.
    len: usize,
    /// Number of buckets (the table's "width").
    capacity: usize,
    /// Total insert calls (including updates).
    insert_ops: usize,
    /// Count of inserts where the target bucket was non-empty (i.e. a collision occurred).
    collision_count: usize,
    /// How many times the table has been resized.
    resize_count: usize,
}

impl SeparateChaining {
    /// Create a new SeparateChaining hash table.
    /// `initial_capacity` is rounded up to the next power of two (minimum 1).
    /// A capacity of 0 is treated as 1 to avoid division-by-zero.
    pub fn new(initial_capacity: usize) -> Self {
        let cap = if initial_capacity == 0 {
            1
        } else {
            next_power_of_two(initial_capacity)
        };
        Self {
            buckets: vec![Vec::new(); cap],
            len: 0,
            capacity: cap,
            insert_ops: 0,
            collision_count: 0,
            resize_count: 0,
        }
    }

    /// Insert a key-value pair.
    /// If the key already exists, update its value (no duplicate keys).
    /// Triggers a resize if load factor exceeds 0.75.
    pub fn insert(&mut self, key: i64, val: i64) {
        // Resize before inserting so that the new entry benefits from the
        // larger table (also avoids a tricky double-hash).
        if self.capacity > 0 && self.load_factor() > 0.75 {
            self.resize();
        }

        self.insert_ops += 1;
        let idx = hash_key(key, self.capacity);
        let bucket = &mut self.buckets[idx];

        // Check for existing key — update if found (no duplicates).
        for (k, v) in bucket.iter_mut() {
            if *k == key {
                *v = val;
                return;
            }
        }

        // New key: a non-empty bucket means a collision.
        if !bucket.is_empty() {
            self.collision_count += 1;
        }
        bucket.push((key, val));
        self.len += 1;
    }

    /// Look up a key and return its value if present.
    pub fn get(&self, key: i64) -> Option<i64> {
        if self.capacity == 0 {
            return None;
        }
        let idx = hash_key(key, self.capacity);
        self.buckets[idx]
            .iter()
            .find(|(k, _)| *k == key)
            .map(|(_, v)| *v)
    }

    /// Remove a key. Returns true if the key was present and removed.
    pub fn remove(&mut self, key: i64) -> bool {
        if self.capacity == 0 {
            return false;
        }
        let idx = hash_key(key, self.capacity);
        let bucket = &mut self.buckets[idx];
        if let Some(pos) = bucket.iter().position(|(k, _)| *k == key) {
            // swap_remove is O(1) and order within a bucket is unimportant.
            bucket.swap_remove(pos);
            self.len -= 1;
            true
        } else {
            false
        }
    }

    /// Return true if the key is present.
    pub fn contains_key(&self, key: i64) -> bool {
        self.get(key).is_some()
    }

    /// Number of key-value pairs stored.
    pub fn len(&self) -> usize {
        self.len
    }

    /// Whether the table is empty.
    pub fn is_empty(&self) -> bool {
        self.len == 0
    }

    /// Number of buckets.
    pub fn capacity(&self) -> usize {
        self.capacity
    }

    /// Current load factor = elements / buckets.
    pub fn load_factor(&self) -> f64 {
        if self.capacity == 0 {
            return 0.0;
        }
        self.len as f64 / self.capacity as f64
    }

    /// Total number of collision events recorded during inserts.
    pub fn collision_count(&self) -> usize {
        self.collision_count
    }

    /// Average chain length across all non-empty buckets.
    pub fn avg_chain_len(&self) -> f64 {
        let non_empty = self.buckets.iter().filter(|b| !b.is_empty()).count();
        if non_empty == 0 {
            return 0.0;
        }
        self.len as f64 / non_empty as f64
    }

    /// Length of the longest chain.
    pub fn max_chain_len(&self) -> usize {
        self.buckets.iter().map(|b| b.len()).max().unwrap_or(0)
    }

    /// How many times the table has been resized.
    pub fn resize_count(&self) -> usize {
        self.resize_count
    }

    /// Return a Stats snapshot.
    pub fn stats(&self) -> Stats {
        Stats {
            collisions: self.collision_count,
            avg_chain_len: self.avg_chain_len(),
            max_chain_len: self.max_chain_len(),
            load_factor: self.load_factor(),
            resize_count: self.resize_count,
        }
    }

    /// Resize to the next power of two >= 2 * current capacity and rehash.
    fn resize(&mut self) {
        let new_cap = next_power_of_two(self.capacity.saturating_mul(2).max(2));
        let old_buckets = std::mem::replace(&mut self.buckets, vec![Vec::new(); new_cap]);
        self.capacity = new_cap;
        self.len = 0; // will be re-incremented below

        for bucket in old_buckets {
            for (k, v) in bucket {
                // Insert without updating stats — we're just rehashing.
                let idx = hash_key(k, self.capacity);
                self.buckets[idx].push((k, v));
                self.len += 1;
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
        let mut sc = SeparateChaining::new(4);
        sc.insert(1, 100);
        sc.insert(2, 200);
        assert_eq!(sc.get(1), Some(100));
        assert_eq!(sc.get(2), Some(200));
        assert_eq!(sc.get(3), None);
        assert!(sc.remove(1));
        assert!(!sc.remove(1));
        assert_eq!(sc.get(1), None);
    }
}
