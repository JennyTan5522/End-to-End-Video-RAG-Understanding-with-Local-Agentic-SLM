"""
Embedding Generation for Vector Search
Creates dense, and sparse embeddings for Qdrant storage
"""
import torch
from fastembed import SparseTextEmbedding as FastEmbedSparse
import logging

logger = logging.getLogger(__name__)

def build_dense_embedding(tokenizer, dense_embedding_model, text: str) -> list[float]:
    """
    Generate a dense vector embedding for given text
    
    Args:
        tokenizer: Tokenizer corresponding to the model
        dense_embedding_model: Transformer model instance (e.g., BGE, E5)
        text: Input text to encode
    
    Returns:
        list[float]: Normalized dense embedding vector
        
    Example:
        >>> from transformers import AutoModel, AutoTokenizer
        >>> model = AutoModel.from_pretrained("BAAI/bge-small-en-v1.5")
        >>> tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-small-en-v1.5")
        >>> embedding = build_dense_embedding(tokenizer, model, "Hello world")
        >>> len(embedding)  # 384
    """
    try:
        # Tokenize input text
        inputs = tokenizer(
            text, 
            padding=True, 
            truncation=True, 
            return_tensors="pt",
            max_length=512
        )

        # Generate embeddings without gradients
        with torch.no_grad():
            outputs = dense_embedding_model(**inputs)

        # Mean pooling over token embeddings
        embeddings = outputs.last_hidden_state.mean(dim=1)

        # L2 normalization
        embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

        return embeddings[0].tolist()
    except Exception as e:
        logger.error(f"Error building dense embedding: {e}")
        raise

def build_sparse_embedding(text: str) -> dict:
    """
    Generate a sparse embedding (BM25-based) for given text
    
    Uses Qdrant's BM25 model for term-based sparse vectors suitable
    for keyword matching in hybrid search.
    
    Args:
        text: Input text to embed
    
    Returns:
        dict: Sparse embedding with 'indices' and 'values' keys
        
    Example:
        >>> sparse_emb = build_sparse_embedding("machine learning")
        >>> print(sparse_emb.keys())  # dict_keys(['indices', 'values'])
    """
    try:
        sparse_embedding_model = FastEmbedSparse(model_name="Qdrant/bm25")
        embeddings = sparse_embedding_model.embed_query(text)
        return embeddings
    except Exception as e:
        logger.error(f"Error building sparse embedding: {e}")
        raise