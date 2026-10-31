class AppError(Exception):
    status_code = 500
    detail = "internal server error"

    def __init__(self, detail: str | None = None) -> None:
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class ConflictError(AppError):
    status_code = 409
    detail = "resource already exists"


class BrokerUnavailable(AppError):
    status_code = 503
    detail = "task broker unavailable"
