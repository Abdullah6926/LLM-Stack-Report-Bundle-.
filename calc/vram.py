#!/usr/bin/env python3
"""Transparent VRAM estimate: weight bits/token are averages, not format guarantees."""
import argparse

def estimate_gib(params_b: float, bpw: float, kv_gib: float = 0.0, overhead: float = 0.10) -> float:
    weights_gib = params_b * 1e9 * bpw / 8 / 2**30
    return (weights_gib + kv_gib) * (1 + overhead)

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--params-b', type=float, default=7)
    p.add_argument('--bpw', type=float, default=4.5)
    p.add_argument('--kv-gib', type=float, default=1.0)
    p.add_argument('--overhead', type=float, default=0.10)
    a = p.parse_args()
    w = a.params_b * 1e9 * a.bpw / 8 / 2**30
    print(f'weights={w:.2f} GiB; KV={a.kv_gib:.2f} GiB; total+overhead={estimate_gib(a.params_b,a.bpw,a.kv_gib,a.overhead):.2f} GiB')

if __name__ == '__main__': main()
