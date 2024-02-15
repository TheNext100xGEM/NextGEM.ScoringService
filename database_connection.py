def store(taskid: str, result: dict):
    # TODO implement
    pass

def check_taskid(taskid: str):
    # TODO implement
    return True

def get_task(taskid: str):
    # TODO implement
    scoring_info = {
        'gpt': {
            'score': 5
        },
        'gemini': {
            'score': 5
        },
        'mistral': {
            'score': 5
        },
    }
    return scoring_info
