#!/usr/bin/env python3

import argparse
import json
import logging
import random
import datetime

from telegram import Update
from telegram.ext import Updater, CallbackContext, CommandHandler, PrefixHandler
from telegram.parsemode import ParseMode

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

with open('token', 'r', encoding='utf-8') as f:
    TOKEN = f.read().strip('\n')
WHITELIST = ['derstolz', 'jes_d', 'Gibbedatbussybaws', 'den_grushentsev']


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', dest='source', help='Content source directory')

    options = parser.parse_args()
    if not options.source:
        parser.error('Source directory with pictures must be provided. Use --help for more info')
    return options


def start(update: Update, context: CallbackContext):
    logging.info(f"User @{update.message.from_user['username']} is now using the bot")
    context.bot.send_message(chat_id=update.message.chat_id,
                             text="*И СНОВА ЗДРАВСТВУЙТЕ*",
                             parse_mode=ParseMode.MARKDOWN)


def error(update, context):
    logger.warning(f"Update {update} caused {context.error}")


def enable(update, context):
    if update.message.from_user['username'] in WHITELIST:
        logging.info(f"MINION IS SERVING @{update.message.from_user['username']}")
    else:
        logging.warning(f"Permission denied: user @{update.message.from_user['username']}")
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text="\U000026D4*Permission denied*\n"
                                 "Sorry, you're not authorized to use this bot",
                                 parse_mode=ParseMode.MARKDOWN)


def stream_collection(context):
    import codecs
    import re
    import itertools
    with codecs.open(f"{context.job.context['content_type']}.collection", 'r', encoding='cp1251') as collection_f:
        collection = json.load(collection_f)
        text = random.choice(list(itertools.chain.from_iterable(collection)))
        formatted_text = re.sub(r"strong", "b", (re.sub(r"<.?br>", '\n', text)))
    context.bot.send_message(context.job.context['chat_id'], text=formatted_text, parse_mode=ParseMode.HTML)


def enable_content_streaming(update, context):
    try:
        interval = int(context.args[0])
    except IndexError:
        interval = 0

    args = {'content_type': update.message.text[1:].split(' ')[0],
            'interval_mins': interval,
            'chat_id': update.message.chat_id}
    if interval == 0:
        job = context.job_queue.run_once(stream_collection, when=datetime.timedelta(seconds=1), context=args)
    else:
        job = context.job_queue.run_repeating(stream_collection, interval=interval*60, context=args)
    context.chat_data['job'] = job


updater = Updater(TOKEN, use_context=True, request_kwargs={'proxy_url': 'socks5h://163.172.152.192:1080'})
dispatcher = updater.dispatcher

start_handler = CommandHandler('start', start)
content_streaming_handler = PrefixHandler('!', ['ylyl', 'butthurt', 'chat'],
                                          enable_content_streaming,
                                          pass_args=True,
                                          pass_chat_data=True,
                                          pass_job_queue=True)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(content_streaming_handler)
dispatcher.add_error_handler(error)

updater.start_polling()
logger.info("BOT DEPLOYED. Ctrl+C to terminate")
updater.idle()
