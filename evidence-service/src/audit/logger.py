from datetime import datetime
import logging
import os

class AuditLogger:
    def __init__(self, log_file='audit.log'):
        self.logger = logging.getLogger('AuditLogger')
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log_action(self, action, user_id=None, details=None):
        log_message = f"Action: {action}"
        if user_id:
            log_message += f", User ID: {user_id}"
        if details:
            log_message += f", Details: {details}"
        self.logger.info(log_message)

    def log_error(self, error_message, user_id=None):
        log_message = f"Error: {error_message}"
        if user_id:
            log_message += f", User ID: {user_id}"
        self.logger.error(log_message)

# Example usage:
# audit_logger = AuditLogger()
# audit_logger.log_action('File uploaded', user_id='123', details='Uploaded file: report.pdf')