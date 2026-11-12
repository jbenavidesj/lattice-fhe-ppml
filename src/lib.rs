#![forbid(unsafe_code)]
pub mod asymred;
pub mod bfv;
pub mod keygen;
pub mod ntt;
pub mod poly;
pub mod rns;
pub use asymred::{asymred, AsymRedError};
pub const MODULI: [u64; 4] = [36028797002170369,36028796951838721,18014398508400641,18014398507892737];
pub const ROOTS: [u64; 4] = [22505317672356688,29410112198941026,9354911369072846,12617745759101472];
pub fn add_mod(a:u64,b:u64,q:u64)->u64 { assert!(q>1&&a<q&&b<q); ((a as u128+b as u128)%q as u128) as u64 }
pub fn sub_mod(a:u64,b:u64,q:u64)->u64 { assert!(q>1&&a<q&&b<q); if a>=b {a-b} else {q-(b-a)} }
pub fn mul_mod(a:u64,b:u64,q:u64)->u64 { assert!(q>1); ((a as u128*b as u128)%q as u128) as u64 }
pub fn pow_mod(mut a:u64,mut e:u64,q:u64)->u64 { assert!(q>1); let mut r=1u64; a%=q; while e>0 {if e&1==1 {r=mul_mod(r,a,q);} a=mul_mod(a,a,q); e>>=1;} r }
#[cfg(test)]
mod tests {
 use super::*;
 #[test] fn modular_arithmetic_matches_wide_reference() {
  for &q in &MODULI {let s=[0,1,2,q/2,q-2,q-1]; for &a in &s {for &b in &s {
   assert_eq!(add_mod(a,b,q) as u128,(a as u128+b as u128)%q as u128);
   assert_eq!(sub_mod(a,b,q),((a as u128+q as u128-b as u128)%q as u128) as u64);
   assert_eq!(mul_mod(a,b,q) as u128,(a as u128*b as u128)%q as u128);
  }}}
 }
}
