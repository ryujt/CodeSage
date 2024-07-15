import os
import json
import hashlib
import chardet
import PyPDF2
import logging
import tiktoken
from sklearn.metrics.pairwise import cosine_similarity
from .config import settings, TOKEN_COUNTER_MODEL

def load_embeddings(file_path):
    embeddings = {}
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                embeddings[data['filename']] = data
    return embeddings

def find_most_similar(query_embedding, embeddings, similarity_threshold=0.25, top_k=100):
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