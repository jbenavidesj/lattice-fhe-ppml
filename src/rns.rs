//! Residue-number-system polynomial representation over the four candidate q_i.
//! CRT reconstruction is exact. Basis extension uses the centered CRT representative,
//! a semantic distinction required by signed polynomial arithmetic.
use num_bigint::{BigInt, BigUint, Sign};
use crate::{ntt::negacyclic_ntt_mul, pow_mod, sub_mod, MODULI, ROOTS};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RnsPoly {
    lanes: [Vec<u64>; 4],
}

/// One gadget evaluation-key pair for relinearizing the quadratic ciphertext component.
/// Required relation: b_j + a_j*s = B^j*s^2 + e_j (mod Q).
/// This stores a pair; secure key generation is deliberately separate.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RnsEvalKeyDigit {
    pub b: RnsPoly,
    pub a: RnsPoly,
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
                lane.push(residue.to_u64_digits().1.first().copied().unwrap_or(0));
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

    /// Number of unsigned gadget digits needed to represent every centered
    /// coefficient modulo Q. The returned L satisfies B^L >= Q.
    pub fn gadget_levels(base: u64) -> Result<usize, &'static str> {
        if base < 2 { return Err("gadget base must be >= 2"); }
        let q = MODULI.iter().fold(BigUint::from(1u8), |p, &q| p * BigUint::from(q));
        let b = BigUint::from(base);
        let mut capacity = BigUint::from(1u8);
        let mut levels = 0usize;
        while capacity < q {
            capacity *= &b;
            levels += 1;
        }
        Ok(levels)
    }

    /// Decompose centered coefficients into signed, unsigned-magnitude base-B digits.
    /// For each coefficient x, this returns d_j in {-(B-1),...,B-1} with
    /// x = sum_j d_j B^j exactly over the integers. The result is encoded in RNS.
    pub fn gadget_decompose_centered(&self, base: u64) -> Result<Vec<Self>, &'static str> {
        if base < 2 { return Err("gadget base must be >= 2"); }
        let levels = Self::gadget_levels(base)?;
        let b = BigUint::from(base);
        let mut digit_lanes: Vec<[Vec<u64>; 4]> = (0..levels).map(|_| {
            std::array::from_fn(|_| Vec::with_capacity(self.lanes[0].len()))
        }).collect();
        for index in 0..self.lanes[0].len() {
            let x = self.crt_reconstruct_centered_coefficient(index)?;
            let negative = x.sign() == Sign::Minus;
            let magnitude = if negative { (-x).to_biguint().ok_or("absolute coefficient conversion failed")? }
                            else { x.to_biguint().ok_or("coefficient conversion failed")? };
            let mut remaining = magnitude;
            for digit_lane in digit_lanes.iter_mut() {
                let digit = &remaining % &b;
                remaining /= &b;
                let digit_signed = BigInt::from_biguint(Sign::Plus, digit);
                let digit_signed = if negative { -digit_signed } else { digit_signed };
                for (lane, &q) in digit_lane.iter_mut().zip(MODULI.iter()) {
                    let modulus = BigInt::from(q);
                    let residue = ((&digit_signed % &modulus) + &modulus) % &modulus;
                    lane.push(low_u64(&residue.to_biguint().ok_or("negative digit residue")?));
                }
            }
            if remaining != BigUint::from(0u8) {
                return Err("gadget digit capacity insufficient");
            }
        }
        digit_lanes.into_iter().map(Self::from_lanes).collect()
    }

    /// Apply exact-reference RNS gadget key switching to a three-component BFV
    /// ciphertext. eval_key[j] must satisfy b_j + a_j*s = B^j*s^2 + e_j (mod Q).
    /// Returns two components. This does not generate keys or claim constant-time behavior.
    pub fn bfv_relinearize(
        components: &[Self; 3],
        eval_key: &[RnsEvalKeyDigit],
        base: u64,
    ) -> Result<[Self; 2], &'static str> {
        let n = components[0].lanes[0].len();
        if components.iter().any(|p| p.lanes[0].len() != n) {
            return Err("ciphertext component dimensions differ");
        }
        let levels = Self::gadget_levels(base)?;
        if eval_key.len() != levels {
            return Err("evaluation key length does not match gadget decomposition");
        }
        if eval_key.iter().any(|k| k.a.lanes[0].len() != n || k.b.lanes[0].len() != n) {
            return Err("evaluation key polynomial dimensions differ");
        }
        let digits = components[2].gadget_decompose_centered(base)?;
        let mut out0 = components[0].clone();
        let mut out1 = components[1].clone();
        for (digit, key) in digits.iter().zip(eval_key) {
            out0 = out0.add(&digit.negacyclic_mul(&key.b)?)?;
            out1 = out1.add(&digit.negacyclic_mul(&key.a)?)?;
        }
        Ok([out0, out1])
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

    fn encode_signed_constant(value: &BigInt, n: usize) -> RnsPoly {
        let lanes = std::array::from_fn(|i| {
            let q = BigInt::from(MODULI[i]);
            let residue = ((value % &q) + &q) % &q;
            let mut lane = vec![0u64; n];
            lane[0] = low_u64(&residue.to_biguint().unwrap());
            lane
        });
        RnsPoly::from_lanes(lanes).unwrap()
    }

    fn q_product_bigint() -> BigInt {
        BigInt::from_biguint(Sign::Plus,
            MODULI.iter().fold(BigUint::from(1u8), |p, &q| p * BigUint::from(q)))
    }
    
    fn encode_signed_coefficients(values: &[BigInt]) -> RnsPoly {
        let lanes = std::array::from_fn(|i| {
            let q = BigInt::from(MODULI[i]);
            values.iter().map(|value| {
                let residue = ((value % &q) + &q) % &q;
                low_u64(&residue.to_biguint().unwrap())
            }).collect()
        });
        RnsPoly::from_lanes(lanes).unwrap()
    }


    #[test]
    fn bfv_scale_and_round_matches_exact_signed_reference() {
        let q = q_product_bigint();
        let values: [BigInt; 7] = [
            BigInt::from(0),
            BigInt::from(1),
            BigInt::from(-1),
            &q / BigInt::from(4u8),
            -(&q / BigInt::from(4u8)),
            (&q / BigInt::from(2u8)) - BigInt::from(1u8),
            -(&q / BigInt::from(2u8)),
        ];
        for value in values {
            let input = encode_signed_constant(&value, 1);
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
        let c0 = encode_signed_constant(&quarter_q, n);
        let zero = encode_signed_constant(&BigInt::from(0), n);
        let two = encode_signed_constant(&BigInt::from(2), n);
        let result = RnsPoly::bfv_tensor_multiply(&c0, &zero, &two, &zero, 17).unwrap();
        // U0[0] = 2*floor(Q/4), so round(17*U0/Q) = 8 (strictly below 8.5).
        for lane in result[0].lanes() {
            assert_eq!(lane[0], 8);
            assert!(lane[1..].iter().all(|&x| x == 0));
        }
        for component in [&result[1], &result[2]] {
            for lane in component.lanes() {
                assert!(lane.iter().all(|&x| x == 0));
            }
        }
    }

    #[test]
    fn gadget_decomposition_reconstructs_signed_coefficients() {
        let q = q_product_bigint();
        let values: [BigInt; 5] = [
            BigInt::from(0),
            BigInt::from(123456789i64),
            BigInt::from(-987654321i64),
            &q / BigInt::from(3u8),
            -(&q / BigInt::from(3u8)),
        ];
        for value in values {
            let input = encode_signed_constant(&value, 1);
            let digits = input.gadget_decompose_centered(1u64 << 16).unwrap();
            let mut reconstructed = BigInt::from(0);
            let mut factor = BigInt::from(1);
            for digit in digits {
                reconstructed += digit.crt_reconstruct_centered_coefficient(0).unwrap() * &factor;
                factor *= 1u64 << 16;
            }
            assert_eq!(reconstructed, value);
        }
    }

    #[test]
    fn rns_relinearization_applies_gadget_key_relation() {
        let n = 8192;
        let base = 1u64 << 16;
        let levels = RnsPoly::gadget_levels(base).unwrap();
        let q = q_product_bigint();
        let c0 = encode_signed_constant(&BigInt::from(5), n);
        let c1 = encode_signed_constant(&BigInt::from(7), n);
        let c2 = encode_signed_constant(&(&q / BigInt::from(5u8)), n);
        let zero = encode_signed_constant(&BigInt::from(0), n);
        // Test secret s=1 and error-free evaluation keys: b_j=0, a_j=B^j.
        let mut eval_key = Vec::with_capacity(levels);
        let mut factor = BigInt::from(1);
        for _ in 0..levels {
            eval_key.push(RnsEvalKeyDigit {
                b: zero.clone(),
                a: encode_signed_constant(&factor, n),
            });
            factor *= base;
        }
        let output = RnsPoly::bfv_relinearize(&[c0.clone(), c1.clone(), c2.clone()], &eval_key, base).unwrap();
        let expected = c1.add(&c2).unwrap();
        assert_eq!(output[0], c0);
        assert_eq!(output[1], expected);
    }

    #[test]
    fn rns_relinearization_preserves_phase_for_nontrivial_secret_polynomial() {
        let n = 8192;
        let base = 1u64 << 16;
        let levels = RnsPoly::gadget_levels(base).unwrap();
        let zero = encode_signed_coefficients(&vec![BigInt::from(0); n]);
        let secret_values: Vec<BigInt> = (0..n).map(|i| match i {
            0 | 3 | 17 => BigInt::from(1),
            5 => BigInt::from(-1),
            _ => BigInt::from(0),
        }).collect();
        let secret = encode_signed_coefficients(&secret_values);
        let secret_squared = secret.negacyclic_mul(&secret).unwrap();
        let c0_values: Vec<BigInt> = (0..n).map(|i| if i==0 {BigInt::from(11)} else {BigInt::from(0)}).collect();
        let c1_values: Vec<BigInt> = (0..n).map(|i| if i==2 {BigInt::from(-7)} else {BigInt::from(0)}).collect();
        let c2_values: Vec<BigInt> = (0..n).map(|i| match i {
            0 => BigInt::from(1234567),
            9 => BigInt::from(-7654321),
            31 => BigInt::from(42),
            _ => BigInt::from(0),
        }).collect();
        let c0 = encode_signed_coefficients(&c0_values);
        let c1 = encode_signed_coefficients(&c1_values);
        let c2 = encode_signed_coefficients(&c2_values);
        let digits = c2.gadget_decompose_centered(base).unwrap();

        // Algebraic test fixture: a_j=0, e_j=0, b_j=B^j*s^2.
        // This verifies phase preservation for a nontrivial polynomial secret,
        // without pretending to implement secure evaluation-key generation.
        // Construct B^j independently in each lane; the q_i are distinct.
        let mut eval_key = Vec::with_capacity(levels);
        let mut factors = [1u64; 4];
        for _ in 0..levels {
            let b_lanes = std::array::from_fn(|i| {
                secret_squared.lanes[i].iter().map(|&x| crate::mul_mod(x, factors[i], MODULI[i])).collect()
            });
            eval_key.push(RnsEvalKeyDigit { b: RnsPoly::from_lanes(b_lanes).unwrap(), a: zero.clone() });
            for i in 0..4 { factors[i] = crate::mul_mod(factors[i], base % MODULI[i], MODULI[i]); }
        }
        let output = RnsPoly::bfv_relinearize(&[c0.clone(), c1.clone(), c2.clone()], &eval_key, base).unwrap();
        let before = c0.add(&c1.negacyclic_mul(&secret).unwrap()).unwrap()
            .add(&c2.negacyclic_mul(&secret_squared).unwrap()).unwrap();
        let after = output[0].add(&output[1].negacyclic_mul(&secret).unwrap()).unwrap();
        assert_eq!(after, before);
        assert_eq!(digits.len(), levels);
    }


    // Independent sparse BigInt oracle for RNS tensor multiplication. It computes
    // negacyclic products over Z, reduces each coefficient to its centered R_Q
    // representative, then applies exact t/Q nearest-integer scaling.
    type SparsePolynomial = [(usize, i64)];
    type SparseProductTerm<'a> = (&'a SparsePolynomial, &'a SparsePolynomial);

    fn reference_tensor_component(
        terms: &[SparseProductTerm<'_>],
        n: usize,
        q: &BigInt,
        t: u64,
    ) -> Vec<BigInt> {
        let mut accum = vec![BigInt::from(0); n];
        for (lhs, rhs) in terms {
            for &(i, a) in *lhs {
                for &(j, b) in *rhs {
                    let product = BigInt::from(a) * BigInt::from(b);
                    let k = i + j;
                    if k < n { accum[k] += product; }
                    else { accum[k - n] -= product; }
                }
            }
        }
        accum.into_iter().map(|value| {
            let residue = ((&value % q) + q) % q;
            let centered = if (&residue << 1usize) > *q { residue - q } else { residue };
            let numerator = centered * t;
            let negative = numerator.sign() == Sign::Minus;
            let magnitude = if negative { -numerator } else { numerator };
            let mut rounded = &magnitude / q;
            if ((&magnitude % q) << 1usize) >= *q { rounded += 1u8; }
            if negative { -rounded } else { rounded }
        }).collect()
    }

    fn encode_reference_rns(values: &[BigInt]) -> RnsPoly {
        encode_signed_coefficients(values)
    }

    #[test]
    fn bfv_rns_tensor_multiplication_matches_independent_bigint_oracle() {
        let n = 8192;
        let q = q_product_bigint();
        let t = 65537u64;
        let c0_sparse = [(0usize, 3i64), (7, -2), (8190, 1)];
        let c1_sparse = [(2usize, -1i64), (19, 4)];
        let d0_sparse = [(1usize, 2i64), (8, 3), (8191, -2)];
        let d1_sparse = [(0usize, -3i64), (11, 1), (20, 2)];

        let expand = |sparse: &[(usize, i64)]| {
            let mut values = vec![BigInt::from(0); n];
            for &(i, value) in sparse { values[i] = BigInt::from(value); }
            encode_reference_rns(&values)
        };
        let c0 = expand(&c0_sparse);
        let c1 = expand(&c1_sparse);
        let d0 = expand(&d0_sparse);
        let d1 = expand(&d1_sparse);

        let got = RnsPoly::bfv_tensor_multiply(&c0, &c1, &d0, &d1, t).unwrap();
        let expected0 = reference_tensor_component(&[(&c0_sparse, &d0_sparse)], n, &q, t);
        let expected1 = reference_tensor_component(
            &[(&c0_sparse, &d1_sparse), (&c1_sparse, &d0_sparse)], n, &q, t
        );
        let expected2 = reference_tensor_component(&[(&c1_sparse, &d1_sparse)], n, &q, t);

        assert_eq!(got[0], encode_reference_rns(&expected0));
        assert_eq!(got[1], encode_reference_rns(&expected1));
        assert_eq!(got[2], encode_reference_rns(&expected2));
    }


    // Deterministic, sparse test fixture only: this is deliberately NOT a
    // uniform sampler and must not be used for cryptographic key generation.
    #[test]
    fn rns_relinearization_with_nonzero_test_errors_preserves_exact_phase_delta() {
        let n = 8192;
        let base = 1u64 << 16;
        let levels = RnsPoly::gadget_levels(base).unwrap();

        let mut secret_values = vec![BigInt::from(0); n];
        secret_values[0] = BigInt::from(1);
        secret_values[3] = BigInt::from(-1);
        secret_values[17] = BigInt::from(1);
        let secret = encode_signed_coefficients(&secret_values);
        let secret_squared = secret.negacyclic_mul(&secret).unwrap();

        let mut c0_values = vec![BigInt::from(0); n];
        c0_values[0] = BigInt::from(11);
        c0_values[4] = BigInt::from(-3);
        let mut c1_values = vec![BigInt::from(0); n];
        c1_values[2] = BigInt::from(-7);
        c1_values[13] = BigInt::from(2);
        let mut c2_values = vec![BigInt::from(0); n];
        c2_values[0] = BigInt::from(1234567);
        c2_values[9] = BigInt::from(-7654321);
        c2_values[31] = BigInt::from(42);
        let c0 = encode_signed_coefficients(&c0_values);
        let c1 = encode_signed_coefficients(&c1_values);
        let c2 = encode_signed_coefficients(&c2_values);
        let digits = c2.gadget_decompose_centered(base).unwrap();
        assert_eq!(digits.len(), levels);

        let negate = |poly: &RnsPoly| {
            let lanes = std::array::from_fn(|i| {
                poly.lanes[i].iter().map(|&x| if x == 0 { 0 } else { MODULI[i] - x }).collect()
            });
            RnsPoly::from_lanes(lanes).unwrap()
        };

        let mut eval_key = Vec::with_capacity(levels);
        let mut errors = Vec::with_capacity(levels);
        let mut gadget_factors = [1u64; 4];
        for j in 0..levels {
            // Fixed sparse signed coefficients make this fixture reproducible.
            // They do not model the distribution of a production RLWE key.
            let mut a_values = vec![BigInt::from(0); n];
            a_values[(37 * j + 1) % n] = BigInt::from((j as i64 % 5) + 1);
            a_values[(53 * j + 7) % n] = BigInt::from(-2);
            a_values[(71 * j + 19) % n] = BigInt::from(1);
            let a = encode_signed_coefficients(&a_values);

            let mut e_values = vec![BigInt::from(0); n];
            e_values[(29 * j + 2) % n] = BigInt::from(1);
            e_values[(43 * j + 5) % n] = BigInt::from(-1);
            e_values[(61 * j + 11) % n] = BigInt::from(1);
            let e = encode_signed_coefficients(&e_values);
            assert!(e_values.iter().any(|x| x != &BigInt::from(0)));

            // b_j = B^j*s^2 - a_j*s + e_j (mod Q), hence
            // b_j + a_j*s = B^j*s^2 + e_j.
            let target_lanes = std::array::from_fn(|i| {
                secret_squared.lanes[i].iter()
                    .map(|&x| crate::mul_mod(x, gadget_factors[i], MODULI[i]))
                    .collect()
            });
            let target = RnsPoly::from_lanes(target_lanes).unwrap();
            let a_times_s = a.negacyclic_mul(&secret).unwrap();
            let b = target.add(&negate(&a_times_s)).unwrap().add(&e).unwrap();
            eval_key.push(RnsEvalKeyDigit { a, b });
            errors.push(e);
            for i in 0..4 {
                gadget_factors[i] = crate::mul_mod(
                    gadget_factors[i], base % MODULI[i], MODULI[i]
                );
            }
        }

        let output = RnsPoly::bfv_relinearize(
            &[c0.clone(), c1.clone(), c2.clone()],
            &eval_key,
            base,
        ).unwrap();

        let before = c0.add(&c1.negacyclic_mul(&secret).unwrap()).unwrap()
            .add(&c2.negacyclic_mul(&secret_squared).unwrap()).unwrap();
        let after = output[0].add(&output[1].negacyclic_mul(&secret).unwrap()).unwrap();

        // The phase delta must be exactly sum_j d_j*e_j in R_Q.
        let mut expected_delta = encode_signed_coefficients(&vec![BigInt::from(0); n]);
        for (digit, error) in digits.iter().zip(&errors) {
            expected_delta = expected_delta.add(&digit.negacyclic_mul(error).unwrap()).unwrap();
        }
        assert_ne!(expected_delta, encode_signed_coefficients(&vec![BigInt::from(0); n]));
        assert_eq!(after, before.add(&expected_delta).unwrap());
    }

    #[test]
    fn rejects_mismatched_lanes() {
        let bad = [vec![0, 1], vec![0], vec![0, 1], vec![0, 1]];
        assert!(RnsPoly::from_lanes(bad).is_err());
    }
}
