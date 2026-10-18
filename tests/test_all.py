import sys, unittest, tempfile, pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'code'))
from calc.kv_cache import kv_bytes
from calc.vram import estimate_gib
from calc.tokens_per_sec import upper_bound_tps
from calc.lora_params import lora_params
from calc.breakeven import api_cost, monthly_selfhost_cost
from code.hybrid_router import route, BudgetExceeded
from code.rag_hybrid import rrf, recall_at_k
from code.agent_loop import agent
from code.mcp_description_pin import DESCRIPTION, verify

class StackTests(unittest.TestCase):
    def test_kv_cache(self): self.assertEqual(kv_bytes(32,8,128,8192,2), 1_073_741_824)
    def test_vram(self): self.assertAlmostEqual(estimate_gib(7,4.5,1,.1),5.135,places=2)
    def test_tps(self): self.assertAlmostEqual(upper_bound_tps(500,5,0),100)
    def test_lora(self): self.assertEqual(lora_params(4096,4096,8),65536)
    def test_cost(self): self.assertEqual(api_cost(100,2),200); self.assertEqual(monthly_selfhost_cost(180,.5,20),190)
    def test_router_sensitive_stays_local(self):
        got=route('private',sensitive=True,hard=True,budget_usd=0)
        self.assertEqual(got.provider,'local')
    def test_router_budget(self):
        with self.assertRaises(BudgetExceeded): route('hard',sensitive=False,hard=True,budget_usd=.001,cloud_call=lambda p:('x',.002))
    def test_rrf_and_recall(self):
        result=rrf([['a','b'],['a','b']]); self.assertEqual(result[0],'a'); self.assertEqual(recall_at_k(['a','b'],{'a'},2),1.0)
    def test_agent_allowlisted(self):
        acts=iter([{'kind':'tool','name':'lookup_fact','args':{'key':'mcp'}},{'kind':'final','text':'ok'}])
        out,trace=agent('q',lambda t,h:next(acts)); self.assertEqual(out,'ok'); self.assertEqual(len(trace),1)
    def test_description_pin_detects_change(self):
        self.assertTrue(verify(DESCRIPTION)); self.assertFalse(verify(DESCRIPTION+' silently changed'))

if __name__=='__main__': unittest.main()
