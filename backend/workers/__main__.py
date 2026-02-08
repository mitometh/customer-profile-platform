"""Allow running workers via ``python -m workers <worker_type>``."""

import sys

from workers.entrypoint import run_worker

if __name__ == "__main__":
    import asyncio

    if len(sys.argv) != 2:
        print("Usage: python -m workers <worker_type>")
        sys.exit(1)
    asyncio.run(run_worker(sys.argv[1]))
