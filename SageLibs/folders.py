from tinydb import TinyDB, Query
import os
import logging
import sys
import traceback

db = TinyDB('sage_folders.json')
folders_table = db.table('folders')
selected_table = db.table('selected')

def get_all_folders():
    return sorted([folder['path'] for folder in folders_table.all()])

def add_folder(folder_path):
    logging.info(f"Attempting to add folder: {folder_path}")
    
    try:
        # 중복 확인
        existing = folders_table.get(Query().path == folder_path)
        if existing:
            logging.info(f"Folder already exists in the list: {folder_path}")
            return False, "Folder already exists in the list"
        
        # DB에 삽입
        folders_table.insert({'path': folder_path})
        logging.info(f"Folder added successfully: {folder_path}")
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