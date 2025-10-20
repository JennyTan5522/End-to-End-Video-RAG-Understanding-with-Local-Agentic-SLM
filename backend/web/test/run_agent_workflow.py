import asyncio
import logging
from web.agent.agent_workflow_builder import build_agent_workflow

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        user_request = "Please process this video file: data/weekly_meeting.mp4"
        audio_mcp_server_url = "http://127.0.0.1:8002/mcp"
        frame_mcp_server_url = "http://127.0.0.1:8003/mcp"
        logger.info("Starting workflow application")
        app = asyncio.run(build_agent_workflow(user_request, audio_mcp_server_url, frame_mcp_server_url))
        logger.info("Workflow application built successfully")
    except RuntimeError as e:
        logger.warning(f"RuntimeError encountered: {e}")
        # If running in Jupyter/IPython 
        import nest_asyncio
        nest_asyncio.apply()
        logger.info("Applied nest_asyncio for Jupyter environment")
        app = asyncio.run(build_agent_workflow(user_request, audio_mcp_server_url, frame_mcp_server_url))
    except Exception as e:
        logger.error(f"Application failed to start: {str(e)}", exc_info=True)
        raise