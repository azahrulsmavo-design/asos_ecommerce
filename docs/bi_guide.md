# Connecting BI Tools to ASOS Data Warehouse

This guide explains how to connect external BI tools like Power BI or Looker Studio to your local PostgreSQL data warehouse running in Docker.

## Database Credentials
These match your `.env` and `docker-compose.yml` configuration:
- **Host**: `localhost`
- **Port**: `5432`
- **Database**: `asos_ecommerce` (or check .env)
- **User**: `postgres`
- **Password**: `postgres` (or check .env)

---

## 1. Power BI Desktop

1.  Open Power BI Desktop.
2.  Click **Get Data** -> **More...**
3.  Search for **PostgreSQL database** and select it.
4.  **Configuration**:
    -   **Server**: `localhost`
    -   **Database**: `asos_ecommerce`
    -   **Data Connectivity mode**: Import (recommended).
5.  Click **OK**.
6.  **Authentication**:
    -   Select **Database** tab.
    -   User: `postgres`
    -   Password: `postgres`
    -   Click **Connect**.
7.  **Navigator (Select These Tables)**:
    -   `fact_sales` (New!)
    -   `fact_inventory` (New!)
    -   `fact_product_attributes`
    -   `dim_product`
    -   `dim_customer` (New!)
    -   `dim_store` (New!)
    -   `dim_brand`
    -   `dim_category`
    -   `dim_size`
    -   Click **Load**.

**Data Modeling**:
Ensure `fact_sales` is connected to `dim_product`, `dim_customer`, and `dim_store` using the respective IDs.

---

## 2. Google Looker Studio / Tableau

Same connection details apply. Use the `PostgreSQL` connector and ensure port `5432` is reachable.
