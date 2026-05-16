from fastapi.responses import JSONResponse


def not_found(msg: str = "not found") -> JSONResponse:
    return JSONResponse({"error": msg}, status_code=404)
