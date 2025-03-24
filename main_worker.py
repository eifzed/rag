"""
Simple NSQ Consumer that reads configuration from environment variables
"""
import json
import time
import signal
import logging
import os
from dotenv import load_dotenv
# from services.document_service import DocumentService
from services.document_service import DocumentService
import nsq

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

# Load environment variables from .env file
load_dotenv()

# NSQ Configuration
NSQ_TOPIC = os.getenv('NSQ_TOPIC', 'messages')
NSQ_CHANNEL = os.getenv('NSQ_CHANNEL', 'processor')
NSQLOOKUPD_HTTP_ADDRESS = os.getenv('NSQLOOKUPD_HTTP_ADDRESS', '127.0.0.1')
NSQLOOKUPD_HTTP_PORT = os.getenv('NSQLOOKUPD_HTTP_PORT', '4161')
NSQ_MAX_IN_FLIGHT = int(os.getenv('NSQ_MAX_IN_FLIGHT', '10'))

buf = []
def process_message(message):
    """
    Process a message from NSQ.
    Return True to mark the message as processed successfully.
    Return False to requeue the message.
    """
    try:
        # Decode message body
        message_body = message.body.decode('utf-8')
        
        data = json.loads(message_body)
        
        logger.info(f"Processing message: {data}")
        DocumentService.process_background_document_embedding(data)

        
        return True
        
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON: {message.body}")
        # Don't retry parsing errors
        return True
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        # Requeue for retry
        return False

logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def on_exception(conn, err):
    logger.error(f"NSQ Exception: {err} on {conn}")

def main():
    """Run the NSQ consumer"""
    # Show configuration
    logger.info(f"Starting NSQ consumer:")
    logger.info(f"  Topic: {NSQ_TOPIC}")
    logger.info(f"  Channel: {NSQ_CHANNEL}")
    logger.info(f"  Lookup Address: {NSQLOOKUPD_HTTP_ADDRESS}:{NSQLOOKUPD_HTTP_PORT}")

    
    # Create the reader
    reader = nsq.Reader(
        topic=NSQ_TOPIC,
        channel=NSQ_CHANNEL,
        message_handler=process_message,
        lookupd_http_addresses=[f"{NSQLOOKUPD_HTTP_ADDRESS}:{NSQLOOKUPD_HTTP_PORT}"],
        max_in_flight=NSQ_MAX_IN_FLIGHT,
    )
    buf.append(reader)

    nsq.run()

if __name__ == "__main__":
    main()