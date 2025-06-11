from functools import wraps
from flask import Flask, render_template, request, redirect, session, url_for, flash, send_file, make_response, jsonify
from config import get_db_connection
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import timedelta, datetime
import pytz
import requests
from config_fonnte import FONNTE_API_KEY
import atexit
import io
import pandas as pd
import pdfkit
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import re
import random

app = Flask(__name__)
app.secret_key = 'secret123'
app.permanent_session_lifetime = timedelta(minutes=30)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reservasi.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Konfigurasi email
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'  # Ganti dengan email Anda
app.config['MAIL_PASSWORD'] = 'your-app-password'     # Ganti dengan password aplikasi Anda

db = SQLAlchemy(app)
mail = Mail(app)

# Tambahkan filter nl2br
@app.template_filter('nl2br')
def nl2br(value):
    if not value:
        return ""
    return value.replace('\n', '<br>')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            return redirect(url_for('dashboard_pegawai'))
        return f(*args, **kwargs)
    return decorated_function

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create ruangan table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ruangan (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nama VARCHAR(100) NOT NULL,
            lokasi VARCHAR(100) NOT NULL,
            kapasitas INT NOT NULL
        )
    """)
    
    # Insert default rooms if table is empty
    cursor.execute("SELECT COUNT(*) FROM ruangan")
    if cursor.fetchone()[0] == 0:
        default_rooms = [
            ('Ruang Rapat Utama', 'Lantai 2', 30),
            ('Ruang Rapat Pleno 1', 'Lantai 3', 20),
            ('Ruang Rapat Pleno 2', 'Lantai 3', 30),
            ('Ruang Rapat Kelompok', 'Lantai 3', 15)
        ]
        cursor.executemany(
            "INSERT INTO ruangan (nama, lokasi, kapasitas) VALUES (%s, %s, %s)",
            default_rooms
        )
    
    conn.commit()
    conn.close()

# Call create_tables when app starts
create_tables()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nip = request.form['nip']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM pegawai WHERE nip = %s", (nip,))
        user = cursor.fetchone()
        conn.close()

        if user and user['password'] == password:
            session['nip'] = user['nip']
            session['nama'] = user['nama']
            session['role'] = user['role']
            print("[DEBUG] Session setelah login:", dict(session))

            if user['role'] == 'admin':
                return redirect(url_for('dashboard_admin'))
            else:
                return redirect(url_for('dashboard_pegawai'))
        else:
            flash('NIP atau Password salah!', 'error')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'nip' not in session:
        return redirect(url_for('login'))

    if session['role'] == 'admin':
        return redirect(url_for('dashboard_admin'))
    else:
        return redirect(url_for('dashboard_pegawai'))

@app.route('/dashboard-admin')
@admin_required
def dashboard_admin():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) as total FROM reservasi")
    total_semua = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) as total FROM reservasi WHERE status = 'Disetujui'")
    total_disetujui = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) as total FROM reservasi WHERE status = 'Ditolak'")
    total_ditolak = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) as total FROM reservasi WHERE status = 'Menunggu'")
    total_menunggu = cursor.fetchone()['total']

    conn.close()

    return render_template(
        'dashboard_admin.html',
        total_semua=total_semua,
        total_disetujui=total_disetujui,
        total_ditolak=total_ditolak,
        total_menunggu=total_menunggu
    )

@app.route('/dashboard-pegawai')
def dashboard_pegawai():
    print("[DEBUG] Session di dashboard-pegawai:", dict(session))
    if 'nip' not in session or session.get('role') != 'pegawai':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM reservasi WHERE nip = %s ORDER BY tanggal DESC
    """, (session['nip'],))
    reservasi = cursor.fetchall()
    conn.close()

    # Info ruangan yang sedang dipakai (status Disetujui)
    ruang_digunakan = [r['ruangan'] for r in reservasi if r['status'] == 'Disetujui']

    return render_template('dashboard_pegawai.html', reservasi=reservasi, ruang_digunakan=ruang_digunakan)

@app.route('/ajukan-reservasi', methods=['GET', 'POST'])
def ajukan_reservasi():
    # Cek login
    if 'nip' not in session:
        return redirect(url_for('login'))

    # Ambil data ruangan dari database
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM ruangan ORDER BY nama")
    ruangan_list = cursor.fetchall()
    conn.close()

    if request.method == 'POST':
        try:
            # Ambil data dari form
            nip = session['nip']  # Ambil NIP dari session
            ruangan = request.form['ruangan']
            tanggal = request.form['tanggal']
            waktu_mulai = request.form['waktu_mulai']
            waktu_selesai = request.form['waktu_selesai']
            keperluan = request.form['keperluan']

            # Validasi input
            if not all([nip, ruangan, tanggal, waktu_mulai, waktu_selesai, keperluan]):
                flash("Semua field harus diisi!", "danger")
                return redirect(url_for('ajukan_reservasi'))

            # Cek ketersediaan ruangan
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM reservasi 
                WHERE ruangan = %s 
                AND tanggal = %s 
                AND status = 'Disetujui'
                AND (
                    (waktu_mulai <= %s AND waktu_selesai > %s)
                    OR (waktu_mulai < %s AND waktu_selesai >= %s)
                    OR (%s <= waktu_mulai AND %s > waktu_mulai)
                )
            """, (ruangan, tanggal, waktu_mulai, waktu_mulai, 
                  waktu_selesai, waktu_selesai, waktu_mulai, waktu_selesai))
            
            if cursor.fetchone():
                flash("Ruangan sudah direservasi pada waktu tersebut!", "danger")
                conn.close()
                return redirect(url_for('ajukan_reservasi'))

            # Simpan data ke database
            cursor.execute("""
                INSERT INTO reservasi (nip, ruangan, tanggal, waktu_mulai, waktu_selesai, keperluan, status, waktu_pengajuan)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """, (nip, ruangan, tanggal, waktu_mulai, waktu_selesai, keperluan, 'Menunggu'))
            conn.commit()

            # Ambil data pemesan untuk notifikasi
            cursor.execute("SELECT nama FROM pegawai WHERE nip = %s", (nip,))
            pemesan = cursor.fetchone()

            # Kirim notifikasi ke admin
            cursor.execute("SELECT no_wa FROM pegawai WHERE role = 'admin'")
            admin_list = cursor.fetchall()
            
            for admin in admin_list:
                if admin['no_wa']:
                    pesan = (
                        f"[PENGAJUAN RESERVASI BARU]\n\n"
                        f"Pemesan: {pemesan['nama']}\n"
                        f"Ruangan: {ruangan}\n"
                        f"Tanggal: {tanggal}\n"
                        f"Waktu: {waktu_mulai} - {waktu_selesai}\n"
                        f"Keperluan: {keperluan}\n\n"
                        f"Silakan verifikasi pengajuan Reservasi melalui panel admin."
                    )
                    kirim_wa(admin['no_wa'], pesan)

            conn.close()
            flash("Reservasi berhasil diajukan!", "success")
            return redirect(url_for('dashboard'))

        except Exception as e:
            print(f"[ERROR] {str(e)}")
            if 'conn' in locals():
                conn.close()
            flash("Terjadi kesalahan saat mengajukan reservasi. Silakan coba lagi.", "danger")
            return redirect(url_for('ajukan_reservasi'))

    # Render template untuk GET request
    return render_template('ajukan_reservasi.html', ruangan_list=ruangan_list)

@app.route('/reservasi-saya')
def reservasi_saya():
    if 'nip' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM reservasi WHERE nip = %s ORDER BY tanggal DESC, waktu_mulai DESC", (session['nip'],))
    data_reservasi = cursor.fetchall()
    conn.close()

    return render_template('daftar_reservasi.html', data=data_reservasi)

@app.route('/logout')
def logout():
    session.clear()
    flash('Anda berhasil logout.', 'info')
    return redirect(url_for('login'))

@app.route('/jadwal')
def jadwal():
    if 'nip' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT r.*, p.nama AS nama_pemesan
        FROM reservasi r
        JOIN pegawai p ON r.nip = p.nip
        WHERE r.status = 'Disetujui'
        ORDER BY r.tanggal DESC, r.waktu_mulai
    """)
    jadwal_list = cursor.fetchall()
    conn.close()

    return render_template('jadwal.html', jadwal_list=jadwal_list)

@app.route('/kalender')
def kalender():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT r.tanggal, r.waktu_mulai, r.waktu_selesai, r.ruangan, r.keperluan, p.nama
        FROM reservasi r
        JOIN pegawai p ON r.nip = p.nip
        WHERE r.status = 'Disetujui'
    """)
    data = cursor.fetchall()
    conn.close()

    events = []
    for row in data:
        events.append({
            'title': f"{row['nama']} - {row['keperluan']} ({row['ruangan']})",
            'start': f"{row['tanggal']}T{row['waktu_mulai']}",
            'end': f"{row['tanggal']}T{row['waktu_selesai']}"
        })

    return render_template('kalender.html', events=events)

@app.route('/batalkan_reservasi/<int:id>', methods=['POST'])
def batalkan_reservasi(id):
    if 'nip' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT status FROM reservasi WHERE id = %s AND nip = %s", (id, session['nip']))
    data = cur.fetchone()

    if data and data['status'] == 'Menunggu':
        cur.execute("DELETE FROM reservasi WHERE id = %s AND nip = %s", (id, session['nip']))
        conn.commit()
        flash('Reservasi berhasil dibatalkan.', 'success')
    else:
        flash('Reservasi tidak dapat dibatalkan.', 'danger')
    
    cur.close()
    conn.close()
    return redirect(url_for('reservasi_saya'))

@app.route('/daftar-reservasi')
def daftar_reservasi():
    if 'nip' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM reservasi WHERE nip = %s ORDER BY tanggal DESC, waktu_mulai DESC", (session['nip'],))
    data = cursor.fetchall()
    conn.close()

    return render_template('daftar_reservasi.html', data=data)

@app.route('/setujui-reservasi/<int:id>', methods=['POST'])
@admin_required
def setujui_reservasi(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Ambil data reservasi dan nama pemesan
    cursor.execute("""
        SELECT r.*, p.nama, p.no_wa
        FROM reservasi r
        JOIN pegawai p ON r.nip = p.nip
        WHERE r.id = %s
    """, (id,))
    data = cursor.fetchone()

    if not data:
        flash('Reservasi tidak ditemukan.', 'danger')
        conn.close()
        return redirect(url_for('kelola_reservasi'))  # <--- redirect ke kelola_reservasi

    # Update status
    cursor.execute("UPDATE reservasi SET status = 'Disetujui' WHERE id = %s", (id,))
    conn.commit()
    conn.close()

    # Kirim WhatsApp
    pesan = (
        f"Hai, {data['nama']}!\n\n"
        f"Reservasi Anda untuk ruang *{data['ruangan']}* pada "
        f"{data['tanggal']} pukul {data['waktu_mulai']} - {data['waktu_selesai']} "
        f"telah *DISETUJUI* oleh admin."
        f"> _Dikirim oleh adm. KOMNAS HAM RI_"
    )

    if data['no_wa']:
        kirim_wa(data['no_wa'], pesan)
    else:
        print("[INFO] Nomor WhatsApp kosong, tidak mengirim WA.")

    flash('Reservasi disetujui & notifikasi dikirim.', 'success')
    return redirect(url_for('kelola_reservasi'))  # <--- redirect ke kelola_reservasi

@app.route('/tolak-reservasi/<int:id>', methods=['POST'])
@admin_required
def tolak_reservasi(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Ambil data reservasi dan pegawai
    cursor.execute("""
        SELECT r.*, p.nama, p.no_wa
        FROM reservasi r
        JOIN pegawai p ON r.nip = p.nip
        WHERE r.id = %s
    """, (id,))
    data = cursor.fetchone()

    if not data:
        flash('Reservasi tidak ditemukan.', 'danger')
        conn.close()
        return redirect(url_for('kelola_reservasi'))

    # Update status menjadi Ditolak
    cursor.execute("UPDATE reservasi SET status = 'Ditolak' WHERE id = %s", (id,))
    conn.commit()

    # Ambil kontak admin
    cursor.execute("SELECT nama, no_wa FROM pegawai WHERE role = 'admin' LIMIT 1")
    admin = cursor.fetchone()
    admin_contact = admin['no_wa'] if admin else "08123456789"  # Ganti dengan nomor default jika tidak ada admin

    # Kirim WA jika nomor tersedia
    pesan = (
        f"Hai, {data['nama']}.\n\n"
        f"Mohon maaf, reservasi Anda untuk ruang *{data['ruangan']}* pada "
        f"{data['tanggal']} pukul {data['waktu_mulai']} - {data['waktu_selesai']} "
        f"telah *DITOLAK* oleh admin.\n\n"
        f"Untuk informasi lebih lanjut mengenai alasan penolakan, "
        f"silakan hubungi admin di nomor berikut:\n"
        f"*{admin_contact}*\n\n"
        f"> _Dikirim oleh adm. KOMNAS HAM RI_"
    )

    if data.get('no_wa'):
        kirim_wa(data['no_wa'], pesan)
    else:
        print("[INFO] Nomor WhatsApp kosong, tidak mengirim WA.")

    flash('Reservasi ditolak & notifikasi dikirim.', 'success')
    return redirect(url_for('kelola_reservasi'))

@app.route('/hapus-reservasi/<int:id>', methods=['POST'])
@admin_required
def hapus_reservasi(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reservasi WHERE id = %s", (id,))
    conn.commit()
    conn.close()
    flash('Reservasi dihapus.', 'danger')
    return redirect(url_for('kelola_reservasi'))  # <--- redirect ke kelola_reservasi

@app.route('/kelola-reservasi')
@admin_required
def kelola_reservasi():
    # Ambil parameter filter dari URL
    filter_status = request.args.get('filter', 'all')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Base query
    base_query = """
        SELECT r.id, p.nama, r.ruangan as nama_ruangan, 
               r.tanggal, r.waktu_mulai, r.waktu_selesai, 
               r.keperluan as kegiatan, r.status
        FROM reservasi r
        JOIN pegawai p ON r.nip = p.nip
    """
    
    # Tambahkan filter sesuai status yang dipilih
    if filter_status != 'all':
        base_query += " WHERE r.status = %s"
        cursor.execute(base_query + " ORDER BY r.tanggal DESC, r.waktu_mulai DESC", (filter_status,))
    else:
        cursor.execute(base_query + " ORDER BY r.tanggal DESC, r.waktu_mulai DESC")
    
    reservasi = cursor.fetchall()
    conn.close()

    return render_template('kelola_reservasi.html', 
                         reservasi=reservasi, 
                         current_filter=filter_status)

# --- Tambahkan route untuk kelola pegawai ---
@app.route('/kelola_pegawai')
@admin_required
def kelola_pegawai():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM pegawai WHERE role='pegawai'")
    pegawai = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('kelola_pegawai.html', pegawai=pegawai)

# --- Route: Edit data pegawai (reset password, ubah nama) ---
@app.route('/edit_pegawai/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_pegawai(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        nama = request.form['nama']
        password = request.form['password']
        if password:
            cursor.execute("UPDATE pegawai SET nama=%s, password=%s WHERE id=%s", (nama, password, id))
        else:
            cursor.execute("UPDATE pegawai SET nama=%s WHERE id=%s", (nama, id))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Data pegawai berhasil diperbarui.', 'success')
        return redirect(url_for('kelola_pegawai'))
    cursor.execute("SELECT * FROM pegawai WHERE id=%s", (id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('edit_pegawai.html', user=user)

@app.route('/tambah-pegawai', methods=['GET', 'POST'])
@admin_required
def tambah_pegawai():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        nip = request.form['nip']
        nama = request.form['nama']
        no_wa = request.form['no_wa']
        password = request.form['password']
        role = request.form['role']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Cek apakah NIP sudah ada
        cursor.execute("SELECT * FROM pegawai WHERE nip = %s", (nip,))
        if cursor.fetchone():
            flash('NIP sudah terdaftar.', 'danger')
            return redirect(url_for('tambah_pegawai'))

        cursor.execute("""
            INSERT INTO pegawai (nip, nama, no_wa, password, role)
            VALUES (%s, %s, %s, %s, %s)
        """, (nip, nama, no_wa, password, role))
        conn.commit()
        conn.close()

        flash('Pegawai berhasil ditambahkan.', 'success')
        return redirect(url_for('kelola_pegawai'))

    return render_template('tambah_pegawai.html')

@app.route('/hapus-pegawai/<int:id>', methods=['POST'])
@admin_required
def hapus_pegawai(id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pegawai WHERE id = %s", (id,))
    conn.commit()
    conn.close()

    flash('Data pegawai berhasil dihapus.', 'success')
    return redirect(url_for('kelola_pegawai'))

@app.route('/manual-kirim-notifikasi')
def trigger_notifikasi():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    kirim_notifikasi_otomatis()
    flash('Notifikasi otomatis dipicu secara manual.', 'info')
    return redirect(url_for('dashboard_admin'))

@app.route('/kirim-notifikasi-otomatis')
def route_kirim_notifikasi_otomatis():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    jumlah = kirim_notifikasi_otomatis()
    flash(f'Notifikasi otomatis dikirim ke {jumlah} pegawai.', 'success')
    return redirect(url_for('dashboard_admin'))

@app.route('/notifikasi/manual')
def notifikasi_manual():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    kirim_notifikasi_otomatis()
    flash('Notifikasi otomatis dipicu secara manual.', 'info')
    return redirect(url_for('dashboard_admin'))

@app.route('/notifikasi/otomatis')
def notifikasi_otomatis():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    jumlah = kirim_notifikasi_otomatis()
    flash(f'Notifikasi otomatis dikirim ke {jumlah} pegawai.', 'success')
    return redirect(url_for('kelola_reservasi'))

@app.route('/export_excel')
@admin_required
def export_excel():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT r.id, p.nama AS nama_pemesan, r.tanggal, r.waktu_mulai, r.waktu_selesai, r.ruangan, r.keperluan AS keterangan, r.status
        FROM reservasi r
        JOIN pegawai p ON r.nip = p.nip
        ORDER BY r.tanggal DESC, r.waktu_mulai DESC
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    # Konversi waktu_mulai dan waktu_selesai ke string (handle timedelta, time, dan str)
    for row in data:
        for key in ['waktu_mulai', 'waktu_selesai']:
            val = row[key]
            if isinstance(val, str) or val is None:
                continue
            elif hasattr(val, 'strftime'):
                row[key] = val.strftime('%H:%M')
            elif isinstance(val, timedelta):
                total_seconds = int(val.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                row[key] = f"{hours:02d}:{minutes:02d}"
            else:
                row[key] = str(val)

    df = pd.DataFrame(data, columns=['id', 'nama_pemesan', 'tanggal', 'waktu_mulai', 'waktu_selesai', 'ruangan', 'keterangan', 'status'])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Laporan Reservasi')
        workbook  = writer.book
        worksheet = writer.sheets['Laporan Reservasi']
        # Format center untuk kolom tanggal (kolom C, index 2)
        center_format = workbook.add_format({'align': 'center'})
        worksheet.set_column('C:C', 15, center_format)  # Kolom C adalah 'tanggal'
    output.seek(0)

    return send_file(output, download_name="laporan_reservasi.xlsx", as_attachment=True)

path_to_wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)

@app.route('/export_pdf')
@admin_required
def export_pdf():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.nama AS nama_pemesan, r.tanggal, r.waktu_mulai, r.waktu_selesai, r.ruangan, r.keperluan AS keterangan, r.status
        FROM reservasi r
        JOIN pegawai p ON r.nip = p.nip
        ORDER BY r.tanggal DESC, r.waktu_mulai DESC
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    print("DEBUG DATA PDF:", data)

    rendered = render_template('laporan_pdf.html', data=data)

    # Convert HTML to PDF dengan konfigurasi path wkhtmltopdf
    pdf = pdfkit.from_string(rendered, False, configuration=config)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=laporan_reservasi.pdf'

    return response

@app.route('/export-laporan')
@admin_required
def export_laporan():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    format_export = request.args.get('format')

    if not (start_date and end_date and format_export):
        return "Parameter tidak lengkap", 400

    # Ambil data dari database
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT p.nama AS nama_pemesan, r.tanggal, r.waktu_mulai, r.waktu_selesai, r.ruangan, r.keperluan AS keterangan, r.status 
        FROM reservasi r 
        JOIN pegawai p ON r.nip = p.nip 
        WHERE r.tanggal BETWEEN %s AND %s
        ORDER BY r.tanggal DESC, r.waktu_mulai DESC
    """
    cursor.execute(query, (start_date, end_date))
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    # Format PDF
    if format_export == 'pdf':
        rendered = render_template('laporan_pdf.html', data=data, start_date=start_date, end_date=end_date)
        path_to_wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"  # sesuaikan jika perlu
        config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)
        pdf = pdfkit.from_string(rendered, False, configuration=config)

        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=laporan_reservasi_{start_date}_sampai_{end_date}.pdf'
        return response

    # Format Excel
    elif format_export == 'excel':
        # Konversi waktu ke string agar tidak error di Excel
        for row in data:
            for key in ['waktu_mulai', 'waktu_selesai']:
                val = row[key]
                if isinstance(val, str) or val is None:
                    continue
                elif hasattr(val, 'strftime'):
                    row[key] = val.strftime('%H:%M')
                elif isinstance(val, timedelta):
                    total_seconds = int(val.total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    row[key] = f"{hours:02d}:{minutes:02d}"
                else:
                    row[key] = str(val)

        df = pd.DataFrame(data, columns=['nama_pemesan', 'tanggal', 'waktu_mulai', 'waktu_selesai', 'ruangan', 'keterangan', 'status'])
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Laporan')
        output.seek(0)

        return send_file(
            output,
            download_name=f"laporan_reservasi_{start_date}_sampai_{end_date}.xlsx",
            as_attachment=True
        )

    else:
        return "Format tidak dikenali", 400

def kirim_notifikasi_otomatis():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    now = datetime.now(pytz.timezone('Asia/Jakarta'))
    tanggal_hari_ini = now.strftime("%Y-%m-%d")

    query = """
        SELECT r.*, p.nama, p.no_wa
        FROM reservasi r
        JOIN pegawai p ON r.nip = p.nip
        WHERE r.status = 'Disetujui'
          AND r.tanggal = %s
    """
    cursor.execute(query, (tanggal_hari_ini,))
    result = cursor.fetchall()

    jumlah_dikirim = 0
    for row in result:
        pesan = (
            f"Hai, {row['nama']}!\n\n"
            f"Ini adalah pengingat bahwa Anda memiliki jadwal di ruang *{row['ruangan']}* "
            f"hari ini, {row['tanggal']} pukul {row['waktu_mulai']} - {row['waktu_selesai']}.\n\n"
            f"> _Dikirim oleh adm. KOMNAS HAM RI_"
        )
        if row['no_wa']:
            kirim_wa(row['no_wa'], pesan)
            jumlah_dikirim += 1
    cursor.close()
    conn.close()
    return jumlah_dikirim

def kirim_wa(no_wa, pesan):
    url = "https://api.fonnte.com/send"
    headers = {
        "Authorization": FONNTE_API_KEY
    }
    data = {
        "target": no_wa,
        "message": pesan,
        "countryCode": "62"  # jika nomor tidak pakai awalan +62
    }
    try:
        response = requests.post(url, headers=headers, data=data)
        print("[INFO] Notifikasi WA:", response.text)
    except Exception as e:
        print("[ERROR] Gagal mengirim WA:", e)

def jadwal_pengingat():
    with app.app_context():
        print("[SCHEDULER] Menjalankan pengingat otomatis...")
        kirim_notifikasi_otomatis()

scheduler = BackgroundScheduler(timezone='Asia/Jakarta')
scheduler.add_job(jadwal_pengingat, 'cron', hour=8, minute=0)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.route('/ajukan-akun', methods=['GET', 'POST'])
def ajukan_akun():
    if request.method == 'POST':
        try:
            nip = request.form['nip']
            nama = request.form['nama']
            no_wa = request.form['no_wa']
            isi_surat = request.form.get('isi_surat', 'Pengajuan akun baru.')
            file_surat = request.files.get('file_surat')  # Ambil file surat

            # Validasi NIP hanya angka dan maksimal 18 digit
            if not nip.isdigit() or len(nip) < 18:
                flash("NIP harus berupa angka dengan maksimal 18 digit.", "danger")
                return redirect(url_for('ajukan_akun'))

            # Proses file surat
            file_surat_filename = None
            if file_surat and file_surat.filename != '':
                file_surat_filename = secure_filename(file_surat.filename)
                file_surat.save(os.path.join('static/uploads', file_surat_filename))

            # Simpan data ke database
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                INSERT INTO pengajuan_akun (nip, nama, no_wa, isi_surat, tanggal_pengajuan, status, file_surat)
                VALUES (%s, %s, %s, %s, NOW(), 'Menunggu', %s)
            ''', (nip, nama, no_wa, isi_surat, file_surat_filename))
            conn.commit()

            # Kirim notifikasi ke admin
            cursor.execute("SELECT no_wa FROM pegawai WHERE role = 'admin'")
            admin_list = cursor.fetchall()
            for admin in admin_list:
                if admin['no_wa']:
                    pesan = (
                        f"[PENGAJUAN AKUN BARU]\n\n"
                        f"Nama: {nama}\n"
                        f"NIP: {nip}\n"
                        f"No. WA: {no_wa}\n\n"
                        f"Silakan verifikasi pengajuan melalui panel admin."
                    )
                    kirim_wa(admin['no_wa'], pesan)

            conn.close()
            flash("Pengajuan akun berhasil dikirim!", "success")
            return redirect(url_for('login'))

        except Exception as e:
            print(f"[ERROR]: {str(e)}")
            flash("Terjadi kesalahan saat mengajukan akun.", "danger")
            return redirect(url_for('ajukan_akun'))

    return render_template('ajukan_akun.html')

@app.route('/verifikasi-pengajuan')
@admin_required
def verifikasi_pengajuan():
    if 'nip' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM pengajuan_akun ORDER BY tanggal_pengajuan DESC")
    pengajuan = cursor.fetchall()
    conn.close()

    return render_template('kelola_pengajuan.html', pengajuan=pengajuan)

@app.route('/setujui_pengajuan/<int:id>', methods=['POST'])
@admin_required
def setujui_pengajuan(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get request data
        cursor.execute("SELECT * FROM pengajuan_akun WHERE id = %s AND status = 'Menunggu'", (id,))
        data = cursor.fetchone()

        if data:
            # Generate default password (can be changed later)
            default_password = "12345"

            # Insert into pegawai table
            cursor.execute('''
                INSERT INTO pegawai (nip, nama, password, no_wa, role)
                VALUES (%s, %s, %s, %s, %s)
            ''', (data['nip'], data['nama'], default_password, data['no_wa'], 'pegawai'))

            # Update request status
            cursor.execute("UPDATE pengajuan_akun SET status = 'Disetujui' WHERE id = %s", (id,))
            conn.commit()
            
            # Send WhatsApp notification
            if data['no_wa']:
                pesan = (
                    f"Hai, {data['nama']}!\n\n"
                    f"Pengajuan akun Anda telah DISETUJUI.\n"
                    f"Silakan login dengan:\n"
                    f"NIP: {data['nip']}\n"
                    f"Password: {default_password}\n\n"
                    f"Mohon segera ubah password Anda setelah login pertama."
                    f"> _Dikirim oleh adm. KOMNAS HAM RI_"
                )
                kirim_wa(data['no_wa'], pesan)

            conn.close()
            return jsonify({
                'success': True,
                'message': 'Pengajuan berhasil disetujui'
            })
        else:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Data pengajuan tidak ditemukan atau sudah diproses'
            }), 404

    except Exception as e:
        print(f"[ERROR VERIFIKASI]: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/tolak_pengajuan/<int:id>', methods=['POST'])
@admin_required
def tolak_pengajuan(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get request data
        cursor.execute("SELECT * FROM pengajuan_akun WHERE id = %s AND status = 'Menunggu'", (id,))
        data = cursor.fetchone()

        if data:
            # Update request status
            cursor.execute("UPDATE pengajuan_akun SET status = 'Ditolak' WHERE id = %s", (id,))
            conn.commit()
            
            # Ambil kontak admin
            cursor.execute("SELECT nama, no_wa FROM pegawai WHERE role = 'admin' LIMIT 1")
            admin = cursor.fetchone()
            admin_contact = admin['no_wa'] if admin else "08123456789"  # Ganti dengan nomor default jika tidak ada admin

            # Send WhatsApp notification
            if data['no_wa']:
                pesan = (
                    f"Hai, {data['nama']}.\n\n"
                    f"Mohon maaf, pengajuan akun Anda telah *DITOLAK*.\n\n"
                    f"Untuk informasi lebih lanjut mengenai alasan penolakan, "
                    f"silakan hubungi admin di nomor berikut:\n"
                    f"*{admin_contact}*\n\n"
                    f"> _Dikirim oleh adm. KOMNAS HAM RI_"
                )
                kirim_wa(data['no_wa'], pesan)

            conn.close()
            return jsonify({
                'success': True,
                'message': 'Pengajuan berhasil ditolak'
            })
        else:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Data pengajuan tidak ditemukan atau sudah diproses'
            }), 404

    except Exception as e:
        print(f"[ERROR VERIFIKASI]: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/surat_pengajuan')
def surat_pengajuan():
    # Get form data from query parameters if available
    nama = request.args.get('nama', '_________________')
    nip = request.args.get('nip', '_________________')
    no_wa = request.args.get('no_wa', '_________________')
    isi_surat = request.args.get('isi_surat', 'Dengan ini mengajukan permohonan pembuatan akun untuk dapat menggunakan sistem reservasi ruang rapat Komnas HAM RI.')
    
    return render_template('surat_pengajuan.html', 
                         nama=nama,
                         nip=nip,
                         no_wa=no_wa,
                         isi_surat=isi_surat,
                         now=datetime.now())

@app.route('/view-pdf/<filename>')
@admin_required
def view_pdf(filename):
    try:
        file_path = os.path.join('static', 'uploads', filename)
        
        if not os.path.exists(file_path):
            flash("File tidak ditemukan.", "danger")
            return redirect(url_for('verifikasi_pengajuan'))
        
        return send_file(
            file_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"[ERROR VIEW PDF]: {str(e)}")
        flash("Gagal mengunduh file PDF.", "danger")
        return redirect(url_for('verifikasi_pengajuan'))

@app.route('/lupa-password', methods=['GET', 'POST'])
def lupa_password():
    if request.method == 'POST':
        nip = request.form['nip']
        no_wa = request.form['no_wa']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Cek apakah NIP dan nomor WA cocok
        cursor.execute("SELECT * FROM pegawai WHERE nip = %s AND no_wa = %s", (nip, no_wa))
        user = cursor.fetchone()
        
        if user:
            # Generate password baru (6 digit angka)
            new_password = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            
            # Update password di database
            cursor.execute("UPDATE pegawai SET password = %s WHERE nip = %s", (new_password, nip))
            conn.commit()
            
            # Kirim password baru via WhatsApp
            pesan = (
                f"Hai, {user['nama']}!\n\n"
                f"Password baru Anda adalah: *{new_password}*\n\n"
                f"Silakan login dengan password baru ini.\n"
                f"Mohon segera ubah password Anda setelah login."
                f"> _Dikirim oleh adm. KOMNAS HAM RI_"
            )
            kirim_wa(no_wa, pesan)
            
            flash("Password baru telah dikirim ke WhatsApp Anda.", "success")
        else:
            flash("NIP atau nomor WhatsApp tidak ditemukan.", "danger")
        
        conn.close()
        return redirect(url_for('login'))
        
    return render_template('lupa_password.html')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'nip' not in session:
            flash('Silakan login terlebih dahulu.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM pegawai WHERE nip = %s", (session['nip'],))
        user = cursor.fetchone()

        # Verifikasi password saat ini
        if user['password'] != current_password:
            flash('Password saat ini tidak sesuai!', 'error')
            return redirect(url_for('profile'))

        # Verifikasi password baru
        if new_password != confirm_password:
            flash('Password baru dan konfirmasi password tidak sesuai!', 'error')
            return redirect(url_for('profile'))

        # Update password
        cursor.execute("UPDATE pegawai SET password = %s WHERE nip = %s", (new_password, session['nip']))
        conn.commit()
        conn.close()

        flash('Password berhasil diubah!', 'success')
        return redirect(url_for('profile'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM pegawai WHERE nip = %s", (session['nip'],))
    user = cursor.fetchone()
    conn.close()

    return render_template('profile.html', user=user)

@app.route('/generate-pdf')
def generate_pdf():
    nip = request.args.get('nip')
    nama = request.args.get('nama')
    no_wa = request.args.get('no_wa')

    # Validasi input
    if not nip or not nama or not no_wa:
        flash("Semua data harus diisi untuk mengunduh surat.", "danger")
        return redirect(url_for('ajukan_akun'))

    # Tambahkan variabel now
    now = datetime.now()

    # Render template surat_pengajuan.html
    rendered = render_template('surat_pengajuan.html', nip=nip, nama=nama, no_wa=no_wa, now=now)

    print("[DEBUG] Rendered HTML:", rendered[:500])  # Cetak 500 karakter pertama dari HTML

    # Generate PDF
    path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    pdf = pdfkit.from_string(
        rendered,
        False,
        configuration=config,
        options={
            'enable-local-file-access': None,  # Aktifkan akses file lokal
            'encoding': 'UTF-8'
        }
    )
    # Return PDF as response
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=surat_pengajuan_{nip}.pdf'
    return response

@app.route('/get-reservations/<type>')
@admin_required
def get_reservations(type):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if type == 'all':
        query = """
            SELECT r.*, p.nama 
            FROM reservasi r 
            JOIN pegawai p ON r.nip = p.nip 
            ORDER BY r.tanggal DESC, r.waktu_mulai DESC
        """
        cursor.execute(query)
    else:
        status_map = {
            'approved': 'Disetujui',
            'rejected': 'Ditolak',
            'pending': 'Menunggu'
        }
        query = """
            SELECT r.*, p.nama 
            FROM reservasi r 
            JOIN pegawai p ON r.nip = p.nip 
            WHERE r.status = %s 
            ORDER BY r.tanggal DESC, r.waktu_mulai DESC
        """
        cursor.execute(query, (status_map.get(type),))
    
    reservations = cursor.fetchall()
    conn.close()
    
    # Convert datetime objects to string for JSON serialization
    for res in reservations:
        res['tanggal'] = res['tanggal'].strftime('%Y-%m-%d')
        res['waktu_mulai'] = str(res['waktu_mulai'])
        res['waktu_selesai'] = str(res['waktu_selesai'])
    
    return jsonify(reservations)

@app.route('/get-reservations-by-date')
def get_reservations_by_date():  # Hapus @admin_required karena ini diakses publik
    date = request.args.get('date')
    print(f"[DEBUG] Tanggal yang diterima: {date}")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT r.*, p.nama 
        FROM reservasi r 
        JOIN pegawai p ON r.nip = p.nip 
        WHERE r.tanggal = %s 
        AND r.status = 'Disetujui'  # Hanya tampilkan yang disetujui
        ORDER BY r.waktu_mulai ASC
    """
    cursor.execute(query, (date,))
    reservations = cursor.fetchall()
    print(f"[DEBUG] Data reservasi: {reservations}")

    conn.close()

    # Convert datetime objects to string for JSON serialization
    for res in reservations:
        res['tanggal'] = res['tanggal'].strftime('%Y-%m-%d')
        res['waktu_mulai'] = str(res['waktu_mulai'])
        res['waktu_selesai'] = str(res['waktu_selesai'])

    return jsonify(reservations)

@app.route('/check-available', methods=['POST'])
def check_available():
    ruangan = request.form.get('ruangan')
    tanggal = request.form.get('tanggal')
    waktu_mulai = request.form.get('waktu_mulai')
    waktu_selesai = request.form.get('waktu_selesai')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Cek apakah ada reservasi yang overlap
    query = """
        SELECT r.*, p.nama 
        FROM reservasi r
        JOIN pegawai p ON r.nip = p.nip
        WHERE r.ruangan = %s 
        AND r.tanggal = %s 
        AND r.status = 'Disetujui'
        AND (
            (r.waktu_mulai <= %s AND r.waktu_selesai > %s)
            OR (r.waktu_mulai < %s AND r.waktu_selesai >= %s)
            OR (%s <= r.waktu_mulai AND %s > r.waktu_mulai)
        )
    """
    cursor.execute(query, (ruangan, tanggal, waktu_mulai, waktu_mulai, 
                         waktu_selesai, waktu_selesai, waktu_mulai, waktu_selesai))
    existing = cursor.fetchone()
    conn.close()

    if existing:
        return jsonify({
            'available': False,
            'message': f"Ruangan sudah direservasi oleh {existing['nama']} pada jam {existing['waktu_mulai']} - {existing['waktu_selesai']}"
        })
    return jsonify({'available': True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)