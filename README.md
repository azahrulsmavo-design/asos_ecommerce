# 👗 ASOS E-commerce Data Analytics (Retail Dashboard Edition)

Selamat datang di proyek **End-to-End Data Analytics** menggunakan dataset katalog produk ASOS yang diperkaya dengan data transaksi sintetis.

Dokumentasi ini dirancang sebagai **panduan edukasi** yang menjelaskan setiap tahapan (Phase) dalam siklus hidup proyek data: mulai dari infrastruktur, pemrosesan data (ETL), analisis mendalam (Machine Learning), hingga pembuatan **Retail Management Dashboard**.

---

## 📋 Daftar Isi
1.  [Gambaran Proyek](#gambaran-proyek)
2.  [Prasyarat & Setup](#prasyarat--setup)
3.  [Phase 1: Infrastructure & Data Modeling (Star Schema)](#phase-1-infrastructure--data-modeling)
4.  [Phase 2: ETL Pipeline (Extract, Transform, Load)](#phase-2-etl-pipeline)
5.  [Phase 3: Synthetic Data Generation](#phase-3-synthetic-data-generation)
6.  [Phase 4: Dashboarding & Reporting](#phase-4-dashboarding--reporting)
7.  [Cara Menjalankan Proyek](#cara-menjalankan-proyek)

---

## 🌟 Gambaran Proyek
Tujuan proyek ini adalah membangun sistem analitik **Retail Dashboard** yang lengkap, mencakup 8 area bisnis utama:
1.  **Executive Summary**: KPI Level C-Level (Revenue, Profit, Orders).
2.  **Sales Performance**: Analisis tren dan heatmap.
3.  **Product Performance**: Analisis margin dan best-seller.
4.  **Inventory**: Manajemen stok dan notifikasi low-stock.
5.  **Customer Analysis**: Demografi dan Segmentasi (RFM).
6.  **Promotion**: Analisis dampak kampanye.
7.  **Store Operations**: Perbandingan performa toko (Online vs Offline).
8.  **Forecasting**: Proyeksi penjualan sederhana.

**Tech Stack:**
*   **Bahasa**: Python 3.9+
*   **Database**: PostgreSQL 15 (Data Warehouse)
*   **Infrastructure**: Docker & Docker Compose
*   **ETL**: Pandas, SQLAlchemy
*   **Dashboard**: Streamlit, Power BI (Tutorial tersedia)

---

## 🛠 Prasyarat & Setup
Sebelum memulai, pastikan Anda memiliki:
*   **Docker Desktop** (untuk menjalankan database tanpa instalasi manual yang ribet).
*   **Python** (untuk menjalankan script).
*   **Git** (untuk version control).

---

## 📚 Phase 1: Infrastructure & Data Modeling

### Konsep: Mengapa Docker & Star Schema?

**1. Docker Containerization**
Alih-alih menginstall PostgreSQL secara manual di laptop (yang bisa berantakan), kita menggunakan **Docker**.
*   Lihat `docker-compose.yml`. File ini mendefinisikan "resep" untuk infrastruktur kita: satu container untuk Database (`postgres`) dan satu untuk Admin UI (`pgadmin`).

**2. Data Modeling: Star Schema**
Kita menggunakan **Star Schema** yang diperluas:
*   **Fact Tables**:
    *   `fact_sales`: Transaksi penjualan (Grain: Order Item). Mendukung analisis Profit & Basket.
    *   `fact_inventory`: Snapshot stok historis (Bulanan) & terkini.
    *   `fact_product_attributes`: Atribut numerik produk asli.
*   **Dimension Tables**:
    *   `dim_product`: Katalog produk lengkap.
    *   `dim_customer`: Data pelanggan.
    *   `dim_store`: Lokasi toko (Fisik & Online).
    *   `dim_brand`, `dim_category`, `dim_size`: Dimensi pendukung.

---

## 🔄 Phase 2: ETL Pipeline

### Konsep: Extract, Transform, Load

Pipeline ETL (`src/etl/etl_pipeline.py`) adalah "pabrik" yang mengolah bahan mentah menjadi produk jadi.
*   **Extract**: Membaca data mentah katalog ASOS (JSON/CSV).
*   **Transform**: Cleaning harga, parsing deskripsi JSON, unnesting list Size.
*   **Load**: Memasukkan `dim_product`, `dim_brand`, `dim_category`, dan `bridge_product_size`.

---

## 🧪 Phase 3: Synthetic Data Generation

Karena dataset asli hanya berisi **Katalog Produk**, kita perlu membuat data simulasi agar dashboard menjadi hidup.

Script: `src/etl/generate_mock_data.py` (Enterprise V2)
1.  **Stores**: Membuat 5 toko (Online, Oxford St, Manchester, dll).
2.  **Customers**: Generate 1,000 profil pelanggan dengan demografi unik.
3.  **Sales**: Mensimulasikan **~12,000 Order** (Multi-item basket) dengan pola musiman realistis.
4.  **Inventory**: Membuat snapshot stok **Bulanan** selama 1 tahun terakhir.

---

## 📊 Phase 4: Dashboarding & Reporting

Data yang canggih tidak berguna jika tidak bisa dibaca user.

**1. Streamlit Retail App**
*   Lihat `src/dashboard/app.py`.
*   Aplikasi web interaktif dengan **8 Halaman** lengkap (Sales, Inv, Cust, dll).
*   **Run**: `streamlit run src/dashboard/app.py`
 
 **2. Business Intelligence (Power BI)**
 *   **Tutorial Pembuatan Dashboard**: Lihat panduan lengkap di [`docs/POWER_BI_TUTORIAL.md`](docs/POWER_BI_TUTORIAL.md).
 *   Panduan ini mencakup cara koneksi PostgreSQL, Star Schema, Measure DAX (**Revenue, Profit, Inventory Trend**), dan cara membuat visualisasi.

---

## 🚀 Cara Menjalankan Proyek

**1. Setup Environment**
```bash
# Buat file .env (isi sesuai .env.example)
cp .env.example .env

# Jalankan Database (via Docker)
docker-compose up -d

# Install Python Library
py -m pip install -r requirements.txt
```

**2. Jalankan Pipeline (Urut)**
```bash
# Setup Schema Database (Kosongkan DB)
py -m src.db_setup

# Download Data Mentah Katalog (jika belum ada)
py -m src.etl.ingest_data

# 1. Jalankan ETL Produk (Catalog Base)
py -m src.etl.etl_pipeline

# 2. Generate Mock Data (Sales, Customer, Inventory)
py src/etl/generate_mock_data.py
# (Tunggu ~30 detik hingga selesai generate data Enterprise)
```

**3. Lihat Hasil**
```bash
# Buka Retail Dashboard
streamlit run src/dashboard/app.py
```
Akses di browser: `http://localhost:8501`

**4. Akses Database Admin (Optional)**
Buka `http://localhost:5050` (pgAdmin), login dengan email/pass yang ada di `docker-compose.yml`.

---
*Dibuat oleh Assistant AI untuk Panduan Edukasi Data Analytics.*
