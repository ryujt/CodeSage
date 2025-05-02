from flask import Flask
import logging
from controllers.index_controller import index_bp
from controllers.analysis_controller import analysis_bp
from controllers.question_controller import question_bp
from controllers.settings_controller import settings_bp
from controllers.folder_controller import folder_bp

def create_app():
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    app = Flask(__name__, template_folder='SageTemplate')
    app.secret_key = 'your_secret_key_here'
    app.register_blueprint(index_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(question_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(folder_bp)
    return app

if __name__ == '__main__':
    create_app().run(debug=True, host='0.0.0.0', port=8080) 