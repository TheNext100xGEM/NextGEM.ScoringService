from flask import Flask, request, jsonify
import threading
from crawler_debug import crawl
from vectorize import vectorize
from extraction import *
from llm_connection import get_openai_completion
from scoring import strict_prompt, moonboy_prompt, call_gpt_agent, call_gemini_agent, call_mistral_agent
from marketcap_utils import get_doge_data
import database_connection as db
from logging.config import dictConfig
from swagger_ui import api_doc

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

app = Flask(__name__)
api_doc(app, config_path='./ScoringSystem-1.0.0-swagger.yaml', url_prefix='/docs', title='API doc')
isError = False
num_jobs = 0

# If true, ai analysis will be returned on the request. If false, just the scraped info of website (and moonboy prompt)
ai_analysis = True
is_meme_season = True  # TODO set manually until calculation is automated


def process_with_prompt_type(url: str, uses_meme: bool, text_chunks, embeddings, taskid: str):
    save_prefix = 'meme_' if uses_meme else ''
    prompt = moonboy_prompt if uses_meme else strict_prompt
    prompt_type = 'meme' if uses_meme else 'strict'

    app.logger.info(f'[{taskid}] Generating analysis for project with prompt type: {prompt_type} ')
    project_context = get_project_context(text_chunks, embeddings, prompt=f'Project: {url}\n{prompt}', top_k=40)
    app.logger.info(f'[{taskid}] Scoring relevant text chunks selected. Char count: {len(project_context)}')
    app.logger.info(f'[{taskid}] Calling OpenAI agent.')
    res1 = call_gpt_agent(url, project_context, not uses_meme, app.logger)
    app.logger.info(f'[{taskid}] OpenAI score: {res1["score"]}')
    app.logger.info(f'[{taskid}] OpenAI description:\n{res1["description"]}')
    app.logger.info(f'[{taskid}] Calling Mistral agent.')
    res2 = call_mistral_agent(url, project_context, not uses_meme, app.logger)
    app.logger.info(f'[{taskid}] Mistral score: {res2["score"]}')
    app.logger.info(f'[{taskid}] Mistral description:\n{res2["description"]}')
    app.logger.info(f'[{taskid}] Calling Gemini agent.')
    if not uses_meme:
        res3 = call_gemini_agent(url, project_context, not uses_meme, app.logger)
        app.logger.info(f'[{taskid}] Gemini score: {res3["score"]}')
        app.logger.info(f'[{taskid}] Gemini description:\n{res3["description"]}')

    # Summary
    if uses_meme:
        summary = get_openai_completion(f'Summarize the project in one sentence!\nOpinion:\n{res1}', app.logger)
        app.logger.info(f'[{taskid}] Summary generated: {summary}')
        return {
            f'{save_prefix}gpt_score': res1['score'],
            f'{save_prefix}gpt_raw': res1['description'],
            f'{save_prefix}mistral_score': res2['score'],
            f'{save_prefix}mistral_raw': res2['description'],
            f'{save_prefix}llm_summary': summary,
        }
    else:
        summary = get_openai_completion(f'Summarize the project in one sentence!\nOpinion 1:\n{res1}\n\nOpinion 2:\n{res2}\n\nOpinion 3:\n{res3}', app.logger)
        app.logger.info(f'[{taskid}] Summary generated: {summary}')
        return {
            f'{save_prefix}gpt_score': res1['score'],
            f'{save_prefix}gpt_raw': res1['description'],
            f'{save_prefix}mistral_score': res2['score'],
            f'{save_prefix}mistral_raw': res2['description'],
            f'{save_prefix}gemini_score': res3['score'],
            f'{save_prefix}gemini_raw': res3['description'],
            f'{save_prefix}llm_summary': summary,
        }


def processing_task(url: str, taskid: str):
    # Tracking active processing jobs
    global num_jobs
    num_jobs += 1

    # Processing
    app.logger.info(f'[{taskid}] URL scrapping started.')
    documents, social_links = crawl(url, app.logger)  # scrape URL and related documents
    app.logger.info(f'[{taskid}] URL scrapping ended.')
    app.logger.info(f'[{taskid}] Social links: {social_links}')
    text_chunks, embeddings = vectorize(documents, logger=app.logger)  # chunk documents and vectorize chunks
    app.logger.info(f'[{taskid}] Project documentation chunked and vectorized. Chunk count: {len(text_chunks)}')

    # Extracting information
    is_memecoin = extract_memecoin_status(url, text_chunks, embeddings, app.logger)
    app.logger.info(f'[{taskid}] Is it a memecoin? {is_memecoin}')
    token_info = extract_token_info(url, text_chunks, embeddings, app.logger)
    app.logger.info(f'[{taskid}] Token info extracted: {token_info}')

    ### PDF related. Will be moved to a different endpoint. ###
    # TODO details
    # summary = get summary field from DB ?
    # narrative = get category field from DB ?
    # details = do the "product description extraction" with marketing maybe?
    industry_info = extract_industry_info(url, text_chunks, embeddings, app.logger)
    app.logger.info(f'[{taskid}] Industry info extracted: {industry_info}')
    team_info = extract_team_info(url, text_chunks, embeddings, app.logger)
    app.logger.info(f'[{taskid}] Team info extracted: {team_info}')
    backers_info = extract_backers_info(url, text_chunks, embeddings, app.logger)
    app.logger.info(f'[{taskid}] Backers info extracted: {backers_info}')
    tokenomics_info = extract_tokenomics_info(url, text_chunks, embeddings, app.logger)
    app.logger.info(f'[{taskid}] Tokenomics info extracted: {tokenomics_info}')
    financials_info = extract_financials_info(url, text_chunks, embeddings, app.logger)
    app.logger.info(f'[{taskid}] Financials info extracted: {financials_info}')
    market_info = extract_market_strat_prompt_info(url, text_chunks, embeddings, app.logger)
    app.logger.info(f'[{taskid}] Market info extracted: {market_info}')
    ### PDF related. Will be moved to a different endpoint. ###

    # Scoring
    uses_meme = is_meme_season and is_memecoin  # Activates moonboy prompt if it's memecoin season
    meme_results = {}
    strict_results = {}

    if uses_meme:
        meme_results = process_with_prompt_type(
            url=url,
            uses_meme=True,
            text_chunks=text_chunks,
            embeddings=embeddings,
            taskid=taskid
        )

    if ai_analysis:
        strict_results = process_with_prompt_type(
            url=url,
            uses_meme=False,
            text_chunks=text_chunks,
            embeddings=embeddings,
            taskid=taskid
        )
    # Saving results
    result = {
        "iteration": 0,
        "analyzed": False,
        "twitterLink": social_links['twitter'],
        "telegramLink": social_links['telegram'],
        "isMemecoin": is_memecoin,
        "tokenName": token_info['tokenName'],
        "tokenSymbol": token_info['tokenSymbol'],
        "chains": token_info['chains']
    }

    if uses_meme:
        result.update(meme_results)

    if ai_analysis:
        result.update(
            {
                "iteration": 1,
                "analyzed": True,
                **strict_results
            }
        )

    db.store(taskid, result)
    app.logger.info(f'[{taskid}] Results saved in DB.')

    # Tracking active processing jobs
    num_jobs -= 1


@app.route('/score', methods=['POST'])
def score():
    """ Starting a project processing job """
    request_data = request.get_json()
    app.logger.info(f'Request arguments: {request_data}')

    if not ('websiteUrl' in request_data or 'projectID' in request_data):
        return jsonify('Missing argument'), 400

    taskid, url = db.resolve_project(request_data, app.logger)
    if taskid is None:
        return jsonify('Project not found'), 404

    # Start the async job
    app.logger.info(f'[{taskid}] Starting to process: {url}')
    thread = threading.Thread(target=processing_task, args=(url, taskid,))
    thread.start()

    return jsonify({'taskid': taskid}), 200


@app.route('/scorings/<taskid>', methods=['GET'])
def scorings(taskid):
    """ Project processing job status and results if available """
    if db.check_taskid(taskid) is None:
        return jsonify({'error': 'Task not found'}), 404

    scoring_info = db.get_task(taskid)

    if scoring_info is None:
        return jsonify({'isFinished': False}), 200

    # Small bug fix that waits for the creation of analyzed field, which means the info is actually ready
    if not ("analyzed" in scoring_info):
        return jsonify({'isFinished': False}), 200
    
    is_analyzed = scoring_info.get('analyzed', False)

    return jsonify({'isFinished': is_analyzed, 'scoringInfo': scoring_info}), 200


@app.route('/memecoin-season', methods=['GET'])
def memecoin_season():
    """ Estimates if it is memecoin season or not """
    doge = get_doge_data()
    if doge is None:
        jsonify({'error': 'Data source is unavailable'}), 500

    doge_mc_dom = doge['quote']['USD']['market_cap_dominance']
    doge_percent_change_30d = doge['quote']['USD']['percent_change_30d']
    is_memecoin_season = True if doge_mc_dom > 0.05 and doge_percent_change_30d > 40 else False
    db.update_memecoin_season(is_memecoin_season)

    out = {
        'isMemecoinSeason': is_memecoin_season,
        'doge_mc_dominance': doge_mc_dom,
        'doge_percent_change_30d': doge_percent_change_30d
    }
    return jsonify(out), 200


@app.route('/status', methods=['GET'])
def status():
    """ Endpoint status """
    global isError
    global num_jobs
    return jsonify({'status': not isError, 'concurrent_jobs': num_jobs}), 200


if __name__ == '__main__':
    app.run(debug=True)
