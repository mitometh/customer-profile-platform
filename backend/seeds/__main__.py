"""Allow running seeds via python -m seeds"""

import asyncio

from seeds.seed import seed_database

if __name__ == "__main__":
    asyncio.run(seed_database())
