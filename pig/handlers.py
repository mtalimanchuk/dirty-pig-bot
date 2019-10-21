import codecs
from contextlib import wraps
import datetime
import json
import itertools
import logging
import random
import re

from telegram.ext import CommandHandler, PrefixHandler
from telegram.parsemode import ParseMode

from config import WHITELIST

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def whitelist_only(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user = update.effective_user
        logger.info(f"@{user.username} ({user.id}) is trying to access a privileged command")
        if user.id not in WHITELIST:
            logger.warning(f"Unauthorized access denied for {user.username}.")
            text = (
                "�🚫 *ACCESS DENIED*"
                "Sorry, you are *not authorized* to use this command"
            )
            update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
            return
        return func(update, context, *args, **kwargs)
    return wrapped


def start(update, context):
    logger.info(f"User @{update.message.from_user['username']} is now using the bot")
    context.bot.send_message(
        chat_id=update.message.chat_id,
        text="*И СНОВА ЗДРАВСТВУЙТЕ*",
        parse_mode=ParseMode.MARKDOWN,
    )


def stream_collection(context):
    filename = context.job.context['content_type']
    with codecs.open(f"{filename}.collection", "r", encoding="cp1251") as collection_f:
        collection = json.load(collection_f)
        text = random.choice(list(itertools.chain.from_iterable(collection)))
        formatted_text = re.sub(r"strong", "b", (re.sub(r"<.?br>", "\n", text)))

    chat_id = context.job.context["chat_id"]
    context.bot.send_message(chat_id, text=formatted_text, parse_mode=ParseMode.HTML)


@whitelist_only
def enable(update, context):
    logging.info(f"Dirty Pig is serving @{update.message.from_user['username']}")
    with open("collection.json", "r", encoding="utf-8") as collection_f:
        collection = json.load(collection_f)

    catalog = "b"
    try:
        random_butthurt = random.choice(collection)
    except IndexError:
        return

    formatted_comment = random_butthurt["formatted_comment"]
    thread_num = random_butthurt["parent"]
    butthurt_string = (
        f"{formatted_comment}\n"
        f"{catalog}/<a href='https://2ch.hk/{catalog}/res/{thread_num}.html'>{thread_num}</a>"
    )
    # collection.remove(random_butthurt)
    context.bot.send_message(
        chat_id=update.message.chat_id,
        text=butthurt_string,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


def enable_content_streaming(update, context):
    try:
        interval = int(context.args[0])
    except IndexError:
        interval = 0

    args = {
        "content_type": update.message.text[1:].split(" ")[0],
        "interval_mins": interval,
        "chat_id": update.message.chat_id,
    }
    if interval == 0:
        job = context.job_queue.run_once(
            stream_collection, when=datetime.timedelta(seconds=1), context=args
        )
    else:
        job = context.job_queue.run_repeating(
            stream_collection, interval=interval * 60, context=args
        )
    context.chat_data["job"] = job


def error(update, context):
    logger.warning(f"Update {update} caused {context.error}")


start_handler = CommandHandler("start", start)
stream_handler = CommandHandler("2ch", enable)
content_streaming_handler = PrefixHandler(
    "!",
    ["ylyl", "butthurt", "chat"],
    enable_content_streaming,
    pass_args=True,
    pass_chat_data=True,
    pass_job_queue=True,
)
