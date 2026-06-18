#!/usr/bin/env python3
"""Run the law opinions web app.

Usage:
    python main.py
"""

import uvicorn
import config

def main():
    print(f"Starting {config.APP_TITLE} on http://{config.APP_HOST}:{config.APP_PORT}")
    uvicorn.run(
        "app:app",
        host=config.APP_HOST,
        port=config.APP_PORT,
        reload=True,
    )

if __name__ == "__main__":
    main()
