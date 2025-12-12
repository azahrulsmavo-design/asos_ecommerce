# ASOS Retail Dashboard - Power BI Tutorial

This guide provides a comprehensive step-by-step walkthrough to build the **Retail Management Dashboard** using the ASOS dataset (augmented with synthetic Sales & Customer data).

---

## 1. Prerequisites

Before starting:
*   **Power BI Desktop**: Installed.
*   **ODBC Driver**: [PostgreSQL ODBC Driver](https://www.postgresql.org/ftp/odbc/versions/msi/) installed.
*   **Data Generation**: Ensure you have run `python src/etl/generate_mock_data.py` so the sales tables exist.

---

## 2. Connecting to Data

1.  **Get Data** -> **PostgreSQL database**.
2.  **Server**: `localhost` | **Database**: `asos_ecommerce` (or name in .env) | **Mode**: Import.
3.  **Credentials**: User=`postgres`, Password=`postgres` (or as per .env).
4.  **Select Tables**:
    *   `fact_sales` (Transactions)
    *   `fact_inventory` (Stock)
    *   `dim_product` (Catalog)
    *   `dim_customer` (People)
    *   `dim_store` (Locations)
    *   `dim_date` (If you created it, otherwise use Auto Date/Time)
    *   `dim_category`, `dim_brand` (Product details)
    *   `dim_size`, `bridge_product_size` (Size details)

5.  **Load**.

---

## 3. Data Modeling (Star Schema)

Go to **Model View** to configure relationships.

### Fact Sales (The Center)
*   `fact_sales[product_id]` (*)--->(1) `dim_product[product_id]`
*   `fact_sales[store_id]` (*)--->(1) `dim_store[store_id]`
*   `fact_sales[customer_id]` (*)--->(1) `dim_customer[customer_id]`
*   `dim_product[category_id]` (*)--->(1) `dim_category[category_id]`
*   `dim_product[brand_id]` (*)--->(1) `dim_brand[brand_id]`

### Fact Inventory
*   `fact_inventory[product_id]` (*)--->(1) `dim_product[product_id]`
*   `fact_inventory[store_id]` (*)--->(1) `dim_store[store_id]`

> **Tip**: Ensure Date columns in `fact_sales` are recognized as Dates. You can create a dedicated Date Table for better time intelligence.

---

## 4. Key DAX Measures

Create a new table `_Measures` to store these.

### A. Sales Performance
```dax
Total Revenue = SUM(fact_sales[total_amount])
Total Cost = SUM(fact_sales[cost])
Total Profit = SUM(fact_sales[profit])
Profit Margin % = DIVIDE([Total Profit], [Total Revenue], 0)
Total Orders = COUNTROWS(fact_sales)
AOV = DIVIDE([Total Revenue], [Total Orders], 0)
```

### B. Inventory
```dax
Total Stock Quantity = SUM(fact_inventory[stock_on_hand])
Low Stock Item Count = CALCULATE(COUNTROWS(fact_inventory), fact_inventory[stock_on_hand] <= fact_inventory[reorder_point])
```

---

## 5. Building the 8-Page Dashboard

Create 8 Report Pages in Power BI.

### Page 1: Executive Summary
*   **Visuals**:
    *   **Card**: `[Total Revenue]`, `[Total Profit]`, `[Total Orders]`, `[Profit Margin %]`.
    *   **Line Chart**: Axis=`Date`, Values=`[Total Revenue]`.
    *   **Donut Chart**: Legend=`dim_category[category_name]`, Values=`[Total Revenue]`.
    *   **Bar Chart (Horizontal)**: Axis=`dim_store[store_name]`, Values=`[Total Revenue]` (Top 5 Stores).

### Page 2: Sales Performance
*   **Visuals**:
    *   **Matrix**: Rows=`Date`, Values=`[Total Revenue]`.
    *   **Heatmap (Matrix)**: Rows=`DayOfWeek`, Columns=`Hour`, Values=`[Total Revenue]` (Use Conditional Formatting for heavy colors).
    *   **Bar Chart**: Axis=`fact_sales[payment_method]`, Values=`[Total Revenue]`.
    *   **Pie Chart**: Legend=`fact_sales[channel]`, Values=`[Total Revenue]` (Offline vs Online).

### Page 3: Product Performance
*   **Visuals**:
    *   **Table**: Columns=`Product Name`, `Brand`, `Category`, `[Total Revenue]`, `[Total Profit]`. Sort by Profit.
    *   **Scatter Plot**: X=`[Avg Unit Price]`, Y=`[Quantity Sold]`. (Price Elasticity).
    *   **Bar Chart**: Top 10 Products by Quantity.

### Page 4: Inventory Management
*   **Visuals**:
    *   **KPI Card**: `[Total Stock Quantity]`.
    *   **Red Alert Card**: `[Low Stock Item Count]`.
    *   **Table**: Filtered where `Stock <= ReorderPoint`. Columns: `Store`, `Product`, `Stock`, `ReorderPoint`.

### Page 5: Customer Analysis
*   **Visuals**:
    *   **Donut**: Legend=`dim_customer[gender]`, Values=`[Customer Count]`.
    *   **Map**: Location=`dim_customer[region]`, Bubble Size=`[Total Revenue]`.
    *   **Histogram**: Axis=`dim_customer[age]`, Values=`[Customer Count]`.

### Page 6: Promotion Analysis (Campaign)
*   **Goal**: Compare two periods.
*   **Setup**: Use a "Date Slicer".
*   **Measure**: `Revenue Previous Period = CALCULATE([Total Revenue], SAMEPERIODLASTYEAR('Date'[Date]))`.
*   **Visual**: Line Chart showing `[Total Revenue]` vs `[Revenue Previous Period]`.

### Page 7: Store Operations
*   **Visuals**:
    *   **Clustered Bar Chart**: Axis=`Store Name`, Values=`[Total Revenue]`, `[Total Profit]`.
    *   **Table**: Store vs `[AOV]`, `[Conversion Rate]` (if traffic data exists).

### Page 8: Forecasting
*   **Power BI Analytics Tab**:
    *   Create a **Line Chart**: Axis=`Date` (Day), Values=`[Total Revenue]`.
    *   Go to **Analytics Pane** (Magnifying glass icon).
    *   Enable **Forecast**.
    *   Set **Forecast length**: 30 Points (Days).
    *   Set **Confidence strength**: 95%.

---

## 6. Final Polish
*   **Theme**: Go to View -> Themes. Choose a dark or sleek theme.
*   **Navigation**: Add buttons to navigate between the 8 pages if you hide the tabs.
*   **Publish**: File -> Publish to Power BI Service provided you have an account.

---
*Tutorial updated for Retail Dashboard v2.0*
