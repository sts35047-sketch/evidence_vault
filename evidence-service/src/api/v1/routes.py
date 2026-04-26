from flask import Blueprint, request, jsonify
from src.services.storage import upload_file, download_file
from src.services.encryption import encrypt_file, decrypt_file
from src.audit.logger import log_audit_event

bp = Blueprint('v1', __name__)

@bp.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file provided'}), 400
    file_path = upload_file(file)
    log_audit_event('File uploaded', file_path)
    return jsonify({'message': 'File uploaded successfully', 'file_path': file_path}), 201

@bp.route('/download/<path:file_path>', methods=['GET'])
def download(file_path):
    try:
        file_data = download_file(file_path)
        log_audit_event('File downloaded', file_path)
        return file_data, 200
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404

@bp.route('/encrypt', methods=['POST'])
def encrypt():
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file provided'}), 400
    encrypted_file_path = encrypt_file(file)
    log_audit_event('File encrypted', encrypted_file_path)
    return jsonify({'message': 'File encrypted successfully', 'file_path': encrypted_file_path}), 201

@bp.route('/decrypt', methods=['POST'])
def decrypt():
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file provided'}), 400
    decrypted_file_path = decrypt_file(file)
    log_audit_event('File decrypted', decrypted_file_path)
    return jsonify({'message': 'File decrypted successfully', 'file_path': decrypted_file_path}), 201