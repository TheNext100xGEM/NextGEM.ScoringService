import requests
import re
from bs4 import BeautifulSoup
import fitz  # PyMuPDF


def get_links(url: str):
    """ Get all page and document links from a given URL """
    links = []
    documents = []
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            href = link.get('href')
            if 'http' not in href:
                href = url + href
            if href:
                if href.endswith('.pdf'):
                    documents.append(href)
                else:
                    links.append(href)
    except Exception as e:
        print(f"Error fetching links from {url}: {e}")
    return links, documents


def get_page_text(url: str):
    """ Get all text fom a page """
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all(text=True)
    except:
        return ''

    texts = [p.text for p in paragraphs if len(p.text) > 3]

    if len(texts) > 1:
        texts = [texts[i] for i in range(1,len(texts) - 1) if texts[i] != texts[i+1]]

    return '\n'.join(texts)


def get_pdf_text(url: str):
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
    except:
        return ""
    return text

def get_important_urls(url: str):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=True)
        try:
            twitter_link = [link['href'] for link in links if 'twitter.com' in link['href']][0]
        except:
            twitter_link = None
        try:
            telegram_link = [link['href'] for link in links if 't.me' in link['href']][0]
        except:
            telegram_link = None
    except:
        twitter_link = telegram_link = None
    return twitter_link, telegram_link

def crawl(url: str):
    # Collect page and document links related to the input URL
    visited = set()
    document_url_list = []
    level_0 = [url]
    level_1 = []
    level_2 = []

    for current_url in level_0:
        if current_url not in visited:
            visited.add(current_url)
            page_links, document_urls = get_links(current_url)
            document_url_list.extend(document_urls)
            level_1.extend([link for link in page_links if link not in visited])

    for current_url in level_1:
        if "docs" not in current_url:
            continue  # Scrape only the project technical documentation in 2 level depth
        if current_url not in visited:
            visited.add(current_url)
            page_links, document_urls = get_links(current_url)
            document_url_list.extend(document_urls)
            level_2.extend([link for link in page_links if link not in visited])

    # Parse pages
    url_list = set(level_0 + level_1 + level_2)
    page_texts_raw = [(i, get_page_text(i)) for i in url_list]
    page_texts = [f"The following text is from {i}:\n{text}" for i, text in page_texts_raw if len(text) > 0]

    # Parse pdf-s (e.g. whitepapers)
    document_texts_raw = [(i, get_pdf_text(i)) for i in document_url_list]
    document_texts = [f"The following text is from {i}:\n{text}" for i, text in document_texts_raw if len(text) > 0]

    # Twitter and telegram links
    twitter_link, telegram_link = get_important_urls(url)

    return page_texts + document_texts, twitter_link, telegram_link
