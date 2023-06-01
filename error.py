class BaseError(RuntimeError):
    def __init__(self, message, level):
        self.message = message
        self.level = level


class RunnerConfigError(BaseError):
    def __init__(self, message, level="error"):
        super().__init__(message, level)


class RunnerError(BaseError):
    def __init__(self, message, level="error"):
        super().__init__(message, level)


class RunnerManagerError(BaseError):
    def __init__(self, message, level="error"):
        super().__init__(message, level)


class ManagerConfigError(BaseError):
    def __init__(self, message, level="error"):
        super().__init__(message, level)
