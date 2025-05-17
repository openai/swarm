import re

from openai import OpenAI  # type: ignore
import qdrant_client  # External: pip install qdrant-client

# # # Initialize connections
client = OpenAI()
qdrant = qdrant_client.QdrantClient(host='localhost')  # prefer_grpc=True)

# # Set embedding model
# # TODO: Add this to global config
EMBEDDING_MODEL = 'text-embedding-3-large'

# # # Set qdrant collection
collection_name = 'help_center'

# # # Query function for qdrant

def query_qdrant(query, collection_name, vector_name='article', top_k=5):
    # Creates embedding vector from user query
    embedded_query = client.embeddings.create(
        input=query,
        model=EMBEDDING_MODEL,
    ).data[0].embedding

    query_results = qdrant.search(
        collection_name=collection_name,
        query_vector=(
            vector_name, embedded_query
        ),
        limit=top_k,
    )

    return query_results


def query_docs(query):
    print(f'Searching knowledge base with query: {query}')
    query_results = query_qdrant(query, collection_name=collection_name)
    output = []

    for i, article in enumerate(query_results):
        title = article.payload["title"]
        text = article.payload["text"]
        url = article.payload["url"]

        output.append((title, text, url))

    if output:
        title, content, _ = output[0]
        response = f"Title: {title}\nContent: {content}"
        # Truncate content for concise printing
        text_to_truncate = content
        if len(text_to_truncate) > 50:
            truncated_text = text_to_truncate[:50] + '...'
        else:
            truncated_text = text_to_truncate
        truncated_content = re.sub(r'\s+', ' ', truncated_text)
        print('Most relevant article title:', truncated_content)
        return {'response': response}
    else:
        print('no results')
        return {'response': 'No results found.'}
