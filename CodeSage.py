import os
import json
import logging
import shutil
import nltk
from datetime import datetime 
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from SageLibs.config import EMBEDDINGS_FILE
from SageLibs.config import load_settings, get_settings, update_settings
from SageLibs.web_requests import get_embedding, get_chat_response
from SageLibs.utilities import load_embeddings, count_tokens, get_relevant_documents, get_file_paths, read_file, hash_content, get_changed_files_in_diff, diff_between_branches
from SageLibs.questions import get_all_questions, get_question_by_id, insert_question, delete_question

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
        relevant_docs = get_relevant_documents(question_part_token_count, question_embedding)

        user_message = f"Please reply in Korean.\n\nQuestion: {question}\n\nContext:\n{json.dumps(relevant_docs, ensure_ascii=False, indent=2)}"
        
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
    return render_template('index.html', questions=questions)

@app.route('/analyze_changes/<analysis_type>', methods=['POST'])
def analyze_changes(analysis_type):
    extract_embeddings()

    question = "Please reply in Korean.\n\nPlease analyze the changes described in 'Diff:', and refer to the existing code in 'Context:' to identify issues and suggest improvements."

    try:
        file_names = get_changed_files_in_diff(analysis_type)
        combined_answer = ""
        error_files = []

        for file_name in file_names:
            try:
                logging.debug(f"Processing changes for file: {file_name}")
                diff_output = diff_between_branches(analysis_type, specific_file=file_name)
                question_embedding = get_embedding(f"{question}\n\nFilename:{file_name}")

                question_part_token_count = count_tokens(f"{question}\n\nDiff:\n{diff_output}")
                relevant_docs = get_relevant_documents(question_part_token_count, question_embedding)

                user_message = f"Question: {question}\n\nFilename: {file_name}\n\nDiff:\n{diff_output}\n\nContext:\n{json.dumps(relevant_docs, ensure_ascii=False, indent=2)}"
                answer = get_chat_response(user_message)
                combined_answer += f"# File: {file_name}\n\n{answer}\n\n"

            except Exception as e:
                logging.error(f"Error processing file {file_name}: {str(e)}", exc_info=True)
                error_files.append(file_name)

        if combined_answer:
            current_time = datetime.now()
            doc_id = insert_question(f'Git diff result ({analysis_type}) - {current_time}', combined_answer)
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

    existing_embeddings = load_embeddings(EMBEDDINGS_FILE)
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

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    nltk.download('punkt', quiet=True)
    load_settings()
    app.run(debug=True, host='0.0.0.0', port=8080)
