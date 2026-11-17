/// FNV-1a hash function adapted for i64 keys.
///
/// FNV-1a (Fowler–Noll–Vo) is a fast, non-cryptographic hash function with
/// good avalanche properties for small keys. We interpret the i64 as 8 bytes
/// in little-endian order and feed each byte through the FNV-1a round:
///   hash = (hash XOR byte) * FNV_PRIME
///
/// This is deterministic across runs and architectures because we always use
/// little-endian byte order regardless of host endianness.
const FNV_OFFSET_BASIS: u64 = 14695981039346656037;
const FNV_PRIME: u64 = 1099511628211;

/// Hash an i64 key using FNV-1a and return the slot index for a table of
/// `capacity` slots. Returns 0 for capacity == 0 (caller must guard).
pub fn hash_key(key: i64, capacity: usize) -> usize {
    if capacity == 0 {
        return 0;
    }
    let bytes = key.to_le_bytes(); // deterministic LE byte order
    let mut h = FNV_OFFSET_BASIS;
    for byte in bytes {
        h ^= byte as u64;
        h = h.wrapping_mul(FNV_PRIME);
    }
    (h as usize) % capacity
}

/// Return the next prime number >= `n`.
/// Used by quadratic probing to maintain a prime-sized table.
/// We use a simple trial-division primality test; for the sizes we care about
/// (up to a few million) this is fast enough.
pub fn next_prime(n: usize) -> usize {
    if n < 2 {
        return 2;
    }
    let mut candidate = n;
    loop {
        if is_prime(candidate) {
            return candidate;
        }
        candidate += 1;
    }
}

fn is_prime(n: usize) -> bool {
    if n < 2 {
        return false;
    }
    if n == 2 {
        return true;
    }
    if n % 2 == 0 {
        return false;
    }
    let mut i = 3usize;
    while i * i <= n {
        if n % i == 0 {
            return false;
        }
        i += 2;
    }
    true
}

/// Return the smallest power of two >= n, with a minimum of 1.
pub fn next_power_of_two(n: usize) -> usize {
    if n <= 1 {
        return 1;
    }
    n.next_power_of_two()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_hash_deterministic() {
        assert_eq!(hash_key(42, 16), hash_key(42, 16));
        assert_eq!(hash_key(-1, 16), hash_key(-1, 16));
    }

    #[test]
    fn test_hash_in_range() {
        for cap in [1, 7, 16, 100, 1000] {
            for key in [-100i64, 0, 1, 42, 999] {
                let idx = hash_key(key, cap);
                assert!(idx < cap, "hash({key}, {cap}) = {idx} out of range");
            }
        }
    }

    #[test]
    fn test_hash_zero_capacity() {
        assert_eq!(hash_key(42, 0), 0);
    }

    #[test]
    fn test_next_prime() {
        assert_eq!(next_prime(0), 2);
        assert_eq!(next_prime(1), 2);
        assert_eq!(next_prime(2), 2);
        assert_eq!(next_prime(3), 3);
        assert_eq!(next_prime(4), 5);
        assert_eq!(next_prime(10), 11);
        assert_eq!(next_prime(14), 17);
    }

    #[test]
    fn test_next_power_of_two() {
        assert_eq!(next_power_of_two(0), 1);
        assert_eq!(next_power_of_two(1), 1);
        assert_eq!(next_power_of_two(2), 2);
        assert_eq!(next_power_of_two(3), 4);
        assert_eq!(next_power_of_two(16), 16);
        assert_eq!(next_power_of_two(17), 32);
    }
}
