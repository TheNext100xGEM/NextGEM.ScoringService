import time
import json
from chunk_selection import get_project_context
from llm_connection import get_openai_completion


token_prompt = 'You are a helpful assistant. brief and precise. You are extracting information from scrapped crypto project websites.\n' \
               'Extract the name of the token, token symbol and which chains is the project deployed!\n' \
               'If there is no information in the text for a field then answer: No information found!\n' \
               'Answer format is parseable JSON!\n' \
               'Example 1: {"tokenName": "ExampleToken", "tokenSymbol": "ET", "chains": ["Ethereum", "BSC"]}\n' \
               'Example 2: {"tokenName": "DummyTokenName", "tokenSymbol": "TIA", "chains": ["Solana"]}\n' \
               'Example 3: {"tokenName": "No information found", "tokenSymbol": "TADA", "chains": ["No information found"]}\n\n' \
               'Text chunks from website:\n'


def extract_token_info(text_chunks, embeddings, logger, max_retries=3):
    project_context = get_project_context(text_chunks, embeddings, prompt=token_prompt, top_k=10)
    #logger.info(f'chain extraction context: {project_context}')

    retries = 0
    while retries < max_retries:
        response = get_openai_completion(token_prompt + project_context, logger)
        if response is None:
            time.sleep(1)
        else:
            try:
                response = json.loads(response)
                return response
            except:
                return {"tokenName": "Extraction error", "tokenSymbol": "Extraction error", "chains": "Extraction error"}
    return {"tokenName": "Extraction error", "tokenSymbol": "Extraction error", "chains": "Extraction error"}

lunchpad_prompt = 'You are a helpful assistant. brief and precise. You are extracting information from scrapped crypto project websites.\n' \
                  'Extract all information about lunchpad participation if the information is available!\n' \
                  'If lunchpad participation is not mentioned then answer: No information found!\n\n' \
                  'Text chunks from website:\n'


def extract_lunchpad_info(text_chunks, embeddings, logger, max_retries=3):
    project_context = get_project_context(text_chunks, embeddings, prompt=lunchpad_prompt, top_k=10)
    #logger.info(f'chain extraction context: {project_context}')

    retries = 0
    while retries < max_retries:
        response = get_openai_completion(lunchpad_prompt + project_context, logger)
        if response is None:
            time.sleep(1)
        else:
            return response
    return 'Extraction failed.'
