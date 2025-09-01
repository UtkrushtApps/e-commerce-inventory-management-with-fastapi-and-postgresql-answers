from typing import List, Optional
from uuid import UUID
import asyncpg

async def search_products(conn: asyncpg.Connection, query: Optional[str], category_id: Optional[UUID], skip: int, limit: int):
    params = []
    sql = """
    SELECT
        p.id, p.name, p.sku, p.description, p.category_id, p.supplier_id, p.created_at, p.updated_at
    FROM products p
    """
    where = []
    if query:
        where.append("(p.name ILIKE $1 OR p.description ILIKE $1 OR p.sku ILIKE $1)")
        params.append(f"%{query}%")
    if category_id:
        # Include all descendant categories via WITH RECURSIVE
        sql += """
        JOIN (
            WITH RECURSIVE cat_tree AS (
                SELECT id FROM categories WHERE id = $2
                UNION
                SELECT c.id FROM categories c JOIN cat_tree t ON c.parent_id = t.id
            ) SELECT id FROM cat_tree
        ) cats ON p.category_id = cats.id
        """
        if not query:
            params.append(category_id)
        else:
            params = [params[0], category_id]
    sql += " WHERE " + " AND ".join(where) if where else ""
    sql += " ORDER BY p.name OFFSET $%d LIMIT $%d" % (len(params)+1, len(params)+2)
    params.extend([skip, limit])
    products = await conn.fetch(sql, *params)
    return [dict(prod) for prod in products]
