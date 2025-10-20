from langchain_core.messages import AIMessage
from langgraph.graph import MessagesState, END
from langgraph.types import Command
from src.vector_database.retriever import query_rag_points, build_doc_context, generate_rag_response
from src.llm.model_loader import model_manager
import logging

logger = logging.getLogger(__name__)

class RAGAgent:
    """
    Agent for handling RAG-based question answering.
    
    This agent retrieves relevant context from the vector database (Qdrant)
    and generates responses based on the retrieved information.
    
    Attributes:
        qdrant_client: Qdrant client for vector search
        collection_name: Name of the collection to query
    """
    
    def __init__(self, qdrant_client, collection_name: str):
        """
        Initialize the RAGAgent.
        
        Args:
            qdrant_client: The Qdrant client instance
            collection_name: The name of the collection to query in Qdrant
        """
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name
        logger.info(f"RAGAgent initialized for collection: '{collection_name}'")

    def rag_node(self, state: MessagesState):
        """
        Process a user query using RAG (Retrieval-Augmented Generation).
        
        Args:
            state: The current messages state containing the user's query.
            
        Returns:
            Command: Updated state with AI response and routing to END.
        """
        logger.info("="*80)
        logger.info("RAG AGENT - Processing Request")
        logger.info("="*80)
        
        try:
            # Extract user message
            user_message = state['messages'][-1].content if state.get('messages') else 'N/A'
            logger.info(f"User Query: {user_message}")
            
            # Get embedding model
            try:
                dense_embedding_model, dense_embedding_tokenizer = model_manager.get_embedding_model()
            except Exception as e:
                logger.error(f"Failed to get embedding model: {str(e)}")
                error_msg = "I'm having trouble loading the AI models. Please try again later."
                state["messages"].append(AIMessage(content=error_msg))
                return Command(update={"messages": state["messages"]}, goto=END)
            
            # Query vector database
            logger.info(f"Querying vector database in collection '{self.collection_name}'...")
            try:
                retrieved_points = query_rag_points(
                    user_message,
                    dense_embedding_model,
                    dense_embedding_tokenizer,
                    self.qdrant_client,
                    self.collection_name
                )
            except Exception as e:
                logger.error(f"Failed to query vector database: {str(e)}", exc_info=True)
                error_msg = "I'm having trouble accessing the knowledge base. Please try again later."
                state["messages"].append(AIMessage(content=error_msg))
                return Command(update={"messages": state["messages"]}, goto=END)
            
            # Build document context
            try:
                doc_context = build_doc_context(retrieved_points)
                logger.info(f"Document context built ({len(doc_context)} characters)")
            except Exception as e:
                logger.error(f"Failed to build document context: {str(e)}", exc_info=True)
                error_msg = "An error occurred while processing the retrieved information."
                state["messages"].append(AIMessage(content=error_msg))
                return Command(update={"messages": state["messages"]}, goto=END)
            
            # Get vision model for response generation
            try:
                qwen_vision_processor, qwen_vision_chat_model = model_manager.get_qwen_vision_model()
            except Exception as e:
                logger.error(f"Failed to get vision model: {str(e)}")
                error_msg = "I'm having trouble loading the response generation model."
                state["messages"].append(AIMessage(content=error_msg))
                return Command(update={"messages": state["messages"]}, goto=END)
            
            # Generate RAG response
            logger.info("Generating RAG response...")
            try:
                response = generate_rag_response(
                    doc_context,
                    user_message,
                    qwen_vision_processor,
                    qwen_vision_chat_model
                )
            except Exception as e:
                logger.error(f"Failed to generate RAG response: {str(e)}", exc_info=True)
                error_msg = "An error occurred while generating the response."
                state["messages"].append(AIMessage(content=error_msg))
                return Command(update={"messages": state["messages"]}, goto=END)
            
            # Validate response
            if not response or not response.strip():
                logger.warning("Generated response is empty")
                response = "I'm sorry, I couldn't generate a meaningful response based on the available information."
            
            logger.info(f"RAG response generated: {response[:100]}...")
            
            # Append response to state
            state["messages"].append(AIMessage(content=response))
            logger.info("Appended AI response to messages state")
            return Command(update={"messages": state["messages"]}, goto=END)
            
        except Exception as e:
            logger.error(f"RAG agent encountered an error: {str(e)}", exc_info=True)
            error_message = "An error occurred while processing your request. Please try again."
            state["messages"].append(AIMessage(content=error_message))
            return Command(update={"messages": state["messages"]}, goto=END)
