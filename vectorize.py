import time
from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from llm_connection import get_multiple_openai_embedding


estimated_char_per_token = 3
char_per_chunk = 500 * estimated_char_per_token

batch_size = 500


def vectorize(documents: List[str], logger=None, chunk_size: int = char_per_chunk, max_retries: int = 10):
    if len(documents) == 0:
        return [], []
    
    # Chunk documents
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=int(0.2 * chunk_size))
    chunks = text_splitter.create_documents(documents)
    text_chunks = [c.page_content for c in chunks]

    # Create embeddings for text chunks
    text_chunks_out = []
    embeddings = []
    for i in range(0, len(text_chunks), batch_size):
        current_chunks = text_chunks[i:i + batch_size]
        retries = 0
        while retries < max_retries:
            response = get_multiple_openai_embedding(current_chunks)
            if response is None:
                retries += 1
                if logger is not None:
                    logger.error(f'OpenAI embedding failed. Retry: {retries}')
                time.sleep(1)
            else:
                text_chunks_out.extend(current_chunks)
                embeddings.extend(response)
                break

    return text_chunks_out, embeddings
