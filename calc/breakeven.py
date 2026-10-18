#!/usr/bin/env python3
"""Monthly self-host vs API break-even; inputs are explicit assumptions."""
import argparse

def api_cost(tokens_m: float, dollars_per_million: float) -> float: return tokens_m * dollars_per_million

def monthly_selfhost_cost(fixed: float, utilization: float, variable_at_full: float = 0.0) -> float:
    if not 0 <= utilization <= 1: raise ValueError('utilization must be in [0,1]')
    return fixed + variable_at_full * utilization

def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument('--tokens-m',type=float,default=100); p.add_argument('--api-usd-per-m',type=float,default=2.0); p.add_argument('--fixed-usd-month',type=float,default=180); p.add_argument('--utilization',type=float,default=.50); p.add_argument('--variable-at-full',type=float,default=20); a=p.parse_args()
    api=api_cost(a.tokens_m,a.api_usd_per_m); local=monthly_selfhost_cost(a.fixed_usd_month,a.utilization,a.variable_at_full)
    print(f'API=${api:,.2f}/month; self-host=${local:,.2f}/month; cheaper={"API" if api < local else "self-host" if local < api else "tie"}')
    print('Assumptions only; exclude engineering, redundancy, quality and utilization variability unless entered.')
if __name__ == '__main__': main()
