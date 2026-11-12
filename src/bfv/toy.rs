//! Tiny-ring BFV correctness model.
//! IMPORTANT: deterministic XorShift sampling is for tests/demonstrations only.
//! This module is not cryptographically secure and must never protect real data.
use crate::poly::negacyclic_mul;

#[derive(Clone, Debug)]
pub struct ToyParams { pub n: usize, pub q: u64, pub t: u64 }
impl ToyParams {
    pub fn validate(&self) -> Result<(), &'static str> {
        if self.n == 0 || !self.n.is_power_of_two() || self.q < 3 || self.q % 2 == 0
            || self.t < 2 || self.t >= self.q || self.q % (2 * self.n as u64) != 1 {
            return Err("invalid toy BFV parameters: require power-of-two N, odd q, 2N | (q-1), and 2 <= t < q");
        }
        Ok(())
    }
    fn delta(&self) -> u64 { self.q / self.t }
}
#[derive(Clone, Debug)]
pub struct ToySecretKey { pub s: Vec<u64> }
#[derive(Clone, Debug)]
pub struct ToyPublicKey { pub b: Vec<u64>, pub a: Vec<u64> }
#[derive(Clone, Debug)]
pub struct ToyCiphertext { pub c0: Vec<u64>, pub c1: Vec<u64> }

/// Deterministic non-cryptographic generator, deliberately confined to this toy module.
struct DemoRng(u64);
impl DemoRng {
    fn next(&mut self) -> u64 {
        let mut x=self.0; x^=x<<13; x^=x>>7; x^=x<<17; self.0=x; x
    }
    fn ternary(&mut self,n:usize)->Vec<u64> {
        (0..n).map(|_| match self.next()%3 {0=>0,1=>1,_=>2}).collect()
    }
    fn uniform(&mut self,n:usize,q:u64)->Vec<u64> {
        (0..n).map(|_|self.next()%q).collect()
    }
}
fn add(a:&[u64],b:&[u64],q:u64)->Vec<u64> {
    a.iter().zip(b).map(|(&x,&y)|((x as u128+y as u128)%q as u128) as u64).collect()
}
fn neg(a:&[u64],q:u64)->Vec<u64> { a.iter().map(|&x|if x==0{0}else{q-x}).collect() }
fn mul(a:&[u64],b:&[u64],q:u64)->Vec<u64> { negacyclic_mul(a,b,q) }
fn lift_message(m:&[u64],p:&ToyParams)->Vec<u64> {
    m.iter().map(|&x|x*p.delta()%p.q).collect()
}
fn centered(x:u64,q:u64)->i128 { if x>q/2{x as i128-q as i128}else{x as i128} }

/// Generate a toy keypair. The seed is deterministic and NOT suitable for cryptography.
pub fn keygen(p:&ToyParams,seed:u64)->Result<(ToySecretKey,ToyPublicKey),&'static str> {
    p.validate()?;
    let mut rng=DemoRng(seed.max(1));
    let s=rng.ternary(p.n); let a=rng.uniform(p.n,p.q); let e=rng.ternary(p.n);
    let b=neg(&add(&mul(&a,&s,p.q),&e,p.q),p.q);
    Ok((ToySecretKey{s},ToyPublicKey{b,a}))
}

/// Encrypt a coefficient-encoded plaintext in Z_t[X]/(X^N+1).
pub fn encrypt(p:&ToyParams,pk:&ToyPublicKey,message:&[u64],seed:u64)->Result<ToyCiphertext,&'static str> {
    p.validate()?;
    if message.len()!=p.n || message.iter().any(|&x|x>=p.t) || pk.a.len()!=p.n || pk.b.len()!=p.n
        || pk.a.iter().chain(&pk.b).any(|&x|x>=p.q) { return Err("dimension or coefficient out of range"); }
    let mut rng=DemoRng(seed.max(1));
    let u=rng.ternary(p.n); let e1=rng.ternary(p.n); let e2=rng.ternary(p.n);
    let c0=add(&add(&mul(&pk.b,&u,p.q),&e1,p.q),&lift_message(message,p),p.q);
    let c1=add(&mul(&pk.a,&u,p.q),&e2,p.q);
    Ok(ToyCiphertext{c0,c1})
}

/// Decrypt by centered-lift phase computation and nearest-integer scale-and-round.
pub fn decrypt(p:&ToyParams,sk:&ToySecretKey,ct:&ToyCiphertext)->Result<Vec<u64>,&'static str> {
    p.validate()?;
    if sk.s.len()!=p.n || ct.c0.len()!=p.n || ct.c1.len()!=p.n
        || sk.s.iter().chain(&ct.c0).chain(&ct.c1).any(|&x|x>=p.q) {
        return Err("ciphertext/key dimension or coefficient out of range");
    }
    let phase=add(&ct.c0,&mul(&ct.c1,&sk.s,p.q),p.q);
    Ok(phase.into_iter().map(|x|{
        let numerator=centered(x,p.q)*p.t as i128;
        let rounded=if numerator>=0 {(numerator+p.q as i128/2)/p.q as i128}
                    else {-((-numerator+p.q as i128/2)/p.q as i128)};
        rounded.rem_euclid(p.t as i128) as u64
    }).collect())
}

/// Add ciphertexts componentwise.
pub fn add_ciphertexts(p:&ToyParams,lhs:&ToyCiphertext,rhs:&ToyCiphertext)->Result<ToyCiphertext,&'static str> {
    p.validate()?;
    if lhs.c0.len()!=p.n || lhs.c1.len()!=p.n || rhs.c0.len()!=p.n || rhs.c1.len()!=p.n
        || lhs.c0.iter().chain(&lhs.c1).chain(&rhs.c0).chain(&rhs.c1).any(|&x|x>=p.q) {
        return Err("ciphertext dimension or coefficient out of range");
    }
    Ok(ToyCiphertext{c0:add(&lhs.c0,&rhs.c0,p.q),c1:add(&lhs.c1,&rhs.c1,p.q)})
}

#[cfg(test)]
mod tests {
    use super::*;
    fn params()->ToyParams { ToyParams{n:8,q:65537,t:17} }
    #[test] fn toy_bfv_encrypt_decrypt_roundtrip() {
        let p=params(); let (sk,pk)=keygen(&p,0x12345678).unwrap();
        let m=vec![0,1,2,3,4,5,6,7];
        let ct=encrypt(&p,&pk,&m,0xabcdef).unwrap();
        assert_eq!(decrypt(&p,&sk,&ct).unwrap(),m);
    }
    #[test] fn toy_bfv_homomorphic_addition() {
        let p=params(); let (sk,pk)=keygen(&p,0x87654321).unwrap();
        let m1=vec![1,2,3,4,5,6,7,8]; let m2=vec![8,7,6,5,4,3,2,1];
        let c1=encrypt(&p,&pk,&m1,0x1111).unwrap(); let c2=encrypt(&p,&pk,&m2,0x2222).unwrap();
        let sum=add_ciphertexts(&p,&c1,&c2).unwrap();
        let expected:Vec<u64>=m1.iter().zip(m2).map(|(&a,b)|(a+b)%p.t).collect();
        assert_eq!(decrypt(&p,&sk,&sum).unwrap(),expected);
    }
    #[test] fn rejects_non_ntt_compatible_modulus() {
        let p=ToyParams{n:8,q:65539,t:17}; assert!(p.validate().is_err());
    }
    #[test] fn deterministic_multiseed_roundtrip_and_addition_sweep() {
        let p=params();
        for seed in 1..=64u64 {
            let (sk,pk)=keygen(&p,seed.wrapping_mul(0x9e3779b97f4a7c15)).unwrap();
            let mut rng=DemoRng(seed.wrapping_mul(0xd6e8feb86659fd93).max(1));
            let m1:Vec<u64>=(0..p.n).map(|_|rng.next()%p.t).collect();
            let m2:Vec<u64>=(0..p.n).map(|_|rng.next()%p.t).collect();
            let c1=encrypt(&p,&pk,&m1,seed.wrapping_add(0x1001)).unwrap();
            let c2=encrypt(&p,&pk,&m2,seed.wrapping_add(0x2002)).unwrap();
            assert_eq!(decrypt(&p,&sk,&c1).unwrap(),m1,"roundtrip seed {seed}");
            let sum=add_ciphertexts(&p,&c1,&c2).unwrap();
            let expected:Vec<u64>=m1.iter().zip(&m2).map(|(&a,&b)|(a+b)%p.t).collect();
            assert_eq!(decrypt(&p,&sk,&sum).unwrap(),expected,"addition seed {seed}");
        }
    }
}
