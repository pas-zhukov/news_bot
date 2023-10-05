import logging
import time
from io import BytesIO
import textwrap as tw

import telebot
from environs import Env

from parser import parse_latest_news_url, parse_news_page
from data_processing import shorten_text


logger = logging.getLogger('TeleBot')


def main():
    env = Env()
    env.read_env()
    api_token = env.str("TG_BOT_TOKEN")
    channel_id = env.int("CHANNEL_ID")

    db_filename = env.str('DB_FILENAME')
    db_path = os.path.join(db_filename)

    logger.setLevel(logging.INFO)
    logger.info('Commence logging.')

    bot = telebot.TeleBot(api_token)

    while True:
        latest_news_url = parse_latest_news_url()
        with open(db_path, 'r', encoding='utf-8') as file:
            old_urls = file.readlines()
        if latest_news_url + '\n' not in old_urls:
            title, img_url, text = parse_news_page(latest_news_url)
            shortened_text = shorten_text(text)
            print(shortened_text)
            post_news(bot, channel_id, title, img_url, shortened_text)
            with open(db_path, 'a+', encoding='utf-8') as file:
                file.write(latest_news_url + '\n')
        else:
            time.sleep(60)


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
