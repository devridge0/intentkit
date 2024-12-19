"""
Logging configuration module
"""
import json
import logging

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": self.formatTime(record),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

def setup_logging(env: str, debug: bool = False):
    """
    Setup global logging configuration.
    
    Args:
        env: Environment name ('local', 'prod', etc.)
        debug: Debug mode flag
    """
    if env == "local" or debug:
        # Set up logging configuration for local/debug
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler()
            ]
        )
    else:
        # For non-local environments, use JSON format
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logging.basicConfig(
            level=logging.INFO,
            handlers=[handler]
        )
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
