from flask import Flask, request, jsonify
import threading
from crawler import crawl
from vectorize import vectorize
from chunk_selection import get_project_context
from extraction import extract_memecoin_status, extract_token_info, extract_lunchpad_info
from llm_connection import get_openai_completion
from scoring import strict_prompt, moonboy_prompt, call_gpt_agent, call_gemini_agent, call_mistral_agent
import database_connection as db
from logging.config import dictConfig


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
isError = False
num_jobs = 0

# If true, ai analysis will be returned on the request. If false, just the scraped info of website
ai_analysis = True
is_meme_season = True  # TODO set by hand until calculation is automated

def process_with_prompt_type(uses_meme: bool, text_chunks, embeddings, taskid: str)
    save_suffix = 'meme_' if uses_meme else ''
    prompt = moonboy_prompt if uses_meme else strict_prompt
    prompt_type = 'meme' if uses_meme else 'strict'

    app.logger.info(f'[{taskid}] Generating analysis for project with prompt type: {prompt_type} ')
    project_context = get_project_context(text_chunks, embeddings, prompt=prompt, top_k=40)
    app.logger.info(f'[{taskid}] Scoring relevant text chunks selected. Char count: {len(project_context)}')
    app.logger.info(f'[{taskid}] Calling OpenAI agent.')
    res1 = call_gpt_agent(project_context, not uses_meme, app.logger)
    app.logger.info(f'[{taskid}] OpenAI score: {res1["score"]}')
    app.logger.info(f'[{taskid}] OpenAI description:\n{res1["description"]}')
    app.logger.info(f'[{taskid}] Calling Mistral agent.')
    res2 = call_mistral_agent(project_context, not uses_meme, app.logger)
    app.logger.info(f'[{taskid}] Mistral score: {res2["score"]}')
    app.logger.info(f'[{taskid}] Mistral description:\n{res2["description"]}')
    app.logger.info(f'[{taskid}] Calling Gemini agent.')
    res3 = call_gemini_agent(project_context, not uses_meme, app.logger)
    app.logger.info(f'[{taskid}] Gemini score: {res3["score"]}')
    app.logger.info(f'[{taskid}] Gemini description:\n{res3["description"]}')

    # Summary
    summary = get_openai_completion(f'Summarize the project in one sentence!\nOpinion 1:\n{res1}\n\nOpinion 2:\n{res2}\n\nOpinion 3:\n{res3}', app.logger)
    app.logger.info(f'[{taskid}] Summary generated: {summary}')

    return {
        f'gpt_{save_suffix}score': res1['score'],
        f'gpt_{save_suffix}raw': res1['description'],
        f'mistral_{save_suffix}score': res2['score'],
        f'mistral_{save_suffix}raw': res2['description'],
        f'gemini_{save_suffix}score': res3['score'],
        f'gemini_{save_suffix}raw': res3['description'],
        f'{save_suffix}llm_summary': summary,
    }


def processing_task(url: str, taskid: str):
    # Tracking active processing jobs
    global num_jobs
    num_jobs += 1

    # Processing
    app.logger.info(f'[{taskid}] URL scrapping started.')
    documents, twitter_link, telegram_link = crawl(url, app.logger)  # scrape URL and related documents
    app.logger.info(f'[{taskid}] URL scrapping ended.')
    app.logger.info(f'[{taskid}] Twitter link: {twitter_link}')
    app.logger.info(f'[{taskid}] Telegram link: {telegram_link}')
    text_chunks, embeddings = vectorize(documents)  # chunk documents and vectorize chunks
    app.logger.info(f'[{taskid}] Project documentation chunked and vectorized. Chunk count: {len(text_chunks)}')

    # Extracting information
    is_memecoin = extract_memecoin_status(text_chunks, embeddings, app.logger)
    app.logger.info(f'[{taskid}] Is it a memecoin? {is_memecoin}')
    token_info = extract_token_info(text_chunks, embeddings, app.logger)
    app.logger.info(f'[{taskid}] Token info extracted: {token_info}')
    lunchpad_info = extract_lunchpad_info(text_chunks, embeddings, app.logger)
    app.logger.info(f'[{taskid}] Lunchpad info extracted: {lunchpad_info}')

    # Scoring
    uses_meme = is_meme_season and is_memecoin  # Activates moonboy prompt if it's memecoin season
    meme_results = {}
    strict_results = {}

    if uses_meme:
        meme_results = process_with_prompt_type(
            uses_meme=True,
            text_chunks=text_chunks,
            embeddings=embeddings,
            taskid=taskid
        )

    if ai_analysis:
        strict_results = process_with_prompt_type(
            uses_meme=False,
            text_chunks=text_chunks,
            embeddings=embeddings,
            taskid=taskid
        )
    # Saving results
    result = {
        "iteration": 0,
        "analyzed": False,
        "twitterLink": twitter_link,
        "telegramLink": telegram_link,
        "isMemecoin": is_memecoin,
        "tokenName": token_info['tokenName'],
        "tokenSymbol": token_info['tokenSymbol'],
        "chains": token_info['chains'],
        "submittedDescription": lunchpad_info
    }

    if uses_meme:
        result.update(meme_results)

    if ai_analysis:
        result = {
            **result, 
            "iteration": 1,
            "analyzed": True,
            **strict_results
        }

    db.store(taskid, result)
    app.logger.info(f'[{taskid}] Results saved in DB.')

    # Tracking active processing jobs
    num_jobs -= 1


@app.route('/score', methods=['POST'])
def score():
    """ Starting a project processing job """
    request_data = request.get_json()
    taskid = db.create_new(request_data.get('websiteUrl', ''))

    # Start the async job
    app.logger.info(f'[{taskid}] Starting to process the project')
    thread = threading.Thread(target=processing_task, args=(request_data.get('websiteUrl', ''), taskid,))
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

    return jsonify({'isFinished': True, 'scoringInfo': scoring_info}), 200


@app.route('/status', methods=['GET'])
def status():
    """ Endpoint status """
    global isError
    global num_jobs
    return jsonify({'status': not isError, 'concurrent_jobs': num_jobs}), 200


if __name__ == '__main__':
    app.run(debug=True)
