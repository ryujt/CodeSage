import os
import requests
import json
import numpy as np
from flask import Flask, render_template, request, redirect, url_for
from sklearn.metrics.pairwise import cosine_similarity
import nltk
import tiktoken
import hashlib
import shutil
import chardet

app = Flask(__name__, template_folder='sage-template')

MODEL = 'text-embedding-3-large'

HEADERS = {}
API_URL = "https://api.openai.com/v1/embeddings"
CHAT_API_URL = "https://api.openai.com/v1/chat/completions"

EMBEDDINGS_FILE = 'embeddings.jsonl'
SETTINGS_FILE = 'sage-settings.json'

settings = {}

def load_settings():
    global settings, HEADERS
    
    default_settings = {
        'api_key': 'your_openai_api_key',
        'extensions': '.md, .vue, .js, .json, .css, .html',
        'ignore_folders': 'node_modules, cypress, sage-template',
        'ignore_files': 'CodeSage.py, sage-settings.json, package-lock.json',
        'essential_files': 'README.md, package.json, src/router/index.js'
    }
    
    try:
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
    except FileNotFoundError:
        settings = default_settings
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
    
    # 문자열 데이터를 리스트로 변환하지 않음
    for key in ['extensions', 'ignore_folders', 'ignore_files', 'essential_files']:
        if isinstance(settings[key], str):
            settings[key] = settings[key].split(', ')
    
    HEADERS = {
        "Authorization": f"Bearer {settings['api_key']}",
        "Content-Type": "application/json"
    }

    print("Loaded settings:", settings)

@app.route('/settings', methods=['GET', 'POST'])
def settings_route():
    global settings
    if request.method == 'POST':
        new_settings = {
            'api_key': request.form.get('apiKey', 'your_openai_api_key'),
            'extensions': request.form.get('extensions', '.md, .vue, .js, .json, .css, .html').split(', '),
            'ignore_folders': request.form.get('ignoreFolders', 'node_modules, cypress, sage-template').split(', '),
            'ignore_files': request.form.get('ignoreFiles', 'CodeSage.py, sage-settings.json, package-lock.json').split(', '),
            'essential_files': request.form.get('essentialFiles', 'README.md, package.json, src/router/index.js').split(', ')
        }
        
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(new_settings, f, indent=2)
        
        load_settings() 
        return redirect(url_for('settings_route'))
    
    load_settings()
    
    return render_template('settings.html', 
                           extensions=', '.join(settings['extensions']),
                           ignore_folders=', '.join(settings['ignore_folders']),
                           ignore_files=', '.join(settings['ignore_files']),
                           essential_files=', '.join(settings['essential_files']),
                           api_key=settings['api_key'])

def get_embedding(text):
    data = json.dumps({
        "input": text,
        "model": MODEL,
        "encoding_format": "float"
    })
    response = requests.post(API_URL, headers=HEADERS, data=data)
    return response.json()['data'][0]['embedding']

def load_embeddings(file_path):
    embeddings = {}
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                embeddings[data['filename']] = data
    return embeddings

def find_most_similar(query_embedding, embeddings, similarity_threshold=0.25, top_k=100):
    global settings
    similarities = {}
    for filename, data in embeddings.items():
        similarity = cosine_similarity([query_embedding], [data['embedding']])[0][0]
        if similarity >= similarity_threshold or filename in settings['essential_files']:
            similarities[filename] = similarity

    # 필수 파일들을 결과에 추가
    for filename in settings['essential_files']:
        if filename in embeddings and filename not in similarities:
            similarities[filename] = 0  # 유사도가 낮더라도 포함

    sorted_files = sorted(similarities.items(), key=lambda item: item[1], reverse=True)
    
    # 필수 파일들을 상위로 올리기
    essential_files = [(f, s) for f, s in sorted_files if f in settings['essential_files']]
    other_files = [(f, s) for f, s in sorted_files if f not in settings['essential_files']]
    
    return essential_files + other_files[:top_k - len(essential_files)]

def get_chat_response(messages):
    data = json.dumps({
        "model": "gpt-4o",
        "messages": messages,
        "temperature": 0
    })
    response = requests.post(CHAT_API_URL, headers=HEADERS, data=data)
    return response.json()['choices'][0]['message']['content']

def get_file_paths(folder_path):
    file_paths = []
    for root, dirs, files in os.walk(folder_path):
        dirs[:] = [d for d in dirs if d not in settings['ignore_folders']]
        for file in files:
            if file not in settings['ignore_files'] and any(file.endswith(ext) for ext in settings['extensions']):
                file_paths.append(os.path.join(root, file))
    return file_paths

def read_file(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    
    detected = chardet.detect(raw_data)
    encodings = [detected['encoding'], 'utf-8', 'euc-kr', 'cp949']
    
    for encoding in encodings:
        try:
            return raw_data.decode(encoding)
        except UnicodeDecodeError:
            continue
    
    return raw_data.decode('utf-8', errors='replace')

def hash_content(content):
    return hashlib.md5(content.encode('utf-8', errors='replace')).hexdigest()

def count_tokens(text):
    encoding = tiktoken.encoding_for_model("gpt-4")
    return len(encoding.encode(text))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        question = request.form['question']
        
        print("\n===== 질문 임베딩 생성 중 =====")
        question_embedding = get_embedding(question)
        print("질문 임베딩 생성 완료")
        
        print("\n===== 유사한 문서 찾는 중 =====")
        embeddings = load_embeddings(EMBEDDINGS_FILE)
        similar_files = find_most_similar(question_embedding, embeddings)
        
        print("\n===== 유사도로 선택된 파일 =====")
        for filename, similarity in similar_files:
            print(f"{filename}: {similarity}")
        
        relevant_docs = []
        total_tokens = 0
        max_tokens = 120000  # GPT-4의 토큰 제한을 고려하여 여유 있게 설정

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

        print(f"\n===== 프롬프트 생성 정보 =====")
        print(f"총 토큰 수: {total_tokens}")
        print(f"사용된 파일: {[doc['filename'] for doc in relevant_docs]}")

        system_message = """You are an AI assistant specialized in answering questions based on provided context. 
Your task is to:
    1. Then, Analyze the full content of the documents if necessary.
    2. Answer the user's question accurately using information from the context.
    3. If the context doesn't contain enough information, say so and provide the best possible answer based on your general knowledge.
    4. Cite the filenames of relevant documents in your answer.
    5. If appropriate, provide code snippets or examples from the context to support your answer.
    6. When creating diagrams, use mermaid."""

        user_message = f"""Question: {question}

Please answer the question based on the provided context. 
Context:
        {json.dumps(relevant_docs, ensure_ascii=False, indent=2)}"""
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]

        print("\n===== OpenAI API 호출 중 =====")
        answer = get_chat_response(messages)
        
        print("\n===== OpenAI 응답 정보 =====")
        print(f"응답 길이: {len(answer)} 글자")
        
        return render_template('result.html', question=question, answer=answer)
    
    return render_template('index.html')

@app.route('/extract_embeddings', methods=['POST'])
def extract_embeddings():
    backup_file = EMBEDDINGS_FILE + ".bak"
    if os.path.exists(EMBEDDINGS_FILE):
        shutil.copy2(EMBEDDINGS_FILE, backup_file)

    existing_embeddings = load_embeddings(backup_file)
    file_paths = get_file_paths('.')

    with open(EMBEDDINGS_FILE, 'w', encoding='utf-8') as f:
        for file_path in file_paths:
            try:
                relative_path = os.path.relpath(file_path)
                print(f"Processing {relative_path}")
                
                content = read_file(file_path)
                content_hash = hash_content(content)

                if relative_path in existing_embeddings and existing_embeddings[relative_path]['content_hash'] == content_hash:
                    file_data = existing_embeddings[relative_path]
                else:
                    print(f"  - Changes detected or new file, generating new embedding")
                    embedding = get_embedding(content)
                    file_data = {
                        "filename": relative_path, 
                        "content": content,
                        "content_hash": content_hash,
                        "embedding": embedding
                    }

                f.write(json.dumps(file_data, ensure_ascii=False) + '\n')

            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")

    print(f"Embedding extraction complete. Results saved to {EMBEDDINGS_FILE}")
    return redirect(url_for('index'))

if __name__ == "__main__":
    nltk.download('punkt', quiet=True)
    load_settings()
    app.run(debug=True, host='0.0.0.0', port=8080)
