from tools.services.pinecone import query_data
from tools.services.openai import get_embeddings
TOP_K = 3


KB_NS = 'demo'
FAQ_NS = 'customer-service-demo'

def retrieve_results(prompt, type, top_k=TOP_K):
    vector = get_embeddings(prompt)
    if type == 'kb':
        namespace = KB_NS
    elif type == 'faq':
        namespace = FAQ_NS
    results = query_data(vector, namespace, top_k)
    results = sorted(results, key=lambda x: x['score'], reverse=True)
    return [r['metadata'] for r in results]
