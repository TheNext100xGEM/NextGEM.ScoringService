import json
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium_stealth import stealth
from bs4 import BeautifulSoup
import fitz  # PyMuPDF
import random
from socials import get_social_urls

# Scrapping API uri (to parallelize calls)
with open('config.json', 'r') as file:
    config = json.load(file)

scrapping_api = config["SCRAPPING_API"]

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


def get_soup(driver, url: str, no_driver=False):
    """ Scraping with or without Selenium driver """
    if no_driver:
        # Used as a fallback if selenium fails
        response = requests.get(url)
        source = response.text
    else:
        driver.get(url)
        while driver.execute_script("return document.readyState") != "complete":
            pass
        source = driver.page_source
    return BeautifulSoup(source, "html.parser")


def soup_to_text(soup):
    """ Extract text from bs4 soup """
    paragraphs = soup.find_all(text=True)

    texts = [p.text for p in paragraphs if len(p.text) > 1 and " " in p.text]  # Filter short texts

    # Concat text segments
    if len(texts) > 1:
        texts = [texts[i] for i in range(1, len(texts) - 1) if texts[i] != texts[i + 1]]
    text = '\n'.join(texts)

    if 'page not found' in text.lower():
        return ''
    else:
        return text


def format_url(url: str):
    """
    Replace whitespaces in urls (frequent typo)
    Remove trailing / or // to decrease duplicated urls (server redirects to correct)
    """
    return url.replace(" ", "").rstrip('/')


def get_links(driver, url: str, logger):
    """ Get all page and document links from a given URL """
    links = []
    documents = []
    soup = None
    try:
        soup = get_soup(driver, url)
        # logger.info(soup)
        for link in soup.find_all('a'):
            href = link.get('href')
            if href is None:
                continue
            if 'http' not in href:
                href = url + href
            if href.endswith('.pdf'):
                documents.append(href)
            else:
                links.append(href)
    except Exception as e:
        print(f"Error fetching links from {url}: {e}")
    return links, documents, soup


def get_page_text(driver, url: str, logger):
    """ Get all text fom a page """
    try:
        soup = get_soup(driver, url)
        logger.info(f'{url} soup text length: {len(soup.text)}')
    except Exception as e:
        # Probably a timeout or bot detection
        logger.info(f'{url} get text exception: {e}')
        try:
            soup = get_soup(driver, url, no_driver=True)
            logger.info(f'{url} soup text length: {len(soup.text)}')
        except Exception as ee:
            logger.info(f'{url} get text fallback exception: {ee}')
            return ''

    text = soup_to_text(soup)
    logger.info(f'{url} extracted text length: {len(text)}')

    return text


def get_pdf_text(url: str, logger):
    try:
        response = requests.get(url)
        pdf = fitz.open("pdf", response.content)

        # Extract text from each page
        text = ""
        for page_number, page in enumerate(pdf):
            page_text = page.get_text()
            if len(page_text) > 0:
                text += page_text
            else:
                # TODO text might be saved as image on the PDF page, probably needs OCR like PyTessaract
                pass

        pdf.close()  # Close the document object when done
    except Exception as e:
        logger.info(f'{url} Document parsing error: {response} - {e}')
        return ""
    return text


def crawl(url: str, logger):
    # Start headless browser (stealthy as fuck)
    service = ChromeService()  # currently broken, install latest: executable_path=ChromeDriverManager().install()

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # run in headless mode
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-popup-blocking')  # disable pop-up blocking
    options.add_argument('--start-maximized')  # start the browser window in maximized mode
    options.add_argument('--disable-extensions')  # disable extensions
    options.add_argument('--no-sandbox')  # disable sandbox mode
    options.add_argument('--disable-dev-shm-usage')  # disable shared memory usage

    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    # TODO: rotate user agent if needed (https://www.zenrows.com/blog/selenium-stealth#scrape-with-stealth)

    stealth(driver, languages=["en-US", "en"], vendor="Google Inc.", platform="Win32", webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine", fix_hairline=True)

    # Collect page and document links related to the input URL
    visited = set(url)
    document_url_list = []
    level_1 = []
    level_2 = []
    soups = {}

    # Extract main page links
    page_links, document_urls, soup = get_links(driver, url, logger)
    social_links = get_social_urls(page_links)
    document_url_list.extend(document_urls)
    level_1.extend([format_url(link) for link in page_links if (link not in visited) and tabu_check_url(link)])
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
            page_links, document_urls, soup = get_links(driver, current_url, logger)
            document_url_list.extend(document_urls)
            level_2.extend([format_url(link) for link in page_links if keep_url(link)])
            if soup is not None:
                soups[current_url] = soup

    # Parse pages
    level_1 = set(level_1)  # deduplication
    level_2 = set(level_2)  # deduplication
    logger.info(f'Level 1: {len(level_1)} - {level_1}')
    logger.info(f'Level 2: {len(level_2)} - {level_2}')
    url_set = set([url]).union(level_1).union(level_2)  # deduplication
    page_texts = []
    control_text_list = []  # helper for deduplication
    for i in random.sample(list(url_set), len(url_set)):
        if i in soups.keys():
            logger.info(f'{i} from stored bs4 soup!')
            text = soup_to_text(soup)
        else:
            text = get_page_text(driver, i, logger)
        if (len(text) > 0) and (text not in control_text_list):
            control_text_list.append(text)
            page_texts.append(f"The following text is from {i}:\n{text}")
        time.sleep(1)

    # Parse pdf-s (e.g. whitepapers)
    document_url_list = set(document_url_list)  # deduplication
    document_texts = []
    control_text_list = []  # helper for deduplication
    for u in document_url_list:
        text = get_pdf_text(u, logger)
        if (len(text) > 0) and (text not in control_text_list):
            control_text_list.append(text)
            document_texts.append(f"The following text is from {u}:\n{text}")

    # Clean up headless browser
    driver.quit()

    logger.info(f'Page count: {len(page_texts)}; Doc count: {len(document_texts)}')

    return page_texts + document_texts, social_links
