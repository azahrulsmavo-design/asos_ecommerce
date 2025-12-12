-- ASOS Retail Dashboard Schema (Enterprise Ready V2)
-- Updates: Renamed cost -> unit_cost, Removed channel (redundant)

-- 1. Dimension Tables ----------------------------------------------------

CREATE TABLE IF NOT EXISTS dim_brand (
    brand_id SERIAL PRIMARY KEY,
    brand_name VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_category (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_color (
    color_id SERIAL PRIMARY KEY,
    color_name VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_material (
    material_id SERIAL PRIMARY KEY,
    material_desc TEXT,
    material_main VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS dim_size (
    size_id SERIAL PRIMARY KEY,
    size_label VARCHAR(50),
    region VARCHAR(10),
    size_numeric FLOAT
);

CREATE TABLE IF NOT EXISTS dim_store (
    store_id SERIAL PRIMARY KEY,
    store_name VARCHAR(100),
    region VARCHAR(100),
    type VARCHAR(50) -- Channel Source of Truth: 'Online' or 'Physical'
);

CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id SERIAL PRIMARY KEY,
    gender VARCHAR(20),
    age INT,
    region VARCHAR(100),
    join_date TIMESTAMP,
    loyalty_score INT
);

-- Product Dimension (Central Catalog)
CREATE TABLE IF NOT EXISTS dim_product (
    product_id SERIAL PRIMARY KEY,
    sku VARCHAR(100) UNIQUE,
    name TEXT,
    url TEXT,
    brand_id INT REFERENCES dim_brand(brand_id),
    category_id INT REFERENCES dim_category(category_id),
    color_id INT REFERENCES dim_color(color_id),
    material_id INT REFERENCES dim_material(material_id),
    base_price NUMERIC,
    has_multiple_sizes BOOLEAN,
    num_sizes INT,
    num_images INT,
    description_clean TEXT
);

-- 2. Bridge Tables -------------------------------------------------------

CREATE TABLE IF NOT EXISTS bridge_product_size (
    product_id INT REFERENCES dim_product(product_id),
    size_id INT REFERENCES dim_size(size_id),
    PRIMARY KEY (product_id, size_id)
);

-- 3. Fact Tables ---------------------------------------------------------

-- Fact Product Features (Machine Learning Attributes)
CREATE TABLE IF NOT EXISTS fact_product_features (
    product_id INT PRIMARY KEY REFERENCES dim_product(product_id),
    price_zscore FLOAT,
    cluster_id INT
);

-- Fact Product Attributes (Extended Info)
CREATE TABLE IF NOT EXISTS fact_product_attributes (
    product_id INT PRIMARY KEY REFERENCES dim_product(product_id),
    price NUMERIC, -- Current Price
    price_bucket VARCHAR(20), -- Low, Mid, High
    num_sizes INT,
    num_images INT,
    desc_length_chars INT,
    has_neutral_color BOOLEAN
);

-- Fact Sales (Transactions)
-- Grain: One row per Product per Order (Line Item)
CREATE TABLE IF NOT EXISTS fact_sales (
    transaction_id SERIAL PRIMARY KEY, -- Unique ID for the Line Item
    order_id VARCHAR(50), -- Tie multiple items to one Basket (MBA Support)
    date TIMESTAMP NOT NULL,
    time TIMESTAMP,
    store_id INT REFERENCES dim_store(store_id),
    customer_id INT REFERENCES dim_customer(customer_id),
    product_id INT REFERENCES dim_product(product_id),
    quantity INT,
    unit_price NUMERIC, -- Price at time of purchase (after discount)
    total_amount NUMERIC, -- quantity * unit_price
    unit_cost NUMERIC, -- BASE cost (not affected by discount)
    total_cost NUMERIC, -- unit_cost * quantity
    profit NUMERIC, -- total_amount - total_cost
    payment_method VARCHAR(50)
    -- channel removed: join dim_store.type instead
);

-- Fact Inventory (Stock Snapshots)
-- Grain: One row per Store per Product per Snapshot
CREATE TABLE IF NOT EXISTS fact_inventory (
    inventory_id SERIAL PRIMARY KEY,
    snapshot_date DATE, -- To track historical stock levels
    store_id INT REFERENCES dim_store(store_id),
    product_id INT REFERENCES dim_product(product_id),
    stock_on_hand INT,
    reorder_point INT,
    last_restock_date TIMESTAMP
);
