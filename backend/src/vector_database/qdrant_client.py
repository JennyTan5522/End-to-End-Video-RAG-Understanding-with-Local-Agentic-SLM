"""
Qdrant Client Initialization and Collection Management
Handles connection to Qdrant vector database and collection operations
"""
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, SparseVectorParams, SparseIndexParams
import logging

logger = logging.getLogger(__name__)


def get_qdrant_client(url: str = "http://localhost:6333", prefer_grpc: bool = True) -> QdrantClient:
    """
    Initialize and return a Qdrant client
    
    Args:
        url: URL of the Qdrant service (default: "http://localhost:6333")
        prefer_grpc: Whether to use gRPC for faster communication (default: True)
    
    Returns:
        QdrantClient: Initialized Qdrant client instance
    """
    try:
        qdrant_client = QdrantClient(url=url, prefer_grpc=prefer_grpc)
        logger.info(f"Connected to Qdrant successfully at {url}")
        return qdrant_client
    except Exception as e:
        logger.error(f"Failed to connect to Qdrant at {url}: {e}")
        raise ConnectionError(f"Failed to connect to Qdrant: {e}")


def get_or_create_collection(qdrant_client: QdrantClient, collection_name: str, dense_vector_size: int = 384) -> bool:
    """
    Ensure that a Qdrant collection exists; create if not found
    
    Supports both dense and sparse embeddings for hybrid retrieval.
    
    Args:
        qdrant_client: Active Qdrant client instance
        collection_name: Name of the collection to check or create
        dense_vector_size: Size of dense embedding vectors (default: 384)
    
    Returns:
        bool: True if collection exists or was created successfully
    """
    try:
        # Retrieve all existing collections
        existing = [c.name for c in qdrant_client.get_collections().collections]

        # Create collection if it doesn't exist
        if collection_name not in existing:
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config={
                    "dense_embedding": VectorParams(
                        size=dense_vector_size, 
                        distance=Distance.COSINE
                    )
                },
                sparse_vectors_config={
                    "sparse_embedding": SparseVectorParams(
                        index=SparseIndexParams(on_disk=False)
                    )
                },
            )
            logger.info(f"Collection '{collection_name}' created successfully")
        else:
            logger.info(f"Collection '{collection_name}' already exists")

        return True
    except Exception as e:
        logger.error(f"Error ensuring collection '{collection_name}': {e}")
        raise

def delete_collection(qdrant_client: QdrantClient, collection_name: str) -> bool:
    """
    Delete a Qdrant collection
    
    Args:
        qdrant_client: Active Qdrant client instance
        collection_name: Name of the collection to delete
    
    Returns:
        bool: True if deletion was successful
    """
    try:
        qdrant_client.delete_collection(collection_name=collection_name)
        logger.info(f"Collection '{collection_name}' deleted successfully")
        return True
    except Exception as e:
        logger.error(f"Error deleting collection '{collection_name}': {e}")
        return False

def collection_exists(qdrant_client: QdrantClient, collection_name: str) -> bool:
    """
    Check if a collection exists in Qdrant
    
    Args:
        qdrant_client: Active Qdrant client instance
        collection_name: Name of the collection to check
    
    Returns:
        bool: True if collection exists
    """
    try:
        existing = [c.name for c in qdrant_client.get_collections().collections]
        return collection_name in existing
    except Exception as e:
        logger.error(f"Error checking collection '{collection_name}': {e}")
        return False

# Clean imports from the module
# from src.vector_store import (
#     get_qdrant_client,
#     get_or_create_collection,
#     build_hybrid_embeddings,
#     build_qdrant_point,
#     upsert_qdrant_points,
#     search_qdrant
# )

# # Initialize client and collection
# client = get_qdrant_client()
# get_or_create_collection(client, "video_transcripts", vector_size=384)

# # Generate embeddings
# embeddings = build_hybrid_embeddings(tokenizer, model, "AI tutorial")

# # Create and upload point
# point = build_qdrant_point(
#     dense_vector=embeddings['dense'],
#     sparse_vector=embeddings['sparse'],
#     text="AI tutorial",
#     metadata={'source': 'youtube', 'duration': 120}
# )
# upsert_qdrant_points(client, "video_transcripts", [point])

# # Search
# results = search_qdrant(client, "video_transcripts", embeddings['dense'], limit=5)