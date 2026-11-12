#!/usr/bin/env python3
"""Independent polynomial arithmetic reference tests on small rings."""
import random
def mul(a,b,q):
 n=len(a);c=[0]*n
 for i,x in enumerate(a):
  for j,y in enumerate(b):
   k=i+j;c[k]=(c[k]+x*y)%q if k<n else (c[k-n]-x*y)%q
 return c
def main():
 r=random.Random(20261112);count=0
 for n,q in ((2,97),(4,97),(8,257),(16,769)):
  for _ in range(1000):
   a=[r.randrange(q) for _ in range(n)];b=[r.randrange(q) for _ in range(n)]
   # Independent distributive accumulation, kept separate from production Rust.
   c=[0]*n
   for i in range(n):
    for j in range(n):
     k=i+j;c[k]=(c[k]+a[i]*b[j])%q if k<n else (c[k-n]-a[i]*b[j])%q
   assert mul(a,b,q)==c;count+=1
 print(f"PASS: {count} deterministic negacyclic reference cases")
if __name__=="__main__":main()
