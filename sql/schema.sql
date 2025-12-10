-- Helper to create tables if not exists

-- 1. Staging Table
CREATE TABLE IF NOT EXISTS stg_asos_raw (
    id_raw SERIAL PRIMARY KEY,
    url TEXT,
    name TEXT,
    size_raw TEXT,
    category_raw TEXT,
    price_raw NUMERIC,
    color_raw TEXT,
    sku_raw TEXT,
    description_raw TEXT,
    images_raw TEXT,
    ingestion_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Dimension Tables
CREATE TABLE IF NOT EXISTS dim_brand (
    brand_id SERIAL PRIMARY KEY,
    brand_name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_category (
    category_id SERIAL PRIMARY KEY,
    category_name TEXT UNIQUE NOT NULL,
    category_group TEXT -- Optional: Higher level grouping
);

CREATE TABLE IF NOT EXISTS dim_color (
    color_id SERIAL PRIMARY KEY,
    color_name TEXT UNIQUE NOT NULL,
    color_family TEXT -- Optional: standardized color
);

CREATE TABLE IF NOT EXISTS dim_size (
    size_id SERIAL PRIMARY KEY,
    size_label TEXT NOT NULL,
    region TEXT, -- UK, US, EU
    size_numeric NUMERIC,
    UNIQUE(size_label, region)
);

CREATE TABLE IF NOT EXISTS dim_material (
    material_id SERIAL PRIMARY KEY,
    material_desc TEXT,
    material_main TEXT
);

CREATE TABLE IF NOT EXISTS dim_product (
    product_id SERIAL PRIMARY KEY,
    sku TEXT UNIQUE,
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

CREATE TABLE IF NOT EXISTS dim_image (
    image_id SERIAL PRIMARY KEY,
    product_id INT REFERENCES dim_product(product_id),
    image_url TEXT,
    image_order INT
);

-- Bridge Table for Many-to-Many relationship between Products and Sizes
CREATE TABLE IF NOT EXISTS bridge_product_size (
    product_id INT REFERENCES dim_product(product_id),
    size_id INT REFERENCES dim_size(size_id),
    PRIMARY KEY (product_id, size_id)
);

-- 3. Fact Table
CREATE TABLE IF NOT EXISTS fact_product_attributes (
    product_id INT REFERENCES dim_product(product_id),
    price NUMERIC,
    price_bucket TEXT, -- Low, Mid, High
    desc_length_chars INT,
    num_sizes INT,
    num_images INT,
    has_neutral_color BOOLEAN,
    is_premium_brand BOOLEAN,
    PRIMARY KEY (product_id)
);
