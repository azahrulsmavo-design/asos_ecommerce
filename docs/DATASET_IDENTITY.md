# 🪪 Identitas Dataset (Dataset Identity)

Dokumen ini menjelaskan metadata lengkap mengenai dataset yang digunakan dalam proyek **ASOS Retail Dashboard**.

---

## 📌 Informasi Umum

| Atribut | Keterangan |
| :--- | :--- |
| **Nama Dataset** | ASOS Retail Intelligence Dataset (Hybrid) |
| **Versi** | 2.0 (Enhanced with Synthetic Transactions) |
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
*   **Jumlah**: ~5,000 SKU unik.
*   **Kualitas**: High Fidelity (Data nyata).

### 2. Data Transaksi & Pelanggan (SINTETIS)
*   **Sumber**: Generated menggunakan Python (`numpy`, `random`).
*   **Tujuan**: Mensimulasikan aktivitas penjualan ritel untuk keperluan dashboard.
*   **Isi**:
    *   **Sales**: 15,000+ Transaksi penjualan selama 12 bulan terakhir.
    *   **Customers**: 1,000 Profil pelanggan unik dengan demografi (Usia, Gender, Lokasi UK).
    *   **Inventory**: Snapshot stok di 5 toko (1 Online, 4 Fisik).
*   **Pola**: Data dibuat dengan pola **musiman** (penjualan naik di Q4/Akhir Tahun) untuk realisme analisis tren.

---

## 📊 Statistik Volume Data

| Tabel | Tipe | Estimasi Baris (Rows) | Deskripsi Utama |
| :--- | :--- | :--- | :--- |
| `dim_product` | Dimension | ~5,000 | Katalog Barang |
| `dim_brand` | Dimension | ~300 | Daftar Merk |
| `dim_customer` | Dimension | 1,000 | Data Pelanggan (CRM) |
| `dim_store` | Dimension | 5 | Lokasi Toko Ops |
| `fact_sales` | Fact | ~16,000 | Riwayat Transaksi |
| `fact_inventory` | Fact | ~25,000 | Stok per Toko per Produk |

---

## 🎯 Kegunaan (Use Cases)

Dataset ini dirancang untuk mendukung pembelajaran dan simulasi kasus bisnis berikut:

1.  **Executive Dashboarding**: Memantau KPI bisnis ritel.
2.  **Customer Segmentation**: Analisis RFM (Recency, Frequency, Monetary).
3.  **Market Basket Analysis**: Mencari pola pembelian produk.
4.  **Demand Forecasting**: Memprediksi penjualan 30 hari ke depan.
5.  **Inventory Optimization**: Mencegah OOS (Out of Stock).

---

## ⚠️ Catatan Lisensi & Privasi

*   **Produk**: Hak cipta nama produk dan brand milik ASOS dan brand masing-masing. Digunakan untuk tujuan edukasi (Fair Use).
*   **Pelanggan**: Data pelanggan adalah **FIKTIF**. Tidak ada data pribadi asli yang digunakan.
