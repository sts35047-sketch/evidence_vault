# Simple in-process background job runner
import threading
import os

JOB_STORE = {}
JOB_LOCK = threading.Lock()


def start_background(target, *args, **kwargs):
    job_id = os.urandom(8).hex()
    def wrapper():
        try:
            result = target(*args, **kwargs)
            with JOB_LOCK:
                JOB_STORE[job_id] = {'status': 'done', 'result': result}
        except Exception as e:
            with JOB_LOCK:
                JOB_STORE[job_id] = {'status': 'error', 'error': str(e)}

    with JOB_LOCK:
        JOB_STORE[job_id] = {'status': 'running'}
    t = threading.Thread(target=wrapper, daemon=True)
    t.start()
    return job_id


def job_status(job_id):
    with JOB_LOCK:
        return JOB_STORE.get(job_id, {'status': 'unknown'})
