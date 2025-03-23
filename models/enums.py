from enum import Enum


class UploadStatus(Enum):
    IN_QUEUE = "IN_QUEUE"
    PROCESSING = "PROCESSING"
    FAILED_PROCESSING = "FAILED_PROCESSING"
    SUCCESS = "SUCCESS"