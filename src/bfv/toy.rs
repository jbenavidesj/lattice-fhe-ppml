//! Tiny-ring BFV correctness model.
//! IMPORTANT: deterministic XorShift sampling is for tests/demonstrations only.
//! This module is not cryptographically secure and must never protect real data.
use crate::poly::negacyclic_mul;

#[derive(Clone, Debug)]
pub struct ToyParams { pub n: usize, pub q: u64, pub t: u64 }
impl ToyParams {
    pub fn validate(&self) -> Result<(), &'static str> {
        if self.n == 0 || !self.n.is_power_of_two() || self.q < 3 || self.q.is_multiple_of(2)
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
#[derive(Clone, Debug)]
pub struct ToyCiphertext3 { pub c0: Vec<u64>, pub c1: Vec<u64>, pub c2: Vec<u64> }
#[derive(Clone, Debug)]
pub struct ToyRelinKey { pub base: u64, pub b: Vec<Vec<u64>>, pub a: Vec<Vec<u64>> }

/// Deterministic non-cryptographic generator, deliberately confined to this toy module.
struct DemoRng(u64);
impl DemoRng {
    fn next(&mut self) -> u64 {
        let mut x=self.0; x^=x<<13; x^=x>>7; x^=x<<17; self.0=x; x
    }
    fn ternary(&mut self,n:usize,q:u64)->Vec<u64> {
        (0..n).map(|_| match self.next()%3 {0=>0,1=>1,_=>q-1}).collect()
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
    let s=rng.ternary(p.n,p.q); let a=rng.uniform(p.n,p.q); let e=rng.ternary(p.n,p.q);
    let b=neg(&add(&mul(&a,&s,p.q),&e,p.q),p.q);
    Ok((ToySecretKey{s},ToyPublicKey{b,a}))
}

/// Encrypt a coefficient-encoded plaintext in Z_t[X]/(X^N+1).
pub fn encrypt(p:&ToyParams,pk:&ToyPublicKey,message:&[u64],seed:u64)->Result<ToyCiphertext,&'static str> {
    p.validate()?;
    if message.len()!=p.n || message.iter().any(|&x|x>=p.t) || pk.a.len()!=p.n || pk.b.len()!=p.n
        || pk.a.iter().chain(&pk.b).any(|&x|x>=p.q) { return Err("dimension or coefficient out of range"); }
    let mut rng=DemoRng(seed.max(1));
    let u=rng.ternary(p.n,p.q); let e1=rng.ternary(p.n,p.q); let e2=rng.ternary(p.n,p.q);
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

/// Compute a polynomial product in R_q, then return centered coefficient lifts.
fn centered_product_mod_q(a:&[u64],b:&[u64],q:u64)->Result<Vec<i128>,&'static str> {
    if a.is_empty() || a.len()!=b.len() || a.iter().chain(b).any(|&x|x>=q) {
        return Err("polynomial dimension or coefficient out of range");
    }
    Ok(mul(a,b,q).into_iter().map(|x|centered(x,q)).collect())
}

/// Apply nearest-integer t/q scale-and-round to integer coefficients, then reduce mod q.
fn scale_and_round_integer(a:&[i128],p:&ToyParams)->Result<Vec<u64>,&'static str> {
    let q=p.q as i128;
    a.iter().map(|&z| {
        let numerator=z.checked_mul(p.t as i128).ok_or("scale-and-round numerator overflow")?;
        let magnitude=numerator.checked_abs().ok_or("scale-and-round absolute-value overflow")?;
        let mut quotient=magnitude/q;
        let remainder=magnitude%q;
        if remainder*2>=q { quotient=quotient.checked_add(1).ok_or("rounding overflow")?; }
        let signed=if numerator<0 {-quotient} else {quotient};
        Ok(signed.rem_euclid(q) as u64)
    }).collect()
}

/// BFV tensor multiplication: form components in R_q, center their residues, then scale-and-round.
pub fn multiply_ciphertexts(p:&ToyParams,lhs:&ToyCiphertext,rhs:&ToyCiphertext)->Result<ToyCiphertext3,&'static str> {
    p.validate()?;
    if lhs.c0.len()!=p.n || lhs.c1.len()!=p.n || rhs.c0.len()!=p.n || rhs.c1.len()!=p.n
        || lhs.c0.iter().chain(&lhs.c1).chain(&rhs.c0).chain(&rhs.c1).any(|&x|x>=p.q) {
        return Err("ciphertext dimension or coefficient out of range");
    }
    // BFV multiplication is performed in R_q. Each U_k is reduced modulo q
    // before selecting its centered representative for the coefficientwise scale-and-round.
    let u0=centered_product_mod_q(&lhs.c0,&rhs.c0,p.q)?;
    let u1a=mul(&lhs.c0,&rhs.c1,p.q);
    let u1b=mul(&lhs.c1,&rhs.c0,p.q);
    let u1=add(&u1a,&u1b,p.q).into_iter().map(|x|centered(x,p.q)).collect::<Vec<_>>();
    let u2=centered_product_mod_q(&lhs.c1,&rhs.c1,p.q)?;
    Ok(ToyCiphertext3{
        c0:scale_and_round_integer(&u0,p)?,
        c1:scale_and_round_integer(&u1,p)?,
        c2:scale_and_round_integer(&u2,p)?,
    })
}

/// Decrypt a three-component tensor ciphertext, without relinearization.
pub fn decrypt_three(p:&ToyParams,sk:&ToySecretKey,ct:&ToyCiphertext3)->Result<Vec<u64>,&'static str> {
    p.validate()?;
    if sk.s.len()!=p.n || ct.c0.len()!=p.n || ct.c1.len()!=p.n || ct.c2.len()!=p.n
        || sk.s.iter().chain(&ct.c0).chain(&ct.c1).chain(&ct.c2).any(|&x|x>=p.q) {
        return Err("ciphertext/key dimension or coefficient out of range");
    }
    let s2=mul(&sk.s,&sk.s,p.q);
    let phase=add(&add(&ct.c0,&mul(&ct.c1,&sk.s,p.q),p.q),&mul(&ct.c2,&s2,p.q),p.q);
    Ok(phase.into_iter().map(|x|{
        let numerator=centered(x,p.q)*p.t as i128;
        let rounded=if numerator>=0 {(numerator+p.q as i128/2)/p.q as i128}
                    else {-((-numerator+p.q as i128/2)/p.q as i128)};
        rounded.rem_euclid(p.t as i128) as u64
    }).collect())
}

/// Generate a toy relinearization key for s^2 using a coefficient-wise gadget base.
/// The deterministic sampler is test-only; this key is NOT cryptographically secure.
pub fn relinearization_keygen(p:&ToyParams,sk:&ToySecretKey,seed:u64,base:u64)->Result<ToyRelinKey,&'static str> {
    p.validate()?;
    if sk.s.len()!=p.n || sk.s.iter().any(|&x|x>=p.q) || base<2 { return Err("invalid secret key or gadget base"); }
    let mut levels=0usize; let mut capacity=1u128;
    while capacity < p.q as u128 { capacity=capacity.checked_mul(base as u128).ok_or("gadget capacity overflow")?; levels+=1; }
    let s2=mul(&sk.s,&sk.s,p.q);
    let mut rng=DemoRng(seed.max(1));
    let mut out_b=Vec::with_capacity(levels); let mut out_a=Vec::with_capacity(levels);
    let mut gadget=1u64;
    for _ in 0..levels {
        let a=rng.uniform(p.n,p.q); let e=rng.ternary(p.n,p.q);
        let target=scale_poly(&s2,gadget,p.q);
        // b + a*s = gadget*s^2 + e (mod q)
        let b=add(&sub_poly(&target,&mul(&a,&sk.s,p.q),p.q),&e,p.q);
        out_b.push(b); out_a.push(a);
        gadget=((gadget as u128*base as u128)%p.q as u128) as u64;
    }
    Ok(ToyRelinKey{base,b:out_b,a:out_a})
}

fn scale_poly(a:&[u64],k:u64,q:u64)->Vec<u64> {
    a.iter().map(|&x|((x as u128*k as u128)%q as u128) as u64).collect()
}
fn sub_poly(a:&[u64],b:&[u64],q:u64)->Vec<u64> {
    a.iter().zip(b).map(|(&x,&y)|if x>=y{x-y}else{q-(y-x)}).collect()
}

/// Decompose canonical c2 coefficients into base-B digit polynomials.
fn gadget_digits(c2:&[u64],q:u64,base:u64,levels:usize)->Vec<Vec<u64>> {
    let mut digits=vec![vec![0u64;c2.len()];levels];
    for (i,&coefficient) in c2.iter().enumerate() {
        let mut value=coefficient;
        for digit in digits.iter_mut() {
            digit[i]=value%base;
            value/=base;
        }
    }
    debug_assert!(c2.iter().all(|&x| {
        let mut value=x; for _ in 0..levels { value/=base; } value==0 && x<q
    }));
    digits
}

/// Apply key switching to a three-component ciphertext, returning two components.
pub fn relinearize(p:&ToyParams,ct:&ToyCiphertext3,rk:&ToyRelinKey)->Result<ToyCiphertext,&'static str> {
    p.validate()?;
    if rk.base<2 || rk.b.is_empty() || rk.b.len()!=rk.a.len()
        || rk.b.iter().chain(&rk.a).any(|v|v.len()!=p.n || v.iter().any(|&x|x>=p.q))
        || ct.c0.len()!=p.n || ct.c1.len()!=p.n || ct.c2.len()!=p.n
        || ct.c0.iter().chain(&ct.c1).chain(&ct.c2).any(|&x|x>=p.q) {
        return Err("invalid relinearization key or ciphertext");
    }
    let digits=gadget_digits(&ct.c2,p.q,rk.base,rk.b.len());
    let mut c0=ct.c0.clone(); let mut c1=ct.c1.clone();
    for j in 0..rk.b.len() {
        c0=add(&c0,&mul(&digits[j],&rk.b[j],p.q),p.q);
        c1=add(&c1,&mul(&digits[j],&rk.a[j],p.q),p.q);
    }
    Ok(ToyCiphertext{c0,c1})
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
    #[test] fn toy_bfv_tensor_product_matches_plaintext_product() {
        let p=ToyParams { n: 8, q: 786433, t: 17 }; let (sk,pk)=keygen(&p,0x31415926).unwrap();
        let m1=vec![1,2,0,1,3,0,2,1];
        let m2=vec![2,1,1,0,1,2,0,3];
        let c1=encrypt(&p,&pk,&m1,0x1234).unwrap();
        let c2=encrypt(&p,&pk,&m2,0x5678).unwrap();
        let product=multiply_ciphertexts(&p,&c1,&c2).unwrap();
        let got=decrypt_three(&p,&sk,&product).unwrap();
        let expected=negacyclic_mul(&m1,&m2,p.t);
        assert_eq!(got,expected);
    }
    #[test] fn deterministic_multiseed_tensor_multiplication_sweep() {
        // Larger q provides enough correctness margin for multiplication noise.
        let p=ToyParams { n: 8, q: 786433, t: 17 };
        for seed in 1..=64u64 {
            let (sk,pk)=keygen(&p,seed.wrapping_mul(0x9e3779b97f4a7c15)).unwrap();
            let mut rng=DemoRng(seed.wrapping_mul(0xd6e8feb86659fd93).max(1));
            let m1:Vec<u64>=(0..p.n).map(|_|rng.next()%p.t).collect();
            let m2:Vec<u64>=(0..p.n).map(|_|rng.next()%p.t).collect();
            let c1=encrypt(&p,&pk,&m1,seed.wrapping_add(0x3003)).unwrap();
            let c2=encrypt(&p,&pk,&m2,seed.wrapping_add(0x4004)).unwrap();
            let product=multiply_ciphertexts(&p,&c1,&c2).unwrap();
            let expected=negacyclic_mul(&m1,&m2,p.t);
            assert_eq!(decrypt_three(&p,&sk,&product).unwrap(),expected,"multiplication seed {seed}");
        }
    }
    #[test] fn toy_bfv_relinearization_matches_three_component_decryption() {
        let p=ToyParams { n: 8, q: 786433, t: 17 };
        let (sk,pk)=keygen(&p,0x27182818).unwrap();
        let rk=relinearization_keygen(&p,&sk,0xabcdef01,2).unwrap();
        let m1=vec![1,2,0,1,3,0,2,1];
        let m2=vec![2,1,1,0,1,2,0,3];
        let c1=encrypt(&p,&pk,&m1,0x11112222).unwrap();
        let c2=encrypt(&p,&pk,&m2,0x33334444).unwrap();
        let product=multiply_ciphertexts(&p,&c1,&c2).unwrap();
        let before=decrypt_three(&p,&sk,&product).unwrap();
        let switched=relinearize(&p,&product,&rk).unwrap();
        let after=decrypt(&p,&sk,&switched).unwrap();
        assert_eq!(after,before);
        assert_eq!(after,negacyclic_mul(&m1,&m2,p.t));
    }
    #[test] fn relinearization_is_stable_across_gadget_bases_and_seeds() {
        let p=ToyParams { n: 8, q: 786433, t: 17 };
        for base in [2u64,4,16] {
            for seed in 1..=16u64 {
                let (sk,pk)=keygen(&p,seed.wrapping_mul(0xa0761d6478bd642f)).unwrap();
                let rk=relinearization_keygen(&p,&sk,seed.wrapping_add(0x5151),base).unwrap();
                let mut rng=DemoRng(seed.wrapping_mul(0xe7037ed1a0b428db).max(1));
                let m1:Vec<u64>=(0..p.n).map(|_|rng.next()%p.t).collect();
                let m2:Vec<u64>=(0..p.n).map(|_|rng.next()%p.t).collect();
                let c1=encrypt(&p,&pk,&m1,seed.wrapping_add(0x6161)).unwrap();
                let c2=encrypt(&p,&pk,&m2,seed.wrapping_add(0x7171)).unwrap();
                let product=multiply_ciphertexts(&p,&c1,&c2).unwrap();
                let tensor_dec=decrypt_three(&p,&sk,&product).unwrap();
                let switched=relinearize(&p,&product,&rk).unwrap();
                assert_eq!(decrypt(&p,&sk,&switched).unwrap(),tensor_dec,
                    "relinearization base {base}, seed {seed}");
            }
        }
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
