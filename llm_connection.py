import json
import openai
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import requests

# API keys
with open('config.json', 'r') as file:
    config = json.load(file)

openai_client = openai.OpenAI(api_key=config['OPENAI_API_KEY'])
mistral_client = MistralClient(api_key=config["MISTRAL_API_KEY"])
genai_key=config["GEMINI_API_KEY"]


def get_openai_embedding(text, client=openai_client):
    try:
        response = client.embeddings.create(model="text-embedding-3-small",
                                            input=text,
                                            encoding_format="float")
        return response.data[0].embedding
    except:
        return None


def get_openai_completion(prompt, logger, client=openai_client, temp=0.0):
    try:
        chat_completion = client.chat.completions.create(messages=[{"role": "user", "content": prompt}],
                                                         model="gpt-4-0125-preview",
                                                         temperature=temp)
        return chat_completion.choices[0].message.content.replace('```', '').replace('json', '')
    except Exception as e:
        logger.error(f'Openai answer generation error: {e}')
        return None


def get_mistral_completion(prompt, logger, client=mistral_client, temp=0.0):
    try:
        chat_completion = client.chat(messages=[ChatMessage(role="user", content=prompt)],
                                      model="mistral-large-latest",
                                      temperature=temp,
                                      safe_mode=False)
        return chat_completion.choices[0].message.content.replace('```', '').replace('json', '')
    except Exception as e:
        logger.error(f'Mistral answer generation error: {e}')
        return None


def get_gemini_completion(prompt, logger, temp=0.0):
    try:
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        headers = {
            'Content-Type': 'application/json',
        }
        params = {
            'key': genai_key,
        }
        data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ],
            "generationConfig": {
                "temperature": temp,
                "candidate_count": 1
            }
        }
        response = requests.post(url, headers=headers, params=params, json=data)
        chat_completion = response.json()
        return chat_completion['candidates'][0]['content']['parts'][0]['text'].replace('```', '').replace('json', '')
    except Exception as e:
        logger.error(f'Gemini answer generation error: {e}')
        return None
