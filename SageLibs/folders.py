from tinydb import TinyDB, Query
import os
import logging
import sys
import traceback

db = TinyDB('sage_folders.json')
folders_table = db.table('folders')
selected_table = db.table('selected')

def get_all_folders():
    return [folder['path'] for folder in folders_table.all()]

def add_folder(folder_path):
    logging.info(f"Attempting to add folder: {folder_path}")
    
    try:
        # 시스템 인코딩 확인
        logging.info(f"File system encoding: {sys.getfilesystemencoding()}")
        
        # 경로 정규화 및 절대 경로 변환
        normalized_path = os.path.normpath(folder_path)
        logging.info(f"Normalized path: {normalized_path}")
        
        abs_path = os.path.abspath(normalized_path)
        logging.info(f"Absolute path: {abs_path}")
        
        # # 경로 존재 여부 확인
        # if not os.path.exists(abs_path):
        #     logging.error(f"Directory does not exist: {abs_path}")
        #     return False, "Invalid directory path (does not exist)"
        
        # # 디렉토리 여부 확인
        # if not os.path.isdir(abs_path):
        #     logging.error(f"Path is not a directory: {abs_path}")
        #     return False, "Invalid directory path (not a directory)"
        
        logging.info(f"Directory exists and is valid: {abs_path}")
        
        # 중복 확인
        existing = folders_table.get(Query().path == abs_path)
        if existing:
            logging.info(f"Folder already exists in the list: {abs_path}")
            return False, "Folder already exists in the list"
        
        # DB에 삽입
        folders_table.insert({'path': abs_path})
        logging.info(f"Folder added successfully: {abs_path}")
        return True, "Folder added successfully"
    
    except Exception as e:
        logging.error(f"Unexpected error in add_folder: {str(e)}")
        logging.error(traceback.format_exc())
        return False, f"Unexpected error: {str(e)}"

def delete_folder(folder_path):
    try:
        abs_path = os.path.abspath(os.path.normpath(folder_path))
        result = folders_table.remove(Query().path == abs_path)
        if result:
            logging.info(f"Folder removed successfully: {abs_path}")
            return True, "Folder removed successfully"
        logging.warning(f"Folder not found in the list: {abs_path}")
        return False, "Folder not found in the list"
    except Exception as e:
        logging.error(f"Error in delete_folder: {str(e)}")
        logging.error(traceback.format_exc())
        return False, f"Error deleting folder: {str(e)}"
    
def save_selected_folders(selected_folders):
    try:
        selected_table.truncate()  # 기존 선택 항목 모두 삭제
        selected_table.insert({'paths': selected_folders})
        logging.info(f"Saved selected folders: {selected_folders}")
        return True, "Selected folders saved successfully"
    except Exception as e:
        logging.error(f"Error saving selected folders: {str(e)}")
        logging.error(traceback.format_exc())
        return False, f"Error saving selected folders: {str(e)}"

def get_selected_folders():
    try:
        selected = selected_table.all()
        if selected:
            selected_folders = selected[0]['paths']
        else:
            selected_folders = []
        logging.info(f"Retrieved selected folders: {selected_folders}")
        return selected_folders
    except Exception as e:
        logging.error(f"Error retrieving selected folders: {str(e)}")
        logging.error(traceback.format_exc())
        return []