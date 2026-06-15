#!/usr/bin/env python3
"""Run the law opinions web app.

Usage:
    .venv/Scripts/python.exe run.py
"""

import uvicorn
import config

if __name__ == "__main__":
    print(f"Starting {config.APP_TITLE} on http://{config.APP_HOST}:{config.APP_PORT}")
    uvicorn.run(
        "app:app",
        host=config.APP_HOST,
        port=config.APP_PORT,
        reload=True,
    )
