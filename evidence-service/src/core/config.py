import os

class Config:
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///evidence.db')
    FERNET_KEY = os.getenv('FERNET_KEY', None)
    THREAD_QUEUE = os.getenv('THREAD_QUEUE', 'False') == 'True'
    REDIS_URL = os.getenv('REDIS_URL', None)
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', None)
    FTS5_ENABLED = os.getenv('FTS5_ENABLED', 'False') == 'True'