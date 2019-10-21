#!/usr/bin/env python3

import argparse
import logging

from telegram.ext import Updater

from config import TOKEN, DEV_KWARGS
from handlers import start_handler, stream_handler, content_streaming_handler, error

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s", "--source", dest="source", help="Content source directory"
    )

    options = parser.parse_args()
    if not options.source:
        parser.error(
            "Source directory with pictures must be provided. Use --help for more info"
        )
    return options


if __name__ == "__main__":
    updater = Updater(TOKEN, use_context=True, request_kwargs=DEV_KWARGS)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(stream_handler)
    dispatcher.add_handler(content_streaming_handler)
    dispatcher.add_error_handler(error)

    updater.start_polling()
    logger.info("BOT DEPLOYED. Ctrl+C to terminate")
    updater.idle()
