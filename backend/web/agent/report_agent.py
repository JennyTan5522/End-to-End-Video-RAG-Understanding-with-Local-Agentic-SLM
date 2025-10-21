import logging
from pathlib import Path
from datetime import datetime
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import MessagesState, END
from langgraph.types import Command
from langgraph.prebuilt import create_react_agent
from markdown_pdf import MarkdownPdf, Section
from config.service_config import settings
from src.prompt_engineering.templates import REPORT_GENERATION_PROMPT

logger = logging.getLogger(__name__)

class ReportAgent:
    """
    Agent for generating PDF reports from video summaries.
    
    This agent uses an LLM to intelligently format summary content into 
    structured markdown, then converts it to a professional PDF report.
    
    Attributes:
        llm: The language model instance for generating markdown content
        agent: The configured ReAct agent for report generation
        collection_name: Name of the video collection being reported on
    """
    
    def __init__(self, llm, collection_name: str):
        """
        Initialize the Report Agent.
        
        Args:
            llm: The language model instance to use for markdown generation
            collection_name: Name of the collection to generate report for
        """
        self.llm = llm
        self.collection_name = collection_name
        self.agent = create_react_agent(
            self.llm,
            tools=[],
            prompt=REPORT_GENERATION_PROMPT
        )
        logger.info(f"ReportAgent initialized for collection: '{collection_name}'")
    
    def report_node(self, state: MessagesState):
        """
        Generate a PDF report from summary content.
        
        This node expects the previous message to be a summary from SummaryAgent.
        It converts that summary into a structured PDF report.
        
        Args:
            state: Current messages state containing summary
            
        Returns:
            Command: Updated state with PDF report path and routing to END
        """
        logger.info("=" * 80)
        logger.info("REPORT AGENT - Generating PDF Report")
        logger.info("=" * 80)
        
        try:
            # Extract the summary from previous message
            if len(state['messages']) < 2:
                error_msg = "No summary available to generate report. Please ensure summary is generated first."
                logger.error(error_msg)
                state["messages"].append(AIMessage(content=error_msg))
                return Command(update={"messages": state["messages"]}, goto=END)
            
            # Get the last AI message (should be the summary)
            summary_content = None
            for message in reversed(state['messages']):
                if isinstance(message, AIMessage):
                    summary_content = message.content
                    break
            
            if not summary_content:
                error_msg = "Could not find summary content to generate report."
                logger.error(error_msg)
                state["messages"].append(AIMessage(content=error_msg))
                return Command(update={"messages": state["messages"]}, goto=END)
            
            logger.info(f"Found summary content ({len(summary_content)} characters)")
            
            # Step 1: Use LLM to generate structured markdown report
            logger.info("Using LLM to generate structured markdown report...")
            markdown_content = self._generate_markdown_with_llm(summary_content)
            
            if not markdown_content:
                error_msg = "Failed to generate markdown content from summary."
                logger.error(error_msg)
                state["messages"].append(AIMessage(content=error_msg))
                return Command(update={"messages": state["messages"]}, goto=END)
            
            logger.info(f"Generated markdown content ({len(markdown_content)} characters)")
            
            # Step 2: Convert markdown to PDF
            logger.info("Converting markdown to PDF...")
            pdf_path = self._generate_pdf_report(markdown_content)
            
            if pdf_path:
                logger.info(f"PDF report generated successfully: {pdf_path}")
                success_message = (
                    f"✅ Report Generated Successfully!\n\n"
                    f"📄 File: `{pdf_path.name}`\n"
                    f"📂 Location: `{pdf_path.parent}`\n"
                    f"📊 Video: {self.collection_name}\n\n"
                    f"You can find your PDF report at:\n`{pdf_path}`"
                )
                state["messages"].append(AIMessage(content=success_message))
            else:
                error_msg = "Failed to generate PDF report. Please check the logs."
                logger.error(error_msg)
                state["messages"].append(AIMessage(content=error_msg))
            
            logger.info("=" * 80)
            logger.info("REPORT AGENT - Complete")
            logger.info("=" * 80)
            
            return Command(update={"messages": state["messages"]}, goto=END)
            
        except Exception as e:
            logger.error(f"Report agent encountered an error: {str(e)}", exc_info=True)
            error_message = f"An error occurred while generating the report: {str(e)}"
            state["messages"].append(AIMessage(content=error_message))
            return Command(update={"messages": state["messages"]}, goto=END)
    
    def _generate_markdown_with_llm(self, summary_content: str) -> str:
        """
        Use LLM to generate structured markdown report from summary.
        
        This method invokes the LLM agent to intelligently format the summary
        into a professional markdown report with proper structure, sections,
        and formatting.
        
        Args:
            summary_content: Raw summary text from SummaryAgent
            
        Returns:
            str: LLM-generated structured markdown content
        """
        try:
            # Extract video name from collection name
            video_name = self.collection_name
            if '_' in video_name:
                parts = video_name.split('_')
                if len(parts) >= 3:
                    # Format: timestamp_originalname -> extract original name
                    video_name = '_'.join(parts[2:])
            
            # Get current timestamp
            current_time = datetime.now().strftime("%B %d, %Y at %I:%M %p")
            
            # Prepare the prompt for the LLM
            user_request = f"""
            Please generate a professional markdown report from the following video summary.
            
            **Video Information:**
            - Video Name: {video_name}
            - Collection ID: {self.collection_name}
            - Report Generated: {current_time}
            
            **Video Summary:**
            {summary_content}
            
            Generate a well-structured markdown report with the following sections:
            1. Title and metadata (video name, date, collection ID)
            2. Executive Summary
            3. Detailed Breakdown (organize the summary logically)
            4. Key Topics and Themes
            5. Timestamps (if available in summary)
            6. Footer with generation info
            
            Use proper markdown formatting with headers, bold text, bullet points, and sections.
            """
            
            logger.info("Invoking LLM agent to generate markdown report...")
            
            # Invoke the agent to generate markdown
            result = self.agent.invoke({
                "messages": [HumanMessage(content=user_request)]
            })
            
            # Extract the markdown content from the agent's response
            if result and "messages" in result:
                last_message = result["messages"][-1]
                if isinstance(last_message, AIMessage):
                    markdown_content = last_message.content
                    logger.info("Successfully generated markdown report using LLM")
                    return markdown_content
                else:
                    logger.warning("Agent did not return an AIMessage")
                    return None
            else:
                logger.warning("Agent did not return expected result format")
                return None
                
        except Exception as e:
            logger.error(f"Failed to generate markdown with LLM: {str(e)}", exc_info=True)
            return None
    
    def _generate_pdf_report(self, markdown_content: str) -> Path:
        """
        Convert markdown content to PDF file.
        
        Args:
            markdown_content: Formatted markdown text
            
        Returns:
            Path: Path to generated PDF file, or None if failed
        """
        try:
            # Create reports directory if it doesn't exist
            reports_dir = settings.DATA_FOLDER / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"report_{self.collection_name}_{timestamp}.pdf"
            pdf_path = reports_dir / pdf_filename
            
            logger.info(f"Generating PDF at: {pdf_path}")
            
            # Create PDF from markdown
            pdf = MarkdownPdf(toc_level=2)
            
            # Add the markdown content as a section
            pdf.add_section(Section(markdown_content))
            
            # Save to file
            pdf.save(str(pdf_path))
            
            logger.info(f"PDF saved successfully: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"Failed to generate PDF: {str(e)}", exc_info=True)
            return None
