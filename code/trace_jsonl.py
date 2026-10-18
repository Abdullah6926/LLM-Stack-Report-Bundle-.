"""Minimal JSONL tracing wrapper. Avoid logging prompts or private tool outputs by default."""
import json, time, pathlib

def traced(call, *, provider, model, input_tokens=0, output_tokens=0, usd_per_m_input=0.0, usd_per_m_output=0.0, out='trace.jsonl'):
    start=time.perf_counter(); result=call(); elapsed=(time.perf_counter()-start)*1000
    cost=(input_tokens*usd_per_m_input+output_tokens*usd_per_m_output)/1_000_000
    row={'provider':provider,'model':model,'latency_ms':round(elapsed,2),'input_tokens':input_tokens,'output_tokens':output_tokens,'estimated_cost_usd':round(cost,8)}
    with pathlib.Path(out).open('a',encoding='utf-8') as f: f.write(json.dumps(row)+'\n')
    return result,row
if __name__=='__main__':
    result,row=traced(lambda:'ok',provider='offline',model='stub',input_tokens=12,output_tokens=4,out='/tmp/llm_trace_demo.jsonl')
    print(row)
