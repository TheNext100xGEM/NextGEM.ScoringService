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
project_collection = db['projects']
settings_collection = db['settings']


def resolve_project(request_data: dict, logger):
    """ Expecting the request_data to have either websiteUrl or projectID key """
    if 'websiteUrl' in request_data.keys():
        url = request_data['websiteUrl']
        result = project_collection.find_one({'websiteLink': url})
        if result is None:
            logger.info('URL not found in DB! Creating new record!')
            result = project_collection.insert_one({'websiteLink': url, 'createdAt': datetime.datetime.now()})
            # Ensure two values are returned here by also returning url
            return str(result.inserted_id), url  
        # Ensure two values are returned
        return str(result['_id']), url
    elif 'projectID' in request_data.keys():
        scoring_info = get_task(request_data['projectID'])
        if scoring_info is not None:
            return request_data['projectID'], scoring_info['websiteLink']
        else:
            # This handles the case where the project ID is not found
            return None, None  
    else:
        # Correctly define the raise to throw an exception
        raise Exception('Unexpected input for resolve_project function!')


def store(taskid: str, data: dict):
    data['updatedAt'] = datetime.datetime.now()
    all_fields = project_collection.find_one({'_id': ObjectId(taskid)})
    
    #If all_fields already has field, do not overwrite.
    
    keys_to_remove = set(all_fields.keys()) - {'_id', 'updatedAt'}
    for key in keys_to_remove:
        data.pop(key, None)

    project_collection.update_one({'_id': ObjectId(taskid)}, {'$set': data})


def check_taskid(taskid: str):
    try:
        result = project_collection.find_one({'_id': ObjectId(taskid)})
        if result is not None:
            return True
    except Exception:
        return None


def get_task(taskid: str):
    try:
        result = project_collection.find_one({'_id': ObjectId(taskid)})
        result['_id'] = str(result['_id'])
        # TODO: remove the updatedAt manipulation
        if 'updatedAt' in result.keys():
            result['updatedAt'] = result['updatedAt'].strftime("%m/%d/%Y, %H:%M:%S")
        return result
    except Exception:
        return None


def update_memecoin_season(is_memecoin_season: bool):
    data = {
        'value': is_memecoin_season,
        'updatedAt': datetime.datetime.now()
    }
    settings_collection.update_one({'_id': 'isMemeSeason'}, {'$set': data})
