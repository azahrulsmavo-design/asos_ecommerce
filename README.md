# 👗 ASOS E-commerce Data Analytics (Retail Dashboard)

Selamat datang di proyek **End-to-End Data Analytics - Retail Edition**. Proyek ini mensimulasikan lingkungan data enterprise untuk analisis bisnis ritel fashion.

---

## 1. Business Question / Objective
Bagaimana cara meningkatkan profitabilitas dan efisiensi operasional dengan memanfaatkan data katalog dan transaksi?
*   **Objective**: Membangun "Retail Management Dashboard" terpusat untuk memantau KPI utama (Revenue, Profit, Margin), mengoptimalkan stok inventaris (Inventory Health), dan menargetkan retensi pelanggan (Customer Segmentation).
*   **Goal**: Mengubah data mentah menjadi *actionable insights* untuk tim Strategi, Merchandising, dan Marketing.

## 2. Data Source
Proyek ini menggunakan pendekatan **Hybrid Dataset**:
*   **Product Catalog (Real-World)**: Scraping publik dari **ASOS.com**.
    *   **Ukuran**: ~30,000 SKU unik.
    *   **Atribut**: Nama, Harga, Brand, Kategori, Warna, Deskripsi.
*   **Sales & Customer (Synthetic Enterprise V2)**: Generated menggunakan Python (`numpy` & `faker`).
    *   **Sales**: ~12,000 Order Unik (20,000+ Baris Item) selama 1 tahun terakhir.
    *   **Inventory**: ~135,000 Baris (Snapshot Bulanan Historical).
    *   **Customer**: 1,000 Profil Pelanggan dengan demografi UK.

## 3. Method
Pendekatan teknis *end-to-end* yang dilakukan:
1.  **Infrastructure**: setup **Docker & PostgreSQL** sebagai Data Warehouse modern.
2.  **Data Modeling**: Desain **Star Schema** (Fact Sales, Fact Inventory, Dim Product, Dim Customer) untuk performa query BI yang optimal.
3.  **ETL Pipeline**:
    *   *Extract*: Ingest raw JSON/CSV data.
    *   *Transform*: Data Cleaning (Parsing JSON descriptions, Price normalization), Feature Engineering (Profit Margin calculation).
    *   *Load*: Menyimpan ke PostgreSQL.
    *   *Brand Master*: Normalisasi dan deduplikasi brand menggunakan Fuzzy Matching (`rapidfuzz`).
4.  **Advanced Analysis**:
    *   **RFM Segmentation**: Mengelompokkan pelanggan berdasarkan Recency, Frequency, Monetary.
    *   **Inventory Analysis**: Melacak stok historis untuk mendeteksi tren dan risiko OOS.

## 4. Key Findings (Simulated Insights)
Berdasarkan analisis data (mock enterprise), ditemukan:
*   **Seasonality Impact**: Penjualan melonjak signifikan (~150% peningkatan) pada **Kuartal 4 (Q4)**, didorong oleh tren belanja akhir tahun, yang menekan ketersediaan stok.
*   **Customer Value**: Segmen **"Champions"** dan **"Loyal Customers"**, meskipun hanya 20% dari total basis pelanggan, menyumbang lebih dari **45% Total Revenue** (Hukum Pareto).
*   **Inventory Risk**: Ditemukan ketidakseimbangan stok pada kategori "Best Seller" di toko Fisik vs Online, di mana toko Fisik sering mengalami *Out of Stock* lebih cepat pada item populer.

## 5. Deliverables
Hasil akhir dari proyek ini meliputi:
*   **Interactive Dashboard (Streamlit)**: Aplikasi web 8 halaman (Sales, Inventory, Customer, dll).
*   **BI Guide (Power BI)**: Tutorial lengkap (.md) untuk replikasi dashboard di Power BI.
*   **SQL Database**: Schema database yang siap pakai (populated).
*   **Brand Master System**: Sistem deduplikasi brand otomatis.
*   **Source Code**: Full Python ETL & Analysis scripts.

## 6. How to Run

### Requirements
*   **Docker Desktop** (Wajib untuk Database)
*   **Python 3.9+** & **Git**

### Langkah Instalasi
1.  **Clone & Setup Env**:
    ```bash
    git clone https://github.com/Start-With-Data/asos-ecommerce.git
    cd asos-ecommerce
    cp .env.example .env
    pip install -r requirements.txt
    ```

2.  **Jalankan Infrastruktur**:
    ```bash
    docker-compose up -d
    # Tunggu sampi container 'asos_postgres' running (status sehat)
    ```

3.  **Eksekusi Pipeline Data (ETL & Generator)**:
    ```bash
    # Reset DB & Ingest
    python -m src.db_setup
    python -m src.etl.ingest_data
    
    # Run ETL & Mock Generator (Enterprise V2)
    python -m src.etl.etl_pipeline
    python src/etl/generate_mock_data.py
    
    # Run Brand Master Pipeline (Cleaning & Deduplication)
    python fix_brands.py
    python -m src.populate_brand_master
    python src/analysis/verify_brand_master.py
    ```

4.  **Jalankan Analisis & Dashboard**:
    ```bash
    # Update RFM Segments
    python src/analysis/customer_segmentation.py
    
    # Buka Dashboard
    streamlit run src/dashboard/app.py
    ```
    Akses di: `http://localhost:8501`

---
*Project by: Azahrul*
