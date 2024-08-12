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
        error_message = "API 요청 실패"
        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code
            server_message = e.response.text
            if status_code == 401:
                error_message = "API 키 인증 실패. API 키를 확인하세요."
            else:
                error_message = f"API 요청 실패 (상태 코드: {status_code})"
            logging.error(f"{error_message}\n서버 응답: {server_message}")
        else:
            logging.error(f"{error_message}: {str(e)}")
        raise ValueError(error_message) from e
    except (KeyError, IndexError, ValueError) as e:
        error_message = f"API 응답 처리 오류: {str(e)}"
        logging.error(error_message)
        raise ValueError(error_message) from e
    
def summarize_content(question, text):
    settings = get_settings()
    api_key = settings.get('openai_api_key', '')

    system_message = "You are an AI assistant specialized in extracting relevant information."
    user_message = f"""Return 'Related' if the content of 'text:' is related to 'question:'.

text:
{text}

question:
{question}
"""
   
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]

    data = json.dumps({
        "model": "gpt-4o-mini",
        "messages": messages,
        "temperature": 0
    })

    try:
        response = requests.post(CHAT_API_URL, headers=headers, data=data)
        response.raise_for_status()

        return response.json()['choices'][0]['message']['content']
    except RequestException as e:
        logging.error(f"Chat API 요청 실패: {str(e)}")
        return ""
    except (KeyError, IndexError) as e:
        logging.error(f"Chat API 응답 처리 오류: {str(e)}")
        return ""

def get_chat_response(user_message):    
    settings = get_settings()

    system_message = """You are an AI assistant specialized in answering questions based on provided context. 
    Your task is to:
        1. Analyze the full content of the relevant_docs and relevant_answers provided in the context.
        2. Answer the user's question accurately using information from both relevant_docs and relevant_answers.
        3. If the context doesn't contain enough information, say so and provide the best possible answer based on your general knowledge.
        4. Cite the filenames of relevant documents and the titles of relevant answers in your response.
        5. If appropriate, provide code snippets or examples from the context to support your answer.
        6. Refer to the JowFlow.md document for the Jow Flow diagram.
        7. When creating diagrams, use mermaid syntax, except when creating a Jow Flow diagram."""

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