#!/usr/bin/env python3
"""Trainable LoRA parameters for one or more adapted linear matrices."""
import argparse

def lora_params(d_in: int, d_out: int, rank: int) -> int:
    return rank * (d_in + d_out)

def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument('--d-in',type=int,default=4096); p.add_argument('--d-out',type=int,default=4096); p.add_argument('--rank',type=int,default=8); p.add_argument('--matrices',type=int,default=1); a=p.parse_args()
    one=lora_params(a.d_in,a.d_out,a.rank); print(f'per matrix={one:,}; {a.matrices} matrix/matrices={one*a.matrices:,} trainable parameters')
if __name__ == '__main__': main()
