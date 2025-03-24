import os
import nsq
import tornado.ioloop
import json
import asyncio
import httpx


NSQD_HTTP_ADDRESS = os.getenv("NSQD_HTTP_ADDRESS")
NSQD_HTTP_PORT = os.getenv("NSQD_HTTP_PORT")

async def publish_to_nsq(topic: str, data: dict):
    """
    Publish a message to NSQ with proper connection handling.
    
    Args:
        topic: The NSQ topic to publish to
        data: Dictionary containing the message data
    
    Returns:
        bool: True if successful, False otherwise
    """
    writer = None
    try:
        # Create a new writer
        writer = nsq.Writer(["https://nsqd-production-99bc.up.railway.app"])
        
        # Give it a moment to establish connections
        await asyncio.sleep(0.5)
        
        # Convert data to JSON bytes
        message_bytes = json.dumps(data).encode()
        
        # Create a future to track completion
        publish_future = asyncio.Future()
        
        def callback(conn, response_data):
            if isinstance(response_data, nsq.Error):
                publish_future.set_exception(Exception(f"NSQ error: {response_data}"))
            else:
                publish_future.set_result(True)
        
        # Publish the message with callback
        writer.pub(topic, message_bytes, callback)
        
        # Wait for the callback (with timeout)
        try:
            result = await asyncio.wait_for(publish_future, timeout=5.0)
            print(f"Successfully published to NSQ topic '{topic}'")
            return result
        except asyncio.TimeoutError:
            print(f"Timeout publishing to NSQ topic '{topic}'")
            return False
            
    except Exception as e:
        print(f"Error publishing to NSQ: {e}")
        return False
    finally:
        # Only close the writer after the operation completes
        if writer:
            writer.close()


async def send_to_nsq_api(topic: str, payload: dict):
    url = f"{NSQD_HTTP_ADDRESS}:{NSQD_HTTP_PORT}/pub?topic={topic}"
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        return response