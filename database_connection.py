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
            'score': 5,
            'description': 'dummy scoring related rambling'
        },
        'gemini': {
            'score': 5,
            'description': 'dummy scoring related rambling'
        },
        'mistral': {
            'score': 5,
            'description': 'dummy scoring related rambling'
        }
    }
    return scoring_info
