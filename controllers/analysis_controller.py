import json
import logging
import os
from datetime import datetime
from flask import Blueprint, request, redirect, url_for, flash, jsonify
from SageLibs.utilities import get_relevant_documents, load_embeddings, hash_content, get_file_paths, read_file
from SageLibs.utilities import get_changed_files_in_diff, diff_between_branches
from SageLibs.folders import get_selected_folders
from SageLibs.web_requests import get_embedding, get_chat_response
from SageLibs.questions import insert_question
from SageLibs.config import EMBEDDINGS_FILE

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/analyze_changes/<analysis_type>', methods=['POST'])
def analyze_changes(analysis_type):
    folders = get_selected_folders()
    if len(folders) != 1:
        flash("분석을 위해 정확히 하나의 폴더를 선택해주세요.", "error")
        return redirect(url_for('index.index'))

    folder = folders[0]

    analysis_prompt = """Analyze the code changes provided in 'Diff:' and refer to the existing code in 'Context:' to generate a detailed report categorized into three sections:

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

                # Format message in JSON structure
                message_data = {
                    "prompt": analysis_prompt,
                    "files": {
                        f"@{file_name}": diff_output
                    },
                    "context": relevant_docs
                }

                user_message = json.dumps(message_data, ensure_ascii=False)
                answer = get_chat_response(user_message)
                combined_answer += f"# File: {file_name}\n\n{answer}\n\n"

            except Exception as e:
                logging.error(f"Error processing file {file_name}: {str(e)}", exc_info=True)
                error_files.append(file_name)

        if combined_answer:
            current_time = datetime.now()
            doc_id = insert_question(f'Git diff ({analysis_type}) - {current_time}\n{folder}', combined_answer)
            return redirect(url_for('question.show_question', question_id=doc_id))

        if error_files:
            flash(f"Errors encountered in files: {', '.join(error_files)}", "warning")
        else:
            flash("No changes to analyze or error in processing all files.", "warning")
        return redirect(url_for('index.index'))

    except Exception as e:
        logging.error(f"General error during analysis: {str(e)}", exc_info=True)
        flash(f"General error during analysis: {str(e)}", "error")
        return redirect(url_for('index.index'))

@analysis_bp.route('/extract_embeddings', methods=['POST'])
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

    return redirect(url_for('index.index')) 