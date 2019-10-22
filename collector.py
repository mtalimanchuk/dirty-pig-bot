#!/usr/bin/env python3

import logging
from pathlib import Path
import requests
import sqlite3

import pandas as pd
from pandas.io.json import json_normalize

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1; rv:52.0) Gecko/20100101 Firefox/52.0'}

DVACH_CONTENT_DIR = Path('content/2ch')
DVACH_CONTENT_DIR.mkdir(parents=True, exist_ok=True)

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 100)
pd.set_option('display.max_colwidth', 100)


def _identify_butthurts(thread_df, caps_ratio_benchmark=0.5):

    tag_replacements = [
        ("em>", "i>"),
        (r'strong>', 'b>'),
        ('<br>', '\n'),
        (r'<a href="(?!http)(?=\/)', '<a href="https://2ch.hk'),
        (r'span.*?>', 'i>'),
        (r" class=.*?\">>>", '>>>'),
    ]

    thread_df['formatted_comment'] = thread_df['comment']
    for initial_tag, corrected_tag in tag_replacements:
        thread_df['formatted_comment'] = thread_df['formatted_comment'].str.replace(initial_tag, corrected_tag)

    tag_replacements = [
        (r"<.*?>", ""),
        ("\n", ""),
        ("&gt;", ""),
    ]

    thread_df['comment_text'] = thread_df['formatted_comment']
    for initial_tag, corrected_tag in tag_replacements:
        thread_df['comment_text'] = thread_df['comment_text'].str.replace(initial_tag, corrected_tag)

    thread_df['has_butthurt_pattern'] = thread_df['comment_text'].str.contains('@')
    caps_letters = thread_df['comment_text'].str.count(r'[A-ZА-Я]')
    total_letters = thread_df['comment_text'].str.count(r'[a-zа-яA-ZА-Я]')
    thread_df['caps_ratio'] = caps_letters / total_letters
    possible_butthurts_df = thread_df[(thread_df['caps_ratio'] > caps_ratio_benchmark) &
                                      (thread_df['has_butthurt_pattern'])]

    return possible_butthurts_df


def parse_thread(session, board, thread_num):
    try:
        r = session.get(f"https://2ch.hk/{board}/res/{thread_num}.json")
        posts = r.json()['threads'][0]['posts']
    except Exception as e:
        print(f"Error {type(e)} when parsing response")
        return None

    posts_df = pd.DataFrame(posts)

    return _identify_butthurts(posts_df)


def parse_catalog(board):
    logging.info(f"Parsing {board}/")
    df = pd.read_json(f"https://2ch.hk/{board}/threads.json")
    catalog_df = json_normalize(df['threads'])

    logging.info(f"Received {len(catalog_df)} threads. Parsing each one...")
    butthurts_collection = []
    with requests.Session() as session:
        for thread_num in catalog_df['num']:
            butthurts_df = parse_thread(session, board, thread_num)
            if isinstance(butthurts_df, pd.DataFrame):
                if not butthurts_df.empty:
                    butthurts_collection.append(butthurts_df)

    full_butthurts_df = pd.concat(butthurts_collection, ignore_index=True)
    # print(full_butthurts_df)
    collection_df = full_butthurts_df[['num', 'formatted_comment', 'parent']]
    collection_df.loc[(collection_df['parent'] == '0'), 'parent'] = collection_df.loc[(collection_df['parent'] == '0'), 'num']
    collection_df['rating'] = 0
    logging.info(f"Done parsing")

    # current_collection_path = DVACH_CONTENT_DIR / 'butthurts.csv'
    # logging.info(f"Saved to {current_collection_path}")

    return collection_df


if __name__ == "__main__":
    catalog = 'b'
    collection = parse_catalog(catalog)
    with sqlite3.connect("content/butthurts.db") as con:
        # create = "CREATE TABLE IF NOT EXISTS butthurt (id INTEGER PRIMARY KEY AUTOINCREMENT, formatted_text TEXT, parent INTEGER, rating INTEGER);"
        # con.execute(create)
        collection.to_sql('butthurt', con, if_exists='replace')
    print(collection)
