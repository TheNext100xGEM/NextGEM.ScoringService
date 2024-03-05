import re
from flask import Flask, request, jsonify
import threading
from crawler import crawl
from vectorize import vectorize
from chunk_selection import get_project_context
from extraction import extract_token_info, extract_lunchpad_info
from llm_connection import get_openai_completion
from scoring import call_gpt_agent, call_gemini_agent, call_mistral_agent
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


#If true, ai analysis will be returned on the request. If false, just the scraped info of website
ai_analysis = False

def processing_task(url: str, taskid: str):
    # Tracking active processing jobs
    global num_jobs
    num_jobs += 1

    # Processing
    app.logger.info(f'[{taskid}] URL scrapping started.')
    documents, twitter_link, telegram_link = crawl(url)  # scrape URL and related documents
    app.logger.info(f'[{taskid}] URL scrapping ended.')
    app.logger.info(f'[{taskid}] Twitter link: {twitter_link}')
    app.logger.info(f'[{taskid}] Telegram link: {telegram_link}')
    text_chunks, embeddings = vectorize(documents)  # chunk documents and vectorize chunks
    app.logger.info(f'[{taskid}] Project documentation chunked and vectorized. Chunk count: {len(text_chunks)}')

    # Extracting information
    token_info = extract_token_info(text_chunks, embeddings, app.logger)
    app.logger.info(f'[{taskid}] Token info extracted: {token_info}')
    lunchpad_info = extract_lunchpad_info(text_chunks, embeddings, app.logger)
    app.logger.info(f'[{taskid}] Lunchpad info extracted: {lunchpad_info}')

    # Scoring
    if(ai_analysis):
        project_context = get_project_context(text_chunks, embeddings, top_k=40)
        app.logger.info(f'[{taskid}] Scoring relevant text chunks selected. Char count: {len(project_context)}')
        app.logger.info(f'[{taskid}] Calling OpenAI agent.')
        res1 = call_gpt_agent(project_context, app.logger)
        app.logger.info(f'[{taskid}] OpenAI score: {res1["score"]}')
        app.logger.info(f'[{taskid}] OpenAI description:\n{res1["description"]}')
        app.logger.info(f'[{taskid}] Calling Mistral agent.')
        res2 = call_mistral_agent(project_context, app.logger)
        app.logger.info(f'[{taskid}] Mistral score: {res2["score"]}')
        app.logger.info(f'[{taskid}] Mistral description:\n{res2["description"]}')
        app.logger.info(f'[{taskid}] Calling Gemini agent.')
        res3 = call_gemini_agent(project_context, app.logger)
        app.logger.info(f'[{taskid}] Gemini score: {res3["score"]}')
        app.logger.info(f'[{taskid}] Gemini description:\n{res3["description"]}')
    
        # Summary
        summary = get_openai_completion(f'Summarize the project in one sentence!\nOpinion 1:\n{res1}\n\nOpinion 2:\n{res2}\n\nOpinion 3:\n{res3}', app.logger)
        app.logger.info(f'[{taskid}] Summary generated: {summary}')
    else:
        app.logger.info(f'[{taskid}] Skipping AI Analysis because it is disabled..')


    # Saving results

    formatted_tokenName, formatted_tokenSymbol = format_token_info(token_info['tokenName'], token_info['tokenSymbol'])
    
    result = {
        "iteration": 1,
        "analyzed": True,
        "twitterLink": twitter_link,
        "telegramLink": telegram_link,
        "tokenName": formatted_tokenName,
        "tokenSymbol": formatted_tokenSymbol,
        "chains": token_info['chains'],
        "submittedDescription": lunchpad_info
    }

    if(ai_analysis):
        result = {
            **result, 
            'gpt_score': res1['score'],
            'gpt_raw': res1['description'],
            'mistral_score': res2['score'],
            'mistral_raw': res2['description'],
            'gemini_score': res3['score'],
            'gemini_raw': res3['description'],
            'llm_summary': summary,
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

    #small bug fix that waits for the creation of analyzed field, which means the info is actually ready
    if not scoring_info.hasattr("analyzed"):
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
