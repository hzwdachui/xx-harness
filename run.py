#!/usr/bin/env python3
"""Start xx-harness web server."""
import uvicorn
from src.config import WEB_PORT, ensure_dirs

if __name__ == "__main__":
    ensure_dirs()
    uvicorn.run("src.web.app:app", host="0.0.0.0", port=WEB_PORT, reload=True)
