from fastapi.responses import JSONResponse


def error_response(status: int, code: str, message: str) -> JSONResponse:
    """Build the standard `{error: {code, message}}` HTTP body."""
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})
