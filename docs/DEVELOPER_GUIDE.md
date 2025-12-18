# Developer Guide & Project Mapping

Dokumen ini berisi panduan teknis mendalam mengenai struktur file proyek dan cara mengakses database untuk keperluan pengembangan atau eksplorasi lebih lanjut.

---

##  1. Project Structure Mapping (Peta File)

Berikut adalah peran dan fungsi dari setiap file utama dalam repository ini:

| File Path | Function (Apa yang dilakukan code ini?) | Role (Peran dalam Proyek) |
| :--- | :--- | :--- |
| **Infrastructure & Config** | | |
| `docker-compose.yml` | Mendefinisikan layanan Container (PostgreSQL & pgAdmin). | **Pondasi**. Menjalankan server database tanpa instalasi manual. |
| `.env` | Menyimpan variabel sensitif (DB Credentials). | **Security**. Memisahkan konfigurasi dari kode. |
| `src/config.py` | Membaca `.env` dan membuat string koneksi DB. | **Jembatan**. Menghubungkan script Python dengan settings environment. |
| `src/sql/schema.sql` | Berisi perintah SQL (`CREATE TABLE`) untuk Star Schema. | **Blueprints**. Cetak biru struktur database (Tables, Dims, Facts). |
| **ETL & Data Processing** | | |
| `src/db_setup.py` | Mereset database (DROP/CREATE Tables) berdasarkan schema. | **Initializer**. Script pertama yang dijalankan untuk membersihkan DB. |
| `src/utils/db_utils.py` | Fungsi bantuan (helper) untuk koneksi & insert dataframe. | **Utility**. Mencegah duplikasi kode koneksi database. |
| `src/etl/etl_pipeline.py` | Membersihkan data Katalog Produk asli (`.json` -> DB). | **Core ETL**. Mengubah raw data produk menjadi tabel dimensi (`dim_product`). |
| `src/etl/generate_mock_data.py` | Membuat data transaksi, stok, dan customer sintetis. | **Data Generator**. "Otak" yang mensimulasikan aktivitas bisnis Enterprise V2. |
| `src/populate_brand_master.py` | Deduplikasi & Normalisasi Brand (Fuzzy Matching). | **Data Governance**. Membuat canonical `brand_master` dari raw data. |
| `src/analysis/verify_brand_master.py` | Verifikasi kualitas data brand (No duplicates). | **Quality Control**. Script pengujian integritas brand master. |
| **Analysis & Dashboard** | | |
| `src/analysis/customer_segmentation.py` | Menghitung RFM Score dan menentukan segmen customer. | **Analytics Engine**. Menjalankan logika bisnis untuk segmentasi pelanggan. |
| `src/dashboard/app.py` | Aplikasi web interaktif menggunakan Streamlit. | **Frontend**. Wajah visual proyek yang diakses oleh End-User. |
| **Documentation** | | |
| `README.md` | Halaman utama yang menjelaskan proyek secara umum. | **Landing Page**. Pintu masuk untuk memahami "Apa proyek ini?". |
| `docs/DATA_DICTIONARY.md` | Kamus data detail (Schema, Kolom, Tipe Data). | **Reference**. Panduan bagi Data Analyst untuk memahami arti kolom. |
| `docs/DATASET_IDENTITY.md` | Identitas dan metadata dataset (Verified Counts). | **Trust**. Bukti validitas dan batasan dataset. |

---

##  2. Cara Mengakses Database (Database Access)

Karena database berjalan di dalam **Docker**, ada 3 cara untuk mengaksesnya:

### Cara A: Menggunakan pgAdmin (Browser UI - Paling Mudah)
Tools ini sudah terinstall otomatis lewat Docker dan berjalan dalam jaringan internal yang sama.

1.  **Buka Browser**: Akses `http://localhost:5050`
2.  **Login pgAdmin**:
    *   **Email**: `admin@admin.com`
    *   **Password**: `admin`
3.  **Hubungkan Server**:
    *   Klik Kanan **Servers** -> **Register** -> **Server...**
    *   **Tab General**: Nama = `ASOS Local`
    *   **Tab Connection**:
        *   **Host**: `postgres`
        *   **Port**: `5432` 
        *   **Maintenance database**: `asos_ecommerce`
        *   **Username**: `postgres`
        *   **Password**: `postgres`
    *   Klik **Save**.
4.  **Explore**: Buka `Databases` -> `asos_ecommerce` -> `Schemas` -> `public` -> `Tables`.

### Cara B: Menggunakan Tools Luar (DBeaver / Tableau / Power BI)
Jika Anda ingin menggunakan aplikasi yang terinstall di Windows/Mac Anda (akses dari luar Docker).

*   **Host**: `localhost`
*   **Port**: `5433` 
*   **Database**: `asos_ecommerce`
*   **Username**: `postgres`
*   **Password**: `postgres`

### Cara C: Menggunakan Terminal (Command Line)
Untuk pengecekan cepat menggunakan perintah SQL text-based.

1.  Buka Terminal/PowerShell.
2.  Jalankan perintah ini untuk masuk ke dalam container database:
    ```powershell
    docker exec -it asos_postgres psql -U postgres -d asos_ecommerce
    ```
3.  Anda sekarang ada di `asos_ecommerce=#` prompt. Coba perintah:
    ```sql
    \dt                      -- Lihat daftar tabel
    SELECT * FROM dim_store; -- Lihat data toko
    \q                       -- Keluar
    ```
