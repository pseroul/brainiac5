import os
import logging


logger = logging.getLogger("uvicorn.error")

def set_env_var() -> None:
    """Set all configuration variables as environment variables."""
    try:
        # Set all config variables as environment variables
        os.environ['CHROMA_DB'] = os.path.join(os.path.dirname(__file__), "data", "embeddings")
        os.environ['NAME_DB'] = os.path.join(os.path.dirname(__file__), "data", "knowledge.db")
        os.environ['USER_DB'] = os.path.join(os.path.dirname(__file__), "data", "users.json")
        os.environ['TOC_CACHE_PATH'] = os.path.join(os.path.dirname(__file__), "data", "toc.json")

        logger.info("All configuration variables have been set as environment variables")
    except Exception as e:
        logger.error(f"Error setting environment variables: {str(e)}")
        raise