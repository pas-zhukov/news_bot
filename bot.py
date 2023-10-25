import logging
import time
from io import BytesIO
import textwrap as tw
import os
from pathlib import Path
import random

import requests
import rollbar
import telebot
from environs import Env

from parser import parse_latest_news_url, parse_news_page
from data_processing import shorten_text, make_img_unique, rephrase_title
from vk import create_post_on_wall


FILTERS_LIST = [
    'aden', 'brooklyn', 'clarendon',
    'lark', 'lofi', 'maven',
    'nashville', 'perpetua', 'slumber',
    'valencia',
]

logger = logging.getLogger('TeleBot')


def main():
    env = Env()
    env.read_env('.env')
    api_token = env.str("TG_BOT_TOKEN")
    channel_id = env.str("TG_CHANNEL_ID")
    dzen_channel_id = env.str('DZEN_TG_CHANNEL_ID')
    gpt_token = env.str('GPT_KEY')

    vk_access_token = env.str('VK_ACCESS_TOKEN')
    vk_group_id = env.str('VK_GROUP_ID')

    db_filename = env.str('DB_FILENAME')
    db_path = os.path.join(db_filename)
    file_path = Path(db_path)
    file_path.touch(exist_ok=True)

    logger.setLevel(logging.INFO)
    logger.info('Commence logging.')

    rollbar.init(env.str('ROLLBAR_ACCESS_TOKEN', None),
                 env.str('ROLLBAR_ENV', None),)
    rollbar.report_message('Rollbar is configured correctly!', 'info')

    bot = telebot.TeleBot(api_token)

    image_path = 'image.jpg'

    while True:
        try:
            latest_news_url = parse_latest_news_url()
            with open(db_path, 'r+', encoding='utf-8') as file:
                old_urls = file.readlines()
            if latest_news_url + '\n' not in old_urls:
                title, img_url, text = parse_news_page(latest_news_url)

                shortened_text = shorten_text(gpt_token, text)
                rephrased_title = rephrase_title(gpt_token, title)
                if len(shortened_text) + len(rephrased_title) + 100 > 1000:
                    continue

                # loading image
                response = requests.get(img_url, verify=False)
                response.raise_for_status()

                image = BytesIO(response.content)
                unique_img = make_img_unique(image, random.choice(FILTERS_LIST), 100, False)

                # post into telegram
                post_news(bot, channel_id, rephrased_title, unique_img, shortened_text)

                # post into dzen
                post_news(bot, dzen_channel_id, rephrased_title, unique_img, shortened_text, add_links=True)

                # post into VK
                with open(image_path, 'bw+') as file:
                    file.write(unique_img)
                create_post_on_wall(image_path, title, shortened_text, vk_access_token, vk_group_id)

                with open(db_path, 'a+', encoding='utf-8') as file:
                    file.write(latest_news_url + '\n')
            else:
                time.sleep(20)

        except requests.HTTPError:
            err_msg = f'Unable to download image! News_title: {title} Img source: {img_url}'
            logging.error(err_msg)
            rollbar.report_message(err_msg, 'error', response)
            continue
        except Exception as ex:
            logging.error(ex)
            rollbar.report_exc_info()
            continue

        finally:
            try:
                os.remove(image_path)
            except FileNotFoundError:
                pass
            time.sleep(20)


def post_news(bot: telebot.TeleBot,
              chat_id: int,
              news_title: str,
              news_img: BytesIO or bytes,
              news_text: str,
              add_links: bool = False):

    text = f"""
    *{news_title}*
    
    {news_text}
    
    {"Ещё больше информации у нас в Телеграм-канале: https://bit.ly/3SgVdfc" if add_links else ''}
    """

    msg = bot.send_photo(chat_id,
                         news_img,
                         tw.dedent(text),
                         'Markdown',
                         )
    return msg


if __name__ == '__main__':
    main()
