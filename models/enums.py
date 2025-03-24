from enum import Enum


class UploadStatus(Enum):
    IN_QUEUE = "IN QUEUE"
    PROCESSING = "PROCESSING"
    FAILED_PROCESSING = "FAILED"
    SUCCESS = "SUCCESS"