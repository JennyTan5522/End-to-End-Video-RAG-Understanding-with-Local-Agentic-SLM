import asyncio
import logging
from typing import Optional
from src.vector_database.qdrant_client import get_qdrant_client
from src.vector_database.utils import query_rag_points, build_doc_context, generate_rag_response
from src.llm.model_loader import model_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_rag(user_query: str, collection_name: str) -> Optional[str]:
    """
    Run RAG process: load models, query vector DB, generate response
    
    Args:
        user_query: The user's question
        collection_name: Name of the Qdrant collection to query
        
    Returns:
        str: Generated response from RAG pipeline, or None if failed
    """
    try:
        logger.info("=" * 80)
        logger.info("STARTING RAG PIPELINE")
        logger.info("=" * 80)
        logger.info(f"User Query: '{user_query}'")
        logger.info(f"Collection: '{collection_name}'")
        
        # Load models
        logger.info("Loading AI models...")
        try:
            await model_manager.load_models()
            logger.info("Models loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load models: {str(e)}", exc_info=True)
            raise RuntimeError(f"Model loading failed: {str(e)}")
        
        # Initialize Qdrant client
        logger.info("Initializing Qdrant client...")
        try:
            qdrant_client = get_qdrant_client()
            logger.info("Qdrant client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {str(e)}", exc_info=True)
            raise RuntimeError(f"Qdrant initialization failed: {str(e)}")
        
        # Get embedding model
        logger.info("Retrieving embedding model...")
        try:
            dense_embedding_model, dense_embedding_tokenizer = model_manager.get_embedding_model()
        except Exception as e:
            logger.error(f"Failed to get embedding model: {str(e)}", exc_info=True)
            raise RuntimeError(f"Embedding model retrieval failed: {str(e)}")
        
        # Query vector database
        logger.info("Querying vector database...")
        try:
            retrieved_points = query_rag_points(
                user_query, 
                dense_embedding_model, 
                dense_embedding_tokenizer, 
                qdrant_client, 
                collection_name
            )
            
            if not retrieved_points:
                logger.warning("No relevant documents found in vector database")
                return "I couldn't find any relevant information to answer your question."
            
            logger.info(f"Retrieval Points: \n{retrieved_points}")
            
        except Exception as e:
            logger.error(f"Vector database query failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"Vector search failed: {str(e)}")
        
        # Build document context
        logger.info("Building document context...")
        try:
            doc_context = build_doc_context(retrieved_points)
            logger.info(f"Document context built ({len(doc_context)} characters)")
        except Exception as e:
            logger.error(f"Failed to build document context: {str(e)}", exc_info=True)
            raise RuntimeError(f"Context building failed: {str(e)}")
        
        # Get vision model
        logger.info("Retrieving vision model for response generation...")
        try:
            qwen_vision_processor, qwen_vision_chat_model = model_manager.get_qwen_vision_model()
            logger.info("Vision model retrieved")
        except Exception as e:
            logger.error(f"Failed to get vision model: {str(e)}", exc_info=True)
            raise RuntimeError(f"Vision model retrieval failed: {str(e)}")
        
        # Generate response
        logger.info("Generating RAG response...")
        try:
            response = generate_rag_response(
                doc_context, 
                user_query, 
                qwen_vision_processor, 
                qwen_vision_chat_model
            )
            
            if not response or response.strip() == "":
                logger.warning("Generated response is empty")
                return "I'm sorry, I couldn't generate a meaningful response."
            
            logger.info("Response generated successfully")
            logger.info(f"Response length: {len(response)} characters")
            
        except Exception as e:
            logger.error(f"Response generation failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"Response generation failed: {str(e)}")
        
        logger.info("=" * 80)
        logger.info("RAG PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        
        return response
        
    except RuntimeError as e:
        # Re-raise RuntimeError (already logged above)
        logger.error(f"RAG pipeline failed: {str(e)}")
        return None
        
    except Exception as e:
        # Catch any unexpected errors
        logger.error(f"Unexpected error in RAG pipeline: {str(e)}", exc_info=True)
        return None


if __name__ == "__main__":
    try:
        logger.info("Starting RAG test script...")
        
        # Input parameters
        user_query = "Generate summary on the Friday meeting"
        collection_name = "20251020_093928_weekly_meeting"
        
        # Validate inputs
        if not user_query or user_query.strip() == "":
            logger.error("User query is empty!")
            exit(1)
        
        if not collection_name or collection_name.strip() == "":
            logger.error("Collection name is empty!")
            exit(1)
        
        # Run RAG pipeline
        rag_response = asyncio.run(run_rag(user_query, collection_name))
        
        # Display results
        if rag_response:
            logger.info("=" * 80)
            logger.info("RAG RESPONSE:")
            logger.info("=" * 80)
            print(rag_response)
            logger.info("=" * 80)
        else:
            logger.error("RAG pipeline returned no response")
            exit(1)
            
    except KeyboardInterrupt:
        logger.info("Script interrupted by user (Ctrl+C)")
        exit(0)
        
    except Exception as e:
        logger.error(f"Fatal error in main: {str(e)}", exc_info=True)
        exit(1)