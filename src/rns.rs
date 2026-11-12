//! Residue-number-system polynomial representation over the four candidate q_i.
//! Arithmetic is lane-wise; exact CRT reconstruction is provided for coefficients.
//! This is still an arithmetic layer, not a BFV ciphertext implementation.
use num_bigint::BigUint;
use crate::{ntt::negacyclic_ntt_mul, pow_mod, sub_mod, mul_mod, MODULI, ROOTS};

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
            self.lanes[i].iter().zip(&rhs.lanes[i])
                .map(|(&a, &b)| crate::add_mod(a, b, MODULI[i])).collect()
        });
        Ok(Self { lanes })
    }

    /// Reconstruct one coefficient in the canonical interval [0,Q), exactly.
    pub fn crt_reconstruct_coefficient(&self, index: usize) -> Result<BigUint, &'static str> {
        if index >= self.lanes[0].len() {
            return Err("coefficient index out of range");
        }
        let mut x = BigUint::from(0u8);
        let mut product = BigUint::from(1u8);
        for (i, &q) in MODULI.iter().enumerate() {
            let x_mod = low_u64(&(&x % q));
            let product_mod = low_u64(&(&product % q));
            let inverse = pow_mod(product_mod, q - 2, q);
            let correction = crate::mul_mod(sub_mod(self.lanes[i][index], x_mod, q), inverse, q);
            x += &product * BigUint::from(correction);
            product *= BigUint::from(q);
        }
        Ok(x)
    }

    /// Negacyclic multiplication by NTT in each residue field.
    /// Candidate roots are fixed for N=8192.
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

fn low_u64(x: &BigUint) -> u64 {
    x.to_u64_digits().first().copied().unwrap_or(0)
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
    fn crt_reconstructs_values_beyond_u128() {
        let value = (BigUint::from(1u8) << 200usize) + BigUint::from(987654321u64);
        let lanes = std::array::from_fn(|i| {
            let q = MODULI[i];
            vec![low_u64(&(&value % q))]
        });
        let rns = RnsPoly::from_lanes(lanes).unwrap();
        assert_eq!(rns.crt_reconstruct_coefficient(0).unwrap(), value);
    }

    #[test]
    fn rejects_mismatched_lanes() {
        let bad = [vec![0, 1], vec![0], vec![0, 1], vec![0, 1]];
        assert!(RnsPoly::from_lanes(bad).is_err());
    }
}
