import sqlite3
import datetime
import random

def get_db_connection():
    conn = sqlite3.connect('inventori.db')
    conn.row_factory = sqlite3.Row
    return conn

def upgrade_database_ke_pos():
    conn = get_db_connection()
    # 1. Hapus tabel lama
    conn.execute('DROP TABLE IF EXISTS barang')
    
    # 2. Bikin tabel barang
    conn.execute('''
        CREATE TABLE barang (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kode_barang TEXT UNIQUE NOT NULL,
            nama_barang TEXT NOT NULL,
            kategori TEXT NOT NULL,
            stok INTEGER NOT NULL,
            harga INTEGER NOT NULL,
            -- FIX ZONA WAKTU (LOCALTIME) --
            tanggal_update TIMESTAMP DEFAULT (datetime('now','localtime')) 
        )
    ''')
    
    # 3. Bikin tabel untuk nota/struk kasir
    conn.execute('DROP TABLE IF EXISTS transaksi_penjualan')
    conn.execute('''
        CREATE TABLE transaksi_penjualan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nomor_nota TEXT NOT NULL,
            total_belanja INTEGER NOT NULL,
            bayar INTEGER NOT NULL,
            kembalian INTEGER NOT NULL,
            -- FIX ZONA WAKTU (LOCALTIME) --
            tanggal TIMESTAMP DEFAULT (datetime('now','localtime'))
        )
    ''')
    
    # 4. Bikin tabel detail barang 
    conn.execute('DROP TABLE IF EXISTS detail_penjualan')
    conn.execute('''
        CREATE TABLE detail_penjualan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nomor_nota TEXT NOT NULL,
            kode_barang TEXT NOT NULL,
            jumlah_beli INTEGER NOT NULL,
            subtotal INTEGER NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database dan Zona Waktu berhasil di-upgrade!")

def init_audit_table():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS audit_trail (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kode_barang TEXT,
            aksi TEXT,
            jumlah INTEGER,
            tanggal TIMESTAMP DEFAULT (datetime('now','localtime'))
        )
    ''')
    conn.commit()
    conn.close()

# --- EKSEKUSI PEMBUATAN TABEL AWAL ---
init_audit_table() 

# --- FUNGSI MASTER DATA ---
def get_semua_barang():
    conn = get_db_connection()
    barang = conn.execute('SELECT * FROM barang ORDER BY id DESC').fetchall()
    conn.close()
    return barang

def get_semua_audit():
    conn = get_db_connection()
    audit = conn.execute('SELECT * FROM audit_trail ORDER BY id DESC').fetchall()
    conn.close()
    return audit

def get_statistik():
    conn = get_db_connection()
    total_item = conn.execute('SELECT COUNT(*) FROM barang').fetchone()[0]
    total_stok = conn.execute('SELECT SUM(stok) FROM barang').fetchone()[0]
    total_stok = total_stok if total_stok else 0
    stok_kritis = conn.execute('SELECT COUNT(*) FROM barang WHERE stok < 10').fetchone()[0]
    conn.close()
    return total_item, total_stok, stok_kritis

# --- PERBAIKAN: Tambah parameter harga ---
def tambah_barang(kode, nama, kategori, stok, harga):
    conn = get_db_connection()
    try:
        # 1. Simpan ke tabel master barang (Sekarang insert 5 data)
        conn.execute('INSERT INTO barang (kode_barang, nama_barang, kategori, stok, harga) VALUES (?, ?, ?, ?, ?)',
                     (kode, nama, kategori, stok, harga))
        
        # 2. Catat ke tabel riwayat (Audit Trail)
        conn.execute('INSERT INTO audit_trail (kode_barang, aksi, jumlah) VALUES (?, ?, ?)',
                     (kode, 'BARANG BARU MASUK', stok))
        
        conn.commit()
        return True 
    except sqlite3.IntegrityError:
        return False 
    finally:
        conn.close()

def hapus_barang(id_barang):
    conn = get_db_connection()
    barang = conn.execute('SELECT kode_barang, stok FROM barang WHERE id = ?', (id_barang,)).fetchone()
    if barang:
        conn.execute('INSERT INTO audit_trail (kode_barang, aksi, jumlah) VALUES (?, ?, ?)',
                     (barang['kode_barang'], 'DIHAPUS DARI SISTEM', barang['stok']))
        conn.execute('DELETE FROM barang WHERE id = ?', (id_barang,))
        conn.commit()
    conn.close()

def get_barang_by_kode(kode_barang):
    conn = get_db_connection()
    barang = conn.execute('SELECT * FROM barang WHERE kode_barang = ?', (kode_barang,)).fetchone()
    conn.close()
    return barang

# --- LOGIKA TRANSAKSI KASIR (POS) ---
def proses_transaksi(keranjang, total, bayar, kembali):
    conn = get_db_connection()
    try:
        # 1. Bikin Nomor Nota/Faktur Otomatis (Contoh: TRX-20260928-1234)
        now = datetime.datetime.now()
        nota = f"TRX-{now.strftime('%Y%m%d')}-{random.randint(1000,9999)}"
        
        # 2. Simpan ke tabel Transaksi Induk
        conn.execute('INSERT INTO transaksi_penjualan (nomor_nota, total_belanja, bayar, kembalian) VALUES (?, ?, ?, ?)',
                     (nota, total, bayar, kembali))
        
        # 3. Looping isi keranjang belanjaan
        for item in keranjang:
            subtotal = item['harga'] * item['qty']
            
            # A. Simpan detail barang apa aja yang dibeli
            conn.execute('INSERT INTO detail_penjualan (nomor_nota, kode_barang, jumlah_beli, subtotal) VALUES (?, ?, ?, ?)',
                         (nota, item['kode'], item['qty'], subtotal))
            
            # B. POTONG STOK DI GUDANG!
            conn.execute('UPDATE barang SET stok = stok - ? WHERE kode_barang = ?', 
                         (item['qty'], item['kode']))
            
            # C. Catat ke Audit Trail (Riwayat) biar admin tau barang keluar
            conn.execute('INSERT INTO audit_trail (kode_barang, aksi, jumlah) VALUES (?, ?, ?)',
                         (item['kode'], f'TERJUAL (Nota: {nota})', item['qty']))

        conn.commit()
        return True, nota
    except Exception as e:
        conn.rollback() # BATALKAN SEMUA JIKA ERROR (Keamanan Data)
        print("Error Transaksi:", e)
        return False, str(e)
    finally:
        conn.close()

def cek_login(username, password):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM admin WHERE username = ? AND password = ?', (username, password)).fetchone()
    conn.close()
    return user is not None

def get_transaksi_by_nota(nomor_nota):
    conn = get_db_connection()
    # Ambil data induk (Total, Bayar, Kembalian)
    trx = conn.execute('SELECT * FROM transaksi_penjualan WHERE nomor_nota = ?', (nomor_nota,)).fetchone()
    
    # Ambil data anak (Barang apa aja yang dibeli di nota tersebut)
    detail = conn.execute('''
        SELECT d.*, b.nama_barang 
        FROM detail_penjualan d 
        JOIN barang b ON d.kode_barang = b.kode_barang 
        WHERE d.nomor_nota = ?
    ''', (nomor_nota,)).fetchall()
    
    conn.close()
    return trx, detail

# --- FUNGSI REGISTRASI USER ---
def register_user(username, password):
    conn = get_db_connection()
    try:
        # Masukin user baru ke tabel admin
        conn.execute('INSERT INTO admin (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        return True # Sukses
    except sqlite3.IntegrityError:
        # Error ini muncul otomatis kalau username udah ada yang pakai (karena UNIQUE)
        return False 
    finally:
        conn.close()