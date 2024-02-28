from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from llm_connection import get_openai_embedding


estimated_char_per_token = 3
chunk_size = 500 * estimated_char_per_token


def vectorize(documents: List[str], chunk_size: int = chunk_size):
    if len(documents) == 0:
        return [], []
    
    # Chunk documents
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=int(0.2 * chunk_size))
    chunks = text_splitter.create_documents(documents)
    text_chunks = [c.page_content for c in chunks]

    # Create embeddings for text chunks
    embeddings = []
    for text in text_chunks:
        response = get_openai_embedding(text)
        if response is None:
            continue
        embeddings.append(response)

    return text_chunks, embeddings
