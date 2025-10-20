import os
import asyncio
import logging
from config.service_config import settings
from src.prompt_engineering.templates import ARGUMENT_EXTRACTION_PROMPT, argument_parser
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import MessagesState, END
from langgraph.types import Command
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

logger = logging.getLogger(__name__)

class ExtractAudioFromVideoAgent:
    """
    Agent for extracting and transcribing audio from video files.
    
    This agent orchestrates a two-step workflow:
    1. Audio Extraction: Extracts audio from video files via MCP server
    2. Audio Transcription: Transcribes the extracted audio to text via MCP server
    
    The agent parses user requests to extract structured parameters (video file path)
    and coordinates with MCP servers to perform the audio extraction and transcription.
    
    Attributes:
        llm: The language model instance for parameter extraction.
        AUDIO_EXTRACTION_SERVER_NAME: Identifier for the audio extraction MCP server.
        AUDIO_TRANSCRIPTION_SERVER_NAME: Identifier for the audio transcription MCP server.
        AUDIO_EXTRACTION_TOOL_NAME: Name of the audio extraction MCP tool.
        AUDIO_TRANSCRIPTION_TOOL_NAME: Name of the audio transcription MCP tool.
        MCP_SERVER_URL: Base URL for MCP server connections.
        parser: Pydantic parser for extracting structured parameters.
        prompt: System prompt for parameter extraction.
        agent: The configured ReAct agent for parameter extraction.
    """
    
    def __init__(self, llm):
        """
        Initialize the ExtractAudioFromVideoAgent.
        
        Args:
            llm: The language model instance to use for parameter extraction.
            mcp_server_url: Base URL for MCP server connections.
        """
        self.llm = llm

        # Server Names (used as client session identifiers)
        self.AUDIO_EXTRACTION_SERVER_NAME = "mcp_audio_extraction"
        self.AUDIO_TRANSCRIPTION_SERVER_NAME = "mcp_audio_transcription"

        # Tool Names (MCP tool names to invoke)
        self.AUDIO_EXTRACTION_TOOL_NAME = "extract_audio_from_video"
        self.AUDIO_TRANSCRIPTION_TOOL_NAME = "transcribe_audio_whisper"

        self.MCP_SERVER_URL = settings.AUDIO_MCP_URL
        self.parser = argument_parser
        self.agent = create_react_agent(
            self.llm,
            tools=[],
            prompt=ARGUMENT_EXTRACTION_PROMPT
        )
        logger.info(f"ExtractAudioFromVideoAgent initialized with MCP server URL: {self.MCP_SERVER_URL}")

    async def run_audio_extraction_server(self, video_file: str, output_folder: str):
        """
        Execute audio extraction via MCP server.
        
        Connects to the audio extraction MCP server and invokes the extract_audio_from_video
        tool to extract audio from a video file and save it as MP3.
        
        Args:
            video_file: Path to the input video file.
            output_folder: Path to the folder where audio output will be saved.
            
        Returns:
            str: The absolute path to the extracted audio file, or None if extraction failed.
            
        Raises:
            Exception: If MCP server connection or tool execution fails.
        """
        logger.info(f"Connecting to audio extraction MCP server at: '{self.MCP_SERVER_URL}'")
        logger.debug(f"Extraction parameters - video: '{video_file}', output: '{output_folder}'")
        
        try:
            client = MultiServerMCPClient({
                self.AUDIO_EXTRACTION_SERVER_NAME: {
                    "url": self.MCP_SERVER_URL, 
                    "transport": "streamable_http"
                }
            })
        
            # List tools to confirm server connectivity
            logger.debug("Listing available tools from MCP server...")
            async with client.session(self.AUDIO_EXTRACTION_SERVER_NAME) as session:
                tools = await session.list_tools()
                logger.info(f"Available MCP tools: {tools}")
        
            # Call the audio extraction tool
            logger.info(f"Calling MCP tool: '{self.AUDIO_EXTRACTION_TOOL_NAME}'")
            async with client.session(self.AUDIO_EXTRACTION_SERVER_NAME) as session:
                result = await session.call_tool(
                    self.AUDIO_EXTRACTION_TOOL_NAME,
                    {
                        "video_file": video_file,
                        "output_folder": output_folder,
                    },
                )
                logger.debug(f"MCP tool execution completed - result type: {type(result)}")
                
                # Extract text content from CallToolResult
                if result and hasattr(result, 'content') and len(result.content) > 0:
                    audio_output_file_path = result.content[0].text
                    logger.info(f"Audio extraction successful - output file: '{audio_output_file_path}'")
                    return audio_output_file_path
                else:
                    logger.warning("MCP tool result has no text content")
                    return None
                    
        except Exception as e:
            logger.error(f"Audio extraction MCP server operation failed: {str(e)}", exc_info=True)
            raise

    async def run_transcription_server(self, audio_path: str, output_folder: str):
        """
        Execute audio transcription via MCP server.

        Connects to the audio transcription MCP server and invokes the transcribe_audio tool
        to transcribe audio from a file and save the text output.

        Args:
            audio_path: Path to the input audio file.
            output_folder: Path to the folder where transcription output will be saved.

        Returns:
            str: The absolute path to the transcribed text file, or None if transcription failed.

        Raises:
            Exception: If MCP server connection or tool execution fails.
        """
        logger.info(f"Connecting to audio transcription MCP server at: '{self.MCP_SERVER_URL}'")
        logger.debug(f"Transcription parameters - audio: '{audio_path}', output: '{output_folder}'")

        try:
            client = MultiServerMCPClient({
                self.AUDIO_TRANSCRIPTION_SERVER_NAME: {
                    "url": self.MCP_SERVER_URL,
                    "transport": "streamable_http"
                }
            })

            # List available tools to confirm server is reachable
            logger.debug("Listing available tools from transcription MCP server...")
            async with client.session(self.AUDIO_TRANSCRIPTION_SERVER_NAME) as session:
                tools = await session.list_tools()
                logger.info(f"Available transcription MCP tools: {tools}")

            # Execute the audio transcription tool
            logger.info(f"Calling MCP tool: '{self.AUDIO_TRANSCRIPTION_TOOL_NAME}'")
            async with client.session(self.AUDIO_TRANSCRIPTION_SERVER_NAME) as session:
                result = await session.call_tool(
                    self.AUDIO_TRANSCRIPTION_TOOL_NAME,
                    {
                        "audio_path": audio_path,
                        "output_folder": output_folder
                    },
                )
                logger.debug(f"MCP tool execution completed - result type: {type(result)}")

                # Extract text content from CallToolResult
                if result and hasattr(result, 'content') and len(result.content) > 0:
                    result_text = result.content[0].text
                    logger.info(f"Transcription successful - output file: '{result_text}'")
                    return result_text
                else:
                    logger.warning("MCP tool result has no text content")
                    return None

        except Exception as e:
            logger.error(f"Audio transcription MCP server operation failed: {str(e)}", exc_info=True)
            raise

    def extract_audio_node(self, state: MessagesState):
        """
        Process audio extraction request by parsing parameters and invoking the MCP tool.
        
        This node:
        1. Invokes LLM to extract video file path from user request
        2. Validates the video file exists
        3. Creates output directory structure
        4. Calls MCP server to perform audio extraction
        5. Routes to transcription node on success
        
        Args:
            state: The current messages state containing the user's extraction request.
            
        Returns:
            Command: Updated state with extraction results and routing to transcription node,
                    or routing to END if extraction fails.
        """
        logger.info("="*80)
        logger.info("EXTRACT AUDIO AGENT - Processing Request")
        logger.info("="*80)
        
        try:
            # Extract user request from first message
            logger.debug("Extracting original user request from message history...")
            first_message = state["messages"][0]
            
            # Handle different message formats
            if isinstance(first_message, dict):
                # Message is a dict like {"role": "user", "content": "..."}
                message_content = first_message.get("content", "")
                logger.debug(f"Extracted content from dict message: '{message_content}'")
            elif isinstance(first_message, AIMessage):
                # AIMessage with potentially structured content
                if isinstance(first_message.content, list) and len(first_message.content) > 0:
                    first_item = first_message.content[0]
                    if isinstance(first_item, dict):
                        message_content = first_item.get("text", str(first_item))
                    else:
                        message_content = str(first_item)
                else:
                    message_content = str(first_message.content)
                logger.debug(f"Extracted content from AIMessage: '{message_content}'")
            elif hasattr(first_message, 'content'):
                # HumanMessage or other LangChain message type
                message_content = first_message.content
                logger.debug(f"Extracted content from message object: '{message_content}'")
            else:
                # Fallback: convert to string
                message_content = str(first_message)
                logger.warning(f"Unknown message type, converted to string: '{message_content}'")
            
            logger.info(f"User request: '{message_content}'")
            logger.info("-"*80)
            
            # Invoke agent to extract parameters
            logger.debug("Invoking parameter extraction agent...")
            response = self.agent.invoke({"messages": [HumanMessage(content=message_content)]})

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

            logger.debug(f"Validating video file exists at: '{video_file}'")
            if not os.path.exists(video_file):
                logger.error(f"Video file not found: '{video_file}'")
                error_message = f"The specified video file does not exist: {video_file}"
                state["messages"].append(AIMessage(content=error_message))
                return Command(update={"messages": state["messages"]}, goto=END)
            logger.info(f"Video file validated successfully: '{video_file}'")
            
            # Create output directory structure
            video_name = os.path.splitext(os.path.basename(video_file))[0]
            audio_output_folder = f"data/{video_name}/audio"
            logger.info(f"Creating output directory: '{audio_output_folder}'")
            
            try:
                os.makedirs(audio_output_folder, exist_ok=True)
                logger.debug(f"Output directory created/verified: '{audio_output_folder}'")
            except Exception as dir_error:
                logger.error(f"Failed to create output directory: {dir_error}", exc_info=True)
                error_message = f"Failed to create output directory: {audio_output_folder}"
                state["messages"].append(AIMessage(content=error_message))
                return Command(update={"messages": state["messages"]}, goto=END)
            
            # Execute audio extraction via MCP server
            logger.info("Initiating audio extraction via MCP server...")
            try:
                audio_output_file_path = asyncio.run(
                    self.run_audio_extraction_server(video_file, audio_output_folder)
                )
            except Exception as mcp_error:
                logger.error(f"MCP server audio extraction failed: {mcp_error}", exc_info=True)
                error_message = f"Audio extraction failed due to server error. Please try again."
                state["messages"].append(AIMessage(content=error_message))
                return Command(update={"messages": state["messages"]}, goto=END)

            if audio_output_file_path is None:
                logger.error("Audio extraction failed - MCP server returned no result")
                error_message = f"Audio extraction failed for '{video_file}'. Please try again."
                state["messages"].append(AIMessage(content=error_message))
                return Command(update={"messages": state["messages"]}, goto=END)
            
            logger.info(f"Audio extraction completed successfully - output: '{audio_output_file_path}'")
            logger.info("="*80)
            
            # Prepare state for transcription node
            extraction_result = {
                "audio_file_path": audio_output_file_path,
                "video_file_path": video_file,
                "video_name": video_name
            }
            state["messages"].append(AIMessage(content=[extraction_result]))
            logger.debug(f"Routing to transcription node with result: {extraction_result}")
            
            return Command(update={"messages": state["messages"]}, goto="transcript_audio_node")
            
        except Exception as e:
            logger.error(f"Extract audio node encountered unexpected error: {str(e)}", exc_info=True)
            error_message = "An unexpected error occurred during audio extraction. Please try again."
            state["messages"].append(AIMessage(content=error_message))
            return Command(update={"messages": state["messages"]}, goto=END)

    def transcribe_audio_node(self, state: MessagesState):
        """
        Process audio transcription request by parsing parameters and invoking the MCP tool.

        This node:
        1. Extracts audio file path and metadata from previous node
        2. Creates output directory for transcription
        3. Calls MCP server to perform audio transcription
        4. Appends transcription result to state and terminates workflow
        
        Args:
            state: The current messages state containing audio extraction results.
            
        Returns:
            Command: Updated state with transcription results and routing to END.
        """
        logger.info("="*80)
        logger.info("TRANSCRIBE AUDIO AGENT - Processing Request")
        logger.info("="*80)
        
        try:
            # Extract parameters from previous node
            last_message_content = state["messages"][-1].content[0]
            audio_file_path = last_message_content.get("audio_file_path")
            video_file_path = last_message_content.get("video_file_path")
            video_name = last_message_content.get("video_name")
            
            logger.info(f"Audio file: '{audio_file_path}'")
            logger.info(f"Video source: '{video_file_path}'")
            logger.info(f"Video name: '{video_name}'")
            logger.info("-"*80)
            
            if not audio_file_path or not video_name:
                logger.error("Missing required parameters for transcription")
                error_message = "Transcription failed: missing audio file information."
                state["messages"].append(AIMessage(content=error_message))
                return Command(update={"messages": state["messages"]}, goto=END)
            
            # Create output directory for transcription
            transcript_output_folder = f"data/{video_name}/transcript"
            logger.info(f"Creating transcription output directory: '{transcript_output_folder}'")
            
            try:
                os.makedirs(transcript_output_folder, exist_ok=True)
                logger.debug(f"Transcription directory created/verified: '{transcript_output_folder}'")
            except Exception as dir_error:
                logger.error(f"Failed to create transcription directory: {dir_error}", exc_info=True)
                error_message = f"Failed to create transcription output directory."
                state["messages"].append(AIMessage(content=error_message))
                return Command(update={"messages": state["messages"]}, goto=END)
            
            # Execute transcription via MCP server
            logger.info("Initiating audio transcription via MCP server...")
            try:
                transcription_path = asyncio.run(
                    self.run_transcription_server(audio_file_path, transcript_output_folder)
                )
            except Exception as mcp_error:
                logger.error(f"MCP server transcription failed: {mcp_error}", exc_info=True)
                error_message = f"Audio transcription failed due to server error. Please try again."
                state["messages"].append(AIMessage(content=error_message))
                return Command(update={"messages": state["messages"]}, goto=END)

            if transcription_path is None:
                logger.error("Transcription failed - MCP server returned no result")
                error_message = f"Audio transcription failed for '{audio_file_path}'. Please try again."
                state["messages"].append(AIMessage(content=error_message))
                return Command(update={"messages": state["messages"]}, goto=END)

            logger.info(f"Transcription completed successfully - output: '{transcription_path}'")
            logger.info("="*80)
            
            # Prepare final result
            transcription_result = {
                "audio_file_path": audio_file_path,
                "video_file_path": video_file_path,
                "video_name": video_name,
                "transcript_file_path": transcription_path
            }
            state["messages"].append(AIMessage(content=[transcription_result]))
            logger.debug(f"Workflow completed with result: {transcription_result}")
            
            return Command(update={"messages": state["messages"]}, goto=END)
            
        except Exception as e:
            logger.error(f"Transcribe audio node encountered unexpected error: {str(e)}", exc_info=True)
            error_message = "An unexpected error occurred during audio transcription. Please try again."
            state["messages"].append(AIMessage(content=error_message))
            return Command(update={"messages": state["messages"]}, goto=END)