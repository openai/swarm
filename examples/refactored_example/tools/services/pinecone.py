from pinecone import Pinecone
from dotenv import load_dotenv

PC_INDEX = 'main_index'

load_dotenv()
pc = Pinecone()

def upsert_data(vectors, username, index=PC_INDEX):
  print(f"Upserting vectors into index {index}...")
  try:
    index = pc.Index(name=index)
    res = index.upsert(
        vectors = vectors,
        namespace = username
    )
    if 'upserted_count' in res:
      print(f"{res['upserted_count']} vectors upserted.")
    else:
      print(f"Failed to upsert vectors: {res}")
  except Exception as e:
    print(f"Failed to upsert vectors: {e}")

def query_data(vector, namespace, top_k=3, index=PC_INDEX):
  print(f"Querying index {index}...")
  try:
    index = pc.Index(index)
    res = index.query(
        vector = vector,
        namespace = namespace,
        top_k = top_k,
        include_metadata = True
    )
    if 'matches' in res:
      print(f"Query successful. Found {len(res['matches'])} matches.")
      return res['matches']
    else:
      print(f"Failed to query vectors: {res}")
  except Exception as e:
    print(f"Failed to query vectors: {e}")
  return []

def delete_namespace(namespace: str, index=PC_INDEX):
  index = pc.Index(index)
  index.delete(delete_all=True, namespace=namespace)