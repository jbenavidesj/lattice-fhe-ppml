//! Residue-number-system polynomial representation over the four candidate q_i.
//! Operations are performed independently in each lane. CRT reconstruction,
//! basis extension, and BFV ciphertext semantics are intentionally out of scope.
use crate::{ntt::negacyclic_ntt_mul, MODULI, ROOTS};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RnsPoly {
    lanes: [Vec<u64>; 4],
}

impl RnsPoly {
    pub fn from_lanes(lanes: [Vec<u64>; 4]) -> Result<Self, &'static str> {
        let n = lanes[0].len();
        if n == 0 || lanes.iter().any(|lane| lane.len() != n) {
            return Err("all RNS lanes must have the same nonzero length");
        }
        for (i, lane) in lanes.iter().enumerate() {
            if lane.iter().any(|&x| x >= MODULI[i]) {
                return Err("coefficient is not canonical for its modulus");
            }
        }
        Ok(Self { lanes })
    }

    pub fn lanes(&self) -> &[Vec<u64>; 4] {
        &self.lanes
    }

    pub fn add(&self, rhs: &Self) -> Result<Self, &'static str> {
        if self.lanes[0].len() != rhs.lanes[0].len() {
            return Err("RNS polynomial dimensions differ");
        }
        let lanes = std::array::from_fn(|i| {
            self.lanes[i]
                .iter()
                .zip(&rhs.lanes[i])
                .map(|(&a, &b)| crate::add_mod(a, b, MODULI[i]))
                .collect()
        });
        Ok(Self { lanes })
    }

    /// Negacyclic multiplication by NTT in each residue field.
    /// Each lane length must be a power of two supported by its supplied root.
    pub fn negacyclic_mul(&self, rhs: &Self) -> Result<Self, &'static str> {
        if self.lanes[0].len() != rhs.lanes[0].len() {
            return Err("RNS polynomial dimensions differ");
        }
        let n = self.lanes[0].len();
        if !n.is_power_of_two() || n != 8192 {
            return Err("candidate roots in this crate are specified for N=8192");
        }
        let lanes = std::array::from_fn(|i| {
            negacyclic_ntt_mul(&self.lanes[i], &rhs.lanes[i], MODULI[i], ROOTS[i])
        });
        Ok(Self { lanes })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn four_lane_addition_is_canonical() {
        let a = RnsPoly::from_lanes(std::array::from_fn(|i| vec![MODULI[i]-1, 1])).unwrap();
        let b = RnsPoly::from_lanes(std::array::from_fn(|i| vec![2, MODULI[i]-1])).unwrap();
        let c = a.add(&b).unwrap();
        for (i, lane) in c.lanes().iter().enumerate() {
            assert_eq!(lane, &vec![1, 0]);
            assert!(lane.iter().all(|&x| x < MODULI[i]));
        }
    }

    #[test]
    fn rejects_mismatched_lanes() {
        let bad = [vec![0, 1], vec![0], vec![0, 1], vec![0, 1]];
        assert!(RnsPoly::from_lanes(bad).is_err());
    }
}
