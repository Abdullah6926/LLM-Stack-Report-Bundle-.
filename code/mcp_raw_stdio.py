"""Minimal JSON-RPC-over-stdio fixture. `--demo` prints each request and response.
For production, use the MCP SDK; this deliberately implements only a tiny subset.
"""
import json, sys

def respond(req):
    method=req.get('method'); params=req.get('params',{}); rid=req.get('id')
    if method=='server/discover': result={'resultType':'complete','supportedVersions':['2026-07-28'],'capabilities':{'tools':{},'resources':{},'prompts':{}},'_meta':{'io.modelcontextprotocol/serverInfo':{'name':'stack-demo','version':'1.0.0'}},'ttlMs':3600000,'cacheScope':'public'}
    elif method=='initialize': result={'protocolVersion':params.get('protocolVersion','2025-11-25'),'capabilities':{'tools':{},'resources':{},'prompts':{}},'serverInfo':{'name':'stack-demo','version':'1.0.0'}}
    elif method=='tools/list': result={'tools':[{'name':'add','description':'Add two integers.','inputSchema':{'type':'object','properties':{'a':{'type':'integer'},'b':{'type':'integer'}},'required':['a','b']}},{'name':'public_status','description':'Return allowlisted public status.','inputSchema':{'type':'object','properties':{'component':{'type':'string','enum':['api','retrieval','worker']}},'required':['component']}}]}
    elif method=='tools/call':
        name=params.get('name'); a=params.get('arguments',{})
        if name=='add': result={'content':[{'type':'text','text':str(int(a['a'])+int(a['b']))}],'structuredContent':{'result':int(a['a'])+int(a['b'])}}
        elif name=='public_status' and a.get('component') in {'api','retrieval','worker'}: result={'content':[{'type':'text','text':'ok'}],'structuredContent':{'component':a['component'],'status':'ok'}}
        else: return {'jsonrpc':'2.0','id':rid,'error':{'code':-32602,'message':'Unknown tool or invalid arguments'}}
    elif method=='resources/list': result={'resources':[{'uri':'stack://overview','name':'overview','mimeType':'text/plain'}]}
    elif method=='resources/read': result={'contents':[{'uri':'stack://overview','mimeType':'text/plain','text':'Models, tools, retrieval, policy, tracing.'}]}
    elif method=='prompts/list': result={'prompts':[{'name':'explain_stack','description':'Build an intuition/mechanism/limitation teaching prompt.'}]}
    elif method=='prompts/get': result={'messages':[{'role':'user','content':{'type':'text','text':'Explain the stack using intuition, mechanism, and a limitation.'}}]}
    elif method=='notifications/initialized': return None
    else: return {'jsonrpc':'2.0','id':rid,'error':{'code':-32601,'message':'Method not implemented in this demo'}}
    return {'jsonrpc':'2.0','id':rid,'result':result} if rid is not None else None

def demo():
    meta={'io.modelcontextprotocol/protocolVersion':'2026-07-28','io.modelcontextprotocol/clientInfo':{'name':'demo','version':'1.0.0'},'io.modelcontextprotocol/clientCapabilities':{}}
    requests=[{'jsonrpc':'2.0','id':1,'method':'server/discover','params':{'_meta':meta}},{'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'add','arguments':{'a':19,'b':23},'_meta':meta}}]
    for req in requests:
        print('> '+json.dumps(req,separators=(',',':')))
        resp=respond(req)
        if resp is not None: print('< '+json.dumps(resp,separators=(',',':')))

def main():
    if '--demo' in sys.argv: demo(); return
    for line in sys.stdin:
        try: req=json.loads(line); resp=respond(req)
        except Exception as e: resp={'jsonrpc':'2.0','id':None,'error':{'code':-32700,'message':str(e)}}
        if resp is not None: print(json.dumps(resp,separators=(',',':')),flush=True)
if __name__=='__main__': main()
