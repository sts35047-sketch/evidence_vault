from rq import Worker, Queue, Connection
import redis
import os

def get_redis_connection():
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    return redis.from_url(redis_url)

if __name__ == '__main__':
    with Connection(get_redis_connection()):
        worker = Worker(map(Queue, ['default']))
        worker.work()