"""Tiny hybrid retrieval demo: lexical BM25-like ranking + toy dense scores + RRF."""
import math
CORPUS={
 'a':'KV cache stores keys and values from earlier tokens to avoid recomputing them.',
 'b':'RAG retrieves relevant passages and supplies source snippets to a language model.',
 'c':'MCP standardizes how hosts connect to tools, resources, and prompts.'}
# Toy dense scores stand in for an embedding model; replace with locally generated embeddings in real use.
TOY_DENSE={'a':0.91,'b':0.21,'c':0.11}
def lexical_scores(query, corpus=CORPUS):
    terms=set(query.lower().split()); out={}
    for k,doc in corpus.items():
        words=doc.lower().split(); out[k]=sum(words.count(t) for t in terms)
    return sorted(out,key=lambda k:(out[k],k),reverse=True)
def rrf(rankings,k=60):
    scores={}
    for ranking in rankings:
        for rank,doc_id in enumerate(ranking,1): scores[doc_id]=scores.get(doc_id,0)+1/(k+rank)
    return sorted(scores,key=lambda d:(scores[d],d),reverse=True)
def recall_at_k(ranked, relevant, k):
    return len(set(ranked[:k]) & set(relevant))/len(relevant) if relevant else 0.0
def run_demo():
    q='KV cache previous tokens'; lexical=lexical_scores(q); dense=sorted(TOY_DENSE,key=TOY_DENSE.get,reverse=True); combined=rrf([lexical,dense])
    print('lexical:',lexical); print('toy_dense:',dense); print('rrf:',combined); print(f'recall@2={recall_at_k(combined,{"a"},2):.2f}')
    print('note: toy dense ranking is deterministic scaffolding, not an embedding benchmark')
if __name__=='__main__': run_demo()
