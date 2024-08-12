import os
import json
import logging
import nltk
from datetime import datetime 
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from SageLibs.config import EMBEDDINGS_FILE, settings
from SageLibs.config import load_settings, get_settings, update_settings
from SageLibs.web_requests import get_embedding, summarize_content, get_chat_response
from SageLibs.utilities import load_embeddings, count_tokens, get_relevant_documents, get_file_paths, read_file, hash_content, get_changed_files_in_diff, diff_between_branches
from SageLibs.questions import get_all_questions, get_question_by_id, insert_question, delete_question, get_relevant_answers
from SageLibs.folders import get_all_folders, add_folder, delete_folder, get_selected_folders, update_selected_folders
from SageLibs.Translator import translate_lines

app = Flask(__name__, template_folder='SageTemplate')
app.secret_key = 'your_secret_key_here'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        question = request.form['question']
        
        logging.debug("질문 임베딩 생성 시작")
        try:
            question_embedding = get_embedding(question)
            logging.debug("질문 임베딩 생성 완료")
        except Exception as e:
            logging.error(f"임베딩 생성 중 오류 발생: {str(e)}", exc_info=True)
            flash(f"임베딩 생성 중 오류 발생: {str(e)}", "error")
            return redirect(url_for('index'))
        
        question_part_token_count = count_tokens(question)
        relevant_answers = get_relevant_answers(question_embedding)
        relevant_docs = get_relevant_documents(get_selected_folders(), question_embedding)

        # 토큰 수 제한 및 선택 로직
        max_tokens = 80000
        remaining_tokens = max_tokens - question_part_token_count
        selected_answers = []
        selected_docs = []
        
        # relevant_answers와 relevant_docs를 유사도 순으로 정렬
        all_items = relevant_answers + relevant_docs
        all_items.sort(key=lambda x: x['similarity'], reverse=True)
        
        for item in all_items:
            if remaining_tokens - item['tokens'] >= 0:
                if 'filename' in item:  # relevant_docs의 항목
                    if settings['filter_content'] == 'on':
                        item['content'] = summarize_content(question, item['content'])
                    selected_docs.append(item)

                else:  # relevant_answers의 항목
                    if settings['filter_content'] == 'on':
                        item['answer'] = summarize_content(question, item['answer'])
                    selected_answers.append(item)

                remaining_tokens -= item['tokens']
           
            if remaining_tokens <= 0:
                break

        user_message = f"Please reply in Korean.\n\nQuestion: {question}\n\nrelevant_docs:\n{json.dumps(selected_docs, ensure_ascii=False)}\n\nrelevant_answers: \n{json.dumps(selected_answers, ensure_ascii=False)}"
        if len(selected_answers) == 0:
            user_message = f"Please reply in Korean.\n\nQuestion: {question}\n\nrelevant_docs:\n{json.dumps(selected_docs, ensure_ascii=False)}\n\nrelevant_answers: none"
        
        try:
            answer = get_chat_response(user_message)
            logging.debug(f"응답 길이: {len(answer)} 글자")
        except Exception as e:
            logging.error(f"API 호출 중 오류 발생: {str(e)}", exc_info=True)
            flash(f"API 호출 중 오류 발생: {str(e)}", "error")
            return redirect(url_for('index'))
        
        doc_id = insert_question(question, answer)
        return redirect(url_for('show_question', question_id=doc_id))

    questions = get_all_questions(revert=True)
    return render_template('index-multi.html', questions=questions)

@app.route('/analyze_changes/<analysis_type>', methods=['POST'])
def analyze_changes(analysis_type):
    folders = get_selected_folders()
    if len(folders) != 1:
        flash("분석을 위해 정확히 하나의 폴더를 선택해주세요.", "error")
        return redirect(url_for('index'))

    folder = folders[0]

    question = """Please reply in Korean.
Analyze the code changes provided in 'Diff:' and refer to the existing code in 'Context:' to generate a detailed report categorized into three sections:

1. Refactoring targets and potential error-prone areas:
   - Complex or duplicated logic
   - Unclear naming
   - Insufficient exception handling
   - Potential bugs or performance issues

2. Clean code principle application areas:
   - Violations of Single Responsibility Principle
   - Function/method length and complexity
   - Necessity of comments or excessive commenting
   - Clarity of variable and function names

3. Other code improvement areas:
   - Potential design pattern applications
   - Areas needing improved testability
   - Code structure and architecture improvements

For each item, please provide specific line numbers and suggestions for improvement. Focus primarily on the changes shown in 'Diff:', but refer to the existing code in 'Context:' when necessary for a comprehensive analysis."""

    try:
        file_names = get_changed_files_in_diff(folder, analysis_type)
        combined_answer = ""
        error_files = []

        for file_name in file_names:
            try:
                logging.debug(f"Processing changes for file: {file_name}")
                diff_output = diff_between_branches(folder, analysis_type, specific_file=file_name)
                question_embedding = get_embedding(f"Filename:{file_name}\n\nDiff:\n{diff_output}")
                relevant_docs = get_relevant_documents([folder], question_embedding)
                user_message = f"Question: {question}\n\nFilename: {file_name}\n\nDiff:\n{diff_output}\n\nContext:\n{json.dumps(relevant_docs, ensure_ascii=False, indent=2)}"

                answer = get_chat_response(user_message)
                combined_answer += f"# File: {file_name}\n\n{answer}\n\n"

            except Exception as e:
                logging.error(f"Error processing file {file_name}: {str(e)}", exc_info=True)
                error_files.append(file_name)

        if combined_answer:
            current_time = datetime.now()
            doc_id = insert_question(f'Git diff ({analysis_type}) - {current_time}\n{folder}', combined_answer)
            return redirect(url_for('show_question', question_id=doc_id))

        if error_files:
            flash(f"Errors encountered in files: {', '.join(error_files)}", "warning")
        else:
            flash("No changes to analyze or error in processing all files.", "warning")
        return redirect(url_for('index'))

    except Exception as e:
        logging.error(f"General error during analysis: {str(e)}", exc_info=True)
        flash(f"General error during analysis: {str(e)}", "error")
        return redirect(url_for('index'))

@app.route('/question/<int:question_id>')
def show_question(question_id):
    question_record = get_question_by_id(question_id)
    if not question_record:
        return redirect(url_for('index'))
    
    return render_template('result.html', question=question_record['question'], answer=question_record['answer'], questions=get_all_questions(revert=True))

@app.route('/delete_question/<int:question_id>', methods=['POST'])
def delete_question_route(question_id):
    try:
        success = delete_question(question_id)
        if success:
            return jsonify({"success": True, "message": "질문이 성공적으로 삭제되었습니다."})
        else:
            return jsonify({"success": False, "message": "질문을 찾을 수 없습니다."}), 404
    except Exception as e:
        logging.error(f"질문 삭제 중 오류 발생 (ID: {question_id}): {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": f"질문 삭제 중 오류 발생: {str(e)}"}), 500

@app.route('/extract_embeddings', methods=['POST'])
def extract_embeddings():
    logging.info("임베딩 추출 시작")

    folders = get_selected_folders()
    logging.info(f"Selected folders: {folders}")

    for folder in folders:
        embedding_file = os.path.join(folder, EMBEDDINGS_FILE)
        existing_embeddings = load_embeddings(embedding_file)
        file_paths = get_file_paths(folder)
        error_files = []

        with open(embedding_file, 'w', encoding='utf-8') as f:
            for file_path in file_paths:
                try:
                    relative_path = os.path.relpath(file_path, start=folder)
                    logging.info(f"Processing {relative_path}")
                    
                    content = read_file(file_path)
                    content_hash = hash_content(content)

                    if relative_path in existing_embeddings and existing_embeddings[relative_path]['content_hash'] == content_hash:
                        file_data = existing_embeddings[relative_path]
                    else:
                        logging.info(f"  - Changes detected or new file, generating new embedding")
                        embedding = get_embedding(content)
                        file_data = {
                            "filename": relative_path, 
                            "content": content,
                            "content_hash": content_hash,
                            "embedding": embedding
                        }

                    f.write(json.dumps(file_data, ensure_ascii=False) + '\n')
                except Exception as e:
                    logging.error(f"Error processing {file_path}: {str(e)}", exc_info=True)
                    error_files.append(relative_path)

        logging.info(f"Embedding extraction complete for folder {folder}. Results saved to {embedding_file}")
        if error_files:
            error_message = f"The following files encountered errors and were skipped in folder {folder}: {', '.join(error_files)}"
            logging.warning(error_message)
            flash(error_message, "warning")
        else:
            flash(f"임베딩 추출이 성공적으로 완료되었습니다 for folder {folder}.", "success")

    return redirect(url_for('index'))

@app.route('/settings', methods=['GET', 'POST'])
def settings_route():
    if request.method == 'POST':
        logging.debug("설정 업데이트 시작")
        new_settings = {
            'openai_api_key': request.form.get('apiKey', 'your_openai_api_key'),
            'filter_content': request.form.get('filterContent'),
            'use_question_history': request.form.get('useQuestionHistory'),
            'extensions': request.form.get('extensions'),
            'ignore_folders': request.form.get('ignoreFolders'),
            'ignore_files': request.form.get('ignoreFiles'),
            'essential_files': request.form.get('essentialFiles')
        }
        
        logging.debug(f"새로운 설정: {new_settings}")
        update_settings(new_settings)
        flash('설정이 성공적으로 업데이트되었습니다.', 'success')
        return redirect(url_for('settings_route'))
    
    settings = get_settings()
    logging.debug(f"현재 설정: {settings}")

    template_data = {
        'openai_api_key': settings.get('openai_api_key', ''),
        'filter_content': settings.get('filter_content', ''),
        'use_question_history': settings.get('use_question_history', ''),
        'extensions': ", ".join(settings.get('extensions', [])),
        'ignore_folders': ", ".join(settings.get('ignore_folders', [])),
        'ignore_files': ", ".join(settings.get('ignore_files', [])),
        'essential_files': ", ".join(settings.get('essential_files', []))
    }

    return render_template('settings.html', **template_data)    

@app.route('/select_folders', methods=['GET'])
def select_folders():
    folders = get_all_folders()
    selected_folders = get_selected_folders()
    return render_template('sage_folders.html', folders=folders, selected_folders=selected_folders)

@app.route('/add_folder', methods=['POST'])
def add_folder_route():
    data = request.json
    folder = data.get('folder')
    if not folder:
        logging.warning("Add folder request received with no folder specified")
        return jsonify({"success": False, "message": "No folder provided"}), 400
    
    logging.info(f"Received request to add folder: {folder}")
    
    try:
        success, message = add_folder(folder)
        if success:
            logging.info(f"Successfully added folder: {folder}")
            return jsonify({"success": True, "message": message})
        else:
            logging.warning(f"Failed to add folder: {folder}. Reason: {message}")
            return jsonify({"success": False, "message": message}), 400
    except Exception as e:
        logging.error(f"Unexpected error in add_folder_route: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

@app.route('/delete_folder', methods=['POST'])
def delete_folder_route():
    folder = request.json.get('folder')
    if not folder:
        return jsonify({"success": False, "message": "No folder provided"}), 400
    
    success, message = delete_folder(folder)
    return jsonify({"success": success, "message": message})

@app.route('/update_selected_folders', methods=['POST'])
def update_selected_folders_route():
    data = request.json
    selected_folders = data.get('selectedFolders', [])
    
    logging.info(f"Received request to save selected folders: {selected_folders}")
    
    try:
        success, message = update_selected_folders(selected_folders)
        if success:
            return jsonify({"success": True, "message": message})
        else:
            return jsonify({"success": False, "message": message}), 400
    except Exception as e:
        logging.error(f"Error saving selected folders: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    # nltk.download('punkt', quiet=True)
    # load_settings()
    # app.run(debug=True, host='0.0.0.0', port=8080)

    print(translate_lines("""import json
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
        # API 요청 실패
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
    user_message = f""Return 'Related' if the content of 'text:' is related to 'question:'.

text:
{text}

question:
{question}
""
   
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

    system_message = ""You are an AI assistant specialized in answering questions based on provided context. 
    Your task is to:
        1. Analyze the full content of the relevant_docs and relevant_answers provided in the context.
        2. Answer the user's question accurately using information from both relevant_docs and relevant_answers.
        3. If the context doesn't contain enough information, say so and provide the best possible answer based on your general knowledge.
        4. Cite the filenames of relevant documents and the titles of relevant answers in your response.
        5. If appropriate, provide code snippets or examples from the context to support your answer.
        6. Refer to the JowFlow.md document for the Jow Flow diagram.
        7. When creating diagrams, use mermaid syntax, except when creating a Jow Flow diagram.""

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
    
def get_chat_response_ollama(message):
    logging.debug("Ollama API 호출 시작")

    url = "http://localhost:11434/api/generate"
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "model": "gemma2",
        "prompt": message,
        "stream": False
    })

    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        result = response.json()
        return result.get('response', "Unexpected response structure from Ollama API")
    except RequestException as e:
        logging.error(f"Ollama API 요청 실패: {str(e)}")
        return f"Error: Ollama API request failed - {str(e)}"
    except json.JSONDecodeError as e:
        logging.error(f"Ollama API 응답 처리 오류: {str(e)}")
        return "Error: Failed to parse Ollama API response"    
"""))