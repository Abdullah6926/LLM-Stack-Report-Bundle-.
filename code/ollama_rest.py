"""Ollama /api/chat NDJSON reader. Default stub; use --live only with Ollama running."""
import json, sys, urllib.request
PAYLOAD={'model':'llama3.2','messages':[{'role':'user','content':'Say hello in four words.'}],'stream':True,'options':{'num_ctx':4096}}
def run_stub():
    lines=[{'message':{'role':'assistant','content':'Hello'},'done':False},{'message':{'role':'assistant','content':' there.'},'done':False},{'done':True,'prompt_eval_count':9,'eval_count':2}]
    for obj in lines: print('ndjson:',json.dumps(obj,sort_keys=True))
    print('note: deterministic fixture, not a live Ollama response')
def run_live():
    req=urllib.request.Request('http://localhost:11434/api/chat',data=json.dumps(PAYLOAD).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=120) as r:
        for raw in r:
            obj=json.loads(raw); print(json.dumps(obj,ensure_ascii=False))
if __name__=='__main__': run_live() if '--live' in sys.argv else run_stub()
