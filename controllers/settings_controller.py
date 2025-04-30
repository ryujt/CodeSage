import logging
from flask import Blueprint, render_template, request, flash, redirect, url_for
from SageLibs.config import get_setting, update_settings

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

@settings_bp.route('/', methods=['GET', 'POST'])
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
        return redirect(url_for('settings.settings_route'))
    
    # Get current settings
    template_data = {
        'openai_api_key': get_setting('openai_api_key', ''),
        'filter_content': get_setting('filter_content', ''),
        'use_question_history': get_setting('use_question_history', ''),
        'extensions': ", ".join(get_setting('extensions', [])),
        'ignore_folders': ", ".join(get_setting('ignore_folders', [])),
        'ignore_files': ", ".join(get_setting('ignore_files', [])),
        'essential_files': ", ".join(get_setting('essential_files', []))
    }

    return render_template('settings.html', **template_data) 