import json
import openai
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import google.generativeai as genai

# API keys
with open('config.json', 'r') as file:
    config = json.load(file)

openai_client = openai.OpenAI(api_key=config['OPENAI_API_KEY'])
mistral_client = MistralClient(api_key=config["MISTRAL_API_KEY"])
genai.configure(api_key=config["GEMINI_API_KEY"])


def get_openai_embedding(text, client=openai_client):
    try:
        response = client.embeddings.create(model="text-embedding-3-small",
                                            input=text,
                                            encoding_format="float")
        return response.data[0].embedding
    except:
        return None


def get_openai_completion(prompt, client=openai_client, temp=0.0):
    try:
        chat_completion = client.chat.completions.create(messages=[{"role": "user", "content": prompt}],
                                                         model="gpt-4-0125-preview",
                                                         temperature=temp)
        return chat_completion.choices[0].message.content
    except:
        return None


def get_mistral_completion(prompt, client=mistral_client, temp=0.0):
    try:
        chat_completion = client.chat(messages=[ChatMessage(role="user", content=prompt)],
                                      model="mistral-small",
                                      temperature=temp)
        return chat_completion.choices[0].message.content
    except:
        return None


def get_gemini_completion(prompt, temp=0.0):
    try:
        model = genai.GenerativeModel('gemini-pro')
        generation_config = genai.types.GenerationConfig(candidate_count=1, temperature=temp)
        chat_completion = model.generate_content(prompt, generation_config=generation_config)
        return chat_completion.text
    except:
        return None
