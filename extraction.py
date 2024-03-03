import time
from chunk_selection import get_project_context
from llm_connection import get_openai_completion


token_prompt = 'You are a helpful assistant. brief and precise. You are extracting information from scrapped crypto project websites.\n' \
               'Extract the name of the token and token symbol!\n' \
               'If no token or token symbol mentioned in the text then answer: No information found!\n' \
               'Answer format:\n' \
               'token name, token symbol'


def extract_token_info(text_chunks, embeddings, logger, max_retries=3):
    project_context = get_project_context(text_chunks, embeddings, prompt=token_prompt, top_k=10)
    #logger.info(f'chain extraction context: {project_context}')

    retries = 0
    while retries < max_retries:
        response = get_openai_completion(token_prompt + project_context, logger)
        if response is None:
            time.sleep(1)
        else:
            return response
    return 'Extraction failed.'

lunchpad_prompt = 'You are a helpful assistant. brief and precise. You are extracting information from scrapped crypto project websites.\n' \
                  'Extract all information about lunchpad participation if the information is available!\n' \
                  'If lunchpad participation is not mentioned then answer: No information found!'


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

chain_prompt = 'You are a helpful assistant. brief and precise. You are extracting information from scrapped crypto project websites.\n' \
               'Extract which chains the project available or planning to be deployed!\n' \
               'If no chain mentioned in the text then answer: No chain information found!'


def extract_chain_info(text_chunks, embeddings, logger, max_retries=3):
    project_context = get_project_context(text_chunks, embeddings, prompt=chain_prompt, top_k=10)
    #logger.info(f'chain extraction context: {project_context}')

    retries = 0
    while retries < max_retries:
        response = get_openai_completion(chain_prompt + project_context, logger)
        if response is None:
            time.sleep(1)
        else:
            return response
    return 'Extraction failed.'
