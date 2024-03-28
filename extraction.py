import re
import time
import json
from chunk_selection import get_project_context
from llm_connection import get_openai_completion
from token_contract import query_base_token_info


def set_none(data: dict):
    for k, v in data.items():
        data[k] = None if (v == "No information found!") or (v == ["No information found!"]) else v
    return data


err_msg = "Extraction error"

memecoin_prompt = 'You are a helpful assistant. brief and precise. You are extracting information from scrapped crypto project websites.\n' \
                  'Decide if the ###URL### project is about a memecoin or not!\n\n' \
                  'Answer format is parseable JSON!\n' \
                  'Example 1: {"is_memecoin": true}\n' \
                  'Example 2: {"is_memecoin": false}\n\n' \
                  'Text chunks from website:\n'


def extract_memecoin_status(url: str, text_chunks, embeddings, logger, max_retries=3):
    augmented_memecoin_prompt = memecoin_prompt.replace('###URL###', url)
    project_context = get_project_context(text_chunks, embeddings, prompt=augmented_memecoin_prompt, top_k=10)
    #logger.info(f'meme extraction context: {project_context}')

    error_out = False
    retries = 0
    while retries < max_retries:
        response = get_openai_completion(augmented_memecoin_prompt + project_context, logger)
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
               'You are looking for the main utility token/coin of the ###URL### project!' \
               'Tokens sometimes called as coins!' \
               'Sometimes the token symbol starts with a $ sign! Token symbols have multiple uppercase letter!' \
               'Project tokens often paired with other currencies like USD, ETH, SOL, etc.\n' \
               'Extract the\n' \
               '- token name\n' \
               '- token symbol\n' \
               '- ETH style complete token contract address\n' \
               '- chains the project is deployed!\n' \
               'If there is no information in the text for a JSON field then answer: No information found!\n' \
               'Answer format is parseable JSON!\n' \
               'Example 1: {"tokenName": "ExampleToken", "tokenSymbol": "ET", "chains": ["Ethereum", "BSC"], "token_contract_address": ["0x323665443CEf804A3b5206103304BD4872EA4253"]}\n' \
               'Example 2: {"tokenName": "DummyTokenName", "tokenSymbol": "TIA", "chains": ["Solana"], "token_contract_address": "No information found"}\n' \
               'Example 3: {"tokenName": "No information found", "tokenSymbol": "TADA", "chains": "No information found", "token_contract_address": ["0xdAC17F958D2ee523a2206206994597C13D831ec7"]}\n\n' \
               'Text chunks from website:\n'


def extract_token_info(url: str, text_chunks, embeddings, logger, max_retries=3):
    augmented_token_prompt = token_prompt.replace('###URL###', url)
    project_context = get_project_context(text_chunks, embeddings, prompt=augmented_token_prompt, top_k=10)

    # Help LLM by recommending token symbol candidates with regex
    def find_token_symbol_candidates(s):
        # Pattern to match words that contain at least two consecutive uppercase letters
        pattern = r'\b\w*[A-Z]{2,}\w*\b'
        return list(set(re.findall(pattern, s)))  # deduplicated
    token_symbol_candidates = find_token_symbol_candidates(project_context)
    if len(token_symbol_candidates) > 0:
        project_context = f'Regex token symbol candidates: {token_symbol_candidates}\n\n' + project_context
    #logger.info(f'token extraction context: {project_context}')

    def call_llm(base_prompt, context, logger, max_retries):
        error_out = {"tokenName": err_msg, "tokenSymbol": err_msg, "chains": err_msg, "token_contract_address": err_msg}
        retries = 0
        while retries < max_retries:
            response = get_openai_completion(base_prompt + context, logger)
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

### PDF extractions ###


industry_prompt = 'You are a helpful assistant. Brief and precise. You are extracting information from scrapped crypto project websites.\n' \
                 'Extract the ###URL### product\n' \
                 '- the problems the product solves\n' \
                 '- the solutions the product offers for the problems\n' \
                 '- strengths (SWOT analysis)\n' \
                 '- weaknesses (SWOT analysis)\n' \
                 '- opportunities (SWOT analysis)\n' \
                 '- threats (SWOT analysis)\n' \
                 'If there is no information in the text for a JSON field then answer: No information found!\n' \
                 'Answer format is parseable JSON!\n' \
                 'Example format: {"problems": problems, "solutions": solutions, "strengths": strengths, "weaknesses": weaknesses, "opportunities": opportunities, "threats": threats}\n\n' \
                 'Text chunks from website:\n'


def extract_industry_info(url: str, text_chunks, embeddings, logger, max_retries=3):
    augmented_industry_prompt = industry_prompt.replace('###URL###', url)
    project_context = get_project_context(text_chunks, embeddings, prompt=augmented_industry_prompt, top_k=15)
    # logger.info(f'backers extraction context: {project_context}')

    retries = 0
    while retries < max_retries:
        response = get_openai_completion(augmented_industry_prompt + project_context, logger)
        if response is None:
            time.sleep(1)
        else:
            return set_none(json.loads(response))
    return err_msg


team_prompt = 'You are a helpful assistant. Brief and precise. You are extracting information from scrapped crypto project websites.\n' \
              'Extract the ###URL### project team members!\n' \
                 '- members (persons)\n' \
                 '- member positions (CEO, CTO, etc.)\n' \
                 '- member Twitter handle\n' \
                 '- member LinkedIn handle\n' \
                 'If there is no information in the text for a JSON field then answer: No information found!\n' \
                 'Answer format is parseable JSON!\n' \
                 'Example format: {"members": [{"name": member name, "position": member position, "twitter": member Twitter handle, "linkedin": member LinkedIn handle}]}\n\n' \
                 'Text chunks from website:\n'


def extract_team_info(url: str, text_chunks, embeddings, logger, max_retries=3):
    augmented_team_prompt = team_prompt.replace('###URL###', url)
    project_context = get_project_context(text_chunks, embeddings, prompt=augmented_team_prompt, top_k=10)
    # logger.info(f'backers extraction context: {project_context}')

    retries = 0
    while retries < max_retries:
        response = get_openai_completion(augmented_team_prompt + project_context, logger)
        if response is None:
            time.sleep(1)
        else:
            data = set_none(json.loads(response))
            if data["members"] is not None:
                data["members"] = [set_none(member) for member in data["members"]]
            return data
    return err_msg


backers_prompt = 'You are a helpful assistant. Brief and precise. You are extracting information from scrapped crypto project websites.\n' \
                 'Extract the ###URL###  project\n' \
                 '- partnerships (projects or companies)\n' \
                 '- investors (persons, projects or companies)\n' \
                 '- lunchpads (platform where a project can raise funds before public listing)\n' \
                 'If there is no information in the text for a JSON field then answer: No information found!\n' \
                 'Answer format is parseable JSON!\n' \
                 'Example format: {"partnerships": partnerships, "investors": investors, "lunchpads": lunchpads}\n\n' \
                 'Text chunks from website:\n'


def extract_backers_info(url: str, text_chunks, embeddings, logger, max_retries=3):
    augmented_backers_prompt = backers_prompt.replace('###URL###', url)
    project_context = get_project_context(text_chunks, embeddings, prompt=augmented_backers_prompt, top_k=10)
    # logger.info(f'backers extraction context: {project_context}')

    retries = 0
    while retries < max_retries:
        response = get_openai_completion(augmented_backers_prompt + project_context, logger)
        if response is None:
            time.sleep(1)
        else:
            data = set_none(json.loads(response))
            if data['partnerships'] is not None:
                data['partnerships'] = [i for i in data['partnerships'] if i not in data['investors']]
                data['partnerships'] = data['partnerships'] if len(data['partnerships']) > 0 else None
            return data
    return err_msg


tokenomics_prompt = 'You are a helpful assistant. Brief and precise. You are extracting information from scrapped crypto project websites.\n' \
                    'You are looking for investment related details on the main utility token/coin of the project!' \
                    'Extract the ###URL### project\n' \
                    '- token utility and purpose\n' \
                    '- token economy (designed mechanisms which drive supply and demand)\n' \
                    '- tokenomics (token distribution, vesting and other factors)\n' \
                    '- valuation (information about token price if capital is raised by the project)\n' \
                    'If there is no information in the text for a JSON field then answer: No information found!\n' \
                    'Answer format is parseable JSON!\n' \
                    'Example format: {"token_utility": token utility, "token_economy": token economy, "tokenomics": tokenomics, "valuation": valuation}\n\n' \
                    'Text chunks from website:\n'


def extract_tokenomics_info(url: str, text_chunks, embeddings, logger, max_retries=3):
    augmented_tokenomics_prompt = tokenomics_prompt.replace('###URL###', url)
    project_context = get_project_context(text_chunks, embeddings, prompt=augmented_tokenomics_prompt, top_k=20)
    # logger.info(f'tokenomics extraction context: {project_context}')

    retries = 0
    while retries < max_retries:
        response = get_openai_completion(augmented_tokenomics_prompt + project_context, logger)
        if response is None:
            time.sleep(1)
        else:
            return set_none(json.loads(response))
    return err_msg


financials_prompt = 'You are a helpful assistant. Brief and precise. You are extracting information from scrapped crypto project websites.\n' \
                    'Extract the ###URL### project\n' \
                    '- revenue model\n' \
                    'If there is no information in the text for a JSON field then answer: No information found!\n' \
                    'Answer format is parseable JSON!\n' \
                    'Example format: {"revenue": revenue model}\n\n' \
                    'Text chunks from website:\n'


def extract_financials_info(url: str, text_chunks, embeddings, logger, max_retries=3):
    augmented_financials_prompt = financials_prompt.replace('###URL###', url)
    project_context = get_project_context(text_chunks, embeddings, prompt=augmented_financials_prompt, top_k=10)
    # logger.info(f'tokenomics extraction context: {project_context}')

    retries = 0
    while retries < max_retries:
        response = get_openai_completion(augmented_financials_prompt + project_context, logger)
        if response is None:
            time.sleep(1)
        else:
            return set_none(json.loads(response))
    return err_msg


market_strat_prompt = 'You are a helpful assistant. Brief and precise. You are extracting information from scrapped crypto project websites.\n' \
                      'You are looking for investment related details! Extract the ###URL### project\n' \
                      '- product description (structured summary)\n' \
                      '- general market information (size, growth, outlook)\n' \
                      '- go-to-market strategy\n' \
                      '- project roadmap\n' \
                      'If there is no information in the text for a JSON field then answer: No information found!\n' \
                      'Answer format is parseable JSON!\n' \
                      'Example format: {"details": product description, "market": market information, "GTG": go-to-market, "roadmap": roadmap}\n\n' \
                      'Text chunks from website:\n'


def extract_market_strat_prompt_info(url: str, text_chunks, embeddings, logger, max_retries=3):
    augmented_market_strat_prompt = market_strat_prompt.replace('###URL###', url)
    project_context = get_project_context(text_chunks, embeddings, prompt=augmented_market_strat_prompt, top_k=10)
    # logger.info(f'market strategy extraction context: {project_context}')

    retries = 0
    while retries < max_retries:
        response = get_openai_completion(augmented_market_strat_prompt + project_context, logger)
        if response is None:
            time.sleep(1)
        else:
            return set_none(json.loads(response))
    return err_msg
