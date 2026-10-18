"""Structured-output pattern with a JSON-schema stub and optional live provider call."""
import json, os, sys
SCHEMA={'type':'object','properties':{'severity':{'type':'string','enum':['low','medium','high']},'summary':{'type':'string'}},'required':['severity','summary'],'additionalProperties':False}
def run_stub():
    data={'severity':'low','summary':'Offline structured-output demonstration.'}
    assert set(data)=={'severity','summary'} and data['severity'] in {'low','medium','high'}
    print(json.dumps(data,sort_keys=True)); print('schema_valid: true [stub]')
def run_live():
    from openai import OpenAI
    c=OpenAI(); model=os.environ.get('OPENAI_MODEL','gpt-4.1-mini')
    r=c.responses.create(model=model,input='Classify this test event: one user typo.',text={'format':{'type':'json_schema','name':'triage','strict':True,'schema':SCHEMA}})
    print(r.output_text); json.loads(r.output_text)
if __name__=='__main__': run_live() if '--live' in sys.argv else run_stub()
