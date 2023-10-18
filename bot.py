import logging
import time
from io import BytesIO
import textwrap as tw
import os

# import git
import requests
import rollbar
import telebot
from environs import Env

from parser import parse_latest_news_url, parse_news_page
from data_processing import shorten_text, unify_image
from vk import create_post_on_wall


logger = logging.getLogger('TeleBot')


def main():
    env = Env()
    env.read_env('.env')
    api_token = env.str("TG_BOT_TOKEN")
    channel_id = env.int("CHANNEL_ID")
    gpt_token = env.str('GPT_KEY')

    vk_access_token = env.str('VK_ACCESS_TOKEN')
    vk_group_id = env.str('VK_GROUP_ID')

    db_filename = env.str('DB_FILENAME')
    db_path = os.path.join(db_filename)

    logger.setLevel(logging.INFO)
    logger.info('Commence logging.')

    # repo = git.Repo(search_parent_directories=True)
    # sha = repo.head.object.hexsha
    sha = 1.0
    rollbar.init(env.str('ROLLBAR_ACCESS_TOKEN', None),
                 env.str('ROLLBAR_ENV', None),
                 code_version=sha)
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

                # loading image
                response = requests.get(img_url, verify=False)
                response.raise_for_status()

                image = BytesIO(response.content)
                unified_img = unify_image(image, 'perpetua', 100, True)

                post_news(bot, channel_id, title, unified_img, shortened_text)

                with open(image_path, 'bw+') as file:
                    file.write(unified_img)
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
