from uuid import UUID
import asyncpg
from fastapi import HTTPException

async def transfer_inventory(
    conn: asyncpg.Connection, 
    product_id: UUID, 
    src_warehouse_id: UUID, 
    dest_warehouse_id: UUID, 
    quantity: int, 
    comment: str = None
):
    if src_warehouse_id == dest_warehouse_id:
        raise HTTPException(400, 'Cannot transfer within the same warehouse.')
    if quantity <= 0:
        raise HTTPException(400, 'Transfer quantity must be positive.')
    async with conn.transaction():
        # Deduct stock from source
        res_src = await conn.fetchrow(
            "SELECT * FROM inventory WHERE product_id = $1 AND warehouse_id = $2 FOR UPDATE",
            product_id, src_warehouse_id
        )
        if not res_src or res_src['quantity'] < quantity:
            raise HTTPException(409, 'Insufficient stock for transfer.')
        new_src_qty = res_src['quantity'] - quantity
        await conn.execute(
            "UPDATE inventory SET quantity = $1 WHERE id = $2",
            new_src_qty, res_src['id']
        )
        # Add stock to dest warehouse
        res_dest = await conn.fetchrow(
            "SELECT * FROM inventory WHERE product_id = $1 AND warehouse_id = $2 FOR UPDATE",
            product_id, dest_warehouse_id
        )
        if not res_dest:
            await conn.execute(
                "INSERT INTO inventory (product_id, warehouse_id, quantity) VALUES ($1, $2, $3)",
                product_id, dest_warehouse_id, quantity
            )
            new_dest_qty = quantity
        else:
            new_dest_qty = res_dest['quantity'] + quantity
            await conn.execute(
                "UPDATE inventory SET quantity = $1 WHERE id = $2",
                new_dest_qty, res_dest['id']
            )
        # Log both ends of the transfer
        movement_out_id = await conn.fetchval(
            """
            INSERT INTO inventory_movements (product_id, warehouse_id, movement_type, quantity, comment)
            VALUES ($1, $2, 'transfer_out', $3, $4) RETURNING id
            """, product_id, src_warehouse_id, -quantity, comment
        )
        await conn.execute(
            """
            INSERT INTO inventory_movements (product_id, warehouse_id, movement_type, related_movement_id, quantity, comment)
            VALUES ($1, $2, 'transfer_in', $3, $4, $5)
            """, product_id, dest_warehouse_id, movement_out_id, quantity, comment
        )
        return {
            "product_id": str(product_id),
            "from": str(src_warehouse_id),
            "to": str(dest_warehouse_id),
            "quantity": quantity,
            "new_source_quantity": new_src_qty,
            "new_dest_quantity": new_dest_qty
        }
