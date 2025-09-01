from typing import List, Optional, Dict
from uuid import UUID
import asyncpg
from fastapi import HTTPException
from asyncpg.transaction import Transaction

async def update_inventory(
    conn: asyncpg.Connection, 
    product_id: UUID, 
    warehouse_id: UUID, 
    quantity_delta: int, 
    movement_type: str, 
    comment: Optional[str]=None,
    related_movement_id: Optional[UUID]=None
):
    async with conn.transaction():
        # Lock inventory row for update
        inventory_row = await conn.fetchrow(
            "SELECT * FROM inventory WHERE product_id = $1 AND warehouse_id = $2 FOR UPDATE",
            product_id, warehouse_id
        )
        if not inventory_row:
            if quantity_delta < 0:
                raise HTTPException(status_code=409, detail='Cannot deduct from non-existing inventory')
            # Insert new inventory row
            new_qty = quantity_delta
            await conn.execute(
                "INSERT INTO inventory (product_id, warehouse_id, quantity) VALUES ($1, $2, $3)",
                product_id, warehouse_id, new_qty
            )
        else:
            new_qty = inventory_row['quantity'] + quantity_delta
            if new_qty < 0:
                raise HTTPException(status_code=409, detail='Insufficient stock')
            await conn.execute(
                "UPDATE inventory SET quantity = $1 WHERE id = $2",
                new_qty, inventory_row['id']
            )
        # Log movement synchronously for immediate consistency; for async/batch, move to background
        await conn.execute(
            """
            INSERT INTO inventory_movements (product_id, warehouse_id, movement_type, related_movement_id, quantity, comment)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            product_id, warehouse_id, movement_type, related_movement_id, quantity_delta, comment
        )
        return {"product_id": str(product_id), "warehouse_id": str(warehouse_id), "new_quantity": new_qty}

async def log_inventory_movement(
    conn: asyncpg.Connection,
    product_id: UUID, warehouse_id: UUID,
    movement_type: str, quantity: int,
    comment: Optional[str]=None, related_movement_id: Optional[UUID]=None
):
    await conn.execute(
        """
        INSERT INTO inventory_movements (product_id, warehouse_id, movement_type, related_movement_id, quantity, comment)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        product_id, warehouse_id, movement_type, related_movement_id, quantity, comment
    )

async def get_low_stock(conn: asyncpg.Connection, threshold: int=10) -> List[Dict]:
    # Get products by their current inventory levels
    rows = await conn.fetch(
        """
        SELECT i.product_id, i.warehouse_id, i.quantity, p.name, p.sku
        FROM inventory i JOIN products p ON i.product_id = p.id
        WHERE i.quantity < $1
        ORDER BY i.warehouse_id, i.product_id
        """, threshold
    )
    return [dict(r) for r in rows]
