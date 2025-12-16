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

### 💡 Best Practice: Time Intelligence
Don't rely on Auto Date/Time. Create a dedicated **Date Table**.
1.  **Modeling Tab** -> **New Table**.
2.  DAX:
    ```dax
    DateTable = CALENDAR(DATE(2023,1,1), DATE(2025,12,31))
    ```
3.  Mark as Date Table.
4.  Connect `DateTable[Date]` to `fact_sales[date]` and `fact_inventory[snapshot_date]`.

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

### B. Basket Analysis (Advanced)
Use `order_id` to measure how many items customers buy at once.
```dax
Total Items Sold = SUM(fact_sales[quantity])
Avg Items per Basket = DIVIDE([Total Items Sold], [Total Orders], 0)
```

### C. Inventory & Stock
```dax
// For current stock, we need the latest snapshot
Latest Date = LASTDATE(fact_inventory[snapshot_date])
Current Stock Quantity = CALCULATE(SUM(fact_inventory[stock_on_hand]), fact_inventory[snapshot_date] = [Latest Date])
Low Stock Item Count = CALCULATE(COUNTROWS(fact_inventory), fact_inventory[stock_on_hand] <= fact_inventory[reorder_point], fact_inventory[snapshot_date] = [Latest Date])
```

---

## 5. Building the 5-Page Dashboard

### Page 1: Executive Overview
**Goal**: Quick decisions in < 30 seconds.

*   **A. KPI Cards (Top Row)**
    *   **Visual**: Card (New) or Multi-row Card.
    *   **Measures**:
        *   `Revenue = SUM(fact_sales[total_amount])`
        *   `Profit = SUM(fact_sales[profit])`
        *   `Margin % = DIVIDE([Profit], [Revenue])`
        *   `Orders = DISTINCTCOUNT(fact_sales[order_id])`
        *   `Units = SUM(fact_sales[quantity])`
        *   `Customers = DISTINCTCOUNT(fact_sales[customer_id])`
        *   `AOV = DIVIDE([Revenue], [Orders])`
    *   **Styling**: No border, subtle shadow, large values, small labels.

*   **B. Trend Revenue & Profit**
    *   **Visual**: Line or Area Chart.
    *   **X-Axis**: Date (Drill: Day → Week → Month).
    *   **Y-Axis**: `[Revenue]`.
    *   **Secondary Y-Axis**: `[Profit]`.

*   **C. Decomposition Tree**
    *   **Analyze**: `[Revenue]`.
    *   **Explain by**: `Store Type`, `Region`, `Category Group`, `Brand`.
    *   *Purpose*: Replaces multiple manual filters.

*   **D. Waterfall (Month-over-Month)**
    *   **Visual**: Waterfall Chart.
    *   **Measure**: `Revenue MoM = [Revenue] - CALCULATE([Revenue], DATEADD(dim_date[date], -1, MONTH))`.

*   **E. Map (Optional)**
    *   **Location**: `Region`.
    *   **Size/Color**: `[Revenue]`.

*   **F. Top N Bar Chart**
    *   **Visual**: Bar Chart.
    *   **Data**: Top 10 Brand or Category by Revenue.

*   **G. Interactions**
    *   Cross-filter ON.
    *   **Drill-through**: Enable to Product Page and Customer Page.

---

### Page 2: Sales Deep Dive
**Goal**: Find the "Why", not just the "What".

*   **A. Matrix (Category x Month)**
    *   **Rows**: `Category Group`.
    *   **Columns**: `Month`.
    *   **Values**: `[Revenue]`, `[Profit]`, `[Margin %]`.
    *   **Conditional Formatting**: Red-Green for Margin, Data Bars for Profit.

*   **B. Small Multiples**
    *   **Visual**: Line Chart.
    *   **Y-Axis**: `[Revenue]`.
    *   **X-Axis**: `Date`.
    *   **Small Multiple**: `Category Group`.

*   **C. Scatter Plot (Price vs Volume)**
    *   **X-Axis**: `Unit Price`.
    *   **Y-Axis**: `Units`.
    *   **Size**: `Profit`.
    *   *Interpretation*: Bottom-right = Expensive but low sales; Top-left = High volume, low margin.

*   **D. Histogram (Binning)**
    *   Create bins for `unit_price` and `total_amount`.
    *   **Visual**: Column Chart using bins to show distribution of basket sizes or price points.

*   **E. Key Influencers (AI Visual)**
    *   **Target**: `Profit` (High) or `Margin %` (High).
    *   **Explain by**: `price_bucket`, `has_neutral_color`, `is_premium_brand`, `category_group`.

---

### Page 3: Product & Pricing Intelligence
**Goal**: SKU-level decisions.

*   **A. Treemap**
    *   **Hierarchy**: `Category` → `Brand`.
    *   **Values**: `[Revenue]`.

*   **B. Ribbon Chart**
    *   **Axis**: `Date`.
    *   **Legend**: `Brand`.
    *   **Values**: `[Revenue]`.
    *   *Purpose*: Shows ranking changes over time.

*   **C. Product Table (Advanced)**
    *   **Columns**: `SKU`, `Product Name`, `[Revenue]`, `[Profit]`, `[Margin %]`, `[Units]`.
    *   **Conditional Formatting**: Icons for Margin (High/Med/Low), Color Scale for Profit.

*   **D. Scatter (Price vs Margin)**
    *   **X-Axis**: `base_price` or `unit_price`.
    *   **Y-Axis**: `Margin %`.
    *   **Color**: `price_bucket`.

*   **E. Image Tooltip (WOW Factor)**
    *   Create a separate tooltip page with `dim_image[image_url]`.
    *   Bind it to the Product Table so hovering reveals the product image.

*   **F. Advanced: Product Clustering**
    *   **Slicer**: `fact_product_features[cluster_id]`.
    *   **Visuals**: Compare `[Revenue]` and `[Margin]` per cluster.

---

### Page 4: Inventory & Replenishment
**Goal**: Actionable operations.

*   **A. Measures**
    *   `Low Stock Flag = IF(SUM(stock_on_hand) < SUM(reorder_point), 1, 0)`
    *   `Sales Velocity = DIVIDE([Units], DISTINCTCOUNT(dim_date[date]))`
    *   `Days Since Restock = DATEDIFF(MAX(last_restock_date), TODAY(), DAY)`

*   **B. KPI Cards**
    *   Total Stock on Hand.
    *   SKU Count below Reorder Point.
    *   Avg Days Since Restock.

*   **C. Trend Stock vs Reorder**
    *   **Visual**: Line Chart.
    *   **Lines**: `stock_on_hand` vs `reorder_point`.
    *   **Drill-down**: Store → Product.

*   **D. Heatmap**
    *   **Visual**: Matrix.
    *   **Rows**: `Store`.
    *   **Columns**: `Category`.
    *   **Values**: `% SKU Low Stock` (color coded).

*   **E. Risk Bar Chart**
    *   **Visual**: Bar Chart.
    *   **Data**: Top 20 SKUs with **Low Stock** AND **High Sales Velocity**.

---

### Page 5: Customer & RFM Segmentation
**Goal**: Retention & Growth.

*   **A. Segment Distribution**
    *   **Visual**: Donut or Bar Chart.
    *   **Legend**: `Customer_Segment` (VIP, Loyal, etc.).
    *   **Values**: `[Customers]`.

*   **B. Revenue by Join Month**
    *   **X-Axis**: `Join Month` (from `dim_customer`).
    *   **Y-Axis**: `[Revenue]`.

*   **C. Segment x Category Matrix**
    *   **Rows**: `Customer Segment`.
    *   **Columns**: `Category Group`.
    *   **Values**: `[Revenue]`, `[Orders]`, `[AOV]`.

*   **D. Pareto Chart (80/20 Rule)**
    *   **X-Axis**: `Customer`.
    *   **Line**: `Cumulative Revenue %`.
    *   **Bars**: `[Revenue]`.

*   **E. Key Influencers (VIP)**
    *   **Target**: `Customer_Segment` is 'VIP'.
    *   **Explain by**: `Frequency`, `Monetary`, `Category Preference`, `Region`.

---

### 🎨 Styling & Theme (Best Practices)
1.  **JSON Theme**: Use a custom `theme.json` with neutral background and 1-2 brand accent colors.
2.  **Consistency**: Use standard font (Segoe UI or Inter) and minimal borders.
3.  **Portfolio Tips**:
    *   Show off **Tooltips**, **Drill-throughs**, and **Bookmarks** for navigation.
    *   Don't clutter! White space is important.
    *   Tell a business story (Problem → Insight → Action).

*Tutorial updated for Retail Dashboard v2.0*
