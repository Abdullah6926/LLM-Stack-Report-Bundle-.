#!/usr/bin/env python3
"""Roofline-style upper bound: effective memory bandwidth / bytes read per token."""
import argparse

def upper_bound_tps(bandwidth_gib_s: float, weights_gib: float, kv_read_gib: float = 0.0) -> float:
    return bandwidth_gib_s / (weights_gib + kv_read_gib) if weights_gib + kv_read_gib > 0 else 0.0

def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument('--bandwidth-gib-s',type=float,default=500); p.add_argument('--weights-gib',type=float,default=4); p.add_argument('--kv-read-gib',type=float,default=0); a=p.parse_args()
    print(f'idealized ceiling={upper_bound_tps(a.bandwidth_gib_s,a.weights_gib,a.kv_read_gib):.1f} tokens/s (real throughput is lower)')
if __name__ == '__main__': main()
