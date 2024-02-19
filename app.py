import uuid
from flask import Flask, request, jsonify
import threading
from crawler import crawl
from vectorize import vectorize
from scoring import call_gpt_agent, call_gemini_agent, call_mistral_agent
import database_connection as db

app = Flask(__name__)
isError = False
num_jobs = 0


def processing_task(url: str, taskid: str):
    # Tracking active processing jobs
    global num_jobs
    num_jobs += 1

    # Processing
    documents = crawl(url)  # scrape URL and related documents
    vectorize(documents)    # chunk documents and vectorize chunks

    result = {
        'gpt': call_gpt_agent(),
        'gemini': call_gemini_agent(),
        'mistral': call_mistral_agent()
    }
    db.store(taskid, result)

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
