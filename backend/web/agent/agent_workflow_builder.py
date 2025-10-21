import logging
from pathlib import Path
from langchain_core.messages import AIMessage
from langgraph.graph import MessagesState, StateGraph, START, END
from web.agent.supervisor_agent import WorkflowSupervisor
from web.agent.general_question_agent import GeneralQuestionAgent
from web.agent.audio_extraction_agent import ExtractAudioFromVideoAgent
from web.agent.frame_extraction_agent import ExtractVideoFramesAgent
from web.agent.summary_agent import SummaryAgent
from web.agent.rag_agent import RAGAgent
from web.agent.report_agent import ReportAgent
from web.mcp_tools.audio_extractor import chunk_transcript_text, summarize_transcript_chunks
from web.mcp_tools.video_frames_extractor import summarize_frame_groups
from src.llm.model_loader import model_manager
from src.vector_database.qdrant_client import get_qdrant_client
from src.vector_database.utils import index_chunks_to_qdrant

logger = logging.getLogger(__name__)

# Global dictionary to store collection names per session
session_collections = {}

def get_collection_name_for_session(session_id: str) -> str:
    """
    Get the collection name for a given session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Collection name if exists, None otherwise
    """
    collection_name = session_collections.get(session_id)
    if collection_name:
        logger.info(f"Retrieved collection name '{collection_name}' for session '{session_id}'")
    else:
        logger.warning(f"No collection name found for session '{session_id}'")
    return collection_name

def set_collection_name_for_session(session_id: str, collection_name: str):
    """
    Store the collection name for a given session.
    
    Args:
        session_id: Session identifier
        collection_name: Name of the Qdrant collection
    """
    session_collections[session_id] = collection_name
    logger.info(f"Stored collection name '{collection_name}' for session '{session_id}'")

async def invoke_summary_agent(session_id: str = "default", user_query: str = "Please provide a summary of the video"):
    """
    Invoke the summary agent for a specific session's video collection.
    
    This function should only be called after video processing is complete
    and the collection has been created in Qdrant.
    
    Args:
        session_id: Session identifier to look up the collection name
        user_query: Optional custom query for summarization
        
    Returns:
        Summary response from the agent
    """
    logger.info("="*80)
    logger.info(f"INVOKING SUMMARY AGENT for session: '{session_id}'")
    logger.info("="*80)
    
    try:
        # Get collection name for this session
        collection_name = get_collection_name_for_session(session_id)
        
        if not collection_name:
            error_msg = f"No video has been processed for session '{session_id}'. Please upload and process a video first."
            logger.error(error_msg)
            return {
                "messages": [AIMessage(content=error_msg)]
            }
        
        logger.info(f"Using collection: '{collection_name}'")
        
        if not model_manager.is_loaded:
            raise RuntimeError("Models not loaded. Ensure server started correctly.")
        
        model = model_manager.get_qwen_chat_model()
        qdrant_client = get_qdrant_client()
        
        # Initialize SummaryAgent with the specific collection name
        summary_agent = SummaryAgent(model, qdrant_client, collection_name=collection_name)
        logger.info(f"SummaryAgent initialized for collection: '{collection_name}'")
        
        # Build summary workflow
        summary_agent_graph = StateGraph(MessagesState)
        summary_agent_graph.add_node("summary_node", summary_agent.summary_node)
        summary_agent_graph.add_edge(START, "summary_node")
        summary_agent_graph.add_edge("summary_node", END)
        summary_agent_workflow = summary_agent_graph.compile()
        
        # Invoke the summary workflow
        result = await summary_agent_workflow.ainvoke({
            "messages": [{"role": "user", "content": user_query}]
        })
        
        logger.info("Summary agent invocation completed")
        return result
        
    except Exception as e:
        logger.error(f"Failed to invoke summary agent: {str(e)}", exc_info=True)
        raise

def create_summary_workflow_node(session_id: str):
    """
    Create a summary workflow node function for a specific session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        An async function that can be used as a workflow node
    """
    async def summary_workflow_node(state: MessagesState):
        """Node function for summary workflow"""
        user_query = state['messages'][-1].content if state.get('messages') else "Please provide a summary of the video"
        result = await invoke_summary_agent(session_id=session_id, user_query=user_query)
        return result
    
    return summary_workflow_node

def create_rag_workflow_node(session_id: str):
    """
    Create a RAG workflow node function for a specific session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        An async function that can be used as a workflow node
    """
    async def rag_workflow_node(state: MessagesState):
        """Node function for RAG workflow"""
        # Get collection name for this session
        collection_name = get_collection_name_for_session(session_id)
        
        if not collection_name:
            error_msg = f"No video has been processed for session '{session_id}'. Please upload and process a video first."
            logger.error(error_msg)
            return {
                "messages": state['messages'] + [AIMessage(content=error_msg)]
            }
        
        logger.info(f"RAG workflow using collection: '{collection_name}'")
        
        # Initialize RAG Agent with the specific collection name
        qdrant_client = get_qdrant_client()
        rag_agent = RAGAgent(qdrant_client, collection_name=collection_name)
        
        # Invoke RAG agent
        result = rag_agent.rag_node(state)
        return result
    
    return rag_workflow_node

def create_report_workflow_node(session_id: str):
    """
    Create a report workflow node function for a specific session.
    
    This workflow chains: summary_node → report_node
    The report agent converts the summary into a PDF report.
    
    Args:
        session_id: Session identifier
        
    Returns:
        An async function that can be used as a workflow node
    """
    async def report_workflow_node(state: MessagesState):
        """Node function for report workflow"""
        logger.info("=" * 80)
        logger.info(f"INVOKING REPORT WORKFLOW for session: '{session_id}'")
        logger.info("=" * 80)
        
        # Get collection name for this session
        collection_name = get_collection_name_for_session(session_id)
        
        if not collection_name:
            error_msg = f"No video has been processed for session '{session_id}'. Please upload and process a video first."
            logger.error(error_msg)
            return {
                "messages": state['messages'] + [AIMessage(content=error_msg)]
            }
        
        logger.info(f"Report workflow using collection: '{collection_name}'")
        
        # Step 1: Generate summary using SummaryAgent
        logger.info("Step 1: Generating summary...")
        
        if not model_manager.is_loaded:
            raise RuntimeError("Models not loaded. Ensure server started correctly.")
        
        model = model_manager.get_qwen_chat_model()
        qdrant_client = get_qdrant_client()
        
        summary_agent = SummaryAgent(model, qdrant_client, collection_name=collection_name)
        
        # Build and invoke summary workflow
        summary_graph = StateGraph(MessagesState)
        summary_graph.add_node("summary_node", summary_agent.summary_node)
        summary_graph.add_edge(START, "summary_node")
        summary_graph.add_edge("summary_node", END)
        summary_workflow = summary_graph.compile()
        
        user_query = state['messages'][-1].content if state.get('messages') else "Please generate a report"
        summary_result = await summary_workflow.ainvoke({
            "messages": [{"role": "user", "content": user_query}]
        })
        
        logger.info("Summary generation complete")
        
        # Step 2: Convert summary to PDF report using ReportAgent
        logger.info("Step 2: Converting summary to PDF report...")
        
        report_agent = ReportAgent(llm=model, collection_name=collection_name)
        
        # Build and invoke report workflow with summary result
        report_graph = StateGraph(MessagesState)
        report_graph.add_node("report_node", report_agent.report_node)
        report_graph.add_edge(START, "report_node")
        report_graph.add_edge("report_node", END)
        report_workflow = report_graph.compile()
        
        # Pass the summary result to report agent
        report_result = await report_workflow.ainvoke({
            "messages": summary_result["messages"]
        })
        
        logger.info("Report generation complete")
        logger.info("=" * 80)
        
        return report_result
    
    return report_workflow_node

async def build_agent_workflow(user_request: str, session_id: str = "default"):
    """
    Main async function to build and run the workflow.
    
    Initializes all agents, builds workflow graphs, and executes the user request
    through the appropriate workflow pipeline.
    
    Args:
        user_request: The user's natural language request.
        session_id: Session identifier to track collection names.
        
    Returns:
        The compiled workflow application.
    """
    logger.info("Initializing main workflow")
    logger.info(f"User request: '{user_request}'")
    logger.info(f"Session ID: '{session_id}'")
    
    try:      
        if not model_manager.is_loaded:
            raise RuntimeError("Models not loaded. Ensure server started correctly.")
        
        model = model_manager.get_qwen_chat_model()
        qdrant_client = get_qdrant_client()
        logger.debug("Core components initialized")
        
        qwen_vision_processor, qwen_vision_chat_model = model_manager.get_qwen_vision_model()
        dense_embedding_model, dense_embedding_tokenizer = model_manager.get_embedding_model()

        supervisor = WorkflowSupervisor(model)
        general_question_agent = GeneralQuestionAgent(model)
        extract_audio_from_video_agent = ExtractAudioFromVideoAgent(model)
        extract_video_frames_agent = ExtractVideoFramesAgent(model)
        # Note: SummaryAgent will be created dynamically based on session's collection
        logger.info("All agents initialized successfully")

        # Build general question workflow (subgraph)
        logger.debug("Building general question workflow...")
        general_agent_graph = StateGraph(MessagesState)
        general_agent_graph.add_node("general_question_workflow", general_question_agent.general_question_node)
        general_agent_graph.add_edge(START, "general_question_workflow")
        general_agent_graph.add_edge("general_question_workflow", END)
        general_agent_workflow = general_agent_graph.compile()

        # Build video frame processing workflow (subgraph)
        logger.debug("Building frame processing workflow...")
        frame_processing_agent_graph = StateGraph(MessagesState)
        frame_processing_agent_graph.add_node("extract_frames_from_video", extract_video_frames_agent.extract_frames_node)
        frame_processing_agent_graph.add_edge(START, "extract_frames_from_video")
        extract_frames_from_video_workflow = frame_processing_agent_graph.compile()

        # Build audio processing workflow (subgraph)
        logger.debug("Building audio processing workflow...")
        audio_processing_agent_graph = StateGraph(MessagesState)
        audio_processing_agent_graph.add_node("extract_audio_from_video", extract_audio_from_video_agent.extract_audio_node)
        audio_processing_agent_graph.add_node("transcript_audio_node", extract_audio_from_video_agent.transcribe_audio_node)
        audio_processing_agent_graph.add_edge(START, "extract_audio_from_video")
        audio_processing_agent_graph.add_edge("extract_audio_from_video", "transcript_audio_node")
        audio_processing_agent_graph.add_edge("transcript_audio_node", END)
        audio_processing_agent_workflow = audio_processing_agent_graph.compile()

        # Build summary workflow (subgraph) - uses session_id to find collection
        logger.debug("Building summary workflow...")
        summary_workflow_node = create_summary_workflow_node(session_id)
        summary_agent_graph = StateGraph(MessagesState)
        summary_agent_graph.add_node("summary_node", summary_workflow_node)
        summary_agent_graph.add_edge(START, "summary_node")
        summary_agent_graph.add_edge("summary_node", END)
        summary_agent_workflow = summary_agent_graph.compile()
        logger.debug("Summary workflow compiled")

        # Build RAG workflow (subgraph) - uses session_id to find collection
        logger.debug("Building RAG workflow...")
        rag_workflow_node = create_rag_workflow_node(session_id)
        rag_agent_graph = StateGraph(MessagesState)
        rag_agent_graph.add_node("rag_node", rag_workflow_node)
        rag_agent_graph.add_edge(START, "rag_node")
        rag_agent_graph.add_edge("rag_node", END)
        rag_agent_workflow = rag_agent_graph.compile()
        logger.debug("RAG workflow compiled")

        # Build report workflow (subgraph) - chains summary → report → PDF
        logger.debug("Building report workflow...")
        report_workflow_node = create_report_workflow_node(session_id)
        report_agent_graph = StateGraph(MessagesState)
        report_agent_graph.add_node("report_node", report_workflow_node)
        report_agent_graph.add_edge(START, "report_node")
        report_agent_graph.add_edge("report_node", END)
        report_agent_workflow = report_agent_graph.compile()
        logger.debug("Report workflow compiled")

        # Build main graph
        logger.debug("Building main workflow graph...")
        main_graph = StateGraph(MessagesState)
        main_graph.add_node("supervisor", supervisor.supervisor_node)
        main_graph.add_node("general_question_workflow", general_agent_workflow)
        main_graph.add_node("frame_processing_workflow", extract_frames_from_video_workflow)
        main_graph.add_node("audio_processing_workflow", audio_processing_agent_workflow)
        main_graph.add_edge("frame_processing_workflow", "audio_processing_workflow")
        main_graph.add_node("summary_workflow", summary_agent_workflow)
        main_graph.add_node("rag_workflow", rag_agent_workflow)
        main_graph.add_node("report_workflow", report_agent_workflow)

        # Add edges
        main_graph.add_edge(START, "supervisor")
        app = main_graph.compile()
        logger.info("Main workflow graph compiled successfully")
        
        logger.info("Invoking workflow with user request...")
        result = await app.ainvoke({"messages": [{"role": "user", "content": user_request}]})

        # Extract results from messages state
        logger.info("Extracting workflow results...")
        frame_group_folder_path = None
        transcript_file_path = None
        video_name = None

        logger.info(result["messages"])
        
        # Traverse messages in reverse to find the latest results
        for message in reversed(result["messages"]):
            if isinstance(message, AIMessage) and isinstance(message.content, list):
                message_data = message.content[0] if len(message.content) > 0 else {}
                
                # Extract frame group path if available
                if "frame_group_folder_path" in message_data and frame_group_folder_path is None:
                    frame_group_folder_path = message_data["frame_group_folder_path"]
                    logger.info(f"Found frame group folder: '{frame_group_folder_path}'")
                
                # Extract transcript path if available
                if "transcript_file_path" in message_data and transcript_file_path is None:
                    transcript_file_path = message_data["transcript_file_path"]
                    video_name = message_data["video_name"]
                    logger.info(f"Found transcript file: '{transcript_file_path}'")
                    logger.info(f"Video name: '{video_name}'")
                
                # Break if we have both
                if frame_group_folder_path and transcript_file_path:
                    break
        
        # Process transcript chunks if available
        collection_name = video_name
        if video_name and transcript_file_path:
            logger.info("="*80)
            logger.info("PROCESSING TRANSCRIPT")
            logger.info("="*80)
            
            try:
                transcript_chunks = chunk_transcript_text(transcript_file_path)
                logger.info(f"Chunked transcript into {len(transcript_chunks)} chunks")
                
                transcript_summary_chunks = summarize_transcript_chunks(
                    transcript_chunks, 
                    qwen_vision_processor, 
                    qwen_vision_chat_model
                )
                logger.info(f"Summarized {len(transcript_summary_chunks)} transcript chunks")
                
                index_chunks_to_qdrant(
                    qdrant_client=qdrant_client,
                    collection_name=collection_name,
                    summary_chunks=transcript_summary_chunks,
                    dense_tokenizer=dense_embedding_tokenizer,
                    dense_embedding_model=dense_embedding_model, 
                    store_type="txt"
                )
                logger.info(f"Successfully indexed transcript chunks to Qdrant collection: '{collection_name}'")
                
                # Store the collection name for this session
                set_collection_name_for_session(session_id, collection_name)
                
            except Exception as transcript_error:
                logger.error(f"Failed to process transcript: {transcript_error}", exc_info=True)
        
        # Process frame groups if available
        if frame_group_folder_path:
            logger.info("="*80)
            logger.info("PROCESSING FRAME GROUPS")
            logger.info("="*80)
            
            try:
                frame_summary_chunks = summarize_frame_groups(
                    frame_group_folder_path,
                    qwen_vision_processor,
                    qwen_vision_chat_model
                )
                logger.info(f"Summarized {len(frame_summary_chunks)} frame groups")
                
                # Index frame summaries to Qdrant (use same collection as transcript)
                if video_name:
                    index_chunks_to_qdrant(
                        qdrant_client=qdrant_client,
                        collection_name=video_name,
                        summary_chunks=frame_summary_chunks,
                        dense_tokenizer=dense_embedding_tokenizer,
                        dense_embedding_model=dense_embedding_model,
                        store_type="img"
                    )
                    logger.info(f"Successfully indexed frame summaries to Qdrant collection: '{video_name}'")
                else:
                    logger.warning("No video name available - skipping frame indexing to Qdrant")
            except Exception as frame_error:
                logger.error(f"Failed to process frame groups: {frame_error}", exc_info=True)

        logger.info(f"Workflow result: {result}")
        logger.info("Workflow completed successfully")
        
        return result
        
    except Exception as e:
        logger.error(f"Main workflow failed: {str(e)}", exc_info=True)
        raise

async def process_uploaded_video(file_path: str, session_id: str = "default"):
    """
    Process an uploaded video file through the agent workflow.
    
    Args:
        file_path: Path to the uploaded video file (e.g., "data/video.mp4")
        session_id: Session identifier to track collection names
        
    Returns:
        Dictionary containing workflow results and status
    """
    try:
        # Convert absolute path to relative path starting from data/
        path_obj = Path(file_path)
        if path_obj.is_absolute():
            # Extract the filename and prepend with data/
            relative_path = f"data/{path_obj.name}"
        else:
            relative_path = file_path
        
        # Construct the user request message
        user_request = f"Please process this video file: {relative_path}"
        
        logger.info(f"Processing video: {relative_path}")
        logger.info(f"Session ID: {session_id}")
        
        # Execute the workflow
        result = await build_agent_workflow(user_request, session_id=session_id)
        
        return {
            "success": True,
            "message": "Video processing completed successfully",
            "file_path": relative_path,
            "workflow_result": result
        }
        
    except Exception as e:
        logger.error(f"Error processing uploaded video: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": f"Video processing failed: {str(e)}",
            "file_path": file_path,
            "error": str(e)
        }
