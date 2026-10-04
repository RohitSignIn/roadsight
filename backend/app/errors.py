class ApplicationError(Exception):
    """Base class for safe, user-facing application errors."""

    code = "application_error"
    status_code = 400


class ModelUnavailableError(ApplicationError):
    code = "model_unavailable"
    status_code = 503


class InvalidMediaError(ApplicationError):
    code = "invalid_media"
    status_code = 415


class UploadTooLargeError(ApplicationError):
    code = "upload_too_large"
    status_code = 413


class JobNotFoundError(ApplicationError):
    code = "job_not_found"
    status_code = 404
