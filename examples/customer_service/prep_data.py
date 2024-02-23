import os
import json
from openai import OpenAI

client = OpenAI()
GPT_MODEL = 'gpt-4'
EMBEDDING_MODEL = "text-embedding-3-large"

article_list = os.listdir('data')

articles = []

for x in article_list:

    article_path = 'data/' + x

    # Opening JSON file
    f = open(article_path)

    # returns JSON object as
    # a dictionary
    data = json.load(f)

    articles.append(data)

    # Closing file
    f.close()

for i, x in enumerate(articles):
    try:
        embedding = client.embeddings.create(model=EMBEDDING_MODEL,input=x['text'])
        articles[i].update({"embedding": embedding.data[0].embedding})
    except Exception as e:
        print(x['title'])
        print(e)

import qdrant_client
from qdrant_client.http import models as rest
import pandas as pd


qdrant = qdrant_client.QdrantClient(host='localhost')
qdrant.get_collections()

collection_name = 'help_center'

vector_size = len(articles[0]['embedding'])
vector_size

article_df = pd.DataFrame(articles)
article_df.head()

# Create Vector DB collection
qdrant.recreate_collection(
    collection_name=collection_name,
    vectors_config={
        'article': rest.VectorParams(
            distance=rest.Distance.COSINE,
            size=vector_size,
        )
    }
)

# Populate collection with vectors

qdrant.upsert(
    collection_name=collection_name,
    points=[
        rest.PointStruct(
            id=k,
            vector={
                'article': v['embedding'],
            },
            payload=v.to_dict(),
        )
        for k, v in article_df.iterrows()
    ],
)
