import os
from dotenv import load_dotenv
from logger_config import setup_logger, log_function_start, log_function_end

# Initialize logger
logger = setup_logger(__name__)


def load_environment_variables():

    log_function_start(logger, "load_environment_variables")
    
    try:
        load_dotenv()
        log_function_end(logger, "load_environment_variables", env_loaded=True)
    except Exception as e:
        logger.error(f"Failed to load environment variables: {e}")
        log_function_end(logger, "load_environment_variables", success=False, error=str(e))


def get_redis_url() -> str:

    log_function_start(logger, "get_redis_url")
    
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    is_local = "localhost" in redis_url or "127.0.0.1" in redis_url
    log_function_end(logger, "get_redis_url", is_local_redis=is_local)
    
    return redis_url


def get_gemini_api_key() -> str:

    log_function_start(logger, "get_gemini_api_key")
    
    api_key = os.getenv("GEMINI_API_KEY")
    has_key = bool(api_key)
    
    log_function_end(logger, "get_gemini_api_key", has_api_key=has_key)
    
    return api_key


def get_github_token() -> str:

    log_function_start(logger, "get_github_token")
    
    token = os.getenv("GITHUB_TOKEN")
    has_token = bool(token)
    
    log_function_end(logger, "get_github_token", has_token=has_token)
    
    return token


def validate_configuration():

    log_function_start(logger, "validate_configuration")
    
    missing_configs = []
    
    if not get_gemini_api_key():
        missing_configs.append("GEMINI_API_KEY")
        
    if not get_github_token():
        missing_configs.append("GITHUB_TOKEN")
    
    if missing_configs:
        error_msg = f"Missing required environment variables: {', '.join(missing_configs)}"
        logger.error(error_msg)
        log_function_end(logger, "validate_configuration", success=False, 
                        missing_configs=missing_configs)
        raise ValueError(error_msg)
    
    log_function_end(logger, "validate_configuration", validation_passed=True)


# Load environment variables on import
load_environment_variables()


REDIS_URL = get_redis_url()
GEMINI_API_KEY = get_gemini_api_key()
GITHUB_TOKEN = get_github_token()

# Validate configuration on import
try:
    validate_configuration()
except ValueError as e:
    logger.warning(f"Configuration validation failed: {e}")
    logger.warning("Application may not function correctly without proper configuration")