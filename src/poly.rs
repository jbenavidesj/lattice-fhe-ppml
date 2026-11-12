use crate::{add_mod,mul_mod,sub_mod};
pub fn negacyclic_mul(a:&[u64],b:&[u64],q:u64)->Vec<u64>{
 assert_eq!(a.len(),b.len());let n=a.len();assert!(n>0&&q>1&&a.iter().chain(b).all(|&x|x<q));let mut out=vec![0;n];
 for i in 0..n {for j in 0..n {let p=mul_mod(a[i],b[j],q);let k=i+j;if k<n{out[k]=add_mod(out[k],p,q);}else{out[k-n]=sub_mod(out[k-n],p,q);}}}out
}
#[cfg(test)] mod tests {use super::*;#[test]fn negacyclic_sign_wrap_is_correct(){assert_eq!(negacyclic_mul(&[1,2],&[3,4],97),vec![92,10]);}}
