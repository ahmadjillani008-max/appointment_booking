"""
Custom exceptions — one handler converts all of these to JSON responses.
"""

from fastapi import status


class AppException(Exception):
    """Base class. `code` is a short machine-readable string."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "bad_request"

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class NotFoundError(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"


class ConflictError(AppException):
    status_code = status.HTTP_409_CONFLICT
    code = "conflict"


class ForbiddenError(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    code = "forbidden"


class UnauthorizedError(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "unauthorized"


class BadRequestError(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "bad_request"