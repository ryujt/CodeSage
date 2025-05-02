import logging
import traceback
from flask import Blueprint, render_template, request, jsonify
from SageLibs.folders import get_all_folders, add_folder, delete_folder, update_selected_folders, get_selected_folders

folder_bp = Blueprint('folders', __name__, url_prefix='/folders')

@folder_bp.route('/select', methods=['GET'])
def select_folders():
    folders = get_all_folders()
    selected_folders = get_selected_folders()
    return render_template('sage_folders.html', folders=folders, selected_folders=selected_folders)

@folder_bp.route('/add', methods=['POST'])
def add_folder_route():
    data = request.json
    folder = data.get('folder')
    if not folder:
        logging.warning("Add folder request received with no folder specified")
        return jsonify({"success": False, "message": "No folder provided"}), 400
    
    logging.info(f"Received request to add folder: {folder}")
    
    try:
        success, message = add_folder(folder)
        if success:
            logging.info(f"Successfully added folder: {folder}")
            return jsonify({"success": True, "message": message})
        else:
            logging.warning(f"Failed to add folder: {folder}. Reason: {message}")
            return jsonify({"success": False, "message": message}), 400
    except Exception as e:
        logging.error(f"Unexpected error in add_folder_route: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

@folder_bp.route('/delete', methods=['POST'])
def delete_folder_route():
    folder = request.json.get('folder')
    if not folder:
        return jsonify({"success": False, "message": "No folder provided"}), 400
    
    success, message = delete_folder(folder)
    return jsonify({"success": success, "message": message})

@folder_bp.route('/update', methods=['POST'])
def update_selected_folders_route():
    data = request.json
    selected_folders = data.get('selectedFolders', [])
    
    logging.info(f"Received request to save selected folders: {selected_folders}")
    
    try:
        success, message = update_selected_folders(selected_folders)
        if success:
            return jsonify({"success": True, "message": message})
        else:
            return jsonify({"success": False, "message": message}), 400
    except Exception as e:
        logging.error(f"Error saving selected folders: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500 