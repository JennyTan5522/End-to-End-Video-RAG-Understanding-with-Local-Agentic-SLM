from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import MessagesState, END
from langgraph.types import Command
from langgraph.prebuilt import create_react_agent
from src.prompt_engineering.templates import SUMMARY_PROMPT
from src.vector_database.retriever import get_summary_chunks
import logging

logger = logging.getLogger(__name__)

class SummaryAgent:
    """
    Agent for handling summarization tasks.

    This agent processes user queries to generate concise summaries based on retrieved
    chunks from a vector database. It uses a ReAct agent for generating responses.

    Attributes:
        llm: The language model instance for generating responses.
        agent: The configured ReAct agent for summarization tasks.
    """
    
    def __init__(self, llm, qdrant_client, collection_name):
        """
        Initialize the SummaryAgent.

        Args:
            llm: The language model instance to use for generating responses.
            qdrant_client: The Qdrant client for retrieving summary chunks.
            collection_name: The name of the collection to query in Qdrant.
        """
        self.llm = llm
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name
        self.agent = create_react_agent(
            self.llm,
            tools=[],
            prompt=SUMMARY_PROMPT
        )
        logger.info("SummaryAgent initialized")

    def summary_node(self, state: MessagesState):
        """
        Process a user query and generate a summary response.

        Args:
            state: The current messages state containing the user's query.

        Returns:
            Command: Updated state with AI response and routing to END.
        """
        logger.info("=" * 80)
        logger.info("SUMMARY AGENT - Processing Request")
        logger.info("=" * 80)

        try:
            # Extract user message
            user_message = state['messages'][-1].content if state.get('messages') else 'N/A'
            logger.info(f"User Query: {user_message}")

            # Retrieve summary chunks
            logger.info("Retrieving summary chunks...")
            filter_type = "txt"
            summary_chunks = get_summary_chunks(self.qdrant_client, self.collection_name, filter_type)

            # Validate summary chunks
            if not summary_chunks:
                logger.warning("No summary chunks retrieved. Returning default response.")
                state["messages"].append(AIMessage(content="No relevant information found to summarize."))
                return Command(update={"messages": state["messages"]}, goto=END)

            # Invoke agent to generate response
            try:
                logger.info("Invoking summarization agent...")
                response = self.agent.invoke({"messages": [HumanMessage(content=summary_chunks)]})
            except Exception as e:
                logger.error(f"Error during agent invocation: {str(e)}", exc_info=True)
                state["messages"].append(AIMessage(content="An error occurred while generating the summary."))
                return Command(update={"messages": state["messages"]}, goto=END)

            # Validate agent response
            if not response or not isinstance(response, dict) or "messages" not in response:
                logger.warning("Invalid response format from agent. Returning default response.")
                state["messages"].append(AIMessage(content="I'm sorry, I couldn't generate a response."))
                return Command(update={"messages": state["messages"]}, goto=END)

            # Extract the last message
            last_msg = response["messages"][-1] if response["messages"] else None
            if not last_msg or not hasattr(last_msg, 'content'):
                logger.warning("Agent did not generate a valid response.")
                response_content = "I'm sorry, I couldn't generate a response. Please try again."
            else:
                response_content = last_msg.content
                logger.info(f"Agent Response: {response_content}")

            # Append response to state
            state["messages"].append(AIMessage(content=response_content))
            logger.info("Appended AI response to messages state")
            return Command(update={"messages": state["messages"]}, goto=END)

        except Exception as e:
            logger.error(f"Summary agent encountered an error: {str(e)}", exc_info=True)
            error_message = "An error occurred while processing your request. Please try again."
            state["messages"].append(AIMessage(content=error_message))
            return Command(update={"messages": state["messages"]}, goto=END)
