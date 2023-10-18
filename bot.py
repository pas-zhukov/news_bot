import logging
import time
from io import BytesIO
import textwrap as tw
import os

import git
import requests
import rollbar
import telebot
from environs import Env

from parser import parse_latest_news_url, parse_news_page
from data_processing import shorten_text, unify_image


logger = logging.getLogger('TeleBot')


def main():
    env = Env()
    env.read_env()
    api_token = env.str("TG_BOT_TOKEN")
    channel_id = env.int("CHANNEL_ID")
    gpt_token = env.str('GPT_KEY')

    db_filename = env.str('DB_FILENAME')
    db_path = os.path.join(db_filename)

    logger.setLevel(logging.INFO)
    logger.info('Commence logging.')

    repo = git.Repo(search_parent_directories=True)
    sha = repo.head.object.hexsha
    rollbar.init(env.str('ROLLBAR_ACCESS_TOKEN', None),
                 env.str('ROLLBAR_ENV', None),
                 code_version=sha)
    rollbar.report_message('Rollbar is configured correctly', 'info')

    bot = telebot.TeleBot(api_token)

    while True:
        time.sleep(20)
        try:
            latest_news_url = parse_latest_news_url()
        except Exception as ex:
            logging.error(ex)
            rollbar.report_exc_info()
            continue
        with open(db_path, 'r+', encoding='utf-8') as file:
            old_urls = file.readlines()
        if latest_news_url + '\n' not in old_urls:
            try:
                title, img_url, text = parse_news_page(latest_news_url)
            except Exception as ex:
                logging.error(ex)
                rollbar.report_exc_info()
                continue
            try:
                shortened_text = shorten_text(gpt_token, text)
            except Exception as ex:
                logging.error(ex)
                rollbar.report_exc_info()
                continue

            #  loading image
            try:
                response = requests.get(img_url, verify=False)
                response.raise_for_status()
            except requests.HTTPError:
                err_msg = f'Unable to download image! News_title: {title} Img source: {img_url}'
                logging.error(err_msg)
                rollbar.report_message(err_msg, 'error', response)
                continue
            except Exception as ex:
                logging.error(ex)
                rollbar.report_exc_info()
                continue
            image = BytesIO(response.content)
            unified_img = unify_image(image, 'perpetua', 1000, True)

            try:
                post_news(bot, channel_id, title, unified_img, shortened_text)
            except Exception as ex:
                logging.error(ex)
                rollbar.report_exc_info()
                continue
            with open(db_path, 'a+', encoding='utf-8') as file:
                file.write(latest_news_url + '\n')
        else:
            time.sleep(20)


def post_news(bot: telebot.TeleBot,
              chat_id: int,
              news_title: str,
              news_img: BytesIO,
              news_text: str):

    text = f"""
    *{news_title}*
    
    {news_text}
    """

    msg = bot.send_photo(chat_id,
                         news_img,
                         tw.dedent(text),
                         'Markdown',
                         )
    return msg


if __name__ == '__main__':
    main()
