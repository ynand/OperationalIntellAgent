from openai import OpenAI
import numpy as np

client = OpenAI(api_key="your_api_key")  # Replace with your API key

def embed_text(text):
    # Use OpenAI's embedding API
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"  # Or another available embedding model
    )
    embedding = response.data[0].embedding
    return np.array(embedding)

# Example: Using FAISS for local vector search (for demo purposes)
# In production, use Pinecone, Weaviate, Qdrant, etc.

try:
    import faiss
except ImportError:
    faiss = None

class SimpleVectorDB:
    def __init__(self):
        self.embeddings = []
        self.texts = []

    def add(self, text, embedding):
        self.texts.append(text)
        self.embeddings.append(embedding)

    def search(self, query_embedding, top_k=3):
        if not self.embeddings:
            return []
        emb_matrix = np.array(self.embeddings).astype("float32")
        query_emb = np.array(query_embedding).astype("float32").reshape(1, -1)
        if faiss:
            index = faiss.IndexFlatL2(emb_matrix.shape[1])
            index.add(emb_matrix)
            _, idxs = index.search(query_emb, top_k)
            return [self.texts[i] for i in idxs[0]]
        else:
            # Fallback: cosine similarity
            scores = emb_matrix @ query_emb.T
            top_idxs = np.argsort(scores.flatten())[::-1][:top_k]
            return [self.texts[i] for i in top_idxs]

# Dummy embedding function (replace with real model, e.g., OpenAI, HuggingFace)
def embed_text(text):
    # For demo: hash-based pseudo-embedding
    np.random.seed(abs(hash(text)) % (2**32))
    return np.random.rand(512)

# Global vector DB instance
vector_db = SimpleVectorDB()

def add_context(text):
    embedding = embed_text(text)
    vector_db.add(text, embedding)

def get_relevant_context(query, top_k=3):
    query_embedding = embed_text(query)
    return "\n---\n".join(vector_db.search(query_embedding, top_k=top_k))