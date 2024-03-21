import re
import time
import json
from chunk_selection import get_project_context
from llm_connection import get_openai_completion
from token_contract import query_base_token_info

err_msg = "Extraction error"

memecoin_prompt = 'You are a helpful assistant. brief and precise. You are extracting information from scrapped crypto project websites.\n' \
                  'Decide if the project is about a memecoin or not!\n\n' \
                  'Answer format is parseable JSON!\n' \
                  'Example 1: {"is_memecoin": true}\n' \
                  'Example 2: {"is_memecoin": false}\n\n' \
                  'Text chunks from website:\n'


def extract_memecoin_status(text_chunks, embeddings, logger, max_retries=3):
    project_context = get_project_context(text_chunks, embeddings, prompt=memecoin_prompt, top_k=10)
    #logger.info(f'chain extraction context: {project_context}')

    error_out = False
    retries = 0
    while retries < max_retries:
        response = get_openai_completion(memecoin_prompt + project_context, logger)
        if response is None:
            time.sleep(1)
        else:
            try:
                return json.loads(response)['is_memecoin']
            except Exception as e:
                logger.info(f'Failed json conversion: {response} - {e}')
                return error_out
    return error_out


token_prompt = 'You are a helpful assistant. brief and precise. You are extracting information from scrapped crypto project websites.\n' \
               'Extract the\n' \
               '- token name\n' \
               '- token symbol\n' \
               '- ETH style complete token contract address\n' \
               '- chains the project is deployed!\n' \
               'The token can be referenced as coin!' \
               'Sometimes the token symbol starts with a $ sign! Token symbols have multiple uppercase letter!' \
               'Project tokens often paired with other currencies like USD, ETH, SOL, etc.\n' \
               'Sort token symbols by importance for the project.\n' \
               'If there is no information in the text for a JSON field then answer: No information found!\n' \
               'Answer format is parseable JSON!\n' \
               'Example 1: {"tokenName": "ExampleToken", "tokenSymbol": "ET", "chains": ["Ethereum", "BSC"], "token_contract_address": ["0x323665443CEf804A3b5206103304BD4872EA4253"]}\n' \
               'Example 2: {"tokenName": "DummyTokenName", "tokenSymbol": "TIA", "chains": ["Solana"], "token_contract_address": "No information found"}\n' \
               'Example 3: {"tokenName": "No information found", "tokenSymbol": "TADA", "chains": "No information found", "token_contract_address": ["0xdAC17F958D2ee523a2206206994597C13D831ec7"]}\n\n' \
               'Text chunks from website:\n'


def extract_token_info(text_chunks, embeddings, logger, max_retries=3):
    project_context = get_project_context(text_chunks, embeddings, prompt=token_prompt, top_k=10)

    # Help LLM by recommending token symbol candidates with regex
    def find_token_symbol_candidates(s):
        # Pattern to match words that contain at least two consecutive uppercase letters
        pattern = r'\b\w*[A-Z]{2,}\w*\b'
        return list(set(re.findall(pattern, s))) # deduplicated
    token_symbol_candidates = find_token_symbol_candidates(project_context)
    if len(token_symbol_candidates) > 0:
        project_context = f'Regex token symbol candidates: {token_symbol_candidates}\n\n' + project_context
    #logger.info(f'chain extraction context: {project_context}')

    def call_llm(token_prompt, project_context, logger, max_retries):
        error_out = {"tokenName": err_msg, "tokenSymbol": err_msg, "chains": err_msg, "token_contract_address": err_msg}
        retries = 0
        while retries < max_retries:
            response = get_openai_completion(token_prompt + project_context, logger)
            if response is None:
                time.sleep(1)
            else:
                try:
                    return json.loads(response)
                except Exception as e:
                    logger.info(f'Failed json conversion: {response} - {e}')
                    return error_out
        return error_out

    token_info = call_llm(token_prompt, project_context, logger, max_retries)

    # Token info from token contract address query
    if type(token_info["token_contract_address"]) is list:
        logger.info(f'Trying to query token details from contract address(es): {token_info["token_contract_address"]}')
        res = query_base_token_info(token_info["token_contract_address"])
        if res is not None:
            return {"tokenName": res[0], "tokenSymbol": res[1], "token_total_supply": res[2], "chains": token_info["chains"]}
    logger.info(f'Fallback to LLM extracted info! Formatting: {token_info}')

    # Formatting LLm extracted token info (fallback)
    def format_token_info(token_name, token_symbol):
        if token_name == "No information found" and token_symbol == "No information found":
            return token_name, token_symbol

        # Handling edge case if multiple token symbol is present (list of symbols)
        if type(token_symbol) is list:
            token_symbol = token_symbol[0]

        def clean_and_format(string, format_type):
            cleaned_string = re.sub(r'\W+', '', string)
            if format_type == 'camelCase':
                return ''.join(word.capitalize() for word in cleaned_string.split())
            elif format_type == 'ALLCAPS':
                return cleaned_string.upper()

        if token_name != "No information found":
            formatted_token_name = clean_and_format(token_name, 'camelCase')
        else:
            formatted_token_name = clean_and_format(token_symbol, 'camelCase')

        if token_symbol != "No information found":
            formatted_token_symbol = clean_and_format(token_symbol, 'ALLCAPS')
        else:
            formatted_token_symbol = clean_and_format(token_name, 'ALLCAPS')

        return formatted_token_name, formatted_token_symbol

    formatted_token_name, formatted_token_symbol = format_token_info(token_info['tokenName'], token_info['tokenSymbol'])

    return {"tokenName": formatted_token_name, "tokenSymbol": formatted_token_symbol, "chains": token_info['chains']}


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
    return err_msg
