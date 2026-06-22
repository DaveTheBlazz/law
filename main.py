#!/usr/bin/env python3
"""Run the law opinions web app.

Usage:
    python main.py          # production (no reload)
    python main.py --reload # development (auto-reload)
"""

import argparse
import uvicorn
import config


def main():
    parser = argparse.ArgumentParser(description=config.APP_TITLE)
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload (development)")
    args = parser.parse_args()

    print(f"Starting {config.APP_TITLE} on http://{config.APP_HOST}:{config.APP_PORT}")
    uvicorn.run(
        "app:app",
        host=config.APP_HOST,
        port=config.APP_PORT,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
