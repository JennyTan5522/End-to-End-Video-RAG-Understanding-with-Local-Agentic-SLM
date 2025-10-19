"""
Vector Store Operations for Qdrant
Handles point creation, upserting, and semantic search operations
"""
from qdrant_client.models import PointStruct
from langchain_qdrant import FastEmbedSparse
from src.vector_database.qdrant_client import get_or_create_collection
from uuid import uuid4
import torch
import logging

logger = logging.getLogger(__name__)

def build_dense_embedding(tokenizer, dense_embedding_model, text: str) -> list[float]:
    """
    Generate dense vector embedding using Hugging Face transformer model
    
    Args:
        tokenizer: Model tokenizer for text preprocessing
        dense_embedding_model: Loaded transformer model (e.g., BGE, E5)
        text: Input text to encode
    
    Returns:
        list[float]: Normalized dense embedding vector
    """
    inputs = tokenizer(text, padding=True, truncation=True, return_tensors="pt")
    
    with torch.no_grad():
        outputs = dense_embedding_model(**inputs)
    
    embeddings = outputs.last_hidden_state.mean(dim=1)
    embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
    
    return embeddings[0].tolist()

def build_sparse_embedding(text: str) -> dict:
    """
    Generate sparse BM25 embedding for text
    
    Args:
        text: Input text to embed
    
    Returns:
        dict: Sparse embedding with 'indices' and 'values' attributes
    """
    sparse_embedding_model = FastEmbedSparse(model_name="Qdrant/bm25")
    embeddings = sparse_embedding_model.embed_query(text)
    return embeddings

def build_qdrant_point(dense_vector: list[float], sparse_vector: dict, payload: dict) -> PointStruct:
    """
    Create Qdrant point with hybrid dense and sparse vectors
    
    Args:
        dense_vector: Dense embedding vector (e.g., 384-dim from BGE)
        sparse_vector: Sparse embedding with 'indices' and 'values' attributes
        payload: Metadata dictionary to store with the point
    
    Returns:
        PointStruct: Qdrant point ready for upload
        
    Raises:
        Exception: If point creation fails
    """
    try:
        point = PointStruct(
            id=str(uuid4()),
            vector={
                "dense_embedding": dense_vector,
                "sparse_embedding": {
                    "indices": sparse_vector.indices,
                    "values": sparse_vector.values,
                },
            },
            payload=payload
        )
        return point
    except Exception as e:
        logger.error(f"Failed to build Qdrant point: {e}")
        raise

def upsert_qdrant_points(qdrant_client, collection_name: str, points: list[PointStruct]) -> None:
    """
    Upload or update points in Qdrant collection
    
    Args:
        qdrant_client: Initialized Qdrant client instance
        collection_name: Target collection name
        points: List of PointStruct objects to upsert
        
    Raises:
        Exception: If upsert operation fails
    """
    try:
        qdrant_client.upsert(
            collection_name=collection_name,
            points=points,
        )
        logger.info(f"Successfully upserted {len(points)} points to '{collection_name}'")
    except Exception as e:
        logger.error(f"Failed to upsert points to '{collection_name}': {e}")
        raise

def index_chunks_to_qdrant(qdrant_client, collection_name: str, summary_chunks: list[dict], dense_tokenizer, dense_embedding_model) -> int:
    """
    Index transcript/image chunks into Qdrant with hybrid embeddings
    
    Args:
        qdrant_client: Initialized Qdrant client
        collection_name: Target collection name
        summary_chunks: List of dicts with 'text', 'summary', 'topics' keys
        dense_tokenizer: Tokenizer for dense embedding model
        dense_embedding_model: Loaded dense embedding model
    
    Returns:
        int: Number of successfully indexed chunks
        
    Note:
        Creates collection if it doesn't exist
        
    Raises:
        Exception: If collection creation or indexing fails
    """
    try:
        get_or_create_collection(qdrant_client, collection_name)
    except Exception as e:
        logger.error(f"Failed to create or get collection '{collection_name}': {e}")
        raise
    
    logger.info(f"Building Qdrant points for collection '{collection_name}'")
    
    qdrant_points = []
    total_chunks = len(summary_chunks)
    failed_chunks = 0
    
    for i, chunk in enumerate(summary_chunks, 1):
        try:
            text = chunk.get("text", "")
            summary = chunk.get("summary", "")
            topics = chunk.get("topics", [])
            
            embed_text = f"Summary: {summary}\nTopics: {', '.join(topics)}\n---\n{text}"
            
            # Build embeddings with error handling
            try:
                dense_vector = build_dense_embedding(dense_tokenizer, dense_embedding_model, embed_text)
            except Exception as e:
                logger.error(f"Failed to build dense embedding for chunk {i}/{total_chunks}: {e}")
                failed_chunks += 1
                continue
            
            try:
                sparse_vector = build_sparse_embedding(embed_text)
            except Exception as e:
                logger.error(f"Failed to build sparse embedding for chunk {i}/{total_chunks}: {e}")
                failed_chunks += 1
                continue
            
            payload = {
                "text": embed_text,
                "summary": summary,
                "topics": topics,
            }
            
            try:
                point = build_qdrant_point(dense_vector, sparse_vector, payload)
                qdrant_points.append(point)
                logger.debug(f"Built point {i}/{total_chunks} with topics: {topics}")
            except Exception as e:
                logger.error(f"Failed to build Qdrant point for chunk {i}/{total_chunks}: {e}")
                failed_chunks += 1
                continue
                
        except Exception as e:
            logger.error(f"Unexpected error processing chunk {i}/{total_chunks}: {e}")
            failed_chunks += 1
            continue
    
    if not qdrant_points:
        error_msg = f"No valid points created. All {total_chunks} chunks failed to process."
        logger.error(error_msg)
        raise Exception(error_msg)
    
    if failed_chunks > 0:
        logger.warning(f"Failed to process {failed_chunks}/{total_chunks} chunks")
    
    try:
        logger.info(f"Upserting {len(qdrant_points)} points to '{collection_name}'")
        upsert_qdrant_points(qdrant_client, collection_name, qdrant_points)
    except Exception as e:
        logger.error(f"Failed to upsert points to '{collection_name}': {e}")
        raise
    
    logger.info(f"Successfully indexed {len(qdrant_points)}/{total_chunks} chunks to Qdrant")
    return len(qdrant_points)