#[derive(Debug,Clone,Copy,PartialEq,Eq)]
pub enum AsymRedError { InvalidModulus, InvalidDelta, InputOutOfRange, IntermediateOutOfRange }
pub fn asymred(z:u128,q:u64,w:u32,delta:u64)->Result<u64,AsymRedError> {
 if w==0||w>=64||q<=1{return Err(AsymRedError::InvalidModulus);}
 let b=1u128<<w;
 if q as u128+delta as u128!=b{return Err(AsymRedError::InvalidModulus);}
 if delta==0||delta as u128>=(1u128<<(w/2)){return Err(AsymRedError::InvalidDelta);}
 if z>=(q as u128)*(q as u128){return Err(AsymRedError::InputOutOfRange);}
 let mask=b-1; let zh=z>>w; let zl=z&mask;
 let u=zh.checked_mul(delta as u128).and_then(|x|x.checked_add(zl)).ok_or(AsymRedError::IntermediateOutOfRange)?;
 let uh=u>>w; let ul=u&mask;
 let v=uh.checked_mul(delta as u128).and_then(|x|x.checked_add(ul)).ok_or(AsymRedError::IntermediateOutOfRange)?;
 if v>=2*q as u128{return Err(AsymRedError::IntermediateOutOfRange);}
 Ok(if v>=q as u128 {(v-q as u128) as u64} else {v as u64})
}
#[cfg(test)]
mod tests {
 use super::*; use crate::MODULI;
 #[test] fn candidate_moduli_differential_grid_and_boundaries() {
  let ws=[55,55,54,54]; let ds=[16793599,67125247,1081343,1589247];
  for i in 0..4 {let q=MODULI[i];let qx=q as u128;let mut vals=vec![0,1,qx-1,qx,qx*qx-1];
   for k in 0..20000u128 {vals.push((k.wrapping_mul(0x9e3779b97f4a7c15u128)^(k<<67))%(qx*qx));}
   for z in vals {assert_eq!(asymred(z,q,ws[i],ds[i]).unwrap(),(z%qx) as u64,"q={q}, z={z}");}
  }
 }
 #[test] fn rejects_out_of_domain(){let q=MODULI[0];assert_eq!(asymred((q as u128)*(q as u128),q,55,16793599),Err(AsymRedError::InputOutOfRange));}
}
