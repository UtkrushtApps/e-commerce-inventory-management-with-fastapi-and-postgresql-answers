# Solution Steps

1. Design all required tables by writing a PostgreSQL schema (schema.sql) that supports products, suppliers, categories (including recursive hierarchy), warehouses, inventory (per warehouse), price history, inventory movements (with movement type and link to related movements), purchase orders, and purchase order items. Add constraints, unique constraints, CHECKs, proper ON DELETE policies, and performance-oriented indexes.

2. Add a materialized view (mv_inventory_valuation) to aggregate warehouse inventory values based on current/latest prices. Index the view. Add triggers to update updated_at on updates for relevant tables.

3. Implement the connection management (database.py) using asyncpg, lazy pool initialization, and FastAPI startup/shutdown lifecycle.

4. Implement the product search CRUD logic (app/crud/products.py): async function supporting search by name/sku/description, and recursive category filtering by category_id with asyncpg to avoid N+1 queries. Support skip/limit pagination.

5. Implement inventory CRUD (app/crud/inventory.py): async update_inventory function handling transactional, row-locked updates to warehouse-level inventory, and logging inventory movements. Add inventory movement logger. Implement low-stock query.

6. Implement pricing bulk-update logic (app/crud/pricing.py) for batch updates, ensuring price history tracking (by insert), single transaction, and input validation.

7. Implement reporting logic (app/crud/reporting.py) fetching from the materialized view, summing inventory value per warehouse, plus a refresh function for the materialized view.

8. Implement warehouse operation (app/crud/warehouse_ops.py) for transfer: transactional deduction from source, addition to dest, logging both with related movement IDs, row locks, and rollback on errors.

9. Create the FastAPI routes (app/api/routes.py) for all required endpoints: product search, inventory update, low stock, bulk price update, inventory valuation report/refresh, warehouse transfer. Wire background task for async movement logging where needed.

10. Wire up main.py to FastAPI app, include the router, and bind the database startup/shutdown events.

