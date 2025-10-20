from langchain_core.messages import AIMessage
from langgraph.graph import MessagesState, END
from langgraph.types import Command
from langgraph.prebuilt import create_react_agent
import logging

logger = logging.getLogger(__name__)

class GeneralQuestionAgent:
    """
    Agent for handling general question-answering tasks.
    
    This agent processes general inquiries and provides clear, concise responses
    without requiring specialized tool invocation. It handles open-ended questions,
    explanations, and informational requests.
    
    Attributes:
        llm: The language model instance for generating responses.
        agent: The configured ReAct agent for answering questions.
    """
    
    def __init__(self, llm):
        """
        Initialize the GeneralQuestionAgent.
        
        Args:
            llm: The language model instance to use for answering questions.
        """
        self.llm = llm
        self.agent = create_react_agent(
            self.llm,
            tools=[],
            prompt="You are a helpful assistant that answers general questions clearly and concisely."
        )
        logger.info("GeneralQuestionAgent initialized")

    def general_question_node(self, state: MessagesState):
        """
        Process a general question and generate a response.
        
        Invokes the LLM to generate a comprehensive answer to the user's question,
        appends the response to the conversation state, and terminates the workflow.
        
        Args:
            state: The current messages state containing the user's question.
            
        Returns:
            Command: Updated state with AI response and routing to END.
        """
        logger.info("="*80)
        logger.info("GENERAL QUESTION AGENT - Processing Request")
        logger.info("="*80)
        
        try:
            user_message = state['messages'][-1].content if state.get('messages') else 'N/A'
            logger.info(f"User Question: {user_message}")
            logger.info("-"*80)
            
            # Invoke agent to generate response
            logger.debug("Invoking general question agent...")
            response = self.agent.invoke(state)
            last_msg = response.get("messages", [])[-1] if response.get("messages") else None

            if not last_msg:
                logger.warning("Agent did not generate a response")
                response_content = "I'm sorry, I couldn't generate a response. Please try again."
                state["messages"].append(AIMessage(content=response_content))
            else:
                response_content = last_msg.content if hasattr(last_msg, 'content') else 'No response generated'
                logger.info(f"Agent Response: {response_content}")
                state["messages"].append(AIMessage(content=last_msg.content))
                logger.debug("Appended AI response to messages state")
            
            logger.info("="*80)
            return Command(update={"messages": state["messages"]}, goto=END)
            
        except Exception as e:
            logger.error(f"General question agent encountered error: {str(e)}", exc_info=True)
            error_message = "An error occurred while processing your question. Please try again."
            state["messages"].append(AIMessage(content=error_message))
            return Command(update={"messages": state["messages"]}, goto=END)
