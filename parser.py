from urllib.parse import urljoin
from io import BytesIO
import time

import requests
from bs4 import BeautifulSoup
from selenium import webdriver


SITE_BASE_URL = 'https://www.vedomosti.ru/'


class NewsNotFoundError(Exception):
    def __init__(self, message: str = "News not found!"):
        super().__init__(message)


def parse_latest_news_url(url: str = 'https://www.vedomosti.ru/sport/rubrics/football') -> str:
    response = requests.get('https://www.vedomosti.ru/sport/rubrics/football')
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'lxml')

    url_selector = 'div.grid-cell:nth-child(4) > div:nth-child(2) > a:nth-child(1)'
    news_url = soup.select_one(url_selector).get('href')
    if not news_url:
        raise NewsNotFoundError
    full_news_url = urljoin(SITE_BASE_URL, news_url)
    return full_news_url


def parse_news_page(url: str):
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    browser = webdriver.Chrome(options=options)
    browser.get(url)
    time.sleep(3)
    html = browser.page_source

    soup = BeautifulSoup(html, 'lxml')

    title_selector = '.article-headline__title'
    subtitle_selector = '.article-headline__subtitle'
    main_image_selector = 'article img'
    paragraphs_selector = 'html body .article-boxes-list__item'

    title = soup.select_one(title_selector).get_text().strip()

    image_url = soup.select_one(main_image_selector).get('src')
    image_url = urljoin(SITE_BASE_URL, image_url)

    paragraphs = soup.select(paragraphs_selector)
    paragraphs_clear = []
    for p in paragraphs:
        if not p.find(attrs={'class': 'box-inset-link'}):
            paragraphs_clear.append(p.get_text())
    full_article_text = ' '.join(paragraphs_clear).strip()

    return title, image_url, full_article_text


def get_img(img_url: str) -> BytesIO:
    response = requests.get(img_url)
    response.raise_for_status()
    image = BytesIO(response.content)
    return image