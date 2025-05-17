import os
import json
# External: pip install openai
from openai import OpenAI  # type: ignore

# External: pip install qdrant-client
import qdrant_client
# External: pip install qdrant-client
from qdrant_client.http import models as rest

# External: pip install pandas pandas-stubs
import pandas as pd  # type: ignore

import typing

client = OpenAI()
GPT_MODEL = 'gpt-4'
EMBEDDING_MODEL = "text-embedding-3-large"

article_list = os.listdir('data')

articles: typing.List[typing.Dict[str, typing.Any]] = []

for filename in article_list:
    if not filename.endswith(".json"):
        # print(f"Skipping non-JSON file: {filename}")
        continue

    article_path = os.path.join('data', filename)

    try:
        with open(article_path, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, dict):
            # print(f"Warn: {filename} content not JSON obj. Skip.")
            continue
        
        articles.append(data)
    except json.JSONDecodeError:
        # print(f"Error decoding JSON from file: {filename}. Skipping.")
        continue
    except Exception:
        # print(f"Unexpected error with file {filename}. Skipping.")
        continue

for i, x in enumerate(articles):  # Now x is guaranteed to be a dict
    try:
        article_text = x.get('text', '')
        if not article_text: 
            # print(f"Warn: Art {i} ({x.get('title', 'NoTi')}) no 'text'.")
            articles[i]["embedding"] = [] 
            continue

        embedding_response = client.embeddings.create(
            model=EMBEDDING_MODEL, input=article_text
        )
        articles[i]["embedding"] = embedding_response.data[0].embedding
    except Exception:
        article_title = x.get('title', f'Article {i} (unknown title)')
        # print(f"Error processing article {article_title}: e")
        # Optionally add a placeholder or skip if embedding fails
        if isinstance(x, dict):  # ensure x is a dict before assignment
            articles[i]["embedding"] = []  # Default for error cases


qdrant = qdrant_client.QdrantClient(host='localhost')
# qdrant.get_collections() # This might raise if DB not up, consider context

collection_name = 'help_center'

vector_size = 0
if articles:
    first_article_embedding = articles[0].get('embedding')
    if isinstance(first_article_embedding, list) and first_article_embedding:
        vector_size = len(first_article_embedding)
    # else:
        # print("Warn: First article no valid 'embedding' for vector size.")
else:
    # print("Warning: No articles processed, vector_size remains 0.")
    pass  # vector_size is already 0

# print(f"Determined vector size: {vector_size}")

# Only proceed if articles and a valid vector_size exist
if articles and vector_size > 0:
    article_df = pd.DataFrame(articles)
    # print(article_df.head())

    # Create Vector DB collection
    try:
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
        # Filter articles: ensure embedding is valid (exists, list, size)
        points_to_upsert = []
        for k, v_series in article_df.iterrows():
            v_dict = v_series.to_dict()
            embedding_value = v_dict.get('embedding')
            is_valid_embedding = (
                embedding_value is not None and
                isinstance(embedding_value, list) and
                len(embedding_value) == vector_size
            )
            if is_valid_embedding:
                points_to_upsert.append(
                    rest.PointStruct(
                        id=k,  # Use DataFrame index as ID
                        vector={
                            'article': v_dict['embedding'],
                        },
                        payload=v_dict,
                    )
                )
            # else:
                # print(f"Skip article {k}: missing/invalid embedding.")

        if points_to_upsert:
            qdrant.upsert(
                collection_name=collection_name,
                points=points_to_upsert,
            )
        # else:
            # print("No valid points to upsert into Qdrant.")

    except Exception:
        # print(f"Error with Qdrant operations: e")
        pass  # Catch Qdrant errors, like connection issues
elif not articles:
    # print("Skipping Qdrant operations: No articles were loaded.")
    pass
else:  # vector_size is 0
    # print("Skip Qdrant ops: Vector size 0 or undetermined.")
    pass
