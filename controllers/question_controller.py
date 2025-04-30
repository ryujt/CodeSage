import logging
from flask import Blueprint, render_template, jsonify, redirect, url_for
from SageLibs.questions import get_question_by_id, get_all_questions, delete_question, delete_all_questions

question_bp = Blueprint('question', __name__, url_prefix='/question')

@question_bp.route('/<int:question_id>')
def show_question(question_id):
    question_record = get_question_by_id(question_id)
    if not question_record:
        return redirect(url_for('index.index'))
    
    return render_template('result.html', 
                          question=question_record['question'], 
                          answer=question_record['answer'], 
                          questions=get_all_questions(revert=True))

@question_bp.route('/delete/<int:question_id>', methods=['POST'])
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

@question_bp.route('/delete-all', methods=['POST'])
def delete_all_questions_route():
    try:
        success = delete_all_questions()
        if success:
            return jsonify({"success": True, "message": "모든 질문이 성공적으로 삭제되었습니다."})
        else:
            return jsonify({"success": False, "message": "질문 삭제 중 오류가 발생했습니다."}), 500
    except Exception as e:
        logging.error(f"모든 질문 삭제 중 오류 발생: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": f"모든 질문 삭제 중 오류 발생: {str(e)}"}), 500 