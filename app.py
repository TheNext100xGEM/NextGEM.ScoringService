from flask import Flask, request, jsonify
import threading
from crawler import crawl
from vectorize import vectorize
from chunk_selection import get_project_context
from scoring import call_gpt_agent, call_gemini_agent, call_mistral_agent
import database_connection as db

import logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
isError = False
num_jobs = 0


def processing_task(url: str, taskid: str):
    # Tracking active processing jobs
    global num_jobs
    num_jobs += 1

    # Processing
    documents = crawl(url)  # scrape URL and related documents
    text_chunks, embeddings = vectorize(documents)  # chunk documents and vectorize chunks
    project_context = get_project_context(text_chunks, embeddings, top_k=40)

    res1 = call_gpt_agent(project_context)
    res2 = call_mistral_agent(project_context)
    res3 = call_gemini_agent(project_context)

    result = {
        'gpt_score': res1['score'],
        'gpt_raw': res1['description'],
        'mistral_score': res2['score'],
        'mistral_raw': res2['description'],
        'gemini_score': res3['score'],
        'gemini_raw': res3['description'],
    }
    db.store(taskid, result)

    # Tracking active processing jobs
    num_jobs -= 1


@app.route('/score', methods=['POST'])
def score():
    """ Starting a project processing job """
    request_data = request.get_json()
    taskid = db.create_new(request_data.get('websiteUrl', ''))

    # TODO handle optional additionalInfo

    # Start the async job
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
