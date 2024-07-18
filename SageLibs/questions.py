from tinydb import TinyDB, Query
from flask import flash
import re

db = TinyDB('question_history.json')
MAX_HISTORY_COUNT = 100 

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
    doc_id = db.insert({'question': question, 'answer': answer, 'title': title})
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
