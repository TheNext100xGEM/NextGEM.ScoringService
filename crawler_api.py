import time
import json
import requests
from bs4 import BeautifulSoup
from typing import List
from socials import get_social_urls

# Scrapping API uri (to parallelize calls)
with open('config.json', 'r') as file:
    config = json.load(file)

scrapping_api = config["SCRAPPING_API"]
scrape_header = {'Content-Type': 'application/json'}

url_tabu_patterns = [
    'twitter', 'facebook', 'youtube', 'discord', 'instagram',
    'dextools', 'dune', 'scan.',  # etherscan.io, bscscan.io and others variants
    'github',
    'metamask'
]


def tabu_check_url(url: str):
    if url is None:
        return False

    for item in url_tabu_patterns:
        if item in url:
            return False

    return True


def scrape_soups(urls: List[str], logger):
    """ Get bs4 soups fom a list of pages """
    try:
        response = requests.post(f'{scrapping_api}scrape_soup', headers=scrape_header, json={'urls': urls})
        return [BeautifulSoup(t, "html.parser") for t in response.json()['texts']]
    except Exception as e:
        logger.error(f'Scrape API error! {e}')
        return [BeautifulSoup('', "html.parser")] * len(urls)


def soup_to_text(soup):
    """ Extract text from bs4 soup """
    paragraphs = soup.find_all(text=True)

    texts = [p.text for p in paragraphs if len(p.text) > 1]  # Filter short texts

    # Concat text segments
    if len(texts) > 1:
        texts = [texts[i] for i in range(1, len(texts) - 1) if texts[i] != texts[i + 1]]
    text = '\n'.join(texts)

    if '404 Page Not Found' in text:
        return ''
    else:
        return text


def format_url(url: str):
    """
    Remove trailing / or // to decrease duplicated urls (server redirects to correct)
    """
    return url.rstrip('/')


def get_links(url: str, logger):
    """ Get all page and document links from a given URL """
    links = []
    documents = []

    soup = scrape_soups([url], logger)[0]
    for link in soup.find_all('a'):
        href = link.get('href')

        if href is None:
            continue

        if 'http' not in href:
            href = url + href

        if href.endswith('.pdf'):
            documents.append(href)
        else:
            links.append(format_url(href))

    return links, documents, soup


def scrape_text(urls: List[str], logger):
    """ Get all text fom a list of pages and pdf docs """
    try:
        response = requests.post(f'{scrapping_api}scrape', headers=scrape_header, json={'urls': urls})
        return response.json()['texts']
    except Exception as e:
        logger.error(f'Scrape API error! {e}')
        return [''] * len(urls)


def crawl(url: str, logger):
    # Collect page and document links related to the input URL
    visited = set(url)
    document_url_list = []
    level_1 = []
    level_2 = []
    soups = {}

    # Extract main page links
    page_links, document_urls, soup = get_links(url, logger)
    social_links = get_social_urls(page_links)  # Eg.: twitter and telegram links
    document_url_list.extend(document_urls)
    level_1.extend([link for link in page_links if (link not in visited) and tabu_check_url(link)])
    if soup is not None:
        soups[url] = soup

    # Extract further links from connected pages
    def keep_url(url_: str):
        is_visited = url_ not in visited
        is_tabu = tabu_check_url(url_)
        is_type = ("docs" in url_) or ("blog" in url_)
        return is_visited and is_tabu and is_type

    for current_url in level_1:
        if ("docs" not in current_url) and ("blog" not in current_url):
            continue  # Scrape only the project technical documentation and blog in 2 level depth
        if current_url not in visited:
            visited.add(current_url)
            page_links, document_urls, soup = get_links(current_url, logger)
            document_url_list.extend(document_urls)
            level_2.extend([link for link in page_links if keep_url(link)])
            if soup is not None:
                soups[current_url] = soup
        time.sleep(1)  # Getting the first level soups(=texts) is the most important! Don't overscrape!

    # Select URL-s to send for scrape API
    document_url_list = set(document_url_list)  # deduplication
    level_1 = set(level_1)  # deduplication
    level_2 = set(level_2)  # deduplication
    logger.info(f'Documents: {len(document_url_list)} - {document_url_list}')
    logger.info(f'Level 1: {len(level_1)} - {level_1}')
    logger.info(f'Level 2: {len(level_2)} - {level_2}')

    url_set = set(url).union(document_url_list).union(level_1).union(level_2)  # deduplication
    logger.info(f'All collected URL: {len(url_set)}')

    urls_to_scrape = [u for u in url_set if u not in soups.keys()]
    logger.info(f'URLs to send scrape API: {len(urls_to_scrape)}')

    # Start scrape job. Save results in dictionary.
    scraped_texts = scrape_text(urls=urls_to_scrape, logger=logger)
    scraped_texts_dict = dict(zip(urls_to_scrape, scraped_texts))

    # Create dictionary for urls and the parsed text of the url
    texts_dict = {u: '' for u in url_set}
    control_text_list = []  # helper for deduplication
    for u in url_set:
        if u in soups.keys():
            # logger.info(f'{u} is from /scrape_soup endpoint! Stored bs4 soup from link collection.')
            content = soup_to_text(soup)
        else:
            # logger.info(f'{u} is from /scrape endpoint!')
            content = scraped_texts_dict[u]
        if (len(content) > 0) and (content not in control_text_list):
            control_text_list.append(content)
            texts_dict[u] = f"The following text is from {u}:\n{content}"

    texts = [t for t in texts_dict.values() if len(t) > 0]  # drop uninformative
    logger.info(f'Parsed URLs with information: {len(texts)}')

    return texts, social_links
