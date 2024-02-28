from flask import Flask, request, jsonify
import threading
from crawler import crawl
from vectorize import vectorize
from chunk_selection import get_project_context
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


def processing_task(url: str, taskid: str):
    # Tracking active processing jobs
    global num_jobs
    num_jobs += 1

    # Processing
    app.logger.info(f'[{taskid}] URL scrapping started.')
    documents = crawl(url)  # scrape URL and related documents
    app.logger.info(f'[{taskid}] URL scrapping ended.')
    text_chunks, embeddings = vectorize(documents)  # chunk documents and vectorize chunks
    app.logger.info(f'[{taskid}] Project documentation chunked and vectorized. Chunk count: {len(text_chunks)}')
    project_context = get_project_context(text_chunks, embeddings, top_k=40)
    app.logger.info(f'[{taskid}] Task relevant text chunks selected. Char count: {len(project_context)}')

    app.logger.info(f'[{taskid}] Calling OpenAI agent.')
    res1 = call_gpt_agent(project_context)
    app.logger.info(f'[{taskid}] Calling Mistral agent.')
    res2 = call_mistral_agent(project_context)
    app.logger.info(f'[{taskid}] Calling Gemini agent.')
    res3 = call_gemini_agent(project_context)
    app.logger.info(f'[{taskid}] All answer arrived.')

    result = {
        'gpt_score': res1['score'],
        'gpt_raw': res1['description'],
        'mistral_score': res2['score'],
        'mistral_raw': res2['description'],
        'gemini_score': res3['score'],
        'gemini_raw': res3['description'],
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

    # TODO handle optional additionalInfo

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

    return jsonify({'isFinished': True, 'scoringInfo': scoring_info}), 200


@app.route('/status', methods=['GET'])
def status():
    """ Endpoint status """
    global isError
    global num_jobs
    return jsonify({'status': not isError, 'concurrent_jobs': num_jobs}), 200


if __name__ == '__main__':
    app.run(debug=True)
