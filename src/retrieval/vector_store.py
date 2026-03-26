import os
from dataclasses import dataclass
from logging import Logger

from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode
from qdrant_client import QdrantClient


@dataclass(slots=True)
class VectorStoreConfig:
    qdrant_url: str = os.getenv("QDRANT_CLUSTER_URL", "")
    qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "")
    collection_name: str = os.getenv("QDRANT_COLLECTION", "multimodal-rag")
    dense_model: str = os.getenv("QDRANT_DENSE_MODEL", "baai/bge-m3")
    sparse_model: str = os.getenv("QDRANT_SPARSE_MODEL", "Qdrant/bm25")
    vector_name: str = os.getenv("QDRANT_VECTOR_NAME", "dense")
    sparse_vector_name: str = os.getenv("QDRANT_SPARSE_VECTOR_NAME", "sparse")


def create_vectorstore(
    config: VectorStoreConfig | None = None,
    logger: Logger | None = None,
) -> tuple[QdrantClient, QdrantVectorStore]:
    config = config or VectorStoreConfig()

    client = QdrantClient(
        url=config.qdrant_url or None,
        api_key=config.qdrant_api_key or None,
    )
    dense = NVIDIAEmbeddings(model=config.dense_model)
    sparse = FastEmbedSparse(model_name=config.sparse_model)

    vectorstore = QdrantVectorStore(
        client=client,
        collection_name=config.collection_name,
        embedding=dense,
        sparse_embedding=sparse,
        retrieval_mode=RetrievalMode.HYBRID,
        vector_name=config.vector_name,
        sparse_vector_name=config.sparse_vector_name,
    )

    if logger is not None:
        points = client.get_collection(config.collection_name).points_count
        logger.info(
            "Vectorstore ready - collection=%s points=%s",
            config.collection_name,
            points,
        )

    return client, vectorstore
