from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from asyncpg import Connection
from uuid import UUID
from typing import List, Optional
from ..database import get_connection_pool
from app.crud import products as crud_products
from app.crud import inventory as crud_inventory
from app.crud import pricing as crud_pricing
from app.crud import reporting as crud_reporting
from app.crud import warehouse_ops as crud_warehouse_ops

router = APIRouter()

# Dependency to get a connection
async def get_conn():
    pool = get_connection_pool()
    async with pool.acquire() as conn:
        yield conn

@router.get("/products/search")
async def search_products(q: Optional[str] = Query(None), category_id: Optional[UUID] = None, skip:int=0, limit:int=25, conn:Connection=Depends(get_conn)):
    return await crud_products.search_products(conn, q, category_id, skip, limit)

@router.post("/inventory/update")
async def update_inventory(product_id: UUID, warehouse_id: UUID, quantity: int, movement_type: str, comment: Optional[str]=None, background_tasks: BackgroundTasks = None, conn:Connection=Depends(get_conn)):
    # For high performance, the movement logging could be offloaded to a background task.
    res = await crud_inventory.update_inventory(conn, product_id, warehouse_id, quantity, movement_type, comment)
    # offload extra movement logging if required as background task
    return res

@router.get("/inventory/low-stock")
async def low_stock(threshold: int = 10, conn:Connection=Depends(get_conn)):
    return await crud_inventory.get_low_stock(conn, threshold)

@router.post("/prices/bulk-update")
async def bulk_update(data: List[dict], conn:Connection=Depends(get_conn)):
    return await crud_pricing.bulk_update_prices(conn, data)

@router.get("/inventory/report/valuation")
async def inventory_valuation(conn:Connection=Depends(get_conn)):
    return await crud_reporting.inventory_valuation_report(conn)

@router.post("/inventory/report/valuation/refresh")
async def refresh_inventory_valuation(conn:Connection=Depends(get_conn)):
    await crud_reporting.refresh_inventory_valuation_mv(conn)
    return {"refreshed": True}

@router.post("/warehouse/transfer")
async def warehouse_transfer(product_id: UUID, src_warehouse_id: UUID, dest_warehouse_id: UUID, quantity: int, comment: Optional[str]=None, conn:Connection=Depends(get_conn)):
    return await crud_warehouse_ops.transfer_inventory(conn, product_id, src_warehouse_id, dest_warehouse_id, quantity, comment)
