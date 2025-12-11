# 👗 ASOS E-commerce Data Analytics (End-to-End Project)

Selamat datang di proyek **End-to-End Data Analytics** menggunakan dataset katalog produk ASOS.

Dokumentasi ini dirancang sebagai **panduan edukasi** yang menjelaskan setiap tahapan (Phase) dalam siklus hidup proyek data: mulai dari infrastruktur, pemrosesan data (ETL), analisis mendalam (Machine Learning), hingga visualisasi dashboard.

---

## 📋 Daftar Isi
1.  [Gambaran Proyek](#gambaran-proyek)
2.  [Prasyarat & Setup](#prasyarat--setup)
3.  [Phase 1: Infrastructure & Data Modeling (Star Schema)](#phase-1-infrastructure--data-modeling)
4.  [Phase 2: ETL Pipeline (Extract, Transform, Load)](#phase-2-etl-pipeline)
5.  [Phase 3: Analysis & Feature Engineering (EDA + ML)](#phase-3-analysis--feature-engineering)
6.  [Phase 4: Dashboarding & Reporting](#phase-4-dashboarding--reporting)
7.  [Cara Menjalankan Proyek](#cara-menjalankan-proyek)

---

## 🌟 Gambaran Proyek
Tujuan proyek ini adalah membangun sistem analitik untuk katalog fashion e-commerce. Kita tidak hanya sekadar membuat grafik, tapi membangun **fondasi data yang kuat** (Data Warehouse) dan **fitur cerdas** (Clustering/Recomendation helper).

**Tech Stack:**
*   **Bahasa**: Python 3.9+
*   **Database**: PostgreSQL 15 (Data Warehouse)
*   **Infrastructure**: Docker & Docker Compose
*   **ETL**: Pandas, SQLAlchemy
*   **Machine Learning**: Scikit-Learn (K-Means, TF-IDF)
*   **Dashboard**: Streamlit, Plotly

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
*   **Keuntungan**: Konsisten. Jika teman Anda menjalankan proyek ini, dia akan mendapatkan versi database yang sama persis.

**2. Data Modeling: Star Schema**
Kita tidak menumpuk semua data dalam satu tabel Excel raksasa. Kita menggunakan **Star Schema**:
*   **Fact Table** (`fact_product_attributes`): Berisi angka-angka/metrik (Harga, Jumlah Size, Skor). Ini adalah "pusat" dari bintang.
*   **Dimension Tables** (`dim_brand`, `dim_category`, `dim_color`): Berisi deskripsi atau konteks.
*   **Keuntungan**: Query jadi cepat dan fleksibel. Misalnya, kita bisa melihat "Rata-rata Harga" (Fact) berdasarkan "Brand" (Dim).

> **Kode Relevan**: `sql/schema.sql` (mendefinisikan struktur tabel).

---

## 🔄 Phase 2: ETL Pipeline

### Konsep: Extract, Transform, Load

Data mentah seringkali kotor. Pipeline ETL (`src/etl/etl_pipeline.py`) adalah "pabrik" yang mengolah bahan mentah menjadi produk jadi.

**1. Extract (E)**
Kita membaca data mentah dari file Parquet/CSV.
*   *Tantangan*: Data deskripsi tersimpan sebagai string JSON yang rumit (`"{'Brand': 'Nike', ...}"`).

**2. Transform (T)**
Ini adalah otak dari pipeline:
*   **Parsing JSON**: Mengubah string JSON menjadi Python Dictionary untuk mengambil info 'Brand' dan 'Material'.
*   **Cleaning**: Membersihkan simbol mata uang pada harga (`£25.00` -> `25.00`).
*   **Normalization**: Memisahkan entitas unik. Misalnya, dari ribuan baris produk, kita ekstrak daftar unik **Brand** untuk mengisi `dim_brand`.
*   **Handling Many-to-Many**: Satu produk bisa punya banyak Size. Kita buat tabel jembatan (`bridge_product_size`) untuk menghubungkan Produk ke Size.

**3. Load (L)**
Memasukkan data bersih ke PostgreSQL.
*   Kita menggunakan `SQLAlchemy` dan `pandas.to_sql`.
*   Penting untuk memuat data dengan urutan yang benar (Dimension dulu, baru Fact) untuk menjaga **Referential Integrity** (Foreign Key).

---

## 🧠 Phase 3: Analysis & Feature Engineering

### Konsep: Dari Data Mentah ke Insight Cerdas

Setelah data bersih masuk ke database, kita melakukan dua hal:

**1. Exploratory Data Analysis (EDA)**
*   Menggunakan Jupyter Notebook (`notebooks/eda_analysis.ipynb`) untuk "berkenalan" dengan data.
*   Contoh Insight: Distribusi harga, Brand paling dominan, dll.

**2. Feature Engineering (Machine Learning)**
Kita membuat fitur tambahan untuk analisis lanjutan di `src/analysis/feature_engineering.py`.

*   **Price Standardization (Z-Score)**:
    *   Harga £50 untuk Kaos itu mahal, tapi £50 untuk Jaket Kulit itu murah.
    *   Kita hitung **Z-Score** per kategori. Nilai positif berarti "lebih mahal dari rata-rata kategori tersebut". Ini membuat perbandingan harga menjadi adil (apples-to-apples).

*   **Text Embedding (TF-IDF + PCA)**:
    *   Komputer tidak mengerti teks deskripsi produk.
    *   **TF-IDF**: Mengubah kata-kata menjadi angka berdasarkan kepentingannya.
    *   **PCA**: Meringkas ribuan fitur kata menjadi 50 fitur utama (kompresi informasi).

*   **Clustering (K-Means)**:
    *   Algoritma mengelompokkan produk yang mirip berdasarkan Harga dan Deskripsi.
    *   Hasilnya: Kita punya `cluster_id` (0-4). Produk di cluster yang sama memiliki karakteristik serupa (misal: "Baju olahraga murah" atau "Gaun malam premium").

---

## 📊 Phase 4: Dashboarding & Reporting

Data yang canggih tidak berguna jika tidak bisa dibaca user.

**1. Streamlit Dashboard**
*   Lihat `src/dashboard/app.py`.
*   Aplikasi web interaktif sederhana menggunakan Python.
*   User bisa memfilter berdasarkan Brand/Category dan melihat sebaran harga serta cluster produk secara visual.

**2. Business Intelligence (BI)**
*   Data Warehouse kita (Postgres) siap dihubungkan ke tools industri seperti **Power BI**, **Tableau**, atau **Looker Studio**.
*   Panduan koneksi ada di `docs/bi_guide.md`.

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
# Setup Schema Database
py -m src.db_setup

# Download Data Mentah
py -m src.etl.ingest_data

# Jalankan ETL (Extract-Transform-Load)
py -m src.etl.etl_pipeline

# Jalankan Feature Engineering (ML)
py -m src.analysis.feature_engineering
```

**3. Lihat Hasil**
```bash
# Buka Dashboard Streamlit
streamlit run src/dashboard/app.py
```
Akses di browser: `http://localhost:8501`

**4. Akses Database Admin (Optional)**
Buka `http://localhost:5050` (pgAdmin), login dengan email/pass yang ada di `docker-compose.yml`.

---
*Dibuat oleh Assistant AI untuk Panduan Edukasi Data Analytics.*
