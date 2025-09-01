from uuid import UUID
from typing import List
import asyncpg
from fastapi import HTTPException

async def bulk_update_prices(conn: asyncpg.Connection, updates: List[dict]):
    # Each update: {product_id: UUID, price: decimal}
    responses = []
    async with conn.transaction():
        for upd in updates:
            product_id, price = upd['product_id'], upd['price']
            # Insert into price_history and validate >=0
            if price < 0:
                raise HTTPException(status_code=400, detail='Price cannot be negative')
            await conn.execute(
                "INSERT INTO price_history (product_id, price, effective_from) VALUES ($1, $2, NOW())",
                product_id, price
            )
            responses.append({"product_id": str(product_id), "new_price": float(price)})
    return responses
