import chromadb
from chromadb.utils.embedding_functions.ollama_embedding_function import (
    OllamaEmbeddingFunction,
)

from ..config import CHROMA_DIR, EMBED_MODEL, OLLAMA_HOST, RAG_COLLECTION


def get_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=RAG_COLLECTION,
        embedding_function=OllamaEmbeddingFunction(url=OLLAMA_HOST, model_name=EMBED_MODEL),
    )
