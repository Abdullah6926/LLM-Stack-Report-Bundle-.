"""Ollama OpenAI-compatible chat endpoint. Default offline stub."""
import os, sys

def run_stub(): print('assistant: Ollama-compatible adapter returned a local stub. [stub]')
def run_live():
    from openai import OpenAI
    c=OpenAI(base_url=os.environ.get('OLLAMA_BASE_URL','http://localhost:11434/v1'),api_key='ollama')
    r=c.chat.completions.create(model=os.environ.get('OLLAMA_MODEL','llama3.2'),messages=[{'role':'user','content':'Explain BPE in one sentence.'}],stream=False)
    print(r.choices[0].message.content)
if __name__=='__main__': run_live() if '--live' in sys.argv else run_stub()
