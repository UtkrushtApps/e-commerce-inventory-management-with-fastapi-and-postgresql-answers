import asyncpg
from typing import List, Dict

async def inventory_valuation_report(conn: asyncpg.Connection):
    sql = """
    SELECT warehouse_id, SUM(total_value) as total_valuation
    FROM mv_inventory_valuation
    GROUP BY warehouse_id
    ORDER BY warehouse_id
    """
    res = await conn.fetch(sql)
    return [dict(r) for r in res]

async def refresh_inventory_valuation_mv(conn: asyncpg.Connection):
    await conn.execute('REFRESH MATERIALIZED VIEW mv_inventory_valuation;')
