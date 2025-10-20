from langchain_core.messages import AIMessage
from langgraph.graph import MessagesState, END
from langgraph.types import Command
from langgraph.prebuilt import create_react_agent
from src.prompt_engineering.templates import AGENT_SUPERVISOR_PROMPT, supervisor_output_parser
from typing import Literal
import logging

logger = logging.getLogger(__name__)

class WorkflowSupervisor:
    """
    Routing supervisor agent that analyzes user requests and routes them to appropriate workflows.
    
    This agent acts as a central dispatcher, determining whether a request should be handled by
    the general question workflow, frame processing workflow, or if the conversation should end.
    
    Attributes:
        llm: The language model instance for routing decisions.
        supervisor_output_parser: Parser for structured routing output.
        supervisor_prompt: System prompt template for routing logic.
        agent: The configured ReAct agent for routing.
    """
    
    def __init__(self, llm):
        """
        Initialize the WorkflowSupervisor.
        
        Args:
            llm: The language model instance to use for routing decisions.
        """
        self.llm = llm 
        self.supervisor_output_parser = supervisor_output_parser
        self.agent = create_react_agent(
            model=llm,
            tools=[], 
            prompt=AGENT_SUPERVISOR_PROMPT
        )
        logger.info("WorkflowSupervisor initialized")

    def supervisor_node(self, state: MessagesState) -> Command[Literal["general_question_workflow", "frame_processing_workflow", "audio_processing_workflow", "summary_workflow", "rag_workflow", "report_workflow", "__end__"]]:
        """
        Process the current state and determine the next workflow to execute.
        
        Analyzes the user's message, invokes the LLM-based routing agent, and returns
        a routing decision to direct the conversation to the appropriate workflow node.
        
        Args:
            state: The current messages state containing user input and conversation history.
            
        Returns:
            Command: Routing command specifying which workflow node to execute next.
                    Returns END if no valid routing decision is made.
        """
        logger.info("="*80)
        logger.info("SUPERVISOR - Analyzing User Request")
        logger.info("="*80)
        
        try:
            message_count = len(state.get('messages', []))
            logger.info(f"State contains {message_count} message(s)")

            if not state.get('messages'):
                logger.warning("No messages in state - routing to END")
                return Command(goto=END)

            user_query = state['messages'][0].content
            logger.info(f"User Query: '{user_query}'")

            # Invoke routing agent
            logger.debug("Invoking supervisor routing agent...")
            response = self.agent.invoke(state)
            logger.debug(f"Agent returned {len(response.get('messages', []))} response message(s)")

            # Extract routing decision
            last_message = response.get("messages", [])[-1] if response.get("messages") else None
    
            if not last_message or not isinstance(last_message, AIMessage):
                logger.warning("Supervisor did not return a valid AIMessage - routing to END")
                return Command(goto=END)
            
            try:
                # Clean the response content before parsing
                raw_content = last_message.content
                logger.debug(f"Raw LLM response: {raw_content}")
                
                # Remove markdown code fences if present
                cleaned_content = raw_content.strip()
                if cleaned_content.startswith("```json"):
                    cleaned_content = cleaned_content[7:]  # Remove ```json
                if cleaned_content.startswith("```"):
                    cleaned_content = cleaned_content[3:]  # Remove ```
                if cleaned_content.endswith("```"):
                    cleaned_content = cleaned_content[:-3]  # Remove trailing ```
                cleaned_content = cleaned_content.strip()
                
                # Replace single quotes with double quotes for valid JSON
                cleaned_content = cleaned_content.replace("'", '"')
                
                logger.debug(f"Cleaned content for parsing: {cleaned_content}")
                
                next_node = self.supervisor_output_parser.parse(cleaned_content).next
            except Exception as parse_error:
                logger.error(f"Failed to parse routing decision: {parse_error}")
                logger.debug(f"Attempted to parse: {last_message.content}")
                logger.warning("Defaulting to END due to parsing failure")
                return Command(goto=END)
            
            if not next_node:
                logger.warning("Supervisor response did not specify a next node - routing to END")
                return Command(goto=END)
            
            logger.info(f"Routing Decision: '{next_node}'")
            
            # Determine final routing target
            if next_node.upper() == "FINISH" or next_node == "__end__":
                goto = END
                logger.info("Workflow terminated - routing to END")
            elif next_node in ["general_question_workflow", "frame_processing_workflow", "audio_processing_workflow", "summary_workflow", "rag_workflow", "report_workflow"]:
                goto = next_node
                logger.info(f"Routing to workflow: '{goto}'")
            else:
                goto = "general_question_workflow"
                logger.warning(f"Unknown routing target '{next_node}' - defaulting to 'general_question_workflow'")
            
            logger.info("="*80)
            return Command(goto=goto)
            
        except Exception as e:
            logger.error(f"Supervisor node encountered unexpected error: {str(e)}", exc_info=True)
            logger.warning("Routing to END due to error")
            return Command(goto=END)