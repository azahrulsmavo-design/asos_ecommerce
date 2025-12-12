# 🪪 Identitas Dataset (Dataset Identity)

Dokumen ini menjelaskan metadata lengkap mengenai dataset yang digunakan dalam proyek **ASOS Retail Dashboard**.

---

## 📌 Informasi Umum

| Atribut | Keterangan |
| :--- | :--- |
| **Nama Dataset** | ASOS Retail Intelligence Dataset (Enterprise Edition) |
| **Versi** | 2.2 (Enterprise Features: Orders, Snapshots, Margin) |
| **Topik** | Fashion E-Commerce & Retail Analytics |
| **Bahasa** | Inggris (Data), Indonesia (Dokumentasi) |
| **Pemilik** | Proyek Edukasi (Open Source) |
| **Dibuat Tanggal** | 12 Desember 2025 |

---

## 📦 Komposisi & Sumber Data

Dataset ini merupakan gabungan dari data **Asli** (Real-world) dan **Sintetis** (Generated).

### 1. Data Katalog Produk (ASLI)
*   **Sumber**: Scraping publik dari website ASOS (asos.com).
*   **Isi**: Nama produk, Harga, Kategori, Brand, Warna, Deskripsi.
*   **Jumlah**: **~30,000 SKU unik** (High Fidelity).
*   **Kualitas**: Data nyata dengan variasi brand dan kategori yang luas.

### 2. Data Transaksi & Pelanggan (SINTETIS)
*   **Sumber**: Generated menggunakan Python (`numpy`, `random`).
*   **Tujuan**: Mensimulasikan aktivitas penjualan ritel untuk keperluan dashboard.
*   **Isi**:
    *   **Sales**: **~12,000 Orders** (Multi-item baskets) menghasilkan ~20,000+ Order Lines.
    *   **Customers**: 1,000 Profil pelanggan unik dengan demografi (Usia, Gender, Lokasi UK).
    *   **Inventory**: **~135,000 Snapshot Data Stok** (Stok produk di 5 cabang toko).
*   **Pola**: Data dibuat dengan pola **musiman** (penjualan naik di Q4/Akhir Tahun) untuk realisme analisis tren.

---

## 📊 Statistik Volume Data (Terverifikasi)

| Tabel | Tipe | Jumlah Baris (Est) | Deskripsi Utama |
| :--- | :--- | :--- | :--- |
| `dim_product` | Dimension | **29,989** | Katalog Barang Lengkap |
| `dim_brand` | Dimension | ~300+ | Daftar Merk |
| `dim_category` | Dimension | **~25** | Kategori Produk (Shoes, Accessories, dll) |
| `dim_customer` | Dimension | 1,000 | Data Pelanggan (CRM) |
| `dim_store` | Dimension | 5 | Lokasi Toko Ops |
| `fact_sales` | Fact | **~20,000** | Order Lines (Detail Transaksi) |
| `fact_inventory` | Fact | **135,116** | Stok per Toko per Produk (High Volume) |

---

## 🎯 Kegunaan (Use Cases)

Dataset ini dirancang untuk mendukung pembelajaran dan simulasi kasus bisnis berikut:

1.  **Executive Dashboarding**: Memantau KPI bisnis ritel.
2.  **Customer Segmentation**: Analisis RFM (Recency, Frequency, Monetary).
3.  **Market Basket Analysis**: Mencari pola pembelian produk menggunakan `order_id`.
4.  **Demand Forecasting**: Memprediksi penjualan 30 hari ke depan.
5.  **Inventory Optimization**: Mencegah OOS (Out of Stock).

---

## ⚠️ Catatan Lisensi & Privasi

*   **Non-Komersial**: Dataset ini **TIDAK UNTUK KOMERSIAL**. Hanya untuk tujuan edukasi dan portfolio analitik.
*   **Scraping Disclaimer**: Data produk diambil dari sumber publik (ASOS) di bawah prinsip Fair Use untuk riset/edukasi. Jika digunakan di produksi, Anda wajib mengganti data ini dengan data dummy/anonim.
*   **Data Sintetis**: Data pelanggan, transaksi, dan stok adalah **FIKTIF**. Tidak ada data pribadi asli yang digunakan.
