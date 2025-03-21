import uuid
import time
import struct

def uuidv7():
    # Get the current timestamp in milliseconds
    timestamp = int(time.time() * 1000)
    
    # Convert timestamp to bytes (first 6 bytes of UUIDv7)
    timestamp_bytes = struct.pack(">Q", timestamp)[2:]  # Use big-endian and take last 6 bytes

    # Generate 10 random bytes for the remaining part of the UUID
    random_bytes = uuid.uuid4().bytes[6:]

    # Combine timestamp and random bytes
    uuid_bytes = timestamp_bytes + random_bytes

    # Set version (7) and variant bits
    uuid_bytes = bytearray(uuid_bytes)
    uuid_bytes[6] = (uuid_bytes[6] & 0x0F) | 0x70  # Set version 7 (0b0111)
    uuid_bytes[8] = (uuid_bytes[8] & 0x3F) | 0x80  # Set variant (0b10)

    return str(uuid.UUID(bytes=bytes(uuid_bytes)))