#!/usr/bin/env python3
"""Python arbitrary-precision differential validation of the two-fold map."""
from audit_parameters import Q,W,D
def red(z,q,w,d):
 b=1<<w;m=b-1;u=(z>>w)*d+(z&m);v=(u>>w)*d+(u&m)
 if v>=2*q:raise AssertionError(f"range lemma failed: {v} >= 2q")
 return v-q if v>=q else v
def main():
 total=0
 for q,w,d in zip(Q,W,D):
  tests={0,1,q-1,q,q*q-1}
  for k in range(200000):tests.add(((k*0x9e3779b97f4a7c15)^(k<<67))%(q*q))
  for z in tests:assert red(z,q,w,d)==z%q,(q,z)
  total+=len(tests)
 print(f"PASS: {total} arbitrary-precision differential inputs")
if __name__=="__main__":main()
