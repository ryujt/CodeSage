from flask import Blueprint, render_template, request, redirect, url_for, flash
import json
import logging
from SageLibs.web_requests import get_embedding, summarize_content, get_chat_response
from SageLibs.utilities import count_tokens
from SageLibs.questions import insert_question, get_all_questions, get_relevant_answers
from SageLibs.utilities import get_relevant_documents
from SageLibs.folders import get_selected_folders
from SageLibs.config import TOKEN_CONTEXT_WINDOW

index_bp = Blueprint('index', __name__, url_prefix='/')

@index_bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        question = request.form['question']
        try:
            question_embedding = get_embedding(question)
        except Exception as e:
            logging.error(f"임베딩 생성 중 오류 발생: {str(e)}", exc_info=True)
            flash(f"임베딩 생성 중 오류 발생: {str(e)}", "error")
            return redirect(url_for('index.index'))
        
        question_part_token_count = count_tokens(question)
        relevant_answers = get_relevant_answers(question_embedding)
        relevant_docs = get_relevant_documents(get_selected_folders(), question_embedding)

        # 토큰 수 제한 및 선택 로직
        max_tokens = TOKEN_CONTEXT_WINDOW
        remaining_tokens = max_tokens - question_part_token_count
        selected_answers = []
        selected_docs = []
        
        # relevant_answers와 relevant_docs를 유사도 순으로 정렬
        all_items = relevant_answers + relevant_docs
        all_items.sort(key=lambda x: x['similarity'], reverse=True)
        
        for item in all_items:
            if remaining_tokens - item['tokens'] >= 0:
                if 'filename' in item:  # relevant_docs의 항목
                    from SageLibs.config import get_setting
                    if get_setting('filter_content') == 'on':
                        item['content'] = summarize_content(question, item['content'])
                    selected_docs.append(item)
                else:  # relevant_answers의 항목
                    from SageLibs.config import get_setting
                    if get_setting('filter_content') == 'on':
                        item['answer'] = summarize_content(question, item['answer'])
                    selected_answers.append(item)

                remaining_tokens -= item['tokens']
           
            if remaining_tokens <= 0:
                break

        # Format message in JSON structure
        data = {
            "prompt": question,
            "files": {},
            "previous_answers": []
        }

        # Add relevant docs to files
        for doc in selected_docs:
            filename = doc.get('filename', '')
            if filename:
                data["files"][f"@{filename}"] = doc.get('content', '')

        # Add relevant answers if any
        if selected_answers:
            data["previous_answers"] = selected_answers

        try:
            answer = get_chat_response(json.dumps(data, ensure_ascii=False))
        except Exception as e:
            logging.error(f"API 호출 중 오류 발생: {str(e)}", exc_info=True)
            flash(f"API 호출 중 오류 발생: {str(e)}", "error")
            return redirect(url_for('index.index'))
        
        doc_id = insert_question(question, answer)
        return redirect(url_for('question.show_question', question_id=doc_id))

    questions = get_all_questions(revert=True)
    return render_template('index-multi.html', questions=questions) 