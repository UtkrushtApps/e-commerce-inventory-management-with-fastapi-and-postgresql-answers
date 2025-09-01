-- PostgreSQL Schema for ShopFlow E-Commerce Inventory
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Suppliers table
CREATE TABLE suppliers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    contact_info JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Categories table (multi-level hierarchy)
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    parent_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(name, parent_id)
);
CREATE INDEX idx_categories_parent_id ON categories(parent_id);

-- Warehouses table
CREATE TABLE warehouses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    location TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Products table
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supplier_id UUID REFERENCES suppliers(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    sku TEXT NOT NULL UNIQUE,
    description TEXT,
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_supplier ON products(supplier_id);

-- Inventory table (warehouse-level)
CREATE TABLE inventory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    warehouse_id UUID NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
    quantity INT NOT NULL CHECK (quantity >= 0),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(product_id, warehouse_id)
);
CREATE INDEX idx_inventory_product ON inventory(product_id);
CREATE INDEX idx_inventory_warehouse ON inventory(warehouse_id);
CREATE INDEX idx_inventory_prod_wh ON inventory(product_id, warehouse_id);

-- Price history table
CREATE TABLE price_history (
    id SERIAL PRIMARY KEY,
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    price NUMERIC(10,2) NOT NULL CHECK (price >= 0),
    effective_from TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_price_history_product ON price_history(product_id);

-- Purchase orders
CREATE TABLE purchase_orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supplier_id UUID REFERENCES suppliers(id) ON DELETE SET NULL,
    warehouse_id UUID REFERENCES warehouses(id) ON DELETE SET NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'ordered', 'received', 'cancelled')),
    placed_at TIMESTAMP,
    received_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_purchase_orders_supplier ON purchase_orders(supplier_id);
CREATE INDEX idx_purchase_orders_warehouse ON purchase_orders(warehouse_id);

-- Purchase order items
CREATE TABLE purchase_order_items (
    id SERIAL PRIMARY KEY,
    purchase_order_id UUID REFERENCES purchase_orders(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id) ON DELETE SET NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    price NUMERIC(10,2) NOT NULL CHECK (price >= 0),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_poi_order ON purchase_order_items(purchase_order_id);
CREATE INDEX idx_poi_product ON purchase_order_items(product_id);

-- Inventory Movements
CREATE TABLE inventory_movements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    warehouse_id UUID NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
    movement_type TEXT NOT NULL CHECK (movement_type in ('inbound','outbound','transfer_in','transfer_out','adjustment')),
    related_movement_id UUID REFERENCES inventory_movements(id) ON DELETE SET NULL,
    quantity INT NOT NULL,
    comment TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_movements_product ON inventory_movements(product_id);
CREATE INDEX idx_movements_warehouse ON inventory_movements(warehouse_id);
CREATE INDEX idx_movements_type ON inventory_movements(movement_type);
CREATE INDEX idx_movements_related ON inventory_movements(related_movement_id);

-- Materialized View: Inventory Valuation per Warehouse
CREATE MATERIALIZED VIEW mv_inventory_valuation AS
SELECT
    i.warehouse_id,
    i.product_id,
    i.quantity,
    (SELECT p.price FROM price_history p WHERE p.product_id = i.product_id ORDER BY effective_from DESC LIMIT 1) AS last_price,
    i.quantity * (SELECT p.price FROM price_history p WHERE p.product_id = i.product_id ORDER BY effective_from DESC LIMIT 1) AS total_value
FROM inventory i;

CREATE INDEX idx_mv_inv_val_wh ON mv_inventory_valuation(warehouse_id);
CREATE INDEX idx_mv_inv_val_prod ON mv_inventory_valuation(product_id);

-- Trigger to update updated_at on row modification
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trg_products_updated_at
BEFORE UPDATE ON products
FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER trg_categories_updated_at
BEFORE UPDATE ON categories
FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER trg_suppliers_updated_at
BEFORE UPDATE ON suppliers
FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER trg_warehouses_updated_at
BEFORE UPDATE ON warehouses
FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER trg_inventory_updated_at
BEFORE UPDATE ON inventory
FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER trg_purchase_orders_updated_at
BEFORE UPDATE ON purchase_orders
FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_column();

-- Constraints for better data consistency
ALTER TABLE inventory
    ADD CONSTRAINT chk_inventory_quantity_nonnegative CHECK (quantity >= 0);

-- END OF SCHEMA
