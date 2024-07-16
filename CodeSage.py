import os
import json
import logging
import shutil
import nltk
from flask import Flask, render_template, request, redirect, url_for, flash
from SageLibs.config import EMBEDDINGS_FILE
from SageLibs.config import load_settings, get_settings, update_settings
from SageLibs import get_embedding, get_chat_response, load_embeddings, find_most_similar, get_file_paths, read_file, hash_content, count_tokens

app = Flask(__name__, template_folder='SageTemplate')
app.secret_key = 'your_secret_key_here'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')
    
    question = request.form['question']
    
    logging.debug("질문 임베딩 생성 시작")
    try:
        question_embedding = get_embedding(question)
        logging.debug("질문 임베딩 생성 완료")
    except Exception as e:
        logging.error(f"임베딩 생성 중 오류 발생: {str(e)}", exc_info=True)
        flash(f"임베딩 생성 중 오류 발생: {str(e)}", "error")
        return render_template('index.html')
    
    logging.debug("유사한 문서 찾기 시작")
    embeddings = load_embeddings(EMBEDDINGS_FILE)
    similar_files = find_most_similar(question_embedding, embeddings)
    
    logging.debug("유사도로 선택된 파일:")
    for filename, similarity in similar_files:
        logging.debug(f"{filename}: {similarity}")
    
    relevant_docs = []
    total_tokens = 0
    max_tokens = 100000 

    for filename, similarity in similar_files:
        content = embeddings[filename]['content']            
        doc_tokens = count_tokens(content)
        
        if total_tokens + doc_tokens > max_tokens:
            break
        
        relevant_docs.append({
            "filename": filename,
            "similarity": similarity,
            "content": content
        })
        total_tokens += doc_tokens

    logging.debug(f"프롬프트 생성 정보:")
    logging.debug(f"총 토큰 수: {total_tokens}")
    logging.debug(f"사용된 파일: {[doc['filename'] for doc in relevant_docs]}")

    user_message = f"""Question: {question}

Please answer the question based on the provided context. 
Context:
        {json.dumps(relevant_docs, ensure_ascii=False, indent=2)}"""
    
    try:
        answer = get_chat_response(user_message)
        logging.debug(f"응답 길이: {len(answer)} 글자")
    except Exception as e:
        logging.error(f"API 호출 중 오류 발생: {str(e)}", exc_info=True)
        flash(f"API 호출 중 오류 발생: {str(e)}", "error")
        return render_template('index.html')
    
    return render_template('result.html', question=question, answer=answer)

@app.route('/settings', methods=['GET', 'POST'])
def settings_route():
    if request.method == 'POST':
        logging.debug("설정 업데이트 시작")
        new_settings = {
            'openai_api_key': request.form.get('apiKey', 'your_openai_api_key'),
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
    return render_template('settings.html', 
                           extensions=", ".join(settings['extensions']),
                           ignore_folders=", ".join(settings['ignore_folders']),
                           ignore_files=", ".join(settings['ignore_files']),
                           essential_files=", ".join(settings['essential_files']),
                           openai_api_key=settings['openai_api_key'])

@app.route('/extract_embeddings', methods=['POST'])
def extract_embeddings():
    logging.info("임베딩 추출 시작")

    backup_file = EMBEDDINGS_FILE + ".bak"
    if os.path.exists(EMBEDDINGS_FILE):
        shutil.copy2(EMBEDDINGS_FILE, backup_file)

    existing_embeddings = load_embeddings(backup_file)
    file_paths = get_file_paths('.')
    error_files = []

    with open(EMBEDDINGS_FILE, 'w', encoding='utf-8') as f:
        for file_path in file_paths:
            try:
                relative_path = os.path.relpath(file_path)
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

    logging.info(f"Embedding extraction complete. Results saved to {EMBEDDINGS_FILE}")
    if error_files:
        error_message = f"The following files encountered errors and were skipped: {', '.join(error_files)}"
        logging.warning(error_message)
        flash(error_message, "warning")
    else:
        flash("임베딩 추출이 성공적으로 완료되었습니다.", "success")
    return redirect(url_for('index'))

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    nltk.download('punkt', quiet=True)
    load_settings()
    app.run(debug=True, host='0.0.0.0', port=8080)
