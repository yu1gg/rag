"""Custom application exceptions."""


class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code if code is not None else status_code


class ConfigError(AppError):
    def __init__(self, message: str = "配置缺失或无效"):
        super().__init__(message=message, status_code=500, code=500)


class ServiceUnavailableError(AppError):
    def __init__(self, message: str = "服务暂不可用"):
        super().__init__(message=message, status_code=503, code=503)

