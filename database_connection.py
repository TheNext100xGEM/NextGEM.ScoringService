import json
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime

# DB connection
with open('config.json', 'r') as file:
    config = json.load(file)
mongo_uri = config['mongo_uri']
client = MongoClient(mongo_uri)
db = client['nextgem']  # Database name
collection = db['projects']


def create_new(url: str):
    result = collection.find_one({'websiteLink': url})
    if result is None:
        result = collection.insert_one({'websiteLink': url, 'createdAt': datetime.datetime.now()})
        return str(result.inserted_id)
    return str(result['_id'])


def store(taskid: str, data: dict):
    data['updatedAt'] = datetime.datetime.now()
    collection.update_one({'_id': ObjectId(taskid)}, {'$set': data})


def check_taskid(taskid: str):
    try:
        result = collection.find_one({'_id': ObjectId(taskid)})
        if result is not None:
            return True
    except:
        pass
    return None


def get_task(taskid: str):
    try:
        result = collection.find_one({'_id': ObjectId(taskid)})
        result['_id'] = str(result['_id'])
        if 'updatedAt' in result.keys():
            result['updatedAt'] = result['updatedAt'].strftime("%m/%d/%Y, %H:%M:%S")
        return result
    except:
        return None
