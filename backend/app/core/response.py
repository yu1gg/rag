"""Response envelope helpers."""

from typing import Any


def success_response(data: Any, message: str = "ok", code: int = 0) -> dict:
    return {
        "code": code,
        "message": message,
        "data": data,
    }


def error_response(message: str, code: int, data: Any = None) -> dict:
    return {
        "code": code,
        "message": message,
        "data": data,
    }

