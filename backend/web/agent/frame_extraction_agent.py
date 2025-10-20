import asyncio
import logging
import os
from langchain_core.messages import AIMessage
from langgraph.graph import MessagesState, END
from langgraph.types import Command
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from src.prompt_engineering.templates import ARGUMENT_EXTRACTION_PROMPT, argument_parser
from web.mcp_tools.video_frames_extractor import get_frame_groups
from typing import Literal

logger = logging.getLogger(__name__)

class ExtractVideoFramesAgent:
    """
    Agent for extracting frames from video files.
    
    This agent orchestrates frame extraction workflow:
    1. Frame Extraction: Extracts frames from video files via MCP server
    
    The agent parses user requests to extract structured parameters (video file path)
    and coordinates with MCP servers to perform the frame extraction.
    
    Attributes:
        llm: The language model instance for parameter extraction.
        VIDEO_FRAME_EXTRACTION_SERVER_NAME: Identifier for the frame extraction MCP server.
        VIDEO_FRAME_EXTRACTION_TOOL_NAME: Name of the frame extraction MCP tool.
        MCP_SERVER_URL: Base URL for MCP server connections.
        parser: Pydantic parser for extracting structured parameters.
        prompt: System prompt for parameter extraction.
        agent: The configured ReAct agent for parameter extraction.
    """
    
    def __init__(self, llm, mcp_server_url):
        """
        Initialize the ExtractVideoFramesAgent.
        
        Args:
            llm: The language model instance to use for parameter extraction.
            mcp_server_url: Base URL for MCP server connections.
        """
        self.llm = llm
        self.VIDEO_FRAME_EXTRACTION_SERVER_NAME = "mcp_video_frame_extraction"
        self.VIDEO_FRAME_EXTRACTION_TOOL_NAME = "extract_video_frames"
        self.MCP_SERVER_URL = mcp_server_url
        self.parser = argument_parser
        self.agent = create_react_agent(
            self.llm,
            tools=[],
            prompt=ARGUMENT_EXTRACTION_PROMPT
        )
        logger.info(f"ExtractVideoFramesAgent initialized with MCP server URL: {mcp_server_url}")

    async def run_frame_extraction_server(self, video_file: str, frames_output_folder: str):
        """
        Execute frame extraction via MCP server.
        
        Args:
            video_file: Path to the input video file.
            frames_output_folder: Path to the folder where frame outputs will be saved.
            
        Returns:
            str: Information about the extracted frames, or None if extraction failed.
            
        Raises:
            Exception: If MCP server connection or tool execution fails.
        """
        logger.info(f"Connecting to video frame extraction MCP server at: '{self.MCP_SERVER_URL}'")
        logger.debug(f"Frame extraction parameters - video: '{video_file}', output folder: '{frames_output_folder}'")
        
        try:
            client = MultiServerMCPClient({
                self.VIDEO_FRAME_EXTRACTION_SERVER_NAME: {
                    "url": self.MCP_SERVER_URL, 
                    "transport": "streamable_http"
                }
            })
        
            # List tools to confirm server connectivity
            logger.debug("Listing available tools from MCP server...")
            async with client.session(self.VIDEO_FRAME_EXTRACTION_SERVER_NAME) as session:
                tools = await session.list_tools()
                logger.info(f"Available MCP tools: {tools}")
        
            # Call the frame extraction tool
            logger.info(f"Calling MCP tool: '{self.VIDEO_FRAME_EXTRACTION_TOOL_NAME}'")
            async with client.session(self.VIDEO_FRAME_EXTRACTION_SERVER_NAME) as session:
                result = await session.call_tool(
                    self.VIDEO_FRAME_EXTRACTION_TOOL_NAME,
                    {
                        "video_file": video_file,
                        "output_folder": frames_output_folder,
                    },
                )
                logger.debug(f"MCP tool execution completed - result type: {type(result)}")
                
                # Extract text content from CallToolResult
                if result and hasattr(result, 'content') and len(result.content) > 0:
                    frames_output_info = result.content[0].text
                    logger.info(f"Frame extraction successful - output info: '{frames_output_info}'")
                    return frames_output_info
                else:
                    logger.warning("MCP tool result has no text content")
                    return None
                    
        except Exception as e:
            logger.error(f"Frame extraction MCP server operation failed: {str(e)}", exc_info=True)
            raise

    def extract_frames_node(self, state: MessagesState):
        """
        Process frame extraction request by parsing parameters and invoking the MCP tool.
        
        This node:
        1. Invokes LLM to extract video file path from user request
        2. Validates the video file exists
        3. Creates output directory structure
        4. Calls MCP server to perform frame extraction
        5. Groups extracted frames and terminates workflow
        
        Args:
            state: The current messages state containing the user's extraction request.
            
        Returns:
            Command: Updated state with extraction results and routing to END.
        """
        logger.info("="*80)
        logger.info("EXTRACT VIDEO FRAME AGENT - Processing Request")
        logger.info("="*80)
        
        try:
            # Invoke agent to extract parameters
            logger.debug("Invoking parameter extraction agent...")
            response = self.agent.invoke(state)
            last_msg = response.get("messages", [])[-1] if response.get("messages") else None

            if not last_msg or not isinstance(last_msg, AIMessage):
                logger.warning("Extract audio agent did not return a valid AIMessage - aborting extraction")
                error_message = "Failed to parse extraction parameters from your request."
                state["messages"].append(AIMessage(content=error_message))
                return Command(update={"messages": state["messages"]}, goto=END)

            response_content = last_msg.content if hasattr(last_msg, 'content') else 'No response generated'
            logger.info(f"Agent Extracted Parameters: {response_content}")
            logger.info("-"*80)

            # Parse video file path
            try:
                video_file = self.parser.parse(last_msg.content).video_file
                logger.info(f"Parsed video file path: '{video_file}'")
            except Exception as parse_error:
                logger.error(f"Failed to parse video file path: {parse_error}", exc_info=True)
                error_message = "Could not extract video file path from your request. Please specify the file path clearly."
                state["messages"].append(AIMessage(content=error_message))
                return Command(update={"messages": state["messages"]}, goto=END)
            
            if not video_file:
                logger.error("Video file path is empty")
                error_message = "No video file path was provided. Please specify a valid file path."
                state["messages"].append(AIMessage(content=error_message))
                return Command(update={"messages": state["messages"]}, goto=END)
            
            # Validate video file exists 
            logger.debug(f"Validating video file exists at: '{video_file}'")
            if not os.path.exists(video_file):
                logger.error(f"Video file not found: '{video_file}'")
                error_message = f"The specified video file does not exist: {video_file}"
                state["messages"].append(AIMessage(content=error_message))
                return Command(update={"messages": state["messages"]}, goto=END)
            logger.info(f"Video file validated successfully: '{video_file}'")
            
            # Create output directory structure
            video_name = os.path.splitext(os.path.basename(video_file))[0]
            frame_output_folder = f"data/{video_name}/frames"
            logger.info(f"Creating output directory: '{frame_output_folder}'")

            try:
                os.makedirs(frame_output_folder, exist_ok=True)
                logger.debug(f"Output directory created/verified: '{frame_output_folder}'")
            except Exception as dir_error:
                logger.error(f"Failed to create output directory: {dir_error}", exc_info=True)
                error_message = f"Failed to create output directory: {frame_output_folder}"
                state["messages"].append(AIMessage(content=error_message))
                return Command(update={"messages": state["messages"]}, goto=END)
            
            # Execute frame extraction via MCP server
            logger.info("Initiating frame extraction via MCP server...")
            try:
                asyncio.run(self.run_frame_extraction_server(video_file, frame_output_folder))
            except Exception as mcp_error:
                logger.error(f"MCP server frame extraction failed: {mcp_error}", exc_info=True)
                error_message = f"Frame extraction failed due to server error. Please try again."
                state["messages"].append(AIMessage(content=error_message))
                return Command(update={"messages": state["messages"]}, goto=END)
            
            logger.info(f"Frame extraction completed successfully - output folder: '{frame_output_folder}'")

            try:
                frame_group_folder_path = get_frame_groups(frame_output_folder)
                logger.info(f"Frame groups: {frame_group_folder_path}")
            except Exception as group_error:
                logger.error(f"Failed to group frames: {group_error}", exc_info=True)
                error_message = "Frame extraction succeeded but grouping failed. Please check the output folder."
                state["messages"].append(AIMessage(content=error_message))
                return Command(update={"messages": state["messages"]}, goto=END)

            state["messages"].append(AIMessage(content=[{"frame_group_folder_path": frame_group_folder_path}]))
            logger.info("="*80)
            
            return Command(update={"messages": state["messages"]}, goto=END)
            
        except Exception as e:
            logger.error(f"Extract audio node encountered unexpected error: {str(e)}", exc_info=True)
            error_message = "An unexpected error occurred during audio extraction. Please try again."
            state["messages"].append(AIMessage(content=error_message))
            return Command(update={"messages": state["messages"]}, goto=END)