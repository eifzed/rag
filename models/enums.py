from enum import Enum


class UploadStatus(Enum):
    IN_QUEUE = "IN QUEUE"
    PROCESSING = "PROCESSING"
    FAILED = "FAILED"
    SUCCESS = "SUCCESS"