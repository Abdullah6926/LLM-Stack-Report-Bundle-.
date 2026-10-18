"""Small bounded agent loop. All tool execution is local, allowlisted, and side-effect-free."""
ALLOWED={'lookup_fact'}
def lookup_fact(key): return {'kv_cache':'stores attention keys and values','mcp':'connects hosts to tools/resources/prompts'}.get(key,'not found')
def agent(task, plan, max_steps=4):
    history=[]
    for step in range(max_steps):
        action=plan(task,history)
        if action.get('kind')=='final': return action.get('text',''),history
        if action.get('kind')!='tool' or action.get('name') not in ALLOWED: raise PermissionError('tool not allowlisted')
        result=lookup_fact(action.get('args',{}).get('key',''))
        history.append({'step':step+1,'tool':action['name'],'result':result})
    return 'Step budget exhausted; provide a partial answer.',history
if __name__=='__main__':
    actions=iter([{'kind':'tool','name':'lookup_fact','args':{'key':'mcp'}},{'kind':'final','text':'MCP standardizes tools, resources and prompts.'}])
    text,trace=agent('What is MCP?',lambda t,h:next(actions))
    print(text); print('steps:',len(trace))
