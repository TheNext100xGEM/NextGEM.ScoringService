import uuid
import json
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
temp_result_memory = {}  # TODO remove when db connecton is up


def processing_task(url: str, taskid: str):
    # Tracking active processing jobs
    global num_jobs
    num_jobs += 1

    # Processing
    documents = crawl(url)  # scrape URL and related documents
    text_chunks, embeddings = vectorize(documents)  # chunk documents and vectorize chunks
    project_context = get_project_context(text_chunks, embeddings, top_k=40)

    result = {
        'gpt': call_gpt_agent(project_context),
        'gemini': call_gemini_agent(project_context),
        'mistral': call_mistral_agent(project_context)
    }

    # TODO replace when db connection is up
    global temp_result_memory
    temp_result_memory[taskid] = result
    #db.store(taskid, result)

    # Tracking active processing jobs
    num_jobs -= 1


@app.route('/score', methods=['POST'])
def score():
    """ Starting a project processing job """
    request_data = request.get_json()
    taskid = str(uuid.uuid4())

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

    # TODO replace when db connection is up
    global temp_result_memory
    try:
        scoring_info = temp_result_memory[taskid]
    except:
        scoring_info = None
    #scoring_info = db.get_task(taskid)

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
