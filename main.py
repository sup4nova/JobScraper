#!/usr/bin/env python3
"""
JobScrapper — point d'entrée principal.

Usage:
  python main.py                    # Lance la web app
  python main.py --host 0.0.0.0 --port 8080
"""
import sys
import argparse
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="JobScrapper web app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true", help="Hot reload (dev)")
    args = parser.parse_args()

    print(f"\nJobScrapper demarre sur http://{args.host}:{args.port}\n")
    uvicorn.run(
        "web.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
