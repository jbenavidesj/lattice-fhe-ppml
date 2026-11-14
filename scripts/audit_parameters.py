#!/usr/bin/env python3
"""Dependency-free deterministic audit of the four 64-bit modulus candidates."""
import math
Q=[36028797002170369,36028796951838721,18014398508400641,18014398507892737]
PSI=[22505317672356688,29410112198941026,9354911369072846,12617745759101472]
W=[55,55,54,54]; D=[16793599,67125247,1081343,1589247]; N=8192
# Auxiliary exact-integer tensor-product NTT basis (N=8192).
AUX_Q = [4503599627124737,4503599626682369,4503599626321921,
         4503599626141697,4503599625830401,4503599625535489,
         4503599625404417,4503599625158657,4503599624962049]
AUX_PSI = [2707758278772395,1841889776165649,1232568238856409,
           3681299526190914,3801184396185815,2821339159676527,
           2673470588363527,1562061910246617,2293421299669720]
def is_prime(n):
 if n<2:return False
 for p in (2,3,5,7,11,13,17,19,23,29,31,37):
  if n%p==0:return n==p
 d=n-1;s=0
 while d%2==0:d//=2;s+=1
 for a in (2,325,9375,28178,450775,9780504,1795265022):
  if a%n==0:continue
  x=pow(a,d,n)
  if x in (1,n-1):continue
  for _ in range(s-1):
   x=pow(x,2,n)
   if x==n-1:break
  else:return False
 return True
def main():
 assert len(set(Q))==4
 for i,(q,p,w,d) in enumerate(zip(Q,PSI,W,D),1):
  assert q==(1<<w)-d and 0<d<(1<<(w//2))
  assert is_prime(q) and q%(2*N)==1
  assert pow(p,2*N,q)==1 and pow(p,N,q)==q-1
  print(f"q{i}: prime; congruence and exact 2N root order PASS")
 for i in range(4):
  for j in range(i):assert math.gcd(Q[i],Q[j])==1
 prod=math.prod(Q);Delta=prod//65537
 for i,(q,p) in enumerate(zip(AUX_Q,AUX_PSI),1):
  assert is_prime(q) and q%(2*N)==1
  assert pow(p,2*N,q)==1 and pow(p,N,q)==q-1
  print(f"auxiliary q{i}: prime; exact 2N root order PASS")
 aux_product=math.prod(AUX_Q)
 assert 2*aux_product > N*prod*prod
 print("auxiliary CRT product exceeds 2*N*(Q/2)^2 bound: PASS")
 print("pairwise coprime: PASS");print("Q bit length:",prod.bit_length());print("log2(Delta):",format(math.log2(Delta),".12f"));print("No RLWE security claim.")
if __name__=="__main__":main()
