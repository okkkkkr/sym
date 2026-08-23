from enum import Enum, StrEnum


class EnumBase(Enum):
    @classmethod
    def get_member_values(cls):
        return [item.value for item in cls._member_map_.values()]

    @classmethod
    def get_member_names(cls):
        return [name for name in cls._member_names_]


class MethodType(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class ProductImportTaskStatus(StrEnum):
    PENDING = "pending"
    UPLOADING = "uploading"
    VALIDATING = "validating"
    VALIDATION_FAILED = "validation_failed"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    WARN = "warn"
    FAILED = "failed"
    CANCELED = "canceled"


class ProductImportTaskItemStatus(StrEnum):
    PENDING = "pending"
    VALIDATED = "validated"
    SUCCESS = "success"
    WARN = "warn"
    FAILED = "failed"
    SKIPPED = "skipped"


class ProductImportStrategy(StrEnum):
    CREATE_ONLY = "create_only"


class VideoResourceStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    UPLOADED = "uploaded"
    FAILED = "failed"


class ProductVideoUpdatePlanStatus(StrEnum):
    ACTIVE = "active"
    APPLIED = "applied"
    FAILED = "failed"
    SUPERSEDED = "superseded"
