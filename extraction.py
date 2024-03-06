import re
import time
import json
from chunk_selection import get_project_context
from llm_connection import get_openai_completion


token_prompt = 'You are a helpful assistant. brief and precise. You are extracting information from scrapped crypto project websites.\n' \
               'Extract the name of the token, token symbol and which chains is the project deployed! The token can be referenced as coin!' \
               'Sometimes the token symbol starts with a $ sign! Project tokens often paired with other currencies like USD, ETH, SOL, etc.\n' \
               'If there is no information in the text for a field then answer: No information found!\n' \
               'Answer format is parseable JSON!\n' \
               'Example 1: {"tokenName": "ExampleToken", "tokenSymbol": "ET", "chains": ["Ethereum", "BSC"]}\n' \
               'Example 2: {"tokenName": "DummyTokenName", "tokenSymbol": "TIA", "chains": ["Solana"]}\n' \
               'Example 3: {"tokenName": "No information found", "tokenSymbol": "TADA", "chains": ["No information found"]}\n\n' \
               'Text chunks from website:\n'


def extract_token_info(text_chunks, embeddings, logger, max_retries=3):
    project_context = get_project_context(text_chunks, embeddings, prompt=token_prompt, top_k=10)
    #logger.info(f'chain extraction context: {project_context}')

    def call_llm(token_prompt, project_context, logger, max_retries):
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

    token_info = call_llm(token_prompt, project_context, logger, max_retries)

    def format_token_info(tokenName, tokenSymbol):
        if tokenName == "No information found" and tokenSymbol == "No information found":
            return tokenName, tokenSymbol

        def clean_and_format(string, format_type):
            cleaned_string = re.sub(r'\W+', '', string)
            if format_type == 'camelCase':
                return ''.join(word.capitalize() for word in cleaned_string.split())
            elif format_type == 'ALLCAPS':
                return cleaned_string.upper()

        if tokenName != "No information found":
            formatted_tokenName = clean_and_format(tokenName, 'camelCase')
        else:
            formatted_tokenName = clean_and_format(tokenSymbol, 'camelCase')

        if tokenSymbol != "No information found":
            formatted_tokenSymbol = clean_and_format(tokenSymbol, 'ALLCAPS')
        else:
            formatted_tokenSymbol = clean_and_format(tokenName, 'ALLCAPS')

        return formatted_tokenName, formatted_tokenSymbol

    formatted_tokenName, formatted_tokenSymbol = format_token_info(token_info['tokenName'], token_info['tokenSymbol'])

    return {"tokenName": formatted_tokenName, "tokenSymbol": formatted_tokenSymbol, "chains": token_info['chains']}


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
