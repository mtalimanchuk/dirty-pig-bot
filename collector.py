#!/usr/bin/env python3

from datetime import datetime, timedelta
import json
from operator import itemgetter
import logging
from pathlib import Path
from textwrap import shorten
from time import sleep

import requests

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.WARNING)
logger = logging.getLogger(__name__)

HEADERS = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1; rv:52.0) Gecko/20100101 Firefox/52.0'}

DVACH_CONTENT_DIR = Path('content/2ch')
DVACH_CONTENT_DIR.mkdir(parents=True, exist_ok=True)


def get_threads(session, board, sort_by):
    print(f"Parsing {board}/")
    r = session.get(f"https://2ch.hk/{board}/threads.json")
    threads = r.json()['threads']
    print(f"Found {len(threads)} threads in {board}/")

    return sorted(threads, key=itemgetter(sort_by), reverse=True)


def get_thread_content(session, board, thread_num):
    url = f"https://2ch.hk/{board}/res/{thread_num}.json"
    r = session.get(url)

    return r.json()


def search_content(thread_json):

    def search_butthurt(posts):
        butthurt_posts = []
        for post in posts:
            is_caps = len([c for c in post['comment'] if c.isupper()]) > len([c for c in post['comment'] if c.islower()])
            is_butthurt = is_caps and '@' in post['comment']
            if is_butthurt:
                butthurt_posts.append(post['comment'])

        return butthurt_posts

    def search_ylyl(title, posts):
        # not implemented yet
        return None

    num = thread_json['current_thread']
    title = thread_json['title']
    posts = thread_json['threads'][0]['posts']

    content = {'thread_num': num,
               'butthurt': search_butthurt(posts),
               'ylyl': search_ylyl(title, posts)}

    return content


def create_collection(content_type):
    content_dir = DVACH_CONTENT_DIR
    collection = []
    for tome in content_dir.iterdir():
        for json_file_path in tome.rglob('[0-9]*.json'):
            with open(json_file_path, 'r', encoding='utf-8') as f:
                thread_json = json.load(f)
            content = search_content(thread_json)
            if content[content_type] and content[content_type] not in collection:
                collection.append(content[content_type])

    with open(f"{content_type}.collection", 'w', encoding='utf-8') as collection_f:
        json.dump(collection, collection_f)
        print(f'New {content_type}.collection created with {len(collection)} entries')

    return collection


def run_parser(board='b', sort_by='posts_count', save_top=10):
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        now = datetime.strftime(datetime.now(), '%d-%m-%y_%H-%M-%S')
        current_writing_dir = DVACH_CONTENT_DIR / now
        current_writing_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Running parser. Current writing directory {current_writing_dir} created successfully")

        threads = get_threads(session, board, sort_by)
        with open(current_writing_dir / "threads.json", 'w', encoding='utf-8') as thread_list_file:
            json.dump(threads, thread_list_file)

        for thread in threads[:save_top]:
            comment_view = shorten(thread['comment'], width=200, placeholder='...')
            print(f"#{thread['num']}: {thread['subject']} | {thread['posts_count']} posts\n"
                  f"{comment_view}\n")

            thread_content = get_thread_content(session, board, thread['num'])
            with open(current_writing_dir / f"{thread['num']}.json", 'w', encoding='utf-8') as thread_content_file:
                json.dump(thread_content, thread_content_file)

        print(f"Done parsing {board}. Saved {save_top} threads to {current_writing_dir}.\n"
              f"Closing session.\n"
              f"Updating collections...")

        create_collection('butthurt')

    except Exception as e:
        logging.warning(f"{type(e)}: {e}")


def idle(hours, minutes, seconds):
    last_parser_run = datetime.now()
    time_left = timedelta(hours=hours, minutes=minutes, seconds=seconds)
    next_parser_run = last_parser_run + time_left

    while time_left.total_seconds() > 0:
        _seconds_left = time_left.total_seconds()
        _hours, _remainder = divmod(_seconds_left, 3600)
        _minutes, _seconds = divmod(_remainder, 60)

        timer_string = f"{int(_minutes + _hours*60):02d}:{int(_seconds):02d}"
        print(f"\rIdling... Next parsing run in {timer_string}", sep=' ', end='', flush=True)
        sleep(1)
        time_left = next_parser_run - datetime.now()
    print(f"\rEnd idling\n{'*' * 40}")


''' Main loop'''
while True:
    try:
        run_parser(board='b', sort_by='posts_count', save_top=10)
        idle(2, 0, 0)
    except KeyboardInterrupt:
        break
