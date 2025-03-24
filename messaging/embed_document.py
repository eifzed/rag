import os
import json
import nsq
import tornado.ioloop



from services.document_service import DocumentService


MAX_RETRIES = int(os.getenv("MAX_RETRIES"))
NSQLOOKUPD_HTTP_ADDRESS = os.getenv("NSQLOOKUPD_HTTP_ADDRESS")
NSQLOOKUPD_HTTP_PORT = os.getenv("NSQLOOKUPD_HTTP_PORT")
nsq_readers = []


def handle_message(message, processor):
    try:
        data = json.loads(message.body.decode())
        print(f"Processing message: {data}")
        processor(data)
        message.finish()
    except Exception as e:
        print(f"Error processing message: {e}")
        message.requeue()

def start_nsq_consumer(topic: str, channel: str, processor):
    reader = nsq.Reader(
        topic=topic,
        channel=channel,
        lookupd_http_addresses=[f"{NSQLOOKUPD_HTTP_ADDRESS}:{NSQLOOKUPD_HTTP_PORT}"],
        # nsqd_tcp_addresses=[f"http://nsqd.railway.internal:4150"],
        message_handler=lambda msg: handle_message(msg, processor),
        max_in_flight=2,
        lookupd_poll_interval=15,  # Increase from default
        lookupd_poll_jitter=0.3,   # Add some jitter
        lookupd_connect_timeout=5  # Increase timeout
    )
    nsq_readers.append(reader)
    return reader


async def close_consumer_conn():
    for reader in nsq_readers:
        reader.close()
    tornado.ioloop.IOLoop.instance().stop()