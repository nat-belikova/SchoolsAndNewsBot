import os
import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from datetime import date, datetime
from fake_useragent import UserAgent
from selenium import webdriver

websites = [
        {
            'url': 'https://lyc1533.mskobr.ru/ads_edu/',
            'school': '1533',
            'type': 'official_news'
        },
        {
            'url': 'https://lyc1533.mskobr.ru/novosti',
            'school': '1533',
            'type': 'official_news'
        },
        {
            'url': 'https://www.lit.msu.ru/news',
            'school': '1533',
            'type': 'website_1533'
        },
        {
            'url': 'https://gym1534uz.mskobr.ru/ads_edu/',
            'school': '1534',
            'type': 'official_news'
        },
        {
            'url': 'https://gym1534uz.mskobr.ru/novosti',
            'school': '1534',
            'type': 'official_news'
        },
        {
            'url': 'https://gym1534uz.mskobr.ru/info_add/usloviya_priema',
            'school': '1534',
            'type': 'official_news'
        },
        {
            'url': 'https://gym1534.ru/',
            'school': '1534',
            'type': 'website_1534_selenium'
        },
        {
            'url': 'https://lycu1580.mskobr.ru/novosti',
            'school': '1580',
            'type': 'official_news'
        },
        {
            'url': 'https://lycu1580.mskobr.ru/ads_edu/',
            'school': '1580',
            'type': 'official_news'
        },
        {
            'url': 'https://lycuz2.mskobr.ru/novosti',
            'school': 'л2ш',
            'type': 'official_news'
        },
        {
            'url': 'https://lycuz2.mskobr.ru/ads_edu/',
            'school': 'л2ш',
            'type': 'official_news'
        },
        {
            'url': 'https://www.sch2.ru/',
            'school': 'л2ш',
            'type': 'website_l2sh'
        }
    ]

school_list = sorted({site['school'] for site in websites})


def contain_keywords(text_list):
    keywords = False
    pattern = re.compile(r'(?i)\bвступительн\w{2,3}|(день|дн\w{1,3})\sоткрытых\sдверей|добор\w{,2}|набор\w{,2}|'
                         r'олимпиад\w{,3}|показ\w{,3}|поступающ\w{2,3}|прием\w{,2}|приемн\w{2,3}|экзамен\w{,3}\b')
    for text in text_list:
        text_norm = re.sub(r'ё', 'е', text.lower())
        if re.search(pattern, text_norm):
            keywords = True
    return keywords

# Parse functions return a list of tuples (date, keywords, headline, link).


def parse_official_news(site):
    r = requests.get(site['url'], headers={'User-Agent': UserAgent().chrome})
    soup = BeautifulSoup(r.text, 'lxml')
    articles = soup.find_all('div', {'class': 'kris-news-box'})
    articles_info = []
    link_start = re.split(r'(?<=\.mskobr\.ru)/', site['url'])[0]
    for article in articles:
        article_date = article.find('div', {'class': 'kris-news-data-txt'}).string.strip()
        article_date_object = datetime.strptime(article_date, '%d.%m.%Y').date()
        headline = article.find('div', {'class': 'h3'}).string.strip()
        text = article.find('div', {'class': 'kris-news-body'}).get_text()
        text = text.replace('\xa0', ' ')
        link = link_start + article.find('a').get('href')
        articles_info.append((article_date_object, contain_keywords([headline, text]), headline, link))
    return articles_info


def parse_website_1533(site):
    r = requests.get(site['url'])
    soup = BeautifulSoup(r.text, 'lxml')
    year_div = soup.find('div', {'id': 'main'})
    year = year_div.find('h1').string.strip()
    articles_info = []
    article_groups = soup.find_all('div', {'class': 'view-grouping'})
    months = {'Январь': 1, 'Февраль': 2, 'Март': 3, 'Апрель': 4, 'Май': 5, 'Июнь': 6,
              'Июль': 7, 'Август': 8, 'Сентябрь': 9, 'Октрябрь': 10, 'Ноябрь': 11, 'Декабрь': 12}
    for article_group in article_groups:
        month = article_group.find('h2').string.strip()
        content = article_group.find('div', {'class': 'view-grouping-content'})
        date_article_pairs = []
        da_pair = []
        for child in content.children:
            if child.name == 'h3':
                article_date = child.string.strip()
                da_pair.append(article_date)
            elif child.name == 'div':
                if len(da_pair) == 0:
                    da_pair.append(article_date)
                da_pair.append(child)
                date_article_pairs.append(da_pair)
                da_pair = []
        for pair in date_article_pairs:
            article_date_object = date(int(year), months[month], int(pair[0]))
            article_div = pair[1]
            headline = article_div.find('h4').string.strip()
            text = ' '.join([x.get_text() for x in article_div.find_all(re.compile(r'^(?!h4)'), recursive=False)])
            text = text.replace('\xa0', ' ')
            articles_info.append((article_date_object, contain_keywords([headline, text]),
                                  headline, site['url']))
    return articles_info


def parse_website_1534(site):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = os.environ.get('GOOGLE_CHROME_PATH')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(executable_path=os.environ.get('CHROMEDRIVER_PATH'),
                              options=chrome_options)
    driver.get(site['url'])
    soup = BeautifulSoup(driver.page_source, 'lxml')
    article_group = soup.find('ul', {'class': 'latestnewslightbox-1'})
    article_links = article_group.find_all('li')
    articles_info = []
    for article in article_links:
        headline = article.get_text().strip()
        link = site['url'][:-1] + article.find('a').get('href')
        driver.get(link)
        article_soup = BeautifulSoup(driver.page_source, 'lxml')
        text = article_soup.find('div', {'itemprop': 'articleBody'}).get_text()
        text = text.replace('\xa0', ' ')
        article_date = article_soup.find('time').get('datetime')
        article_date_object = datetime.strptime(article_date[:10], '%Y-%m-%d').date()
        articles_info.append((article_date_object, contain_keywords([headline, text]), headline, link))
    driver.quit()
    return articles_info


def parse_website_l2sh(site):
    r = requests.get(site['url'])
    soup = BeautifulSoup(r.text, 'lxml')
    articles = soup.find_all('div', {'class': 'items-row'})
    articles_info = []
    for article in articles:
        article_date = article.find('time').get('datetime')
        article_date_object = datetime.strptime(article_date[:10], '%Y-%m-%d').date()
        headline = article.find('h2').string.strip()
        article_div = article.find('div')
        text = ' '.join([x.get_text() for x in article_div.find_all(re.compile(r'^(?!h2)(?!dl)'), recursive=False)])
        text = text.replace('\xa0', ' ')
        articles_info.append((article_date_object, contain_keywords([headline, text]), headline, site['url']))
    return articles_info


def format_html(dataframe):
    formatted_articles = []
    for _, row in dataframe.iterrows():
        formatted_text = row['Date'].strftime('%d.%m.%Y') + ' ' + row['Headline'] + '\n'
        if row['Keywords']:
            formatted_text = '<b>' + formatted_text + '</b>'
        formatted_text += ' '.join('(<a href="' + link + '">' + link.split('/')[2] + '</a>)' for link in row['Link'])
        formatted_articles.append(formatted_text)
    return '\n\n'.join(formatted_articles)


def school_info(school_num):
    school_sites = [site for site in websites if site['school'] == school_num]
    school_data = []
    for site in school_sites:
        try:
            if site['type'] == 'official_news':
                parsed_site = parse_official_news(site)
            elif site['type'] == 'website_1533':
                parsed_site = parse_website_1533(site)
            elif site['type'] == 'website_1534_selenium':
                parsed_site = parse_website_1534(site)
            elif site['type'] == 'website_l2sh':
                parsed_site = parse_website_l2sh(site)
            school_data += parsed_site
        except:
            pass
    df = pd.DataFrame(school_data, columns=['Date', 'Keywords', 'Headline', 'Link'])
    today = date.today()
    year_ago = today.replace(year=today.year - 1)
    df = df[df['Date'] >= year_ago]
    if df.empty:
        return 'Я не смог найти новости этой школы :('
    else:
        df_no_dupl = df.groupby(['Date', 'Headline']).agg({'Keywords': any, 'Link': list}) \
            .reset_index()
        df_sorted = df_no_dupl.sort_values('Date').tail(10)
        return format_html(df_sorted)
