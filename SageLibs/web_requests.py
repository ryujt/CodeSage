import json
import requests
import logging
from requests.exceptions import RequestException
from .config import get_settings, API_URL, CHAT_API_URL, EMBEDDINGS_MODEL, CHAT_MODEL, CLAUDE_API_URL, CLAUDE_MODEL

def get_embedding(text):
    settings = get_settings()

    headers = {
        "Authorization": f"Bearer {settings['openai_api_key']}",
        "Content-Type": "application/json"
    }

    data = json.dumps({
        "input": text,
        "model": EMBEDDINGS_MODEL,
        "encoding_format": "float"
    })

    try:
        response = requests.post(API_URL, headers=headers, data=data)
        response.raise_for_status()
        result = response.json()
        if 'data' not in result or not result['data']:
            raise ValueError(f"Unexpected API response structure: {result}")
        return result['data'][0]['embedding']
    except RequestException as e:
        if hasattr(e, 'response') and e.response is not None:
            if e.response.status_code == 401:
                logging.error("API 키 인증 실패. API 키를 확인하세요.")
                raise ValueError("API 키 인증 실패") from e
            else:
                logging.error(f"API 요청 실패: 상태 코드 {e.response.status_code}")
        else:
            logging.error(f"API 요청 실패: {str(e)}")
        raise
    except (KeyError, IndexError, ValueError) as e:
        logging.error(f"API 응답 처리 오류: {str(e)}")
        raise

def get_chat_response(user_message):    
    settings = get_settings()

    system_message = """You are an AI assistant specialized in answering questions based on provided context. 
Your task is to:
    1. Then, Analyze the full content of the documents if necessary.
    2. Answer the user's question accurately using information from the context.
    3. If the context doesn't contain enough information, say so and provide the best possible answer based on your general knowledge.
    4. Cite the filenames of relevant documents in your answer.
    5. If appropriate, provide code snippets or examples from the context to support your answer.
    6. When creating diagrams, use mermaid."""

    claude_api_key = settings.get('claude_api_key', '')
    if claude_api_key:
        return get_chat_response_claude(claude_api_key, system_message, user_message)
    else:
        return get_chat_response_openai(settings['openai_api_key'], system_message, user_message)

def get_chat_response_openai(api_key, system_message, user_message):
    logging.debug("OpenAI API 호출 시작")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]

    data = json.dumps({
        "model": CHAT_MODEL,
        "messages": messages,
        "temperature": 0
    })
    try:
        response = requests.post(CHAT_API_URL, headers=headers, data=data)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except RequestException as e:
        logging.error(f"Chat API 요청 실패: {str(e)}")
        raise
    except (KeyError, IndexError) as e:
        logging.error(f"Chat API 응답 처리 오류: {str(e)}")
        raise

def get_chat_response_claude(api_key, system_message, user_message):
    logging.debug("Claude API 호출 시작")

    settings = get_settings()

    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }    

    data = json.dumps({
        "model": CLAUDE_MODEL,
        "max_tokens": 4000,
        "temperature": 0,
        "system": system_message,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_message
                    }
                ]
            }
        ],
    })
    
    response = requests.post(CLAUDE_API_URL, headers=headers, data=data)
    response_json = response.json()
    
    if 'content' in response_json:
        return response_json['content'][0]['text']
    elif 'error' in response_json:
        return f"Error: {response_json['error']['message']}"
    else:
        return "Unexpected response structure from Claude API"    