# Connecting BI Tools to ASOS Data Warehouse

This guide explains how to connect external BI tools like Power BI or Looker Studio to your local PostgreSQL data warehouse running in Docker.

## Database Credentials
These match your `.env` and `docker-compose.yml` configuration:
- **Host**: `localhost`
- **Port**: `5432`
- **Database**: `asos_db` (or whatever is in your .env)
- **User**: `postgres`
- **Password**: `password_rahasia_anda` (or whatever you set in .env)

---

## 1. Power BI Desktop

1.  Open Power BI Desktop.
2.  Click **Get Data** -> **More...**
3.  Search for **PostgreSQL database** and select it.
4.  **Configuration**:
    -   **Server**: `localhost:5432`
    -   **Database**: `asos_db`
    -   **Data Connectivity mode**: Import (recommended for speed) or DirectQuery.
5.  Click **OK**.
6.  **Authentication**:
    -   Select **Database** tab on the left.
    -   Enter **User name**: `postgres`
    -   Enter **Password**: *[your password]*
7.  Click **Connect**.
8.  **Navigator**:
    -   Select the tables you want to analyze:
        -   `fact_product_attributes`
        -   `fact_product_features`
        -   `dim_product`
        -   `dim_brand`
        -   `dim_category`
        -   `dim_size`
        -   `dim_color`
    -   Click **Load**.

**Tip**: In Power BI "Model View", ensure relationships are detected automatically (Star Schema). Usually Power BI handles `product_id` joins correctly.

---

## 2. Google Looker Studio (formerly Data Studio)

*Note: Connecting Looker Studio (Cloud) to localhost requires a tunnel (like ngrok) or exposing your port. If you are just testing locally, Power BI Desktop is easier.*

If you want to try:
1.  Use a tool like `ngrok` to expose port 5432: `ngrok tcp 5432`.
2.  In Looker Studio, add data source -> **PostgreSQL**.
3.  Enter the `ngrok` host and port, along with your credentials.

---

## 3. Tableau / Other Tools

-   Select **PostgreSQL** connector.
-   Use `localhost`, `5432`, `postgres`, `[password]`.
