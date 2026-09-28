import sqlite3

print("Membangun Database...")

conn = sqlite3.connect('inventori.db')
cursor = conn.cursor()

# Tabel Barang
cursor.execute('''
    CREATE TABLE IF NOT EXISTS barang (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kode_barang TEXT UNIQUE,
        nama_barang TEXT,
        kategori TEXT,
        stok INTEGER,
        tanggal_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Tabel Admin
cursor.execute('''
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
''')

# Akun admin default
cursor.execute("INSERT OR IGNORE INTO admin (username, password) VALUES ('admin', 'admin123')")

conn.commit()
conn.close()

print("[+] Database 'inventori.db' berhasil dibuat.")