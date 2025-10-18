"""
Load hugging face embedding models
"""
from transformers import AutoModel, AutoTokenizer

def load_embedding_model(model_name: str):
    """
    Load embedding model and tokenizer

    Args:
        model_name: Hugging Face embedding model (e.g., 'BAAI/bge-small-en-v1.5')

    Returns:
        tuple: (model, tokenizer) - Loaded embedding model and tokenizer
    """
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)

    return model, tokenizer
    