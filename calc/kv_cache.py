#!/usr/bin/env python3
"""Estimate decoder KV-cache memory (MiB/GiB), excluding allocator overhead."""
import argparse

def kv_bytes(layers: int, kv_heads: int, head_dim: int, tokens: int, bytes_per_value: int = 2) -> int:
    values = (layers * kv_heads * head_dim * tokens * 2)  # K and V
    return values * bytes_per_value

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--layers', type=int, default=32)
    p.add_argument('--kv-heads', type=int, default=8)
    p.add_argument('--head-dim', type=int, default=128)
    p.add_argument('--tokens', type=int, default=8192)
    p.add_argument('--bytes-per-value', type=int, default=2, help='2=FP16/BF16, 1=FP8/int8')
    a = p.parse_args()
    b = kv_bytes(a.layers, a.kv_heads, a.head_dim, a.tokens, a.bytes_per_value)
    print(f'KV cache: {b:,} bytes = {b / 2**30:.3f} GiB')

if __name__ == '__main__': main()
