//! Residue-number-system polynomial representation over the four candidate q_i.
//! CRT reconstruction is exact. Basis extension uses the centered CRT representative,
//! a semantic distinction required by signed polynomial arithmetic.
use num_bigint::{BigInt, BigUint, Sign};
use crate::{ntt::negacyclic_ntt_mul, pow_mod, sub_mod, MODULI, ROOTS};

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

    pub fn lanes(&self) -> &[Vec<u64>; 4] { &self.lanes }

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
    /// Assumes the configured q_i are pairwise coprime primes.
    pub fn crt_reconstruct_coefficient(&self, index: usize) -> Result<BigUint, &'static str> {
        if index >= self.lanes[0].len() { return Err("coefficient index out of range"); }
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

    /// Return the signed centered representative in (-Q/2,Q/2].
    pub fn crt_reconstruct_centered_coefficient(&self, index: usize) -> Result<BigInt, &'static str> {
        let x = self.crt_reconstruct_coefficient(index)?;
        let q_product = MODULI.iter().fold(BigUint::from(1u8), |p, &q| p * BigUint::from(q));
        if (&x << 1usize) > q_product {
            Ok(BigInt::from_biguint(Sign::Plus, x) - BigInt::from_biguint(Sign::Plus, q_product))
        } else {
            Ok(BigInt::from_biguint(Sign::Plus, x))
        }
    }

    /// Exact BFV coefficientwise scale-and-round reference map.
    ///
    /// For each coefficient, reconstruct its centered representative x in (-Q/2,Q/2],
    /// compute round(t*x/Q) with ties away from zero, then encode the result in every
    /// RNS lane. This BigInt implementation is a correctness oracle, not a fast RNS
    /// implementation and not a complete ciphertext multiplication by itself.
    pub fn bfv_scale_and_round(&self, plaintext_modulus: u64) -> Result<Self, &'static str> {
        if plaintext_modulus < 2 {
            return Err("plaintext modulus must be >= 2");
        }
        let q_product = MODULI.iter().fold(BigUint::from(1u8), |p, &q| p * BigUint::from(q));
        let denominator = BigInt::from_biguint(Sign::Plus, q_product);
        let mut lanes: [Vec<u64>; 4] = std::array::from_fn(|_| Vec::with_capacity(self.lanes[0].len()));
        for index in 0..self.lanes[0].len() {
            let x = self.crt_reconstruct_centered_coefficient(index)?;
            let numerator = x * BigInt::from(plaintext_modulus);
            let negative = numerator.sign() == Sign::Minus;
            let magnitude = if negative { -numerator } else { numerator };
            let mut quotient = &magnitude / &denominator;
            let remainder = &magnitude % &denominator;
            if (&remainder << 1usize) >= denominator {
                quotient += 1u8;
            }
            let rounded = if negative { -quotient } else { quotient };
            for (lane, &q) in lanes.iter_mut().zip(MODULI.iter()) {
                let modulus = BigInt::from(q);
                let residue = ((&rounded % &modulus) + &modulus) % &modulus;
                lane.push(residue.to_u64_digits().first().copied().unwrap_or(0));
            }
        }
        Ok(Self { lanes })
    }

    /// Exact centered basis extension: reconstruct each coefficient as its signed
    /// representative modulo Q, then reduce that integer into every target modulus.
    /// This is exact extension, not an approximate fast base-conversion algorithm.
    pub fn basis_extend_centered(&self, target_moduli: &[u64]) -> Result<Vec<Vec<u64>>, &'static str> {
        if target_moduli.is_empty() || target_moduli.iter().any(|&q| q < 2) {
            return Err("target basis must contain moduli >= 2");
        }
        let mut output = vec![Vec::with_capacity(self.lanes[0].len()); target_moduli.len()];
        for index in 0..self.lanes[0].len() {
            let signed = self.crt_reconstruct_centered_coefficient(index)?;
            for (lane, &q) in output.iter_mut().zip(target_moduli) {
                let residue = (&signed % BigInt::from(q) + BigInt::from(q)) % BigInt::from(q);
                lane.push(low_u64(&residue.to_biguint().ok_or("negative residue after normalization")?));
            }
        }
        Ok(output)
    }

    /// Exact-reference BFV tensor multiplication over the configured four-lane RNS basis.
    ///
    /// Tensor products are first formed in R_Q via lane-wise NTT multiplication. Each
    /// tensor component is then reconstructed as a centered integer coefficient and
    /// mapped by t/Q scale-and-round. Returns the three components before relinearization.
    pub fn bfv_tensor_multiply(
        c0: &Self, c1: &Self, d0: &Self, d1: &Self, plaintext_modulus: u64
    ) -> Result<[Self; 3], &'static str> {
        let n = c0.lanes[0].len();
        if [c1, d0, d1].iter().any(|p| p.lanes[0].len() != n) {
            return Err("BFV ciphertext polynomial dimensions differ");
        }
        let u0 = c0.negacyclic_mul(d0)?;
        let u1 = c0.negacyclic_mul(d1)?.add(&c1.negacyclic_mul(d0)?)?;
        let u2 = c1.negacyclic_mul(d1)?;
        Ok([
            u0.bfv_scale_and_round(plaintext_modulus)?,
            u1.bfv_scale_and_round(plaintext_modulus)?,
            u2.bfv_scale_and_round(plaintext_modulus)?,
        ])
    }

    /// Negacyclic multiplication by NTT in each residue field. Candidate roots are fixed for N=8192.
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

fn low_u64(x: &BigUint) -> u64 { x.to_u64_digits().first().copied().unwrap_or(0) }

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
    fn centered_crt_and_basis_extension_preserve_signed_value() {
        let signed = BigInt::from(-1234567890123456789i128);
        let lanes = std::array::from_fn(|i| {
            let q = MODULI[i];
            let r = (&signed % BigInt::from(q) + BigInt::from(q)) % BigInt::from(q);
            vec![low_u64(&r.to_biguint().unwrap())]
        });
        let rns = RnsPoly::from_lanes(lanes).unwrap();
        assert_eq!(rns.crt_reconstruct_centered_coefficient(0).unwrap(), signed);
        let targets = [65537u64, 1000000007u64];
        let extended = rns.basis_extend_centered(&targets).unwrap();
        for (i, &q) in targets.iter().enumerate() {
            let expected = (&signed % BigInt::from(q) + BigInt::from(q)) % BigInt::from(q);
            assert_eq!(extended[i][0], low_u64(&expected.to_biguint().unwrap()));
        }
    }

    fn encode_signed(value: &BigInt, n: usize) -> RnsPoly {
        let lanes = std::array::from_fn(|i| {
            let q = BigInt::from(MODULI[i]);
            let residue = ((value % &q) + &q) % &q;
            vec![low_u64(&residue.to_biguint().unwrap()); n]
        });
        RnsPoly::from_lanes(lanes).unwrap()
    }

    fn q_product_bigint() -> BigInt {
        BigInt::from_biguint(Sign::Plus,
            MODULI.iter().fold(BigUint::from(1u8), |p, &q| p * BigUint::from(q)))
    }

    #[test]
    fn bfv_scale_and_round_matches_exact_signed_reference() {
        let q = q_product_bigint();
        let values = [
            BigInt::from(0),
            BigInt::from(1),
            BigInt::from(-1),
            &q / 4,
            -(&q / 4),
            (&q / 2) - 1,
            -(&q / 2),
        ];
        for value in values {
            let input = encode_signed(&value, 1);
            let output = input.bfv_scale_and_round(65537).unwrap();
            let numerator = &value * 65537u64;
            let negative = numerator.sign() == Sign::Minus;
            let magnitude = if negative { -numerator } else { numerator };
            let denominator = q.clone();
            let mut expected = &magnitude / &denominator;
            if ((&magnitude % &denominator) << 1usize) >= denominator { expected += 1u8; }
            if negative { expected = -expected; }
            for (i, lane) in output.lanes().iter().enumerate() {
                let modulus = BigInt::from(MODULI[i]);
                let residue = ((&expected % &modulus) + &modulus) % &modulus;
                assert_eq!(lane[0], low_u64(&residue.to_biguint().unwrap()));
            }
        }
    }

    #[test]
    fn bfv_tensor_multiply_scales_sparse_product() {
        let n = 8192;
        let quarter_q = q_product_bigint() / 4;
        let c0 = encode_signed(&quarter_q, n);
        let zero = encode_signed(&BigInt::from(0), n);
        let two = encode_signed(&BigInt::from(2), n);
        let result = RnsPoly::bfv_tensor_multiply(&c0, &zero, &two, &zero, 17).unwrap();
        // U0[0] = 2*floor(Q/4), so round(17*U0/Q) = 9.
        for lane in result[0].lanes() {
            assert_eq!(lane[0], 9);
            assert!(lane[1..].iter().all(|&x| x == 0));
        }
        for component in [&result[1], &result[2]] {
            for lane in component.lanes() {
                assert!(lane.iter().all(|&x| x == 0));
            }
        }
    }

    #[test]
    fn rejects_mismatched_lanes() {
        let bad = [vec![0, 1], vec![0], vec![0, 1], vec![0, 1]];
        assert!(RnsPoly::from_lanes(bad).is_err());
    }
}
