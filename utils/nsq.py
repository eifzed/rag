import os
import pynsq
import json


NSQD_TCP_ADDRESS = os.getenv("NSQD_TCP_ADDRESS")
NSQD_TCP_PORT = os.getenv("NSQD_TCP_PORT")


async def publish_to_nsq(topic: str, data: dict):
    writer = await pynsq.Nsqd(f"{NSQD_TCP_ADDRESS}:{NSQD_TCP_PORT}")
    await writer.pub(topic, json.dumps(data).encode())
    return {"message": "Published successfully"}