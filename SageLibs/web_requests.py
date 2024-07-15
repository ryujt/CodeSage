import json
import requests
import logging
from requests.exceptions import RequestException
from .config import get_settings, API_URL, CHAT_API_URL, EMBEDDINGS_MODEL, CHAT_MODEL

def get_embedding(text):
    settings = get_settings()

    headers = {
        "Authorization": f"Bearer {settings['api_key']}",
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

def get_chat_response(messages):
    settings = get_settings()

    headers = {
        "Authorization": f"Bearer {settings['api_key']}",
        "Content-Type": "application/json"
    }

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