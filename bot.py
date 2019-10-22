#!/usr/bin/env python3
import logging

from telegram.ext import Updater

from pig.config import TOKEN, DEV_KWARGS
from pig.handlers import (
    start_handler,
    stream_handler,
    content_streaming_handler,
    rating_callback_handler,
    error,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename=f"{__name__}.log",
)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    updater = Updater(TOKEN, use_context=True, request_kwargs=DEV_KWARGS)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(stream_handler)
    dispatcher.add_handler(content_streaming_handler)
    dispatcher.add_handler(rating_callback_handler)
    dispatcher.add_error_handler(error)

    updater.start_polling()
    logger.info("BOT DEPLOYED. Ctrl+C to terminate")
    updater.idle()
