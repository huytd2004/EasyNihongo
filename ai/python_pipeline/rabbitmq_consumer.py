import pika
import json
import os
import threading
import redis
import time

try:
    from .review_pipeline import ReviewPipeline
except ImportError:
    from review_pipeline import ReviewPipeline

def start_consumer():
    rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
    rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))
    rabbitmq_user = os.getenv('RABBITMQ_USER', 'guest')
    rabbitmq_pass = os.getenv('RABBITMQ_PASS', 'guest')
    
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_port = int(os.getenv('REDIS_PORT', 6379))
    
    # Initialize redis client
    r = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)
    review_pipeline = ReviewPipeline()
    
    # Connection credentials
    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
    parameters = pika.ConnectionParameters(
        host=rabbitmq_host,
        port=rabbitmq_port,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300
    )
    
    connection = None
    # Wait for RabbitMQ service to boot up
    for attempt in range(15):
        try:
            connection = pika.BlockingConnection(parameters)
            print("Successfully connected to RabbitMQ.")
            break
        except Exception as e:
            print(f"Failed to connect to RabbitMQ (attempt {attempt+1}/15): {e}")
            time.sleep(5)
            
    if not connection:
        print("Could not connect to RabbitMQ after 15 attempts. Exiting consumer.")
        return
        
    channel = connection.channel()
    
    # Declare Exchange
    channel.exchange_declare(exchange='review.exchange', exchange_type='topic')
    
    # Declare Quiz Queue
    channel.queue_declare(queue='review.quiz.queue', durable=True)
    channel.queue_bind(exchange='review.exchange', queue='review.quiz.queue', routing_key='review.quiz.generate')
    
    # Declare Story Queue
    channel.queue_declare(queue='review.story.queue', durable=True)
    channel.queue_bind(exchange='review.exchange', queue='review.story.queue', routing_key='review.story.generate')
    
    def callback(ch, method, properties, body):
        task_id = None
        try:
            task = json.loads(body.decode('utf-8'))
            task_id = task.get('taskId')
            words = task.get('words', [])
            level = task.get('level', 'N3')
            
            if not task_id:
                print("Task ID is missing in message payload.")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
                
            print(f"[{task_id}] Processing task from queue routing key: {method.routing_key}")
            r.set(f"task:status:{task_id}", "PROCESSING", ex=3600)
            
            if method.routing_key == 'review.quiz.generate':
                question_count = task.get('questionCount', 20)
                recent_mistakes = task.get('recentMistakes', [])
                result = review_pipeline.generate_quiz(
                    words=words,
                    level=level,
                    question_count=question_count,
                    recent_mistakes=recent_mistakes
                )
            elif method.routing_key == 'review.story.generate':
                recent_mistakes = task.get('recentMistakes', [])
                result = review_pipeline.generate_story(
                    words=words,
                    level=level,
                    recent_mistakes=recent_mistakes
                )
            else:
                raise ValueError(f"Unknown routing key: {method.routing_key}")
                
            # Store result and set status to SUCCESS
            r.set(f"task:result:{task_id}", json.dumps(result), ex=3600)
            r.set(f"task:status:{task_id}", "SUCCESS", ex=3600)
            print(f"[{task_id}] Task completed successfully.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            print(f"Error handling RabbitMQ message for task {task_id}: {e}")
            if task_id:
                try:
                    r.set(f"task:status:{task_id}", "FAILED", ex=3600)
                except Exception as re:
                    print(f"Failed to set status to FAILED in redis: {re}")
            # ACK so the poison/broken message is discarded and doesn't crash the loop
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='review.quiz.queue', on_message_callback=callback)
    channel.basic_consume(queue='review.story.queue', on_message_callback=callback)
    
    print("Started RabbitMQ consuming loop.")
    channel.start_consuming()

def start_rabbitmq_thread():
    t = threading.Thread(target=start_consumer, daemon=True)
    t.start()
