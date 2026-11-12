use crate::{add_mod, mul_mod, sub_mod};

pub fn negacyclic_mul(a: &[u64], b: &[u64], q: u64) -> Vec<u64> {
    assert_eq!(a.len(), b.len());
    let n = a.len();
    assert!(n > 0 && q > 1 && a.iter().chain(b).all(|&x| x < q));
    let mut out = vec![0u64; n];
    for (i, &ai) in a.iter().enumerate() {
        for (j, &bj) in b.iter().enumerate() {
            let p = mul_mod(ai, bj, q);
            let k = i + j;
            if k < n {
                out[k] = add_mod(out[k], p, q);
            } else {
                out[k - n] = sub_mod(out[k - n], p, q);
            }
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn negacyclic_sign_wrap_is_correct() {
        // (1 + 2X)(3 + 4X) = 3 + 10X + 8X^2; X^2 = -1.
        assert_eq!(negacyclic_mul(&[1, 2], &[3, 4], 97), vec![92, 10]);
    }
}
