import os
import json
import hashlib
import chardet
import PyPDF2
import logging
import tiktoken
import subprocess
from sklearn.metrics.pairwise import cosine_similarity
from .config import settings, TOKEN_COUNTER_MODEL, EMBEDDINGS_FILE

def load_embeddings(file_path):
    embeddings = {}
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                embeddings[data['filename']] = data
    return embeddings

def find_most_similar(query_embedding, embeddings, similarity_threshold=0.3, top_k=100):
    similarities = {}
    for filename, data in embeddings.items():
        if not any(filename.endswith(ext) for ext in settings['extensions']):
            continue
        if filename in settings['ignore_files']:
            continue
        if any(ignore_folder in filename for ignore_folder in settings['ignore_folders']):
            continue
        
        similarity = cosine_similarity([query_embedding], [data['embedding']])[0][0]
        if similarity >= similarity_threshold or filename in settings['essential_files']:
            similarities[filename] = similarity

    for filename in settings['essential_files']:
        if filename in embeddings and filename not in similarities:
            similarities[filename] = 0

    sorted_files = sorted(similarities.items(), key=lambda item: item[1], reverse=True)
    
    essential_files = [(f, s) for f, s in sorted_files if f in settings['essential_files']]
    other_files = [(f, s) for f, s in sorted_files if f not in settings['essential_files']]
    
    return essential_files + other_files[:top_k - len(essential_files)]

def get_file_paths(folder_path):
    file_paths = []
    for root, dirs, files in os.walk(folder_path):
        dirs[:] = [d for d in dirs if d not in settings['ignore_folders']]
        for file in files:
            if file not in settings['ignore_files'] and any(file.endswith(ext) for ext in settings['extensions']):
                file_paths.append(os.path.join(root, file))
    return file_paths

def pdf_to_text(pdf_path):
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        logging.error(f"Error processing PDF {pdf_path}: {str(e)}")
        return ""

def read_file(file_path):
    if file_path.lower().endswith('.pdf'):
        return pdf_to_text(file_path)
    
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
    encoding = tiktoken.encoding_for_model(TOKEN_COUNTER_MODEL)
    return len(encoding.encode(text))

def get_relevant_documents(question_part_token_count, question_embedding, max_tokens=100000):
    logging.debug("유사한 문서 찾기 시작")
    embeddings = load_embeddings(EMBEDDINGS_FILE)
    similar_files = find_most_similar(question_embedding, embeddings)
    
    logging.debug("유사도로 선택된 파일:")
    for filename, similarity in similar_files:
        logging.debug(f"{filename}: {similarity}")
    
    relevant_docs = []
    total_tokens = question_part_token_count

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

    logging.debug(f"프롬프트 생성 정보:")
    logging.debug(f"총 토큰 수: {total_tokens}")
    logging.debug(f"사용된 파일: {[doc['filename'] for doc in relevant_docs]}")

    return relevant_docs

def get_git_branches():
    try:
        branches = subprocess.check_output(['git', 'branch', '--list'], encoding='utf-8')
        return branches.split()
    except subprocess.CalledProcessError as e:
        raise Exception("Git 명령을 실행하는데 실패했습니다.") from e
    
def get_changed_files_in_diff(analysis_type):
    branches = get_git_branches()
    base_branch = 'main' if 'main' in branches else 'master' if 'master' in branches else None
    if not base_branch:
        raise Exception("필요한 브랜치(main 또는 master)가 존재하지 않습니다.")

    command = []
    if analysis_type == 'main':
        command = ['git', 'diff', f'{base_branch}..HEAD', '--name-only']
    elif analysis_type == 'recent':
        command = ['git', 'diff', 'HEAD~1..HEAD', '--name-only']
    else:
        raise Exception("분석 유형이 잘못 지정되었습니다.")

    try:
        all_changed_files = subprocess.check_output(command, encoding='utf-8').strip().split('\n')
        
        # Filter the changed files based on settings
        filtered_changed_files = []
        for file in all_changed_files:
            if file in settings['ignore_files']:
                continue
            if any(ignore_folder in file for ignore_folder in settings['ignore_folders']):
                continue
            if not any(file.endswith(ext) for ext in settings['extensions']):
                continue
            filtered_changed_files.append(file)
        
        return filtered_changed_files
    except subprocess.CalledProcessError as e:
        raise Exception(f"{analysis_type}에 해당하는 diff 계산 실패.") from e
   
def diff_between_branches(analysis_type, specific_file=None):
    branches = get_git_branches()
    base_branch = 'main' if 'main' in branches else 'master' if 'master' in branches else None
    
    if not base_branch:
        raise Exception("Required branch (main or master) is missing.")

    command = ['git', 'diff', f'{base_branch}..HEAD', '--', specific_file] if specific_file else ['git', 'diff', f'{base_branch}..HEAD']
    try:
        return subprocess.check_output(command, encoding='utf-8')
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to calculate diff for {analysis_type}.") from e    