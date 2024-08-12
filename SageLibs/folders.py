from tinydb import TinyDB, Query
import logging

db = TinyDB('SageFolders.json')
folders_table = db.table('folders')

def get_all_folders():
    return sorted([folder['path'] for folder in folders_table.all()])

def add_folder(folder_path):
    logging.info(f"Attempting to add folder: {folder_path}")
    
    try:
        existing = folders_table.get(Query().path == folder_path)
        if existing:
            logging.info(f"Folder already exists in the list: {folder_path}")
            return False, "Folder already exists in the list"
        
        folders_table.insert({'path': folder_path, 'selected': False})
        logging.info(f"Folder added successfully: {folder_path}")
        return True, "Folder added successfully"
    
    except Exception as e:
        logging.error(f"Unexpected error in add_folder: {str(e)}")
        return False, f"Unexpected error: {str(e)}"

def delete_folder(folder_path):
    try:
        result = folders_table.remove(Query().path == folder_path)
        if result:
            logging.info(f"Folder removed successfully: {folder_path}")
            return True, "Folder removed successfully"
        logging.warning(f"Folder not found in the list: {folder_path}")
        return False, "Folder not found in the list"
    except Exception as e:
        logging.error(f"Error in delete_folder: {str(e)}")
        return False, f"Error deleting folder: {str(e)}"
    
def update_selected_folders(selected_folders):
    try:
        for folder in folders_table.all():
            folders_table.update({'selected': folder['path'] in selected_folders}, Query().path == folder['path'])
        logging.info(f"Updated selected folders: {selected_folders}")
        return True, "Selected folders updated successfully"
    except Exception as e:
        logging.error(f"Error updating selected folders: {str(e)}")
        return False, f"Error updating selected folders: {str(e)}"

def get_selected_folders():
    try:
        selected_folders = [folder['path'] for folder in folders_table.search(Query().selected == True)]
        logging.info(f"Retrieved selected folders: {selected_folders}")
        return selected_folders
    except Exception as e:
        logging.error(f"Error retrieving selected folders: {str(e)}")
        return []