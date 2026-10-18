"""A safe tool-call loop. Stub output can be tested without API keys."""
import json
ALLOWED = {'multiply'}
def multiply(a: float, b: float) -> float: return a * b

def run_stub():
    planned = {'name': 'multiply', 'arguments': {'a': 6, 'b': 7}}
    if planned['name'] not in ALLOWED: raise PermissionError(planned['name'])
    result = multiply(**planned['arguments'])
    print('tool_call:', json.dumps(planned, sort_keys=True))
    print('tool_result:', result, '[stub]')
    print('final: 6 × 7 = 42 [stub]')

def run_live():
    import os
    from openai import OpenAI
    c=OpenAI(); model=os.environ.get('OPENAI_MODEL','gpt-4.1-mini')
    tools=[{'type':'function','name':'multiply','description':'Multiply two numbers.','parameters':{'type':'object','properties':{'a':{'type':'number'},'b':{'type':'number'}},'required':['a','b'],'additionalProperties':False},'strict':True}]
    r=c.responses.create(model=model,input='What is 6 times 7?',tools=tools)
    for item in r.output:
        if item.type=='function_call' and item.name in ALLOWED:
            args=json.loads(item.arguments); out=multiply(**args)
            r=c.responses.create(model=model,previous_response_id=r.id,input=[{'type':'function_call_output','call_id':item.call_id,'output':str(out)}],tools=tools)
    print(r.output_text)
if __name__=='__main__':
    import sys
    run_live() if '--live' in sys.argv else run_stub()
