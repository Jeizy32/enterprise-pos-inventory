# 📦 Enterprise POS & Inventory Management System

Sebuah aplikasi Point of Sales (POS) dan Manajemen Inventori *full-stack* berskala *enterprise* yang dirancang untuk mengotomatisasi pelacakan rantai pasok (*supply chain*) dan operasional kasir. Dibangun menggunakan arsitektur MVC dengan implementasi keamanan *Database Transactional* (ACID).

## ✨ Fitur Utama (Core Features)

*   **Terminal Kasir Pintar (POS):** Antarmuka kasir dinamis dengan integrasi *hardware scanner* (HTML5-QRCode) untuk membaca *barcode* FMCG/EAN-13 secara *real-time* menggunakan AJAX.
*   **ACID Database Transactions:** Menerapkan logika *Commit/Rollback* pada transaksi penjualan untuk menjamin konsistensi data (Stok dan Laporan Keuangan) saat terjadi anomali sistem.
*   **Immutable Audit Trail:** Perekaman otomatis (*trigger-based*) untuk setiap aktivitas keluar-masuk barang dan penghapusan data guna keperluan audit internal.
*   **Client-Side State Management:** Kalkulasi *subtotal*, agregasi *quantity* (SKU), dan kembalian kasir diproses secara asinkron di sisi klien sebelum dikirim ke API *backend*.
*   **Multi-User Authentication:** Sistem login berbasis *session* untuk akuntabilitas kasir, di mana setiap transaksi faktur tercetak dengan identitas *user* yang terotentikasi.
*   **Thermal Receipt Integration:** Fitur cetak struk khusus yang dirancang menggunakan manipulasi `CSS Print Media` untuk kompatibilitas langsung dengan mesin *Printer Thermal* 58mm.

## 🛠️ Tech Stack
*   **Backend:** Python 3, Flask, RESTful API
*   **Frontend:** HTML5, CSS3, Bootstrap 5, JavaScript (ES6), SweetAlert2
*   **Database:** SQLite (Relational Database)
*   **Hardware Integration:** html5-qrcode (Camera/Scanner Engine)

## 🚀 Instalasi & Menjalankan Aplikasi

1. Clone repositori ini:
   ```bash
   git clone [https://github.com/Jeizy32/nama-repo-lu.git](https://github.com/Jeizy32/nama-repo-lu.git)
   cd nama-repo-lu