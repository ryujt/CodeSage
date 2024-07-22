from tinydb import TinyDB, Query
from flask import flash
import re
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from .config import SIMILARITY_THRESHOLD
from .web_requests import get_embedding
from .utilities import hash_content, count_tokens

db = TinyDB('question_history.json')
MAX_HISTORY_COUNT = 512 

def get_all_questions(revert=False):
    questions = db.all()
    if revert:
        questions.reverse()
    return questions

def get_question_by_id(question_id):
    question_record = db.get(doc_id=question_id)
    if not question_record:
        flash("Requested question does not exist.", "error")
        return None
    return question_record

def insert_question(question, answer):
    title = extract_first_sentence(question)
    combined_content = f"{question}\n\n{answer}"
    content_hash = hash_content(combined_content)
    
    try:
        embedding = get_embedding(combined_content)
    except Exception as e:
        flash(f"Error generating embedding: {str(e)}", "error")
        embedding = None

    doc_id = db.insert({
        'question': question, 
        'answer': answer, 
        'title': title,
        'content_hash': content_hash,
        'embedding': embedding
    })
    maintain_history_limit()
    return doc_id

def delete_question(question_id):
    question = db.get(doc_id=question_id)
    if question:
        db.remove(doc_ids=[question_id])
        return True
    return False

def extract_first_sentence(text):
    first_sentence = re.split(r'\.|\?|\n', text)[0].strip()
    return first_sentence if first_sentence else text

def maintain_history_limit():
    """ 이력의 최대 개수를 유지하기 위해 필요한 경우 가장 오래된 이력을 제거 """
    all_questions = db.all()
    if len(all_questions) > MAX_HISTORY_COUNT:
        number_to_delete = len(all_questions) - MAX_HISTORY_COUNT
        # TinyDB는 도큐먼트 추가 순으로 ID가 부여되므로, ID가 작은 것부터 삭제
        for _ in range(number_to_delete):
            min_id = min(question.doc_id for question in all_questions)
            db.remove(doc_ids=[min_id])
            all_questions = db.all()  # 재조회 필요

def get_relevant_answers(question_embedding, similarity_threshold=SIMILARITY_THRESHOLD, max_tokens=80000):
    all_questions = db.all()
    all_questions.reverse()

    relevant_questions = []
    total_tokens = 0

    # 모든 질문의 임베딩을 numpy 배열로 변환
    all_embeddings = np.array([q['embedding'] for q in all_questions if q['embedding'] is not None])
    
    if len(all_embeddings) > 0:
        # 코사인 유사도 계산
        similarities = cosine_similarity([question_embedding], all_embeddings)[0]

        # 유사도가 높은 순으로 정렬
        sorted_indices = np.argsort(similarities)[::-1]

        for idx in sorted_indices:
            if similarities[idx] < similarity_threshold:
                break

            question = all_questions[idx]
            answer_tokens = count_tokens(question['title'] + "\n\n" + question['answer'])

            if total_tokens + answer_tokens > max_tokens:
                break

            relevant_questions.append({
                "tokens": answer_tokens,
                "title": question['title'],
                "similarity": float(similarities[idx]),  # numpy.float32를 Python float으로 변환
                "answer": question['answer']
            })

            total_tokens += answer_tokens

    return relevant_questions