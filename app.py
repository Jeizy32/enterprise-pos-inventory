from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, jsonify
import database
import csv
import io
import os
from dotenv import load_dotenv  
from flask import send_file
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# Route Halaman Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if database.cek_login(username, password):
            session['logged_in'] = True # Bikin kartu akses
            session['username'] = username
            flash(f'Selamat datang, {username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Username atau Password salah!', 'error')
            
    return render_template('login.html')

# ROUTE HALAMAN DAFTAR (REGISTER)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Panggil fungsi database buat nyimpen
        sukses = database.register_user(username, password)
        
        if sukses:
            flash('Registrasi berhasil! Silakan login dengan akun baru Anda.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username sudah terpakai! Silakan pilih nama lain.', 'error')
            
    return render_template('register.html')

# Route Logout
@app.route('/logout')
def logout():
    session.clear() # Hapus kartu akses
    flash('Anda berhasil logout.', 'success')
    return redirect(url_for('login'))

@app.route('/')
def index():
    # Proteksi: Kalau nggak punya tiket login, tendang ke halaman login
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    barang = database.get_semua_barang()
    total_item, total_stok, stok_kritis = database.get_statistik()
    return render_template('index.html', barang=barang, total_item=total_item, total_stok=total_stok, stok_kritis=stok_kritis)

@app.route('/tambah', methods=('POST',))
def tambah():
    if not session.get('logged_in'): return redirect(url_for('login'))

    # Menangkap 5 data dari HTML, termasuk 'harga'
    sukses = database.tambah_barang(
        request.form['kode_barang'], 
        request.form['nama_barang'], 
        request.form['kategori'], 
        request.form['stok'],
        request.form['harga']
    )
    
    if sukses:
        flash('Data barang berhasil ditambahkan!', 'success')
    else:
        flash('Gagal! Kode Barang sudah ada di sistem.', 'error')
    return redirect(url_for('index'))

@app.route('/hapus/<int:id>', methods=('POST',))
def hapus(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    database.hapus_barang(id)
    flash('Data barang berhasil dihapus!', 'success')
    return redirect(url_for('index'))

# Route Halaman Tampilan Audit Trail untuk Admin
@app.route('/audit')
def audit_page():
    # Proteksi: Harus login
    if not session.get('logged_in'): 
        return redirect(url_for('login'))
        
    # Ambil data dari database.py
    audit_data = database.get_semua_audit()
    
    # Kirim data ke template audit.html
    return render_template('audit.html', audit_data=audit_data)

# Route Export ke Excel (CSV)
@app.route('/export')
def export_excel():
    # Cek login kasir
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # Ambil data dari database
    barang_list = database.get_semua_barang()

    # Bikin file Excel baru
    wb = Workbook()
    ws = wb.active
    ws.title = "Data Inventori"

    # --- 1. CUSTOM JUDUL BESAR ---
    ws.merge_cells('A1:G1') # Gabungin cell A sampai G
    judul = ws['A1']
    judul.value = "LAPORAN INVENTORI ENTERPRISE"
    judul.font = Font(size=16, bold=True, color="FFFFFF")
    judul.fill = PatternFill(start_color="0f172a", end_color="0f172a", fill_type="solid") # Warna Dark Slate
    judul.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30 # Bikin barisnya agak tinggi

    # --- 2. CUSTOM HEADER TABEL ---
    headers = ['ID', 'Kode Barang', 'Nama Barang', 'Kategori', 'Harga (Rp)', 'Stok', 'Tgl Update']
    for col_num, header_title in enumerate(headers, 1):
        cell = ws.cell(row=2, column=col_num)
        cell.value = header_title
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="0ea5e9", end_color="0ea5e9", fill_type="solid") # Warna Biru Elegan
        cell.alignment = Alignment(horizontal="center")

    # --- 3. MASUKIN DATA DARI DATABASE ---
    for row_num, barang in enumerate(barang_list, 3): # Mulai ngisi di baris ke-3
        ws.cell(row=row_num, column=1, value=barang['id']).alignment = Alignment(horizontal="center")
        
        # PERBAIKAN BARCODE: Jadikan string biar nggak jadi mutan E+12
        sel_kode = ws.cell(row=row_num, column=2, value=str(barang['kode_barang']))
        sel_kode.alignment = Alignment(horizontal="center")
        
        ws.cell(row=row_num, column=3, value=barang['nama_barang'])
        ws.cell(row=row_num, column=4, value=barang['kategori'])
        
        # Format Harga ada pemisah ribuan
        sel_harga = ws.cell(row=row_num, column=5, value=barang['harga'])
        sel_harga.number_format = '#,##0' 
        
        ws.cell(row=row_num, column=6, value=barang['stok']).alignment = Alignment(horizontal="center")
        ws.cell(row=row_num, column=7, value=barang['tanggal_update'])

    # --- 4. LEBARIN KOLOM OTOMATIS ---
    lebar_kolom = {'A': 5, 'B': 20, 'C': 35, 'D': 25, 'E': 15, 'F': 10, 'G': 25}
    for kolom, lebar in lebar_kolom.items():
        ws.column_dimensions[kolom].width = lebar

    # --- 5. SIMPAN KE MEMORY & KIRIM KE BROWSER ---
    excel_file = io.BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)

    return send_file(
        excel_file,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='Laporan_Inventori_Enterprise.xlsx'
    )

@app.route('/api/barang', methods=['GET'])
def api_barang():
    # Ini endpoint buat disedot sama aplikasi E-Commerce / Mobile Android
    barang = database.get_semua_barang()
    # Convert data SQL jadi format Array Dictionary (JSON)
    hasil = [dict(b) for b in barang]
    
    return jsonify({
        'status': 'success',
        'message': 'Data inventori berhasil diambil',
        'total_data': len(hasil),
        'data': hasil
    })

@app.route('/api/audit', methods=['GET'])
def api_audit():
    # Endpoint untuk melihat riwayat jejak audit (Audit Trail)
    # Proteksi: API ini cuma bisa diakses kalau punya token/session admin
    if not session.get('logged_in'):
        return jsonify({'status': 'error', 'message': 'Akses Ditolak. Harus Login!'}), 401
        
    audit = database.get_semua_audit()
    return jsonify({
        'status': 'success',
        'data': [dict(a) for a in audit]
    })

# API Khusus buat lookup Barcode Scanner (AJAX)
@app.route('/api/cek_barang/<kode>', methods=['GET'])
def api_cek_barang(kode):
    barang = database.get_barang_by_kode(kode)
    if barang:
        return jsonify({
            'status': 'found', 
            'nama_barang': barang['nama_barang'], 
            'kategori': barang['kategori'],
            'harga': barang['harga']
        })
    else:
        return jsonify({'status': 'not_found'})

# ROUTE HALAMAN KASIR (POS)
@app.route('/kasir')
def kasir_page():
    if not session.get('logged_in'): 
        return redirect(url_for('login'))
    return render_template('kasir.html')

@app.route('/api/checkout', methods=['POST'])
def api_checkout():
    if not session.get('logged_in'): 
        return jsonify({'status': 'error', 'message': 'Akses ditolak'})
    
    # Tangkap paket JSON dari JavaScript Kasir
    data = request.json 
    keranjang = data.get('keranjang')
    total = data.get('total')
    bayar = data.get('bayar')
    kembali = data.get('kembali')
    
    # Lempar ke database buat dipotong stoknya
    sukses, nota = database.proses_transaksi(keranjang, total, bayar, kembali)
    
    if sukses:
        return jsonify({'status': 'success', 'nota': nota})
    else:
        return jsonify({'status': 'error', 'message': 'Gagal memproses transaksi'})

# ROUTE CETAK STRUK KASIR
@app.route('/struk/<nota>')
def cetak_struk(nota):
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    trx, detail = database.get_transaksi_by_nota(nota)
    if not trx:
        return "Nota tidak ditemukan", 404
        
    return render_template('struk.html', trx=trx, detail=detail)
   
if __name__ == '__main__':
    app.run(debug=True, port=8000)