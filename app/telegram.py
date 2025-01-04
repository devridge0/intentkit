import logging

from app.entrypoints.tg import run_telegram_server

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    run_telegram_server()
