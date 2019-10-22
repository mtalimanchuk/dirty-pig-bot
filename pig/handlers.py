from contextlib import wraps
import datetime
import logging
import sqlite3

from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup

from telegram.ext import CommandHandler, PrefixHandler, CallbackQueryHandler
from pig.config import WHITELIST

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename=f"{__name__}.log",
)
logger = logging.getLogger(__name__)


def _build_reply_markup(num, rating):
    buttons = [
        InlineKeyboardButton("👎", callback_data=f"{num}+-1"),
        InlineKeyboardButton(f"{rating:+}", callback_data=f"{num}+1"),
        InlineKeyboardButton("👍", callback_data=f"{num}+1"),
    ]
    return InlineKeyboardMarkup.from_row(buttons)


def whitelist_only(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user = update.effective_user
        logger.info(
            f"@{user.username} ({user.id}) is trying to access a privileged command"
        )
        if user.id not in WHITELIST:
            logger.warning(f"Unauthorized access denied for {user.username}.")
            text = (
                "🚫 *ACCESS DENIED*\n"
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
        text="И СНОВА ЗДРАВСТВУЙТЕ",
        parse_mode=ParseMode.HTML,
    )


def stream_collection(context):
    filename = context.job.context["content_type"]
    chat_id = context.job.context["chat_id"]
    text = "Move on, nothing here yet"
    context.bot.send_message(chat_id, text=text, parse_mode=ParseMode.HTML)


@whitelist_only
def enable(update, context):
    logging.info(f"Dirty Pig is serving @{update.message.from_user['username']}")
    catalog = "b"
    with sqlite3.connect("content/butthurts.db") as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM butthurt ORDER BY random() LIMIT 1")
        random_butthurt = c.fetchone()
        _, num, text, parent, rating = random_butthurt
        butthurt_string = (
            f"{text}\n"
            f"{catalog}/<a href='https://2ch.hk/{catalog}/res/{parent}.html#{num}'>{parent}</a>"
        )

    context.bot.send_message(
        chat_id=update.message.chat_id,
        text=butthurt_string,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=_build_reply_markup(num, rating),
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


@whitelist_only
def update_rating(update, context):
    query = update.callback_query
    num, vote = [int(i) for i in query.data.split("+")]
    if vote:
        logger.info(f"{num} was voted {vote}")
        with sqlite3.connect("content/butthurts.db") as conn:
            c = conn.cursor()
            c.execute("UPDATE butthurt SET rating = rating + ? WHERE num = ?;", (vote, num))
            c.execute("SELECT rating FROM butthurt WHERE num = ?;", (num,))
            rating = c.fetchone()[0]
        query.answer()
        query.edit_message_reply_markup(_build_reply_markup(num, rating))


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
rating_callback_handler = CallbackQueryHandler(update_rating)
