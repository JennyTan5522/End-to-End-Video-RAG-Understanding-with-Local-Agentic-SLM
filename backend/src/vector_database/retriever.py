from qdrant_client import models
import logging
from qdrant_client.models import models
from src.prompt_engineering.templates import rag_output_parser, RAG_QA_PROMPT
from src.llm.inference import generate_qwen_response
from src.vector_database.utils import build_dense_embedding, build_sparse_embedding
import logging

logger = logging.getLogger(__name__)

def query_rag_points(user_query: str, dense_embedding_model, dense_tokenizer, qdrant_client, collection_name: str, limit: int = 10):
    """
    Run hybrid (dense + sparse) retrieval against Qdrant using RRF fusion.

    Args:
        user_query (str): The user question/query.
        dense_tokenizer: Tokenizer instance for the dense model.
        dense_embedding_model: Dense embedding model instance.
        qdrant_client: Initialized QdrantClient.
        collection_name (str): Qdrant collection to search.
        limit (int): Per-branch limit for Prefetch (dense and sparse).

    Returns:
        retrieved_points: Qdrant query result.
    """
    try:
        # Build embeddings
        dense_vector = build_dense_embedding(dense_tokenizer, dense_embedding_model, user_query)
        sparse_vector = build_sparse_embedding(user_query)
    
        # Query Qdrant with RRF fusion
        retrieved_points = qdrant_client.query_points(
            collection_name=collection_name,
            prefetch=[
                models.Prefetch(
                    query=models.SparseVector(indices=sparse_vector.indices, values=sparse_vector.values),
                    using="sparse_embedding",
                    limit=limit
                ),
                models.Prefetch(
                    query=dense_vector,
                    using="dense_embedding",
                    limit=limit
                )
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF)
        )
    
        logger.info(f"Retrieval Points: \n{retrieved_points}")
        return retrieved_points
    except Exception as e:
        logger.error(f"Error while retrieving the related documents from Qdrant Vector Store: {e}")

def build_doc_context(retrieved_points, top_k: int = 5) -> str:
    """
    Build a formatted document context string from retrieved Qdrant points for LLM input.

    Args:
        retrieved_points: Result object from qdrant_client.query_points().
        top_k (int): Number of top retrieved points to include in the context.

    Returns:
        str: A structured string combining summaries, topics, and transcript text.
    """
    try:
        doc_context = ""
    
        for point in retrieved_points.points[:top_k]:
            payload = point.payload
            score = point.score
            summary = payload.get("summary", "")
            text = payload.get("text", "")
            topics = payload.get("topics", "")
            doc_type = payload.get("store_type", "")
    
            context_block = (
                f"### Document Type: {doc_type}\n"
                f"**Relevance Score:** {score:.4f}\n\n"
                f"**Summary:** {summary}\n\n"
                f"**Topics:** {', '.join(topics) if isinstance(topics, list) else topics}\n\n"
                f"**Transcript Text:**\n{text}\n"
                "------------------------------------------------------------\n"
            )
            doc_context += context_block

        logger.info(f"Document Context for LLM: \n{doc_context}")
        return doc_context
    except Exception as e:
        logger.error(f"Error while building the document context: {e}")

def generate_rag_response(doc_context: str, user_query: str, processor, model):
    """
    Generate an LLM response using a RAG-style QA prompt and retrieved document context.

    Args:
        doc_context (str): Formatted text context built from retrieved Qdrant points.
        user_query (str): The user’s question or query.
        processor: The model’s processor/tokenizer for the Qwen model.
        model: The Qwen model instance.

    Returns:
        The generated model response object.
    """
    # Build full system prompt
    complete_prompt = RAG_QA_PROMPT.format(doc_context=doc_context) + rag_output_parser.get_format_instructions()

    # Construct messages
    rag_messages = [
        {
            "role": "system",
            "content": [{"type": "text", "text": complete_prompt}],
        },
        {
            "role": "user",
            "content": [{"type": "text", "text": f"User Query: {user_query}"}],
        },
    ]

    # Generate and return the model response
    response = generate_qwen_response(processor, model, rag_messages)
    parse_response = rag_output_parser.parse(response).response_text
    return parse_response

def get_summary_chunks(qdrant_client, collection_name: str, match_type: str) -> str:
    """
    Retrieve and combine summaries (and topics) from Qdrant based on sequence order.
    
    Args:
        qdrant_client: Active Qdrant client instance.
        collection_name (str): Name of the Qdrant collection.
        match_type (str): The 'type' value to match (e.g., 'txt', 'img').
    
    Returns:
        str: Combined summary string in sequence order.
    """
    # Scroll through collection
    retrieval_record = qdrant_client.scroll(
        collection_name=collection_name,
        scroll_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="type",
                    match=models.MatchValue(value=match_type)
                )
            ]
        ),
    )

    logger.info("\nRetrieval Points:")
    retrieval_points = retrieval_record[0]
    logger.info(retrieval_points)

    # Sort by sequence index
    sorted_retrieval_points = sorted(
        retrieval_points, key=lambda p: p.payload.get("sequence_index", 0)
    )

    logger.info("\nCheck (sorted by sequence index):")

    # Build combined summaries + topics
    txt_summary_chunks = []
    for idx, point in enumerate(sorted_retrieval_points, start=1):
        payload = point.payload
        summary = payload.get("summary", "").strip()
        topics = payload.get("topics", [])
        seq_index = payload.get("sequence_index", idx)

        formatted = f"[Seq {seq_index}] {summary}\nTopics: {', '.join(topics)}"
        txt_summary_chunks.append(formatted)
        logger.info(f" Seq {seq_index} | Chunk {idx}:\n{formatted}\n")

    logger.info("\nSummary Chunks (in sequence order):")
    logger.info(txt_summary_chunks)

    return "\n\n".join(txt_summary_chunks)
