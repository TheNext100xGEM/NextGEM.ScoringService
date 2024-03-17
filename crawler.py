import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium_stealth import stealth
from bs4 import BeautifulSoup
import fitz  # PyMuPDF


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


def tabu_check_url(url: str):
    if url is None:
        return False

    for item in ['twitter', 'facebook', 'dextools', 'dune', 'youtube', 'metamask', 'discord']:
        if item in url:
            return False

    return True


def get_links(driver, url: str, logger):
    """ Get all page and document links from a given URL """
    links = []
    documents = []
    try:
        soup = get_soup(driver, url)
        #logger.info(soup)
        for link in soup.find_all('a'):
            href = link.get('href')
            if 'http' not in href:
                href = url + href
            if tabu_check_url(href):
                if href.endswith('.pdf'):
                    documents.append(href)
                else:
                    links.append(href)
    except Exception as e:
        print(f"Error fetching links from {url}: {e}")
    return links, documents


def get_page_text(driver, url: str, logger):
    """ Get all text fom a page """
    try:
        soup = get_soup(driver, url)
        logger.info(f'{url} soup text length: {len(soup.text)}')
        paragraphs = soup.find_all(text=True)
    except Exception as e:
        # Probably a timeout or bot detection
        logger.info(f'{url} get text exception: {e}')
        try:
            soup = get_soup(driver, url, no_driver=True)
            logger.info(f'{url} soup text length: {len(soup.text)}')
            paragraphs = soup.find_all(text=True)
        except Exception as ee:
            logger.info(f'{url} get text fallback exception: {ee}')
            return ''

    texts = [p.text for p in paragraphs if len(p.text) > 3]

    if len(texts) > 1:
        texts = [texts[i] for i in range(1, len(texts) - 1) if texts[i] != texts[i+1]]

    return '\n'.join(texts)


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
                # TODO text might be saved as image on the PDF page, needs OCR like PyTessaract
                pass

        pdf.close()  # Close the document object when done
    except Exception as e:
        logger.info(f'Document parsing error: {e}')
        return ""
    return text


def get_important_urls(driver, url: str):
    try:
        soup = get_soup(driver, url)
        links = soup.find_all('a', href=True)
        try:
            twitter_link = [link['href'] for link in links if 'twitter.com' in link['href']][0]
        except Exception:
            twitter_link = None
        try:
            telegram_link = [link['href'] for link in links if 't.me' in link['href']][0]
        except Exception:
            telegram_link = None
    except Exception:
        twitter_link = telegram_link = None
    return twitter_link, telegram_link


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
    visited = set()
    document_url_list = []
    level_0 = [url]
    level_1 = []
    level_2 = []

    for current_url in level_0:
        if current_url not in visited:
            visited.add(current_url)
            page_links, document_urls = get_links(driver, current_url, logger)
            document_url_list.extend(document_urls)
            level_1.extend([link for link in page_links if link not in visited])

    for current_url in level_1:
        if "docs" not in current_url:
            continue  # Scrape only the project technical documentation in 2 level depth
        if current_url not in visited:
            visited.add(current_url)
            page_links, document_urls = get_links(driver, current_url, logger)
            document_url_list.extend(document_urls)
            level_2.extend([link for link in page_links if link not in visited])

    # Parse pages
    logger.info(f'Level 1: {len(list(set(level_1)))} - {list(set(level_1))}')
    logger.info(f'Level 2: {len(list(set(level_2)))} - {list(set(level_2))}')
    url_list = set(level_0 + level_1 + level_2)
    page_texts = []
    for i in url_list:
        text = get_page_text(driver, i, logger)
        if len(text) > 0:
            page_texts.append(f"The following text is from {i}:\n{text}")
        time.sleep(1)
    page_texts = list(set(page_texts))  # deduplication

    # Parse pdf-s (e.g. whitepapers)
    document_texts_raw = [(i, get_pdf_text(i)) for i in document_url_list]
    document_texts = [f"The following text is from {i}:\n{text}" for i, text in document_texts_raw if len(text) > 0]
    document_texts = list(set(document_texts))  # deduplication

    # Twitter and telegram links
    twitter_link, telegram_link = get_important_urls(driver, url)

    # Clean up headless browser
    driver.quit()

    logger.info(f'Page count: {len(page_texts)}; Doc count: {len(document_texts)}')

    return page_texts + document_texts, twitter_link, telegram_link
