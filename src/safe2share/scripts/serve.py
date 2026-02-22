import argparse

import uvicorn


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="safe2share-api", description="Run Safe2Share FastAPI server."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    uvicorn.run(
        "safe2share.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
    return 0
