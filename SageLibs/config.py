import json
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # 기존 설정을 덮어쓰기
)

EMBEDDINGS_MODEL = 'text-embedding-3-large'
CHAT_MODEL = 'gpt-4o'
TOKEN_COUNTER_MODEL = 'gpt-4'

TOKEN_CONTEXT_WINDOW = 100000
TOKEN_CONTEXT_WINDOW_EMBEDDINGS= 8000

API_URL = "https://api.openai.com/v1/embeddings"
CHAT_API_URL = "https://api.openai.com/v1/chat/completions"

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = 'claude-3-sonnet' 

EMBEDDINGS_FILE = 'embeddings.jsonl'
SETTINGS_FILE = 'SageSettings.json'

SIMILARITY_THRESHOLD = 0.30

USE_RERANKER = True
RERANKER_MODEL = 'cross-encoder/ms-marco-MiniLM-L-6-v2'
RERANKER_TOP_K = 20

USE_HYBRID_SEARCH = True
BM25_WEIGHT = 0.3
SEMANTIC_WEIGHT = 0.7

CHUNK_OVERLAP_TOKENS = 200

settings = {}

def load_settings():
    global settings
    
    default_settings = {
        'openai_api_key': 'your_openai_api_key',
        'filter_content': '',
        'use_question_history': '',
        'extensions': ['.md', '.vue', '.js', '.json', '.css', '.html', '.py', '.pdf', '.java', '.ts', '.jsx', '.tsx', '.php', '.c', '.cpp', '.h', '.cs', '.swift', '.rb', '.go', '.kt', '.sql', '.hpp', '.m', '.mm'],
        'ignore_folders': ['node_modules', 'cypress', '.gradle', '.idea', 'build', 'test', 'bin', 'dist', '.vscode', '.git', '.github', '.expo'],
        'ignore_files': ['CodeSage.py', 'SageSettings.json', 'SageQuestions.json', 'SageFolders.json', 'embeddings.jsonl', 'package-lock.json'],
        'essential_files': ['JobFlow.md'],
        'use_reranker': True,
        'use_hybrid_search': True,
        'chunk_overlap_tokens': 200
    }
    
    try:
        with open(SETTINGS_FILE, 'r') as f:
            settings.update(json.load(f))
    except FileNotFoundError:
        settings.update(default_settings)
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
    
    for key in ['extensions', 'ignore_folders', 'ignore_files', 'essential_files']:
        if isinstance(settings[key], str):
            settings[key] = [item.strip() for item in settings[key].split(',')]
        elif isinstance(settings[key], list):
            settings[key] = [item.strip() for item in settings[key]]

    logging.info("Settings loaded.")
    logging.info(f"API URL: {API_URL}")
    logging.info(f"EMBEDDINGS_MODEL: {EMBEDDINGS_MODEL}")
    logging.info(f"CHAT_MODEL: {CHAT_MODEL}")

    return settings

def get_settings():
    global settings
    if not settings:
        load_settings()
    return settings

def get_setting(key, default=None):
    return get_settings().get(key, default)

def update_settings(new_settings):
    global settings
    settings.update(new_settings)
    
    for key in ['extensions', 'ignore_folders', 'ignore_files', 'essential_files']:
        if isinstance(settings[key], str):
            settings[key] = settings[key].split(', ')
    
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

    logging.info("Settings updated.")