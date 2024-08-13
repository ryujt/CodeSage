import os
import json
import hashlib
import chardet
import PyPDF2
import logging
import tiktoken
import subprocess
from sklearn.metrics.pairwise import cosine_similarity
from .config import get_settings, TOKEN_COUNTER_MODEL, EMBEDDINGS_FILE, SIMILARITY_THRESHOLD

def load_embeddings(file_path):
    embeddings = {}
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                embeddings[data['filename']] = data
    return embeddings

def find_most_similar(query_embedding, embeddings, similarity_threshold=SIMILARITY_THRESHOLD, top_k=100):
    essential_files = {filename: 10 for filename in get_settings('essential_files')}

    similarities = {}
    for filename, data in embeddings.items():
        if filename in essential_files:
            continue
        
        if not any(filename.endswith(ext) for ext in get_settings('extensions')):
            continue
        if filename in get_settings('ignore_files'):
            continue
        if any(ignore_folder in filename for ignore_folder in get_settings('ignore_folders')):
            continue
        
        similarity = cosine_similarity([query_embedding], [data['embedding']])[0][0]
        if similarity >= similarity_threshold:
            similarities[filename] = similarity

    sorted_files = sorted(similarities.items(), key=lambda item: item[1], reverse=True)
    
    result = list(essential_files.items()) + sorted_files[:top_k - len(essential_files)]
    
    return result[:top_k]

def get_file_paths(folder_path):
    file_paths = []
    for root, dirs, files in os.walk(folder_path):
        dirs[:] = [d for d in dirs if d not in get_settings('ignore_folders')]
        for file in files:
            if file not in get_settings('ignore_files') and any(file.endswith(ext) for ext in get_settings('extensions')):
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

def get_relevant_documents(folders, question_embedding, max_tokens=80000):
    relevant_docs = []
    total_tokens = 0

    for folder in folders:
        if not folder.endswith('/') and not folder.endswith('\\'):
            folder += '/'
        
        embedding_file = os.path.join(folder, EMBEDDINGS_FILE)
        logging.debug(f"임베딩 파일 로드: {embedding_file}")
        
        try:
            embeddings = load_embeddings(embedding_file)
        except Exception as e:
            logging.error(f"Error loading embeddings from {embedding_file}: {str(e)}")
            continue

        similar_files = find_most_similar(question_embedding, embeddings)
        
        logging.debug(f"{folder}에서 유사도로 선택된 파일:")
        for filename, similarity in similar_files:
            logging.debug(f"{filename}: {similarity}")
        
        for filename, similarity in similar_files:
            if filename not in embeddings:
                logging.warning(f"File {filename} not found in embeddings. Skipping.")
                continue

            content = embeddings[filename]['content']
            doc_tokens = count_tokens(filename + "\n\n" + content)
            
            if total_tokens + doc_tokens > max_tokens:
                logging.info("최대 토큰 수 도달, 추가 파일 처리 중지")
                return relevant_docs
            
            relevant_docs.append({
                "tokens": doc_tokens,
                "filename": filename,
                "similarity": similarity,
                "content": content
            })
            total_tokens += doc_tokens

    logging.debug(f"프롬프트 생성 정보:")
    logging.debug(f"총 토큰 수: {total_tokens}")
    logging.debug(f"사용된 파일: {[doc['filename'] for doc in relevant_docs]}")

    return relevant_docs

def get_git_branches(folder):
    try:
        branches = subprocess.check_output(['git', '-C', folder, 'branch', '--list'], encoding='utf-8')
        return branches.split()
    except subprocess.CalledProcessError as e:
        raise Exception(f"{folder}에서 Git 명령을 실행하는데 실패했습니다.") from e
    
def get_changed_files_in_diff(folder, analysis_type):
    branches = get_git_branches(folder)
    base_branch = 'main' if 'main' in branches else 'master' if 'master' in branches else None
    if not base_branch:
        raise Exception(f"{folder}에서 필요한 브랜치(main 또는 master)가 존재하지 않습니다.")

    command = []
    if analysis_type == 'main':
        command = ['git', '-C', folder, 'diff', f'{base_branch}..HEAD', '--name-only']
    elif analysis_type == 'recent':
        command = ['git', '-C', folder, 'diff', 'HEAD^', 'HEAD', '--name-only']
    else:
        raise Exception("분석 유형이 잘못 지정되었습니다.")

    try:
        output = subprocess.check_output(command, encoding='utf-8').strip().split('\n')
        all_changed_files = [file for file in output if file]

        programming_extensions = [
            '.py', '.js', '.html', '.css', '.java', '.c', '.cpp', '.h', 'hpp', '.ts', 
            '.tsx', '.jsx', '.json', '.xml', '.php', '.rb', '.go', '.rs', 'pas'
        ]

        # Filter the changed files based on settings
        filtered_changed_files = []
        for file in all_changed_files:
            file_name = os.path.basename(file)
            file_dir = os.path.dirname(file)

            # 확장자 필터링이 처음에 적용되도록 설정
            if not any(file_name.endswith(ext) for ext in programming_extensions):
                print(f"File ignored due to extensions: {file_name}")
                continue
            
            if file_name in get_settings('ignore_files'):
                print(f"File ignored due to ignore_files: {file_name}")
                continue
            if any(ignore_folder in file_dir.split(os.sep) for ignore_folder in get_settings('ignore_folders')):
                print(f"File ignored due to ignore_folders: {file}")
                continue

            filtered_changed_files.append(file)
        
        if not filtered_changed_files:
            print(f"Warning: No changed files found in {folder} for {analysis_type} analysis.")
        else:
            print(f"Found {len(filtered_changed_files)} changed files in {folder} for {analysis_type} analysis.")

        return filtered_changed_files
    except subprocess.CalledProcessError as e:
        raise Exception(f"{folder}에서 {analysis_type}에 해당하는 diff 계산 실패.") from e
   
def diff_between_branches(folder, analysis_type, specific_file=None):
    branches = get_git_branches(folder)
    print(f"Branches found: {branches}")

    base_branch = 'main' if 'main' in branches else 'master' if 'master' in branches else None
    print(f"Base branch: {base_branch}")
    
    if not base_branch:
        raise Exception(f"{folder}에서 필요한 브랜치(main 또는 master)가 존재하지 않습니다.")

    if analysis_type == 'main':
        diff_command = f'{base_branch}..HEAD'
    elif analysis_type == 'recent':
        diff_command = 'HEAD^..HEAD'
    else:
        raise Exception("분석 유형이 잘못 지정되었습니다.")

    if specific_file:
        specific_file = os.path.join(folder, specific_file)
        print(f"Specific file for diff: {specific_file}")
        command = ['git', '-C', folder, 'diff', diff_command, '--', specific_file]
    else:
        print("No specific file provided, diffing entire branch.")
        command = ['git', '-C', folder, 'diff', diff_command]
    
    try:
        # UTF-8 디코딩을 시도합니다.
        output = subprocess.check_output(command, encoding='utf-8')
    except UnicodeDecodeError:
        # UTF-8 디코딩에 실패하면 바이트 문자열로 출력을 가져옵니다.
        raw_output = subprocess.check_output(command)
        # chardet를 사용하여 인코딩을 감지합니다.
        detected = chardet.detect(raw_output)
        encoding = detected['encoding']
        print(f"Detected encoding: {encoding}")
        # 감지된 인코딩을 사용하여 디코딩합니다.
        output = raw_output.decode(encoding)

    return output
