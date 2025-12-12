# ASOS Retail Dashboard - Power BI Tutorial

This guide provides a comprehensive step-by-step walkthrough to build the **Retail Management Dashboard** using the ASOS dataset (Enterprise V2).

---

## 1. Prerequisites

Before starting:
*   **Power BI Desktop**: Installed.
*   **ODBC Driver**: [PostgreSQL ODBC Driver](https://www.postgresql.org/ftp/odbc/versions/msi/) installed.
*   **Data Generation**: Ensure you have run `python src/etl/generate_mock_data.py` (V2) so the tables exist.

---

## 2. Connecting to Data

1.  **Get Data** -> **PostgreSQL database**.
2.  **Server**: `localhost` | **Database**: `asos_ecommerce` (or name in .env) | **Mode**: Import.
3.  **Credentials**: User=`postgres`, Password=`postgres`.
4.  **Select Tables**:
    *   `fact_sales` (Transactions)
    *   `fact_inventory` (Stock - Historical)
    *   `dim_product` (Catalog)
    *   `dim_customer` (People)
    *   `dim_store` (Locations & Channel)
    *   `dim_date` (Optional, use Auto Date/Time)
    *   `dim_category`, `dim_brand`, `dim_size`

5.  **Load**.

---

## 3. Data Modeling (Star Schema)

Go to **Model View** to configure relationships.

### Fact Sales (The Center)
*   `fact_sales[product_id]` (*)--->(1) `dim_product[product_id]`
*   `fact_sales[store_id]` (*)--->(1) `dim_store[store_id]`
*   `fact_sales[customer_id]` (*)--->(1) `dim_customer[customer_id]`

### Fact Inventory
*   `fact_inventory[product_id]` (*)--->(1) `dim_product[product_id]`
*   `fact_inventory[store_id]` (*)--->(1) `dim_store[store_id]`

> **Tip**: Ensure Date columns in `fact_sales` and `fact_inventory` (`snapshot_date`) are recognized as Dates.

---

## 4. Key DAX Measures

Create a new table `_Measures` to store these.

### A. Sales Performance
```dax
Total Revenue = SUM(fact_sales[total_amount])
Total Cost = SUM(fact_sales[total_cost])
Total Profit = SUM(fact_sales[profit])
Profit Margin % = DIVIDE([Total Profit], [Total Revenue], 0)
Total Orders = DISTINCTCOUNT(fact_sales[order_id])
AOV = DIVIDE([Total Revenue], [Total Orders], 0)
```

### B. Inventory & Stock
```dax
// For current stock, we need the latest snapshot
Latest Date = LASTDATE(fact_inventory[snapshot_date])
Current Stock Quantity = CALCULATE(SUM(fact_inventory[stock_on_hand]), fact_inventory[snapshot_date] = [Latest Date])
Low Stock Item Count = CALCULATE(COUNTROWS(fact_inventory), fact_inventory[stock_on_hand] <= fact_inventory[reorder_point], fact_inventory[snapshot_date] = [Latest Date])
```

---

## 5. Building the 8-Page Dashboard

### Page 1: Executive Summary
*   **Visuals**:
    *   **Card**: `[Total Revenue]`, `[Total Profit]`, `[Total Orders]`, `[Profit Margin %]`.
    *   **Donut Chart**: Legend=`dim_store[type]` (Channel), Values=`[Total Revenue]`.

### Page 2: Sales Performance
*   **Visuals**:
    *   **Heatmap (Matrix)**: Rows=`DayOfWeek`, Columns=`Hour`, Values=`[Total Orders]`.
    *   **Bar Chart**: Axis=`fact_sales[payment_method]`, Values=`[Total Revenue]`.

### Page 3: Product Performance & Margin
*   **Visuals**:
    *   **Table**: Columns=`Product Name`, `[Total Revenue]`, `[Total Profit]`, `[Profit Margin %]`.
    *   **Scatter Plot**: X=`[Total Quantity]`, Y=`[Profit Margin %]`.

### Page 4: Inventory Trends
*   **Visuals**:
    *   **Line Chart**: Axis=`snapshot_date`, Values=`Sum(stock_on_hand)`. (See Stock Trend).
    *   **Table**: Filtered by Latest Date & Low Stock.

### Page 5: Customer Analysis
*   **Visuals**:
    *   **Map**: Location=`dim_customer[region]`, Bubble Size=`[Total Revenue]`.

### Page 6: Basket Analysis (New!)
*   **Visuals**:
    *   **Card**: `Avg Items per Basket` = `COUNTROWS(fact_sales) / [Total Orders]`.

### Page 7: Store Operations
*   **Visuals**:
    *   **Clustered Bar Chart**: Axis=`Store Name`, Values=`[Total Revenue]`, `[Total Profit]`.

### Page 8: Forecasting
*   **Power BI Analytics Tab**:
    *   Create a **Line Chart**: Axis=`Date` (Day), Values=`[Total Revenue]`.
    *   Enable **Forecast** (30 Days).

---
*Tutorial updated for Retail Dashboard v2.0 (Enterprise)*
