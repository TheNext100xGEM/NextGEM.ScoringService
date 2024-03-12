from requests import Session
import json


with open('config.json', 'r') as file:
    config = json.load(file)
coinmarketcap_key = config["COINMARKETCAP_KEY"]


def get_doge_data():
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    parameters = {
        'start': '1',
        'limit': '50',
        'convert': 'USD'
    }
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': coinmarketcap_key,
    }

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params=parameters)
        parsed_response = json.loads(response.text)
        doge = list(filter(lambda x: x.get('symbol', '') == 'DOGE', parsed_response['data']))[0]
        return doge
    except Exception:
        return None
