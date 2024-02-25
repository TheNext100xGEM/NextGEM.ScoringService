import requests
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
    return '\n'.join([p.text for p in paragraphs])


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
        if current_url not in visited:
            visited.add(current_url)
            page_links, document_urls = get_links(current_url)
            document_url_list.extend(document_urls)
            level_2.extend([link for link in page_links if link not in visited])
        if len(level_2) > 2000:
            break

    # Parse pages
    url_list = set(level_0 + level_1 + level_2)
    page_texts = [f"The following text is from {i}:\n\n{get_page_text(i)}" for i in url_list]

    # Parse pdf-s (e.g. whitepapers)
    document_texts = [f"The following text is from {i}:\n\n{get_pdf_text(i)}" for i in document_url_list]

    return page_texts + document_texts
