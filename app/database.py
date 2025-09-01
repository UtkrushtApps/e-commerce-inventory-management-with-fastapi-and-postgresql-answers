import asyncpg
from fastapi import FastAPI
from functools import lru_cache

DATABASE_URL = "postgresql://shopflow:password@localhost:5432/shopflow"

class _PoolHolder:
    pool = None

@lru_cache
def get_connection_pool():
    return _PoolHolder.pool

async def startup(app: FastAPI):
    _PoolHolder.pool = await asyncpg.create_pool(dsn=DATABASE_URL, min_size=2, max_size=10)

async def shutdown(app: FastAPI):
    if _PoolHolder.pool:
        await _PoolHolder.pool.close()
