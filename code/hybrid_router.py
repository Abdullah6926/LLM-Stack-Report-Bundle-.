"""Policy-first local/cloud router with fallback and a per-request spend cap."""
from dataclasses import dataclass
@dataclass
class Result: provider: str; text: str; cost_usd: float
class BudgetExceeded(RuntimeError): pass

def route(prompt: str, *, sensitive: bool, hard: bool, budget_usd: float,
          local_call=None, cloud_call=None) -> Result:
    local_call = local_call or (lambda p: 'local answer [stub]')
    cloud_call = cloud_call or (lambda p: ('cloud answer [stub]', 0.002))
    if sensitive:
        return Result('local', local_call(prompt), 0.0)
    if not hard:
        try: return Result('local', local_call(prompt), 0.0)
        except Exception: pass
    text, cost = cloud_call(prompt)
    if cost > budget_usd: raise BudgetExceeded(f'quoted cost ${cost:.4f} exceeds cap ${budget_usd:.4f}')
    return Result('cloud', text, cost)

if __name__=='__main__':
    print(route('summarize',sensitive=False,hard=True,budget_usd=.01))
    print(route('patient record',sensitive=True,hard=True,budget_usd=0))
