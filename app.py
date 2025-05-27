from functools import wraps
from flask import Flask, render_template, request, redirect, session, url_for, flash, send_file, make_response
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

app = Flask(__name__)
app.secret_key = 'secret123'
app.permanent_session_lifetime = timedelta(minutes=30)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            return redirect(url_for('dashboard_pegawai'))
        return f(*args, **kwargs)
    return decorated_function

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
    if 'nip' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        ruangan = request.form['ruangan']
        tanggal = request.form['tanggal']
        waktu_mulai = request.form['waktu_mulai']
        waktu_selesai = request.form['waktu_selesai']
        keperluan = request.form['keperluan']
        nip = session['nip']

        # Handle file upload
        lampiran_file = request.files.get('lampiran')
        lampiran_filename = None

        if lampiran_file and lampiran_file.filename != '':
            lampiran_filename = secure_filename(lampiran_file.filename)
            lampiran_file.save(os.path.join('static/uploads', lampiran_filename))

        try:
            print("[DEBUG] Mulai proses reservasi")

            waktu_reservasi = datetime.strptime(f"{tanggal} {waktu_mulai}", "%Y-%m-%d %H:%M")
            waktu_sekarang = datetime.now(pytz.timezone('Asia/Jakarta'))  # gunakan timezone Asia/Jakarta

            print(f"[DEBUG] Waktu reservasi: {waktu_reservasi}, sekarang: {waktu_sekarang}")

            waktu_selesai_dt = datetime.strptime(f"{tanggal} {waktu_selesai}", "%Y-%m-%d %H:%M")

            # Validasi waktu sudah lewat
            # if waktu_reservasi < waktu_sekarang:
            #     flash("Tidak bisa melakukan reservasi di waktu yang telah lewat.", "danger")
            #     return redirect(url_for('ajukan_reservasi'))

            # Validasi jam kerja
            # jam_kerja_mulai = datetime.strptime("08:00", "%H:%M").time()
            # jam_kerja_selesai = datetime.strptime("17:00", "%H:%M").time()
            # if not (jam_kerja_mulai <= waktu_reservasi.time() <= jam_kerja_selesai) or not (jam_kerja_mulai <= waktu_selesai_dt.time() <= jam_kerja_selesai):
            #     flash("Waktu reservasi harus berada dalam jam kerja (08:00 - 17:00).", "danger")
            #     return redirect(url_for('ajukan_reservasi'))

            if waktu_selesai_dt <= waktu_reservasi:
                flash("Waktu selesai harus lebih besar dari waktu mulai.", "danger")
                return redirect(url_for('ajukan_reservasi'))

            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            query = '''
            SELECT * FROM reservasi 
            WHERE ruangan = %s 
            AND tanggal = %s 
            AND status != 'Ditolak'
            AND (
                (waktu_mulai <= %s AND waktu_selesai > %s) OR
                (waktu_mulai < %s AND waktu_selesai >= %s) OR
                (waktu_mulai >= %s AND waktu_selesai <= %s)
            )
            '''
            print("[DEBUG] Cek bentrok...")
            cursor.execute(query, (
                ruangan, tanggal,
                waktu_mulai, waktu_mulai,
                waktu_selesai, waktu_selesai,
                waktu_mulai, waktu_selesai
            ))
            if cursor.fetchone():
                flash("Ruangan sudah terisi pada waktu tersebut!", "danger")
                return redirect(url_for('ajukan_reservasi'))

            # Modified INSERT query
            insert_query = '''
            INSERT INTO reservasi (
                nip, ruangan, tanggal, waktu_mulai, waktu_selesai, keperluan, 
                status, waktu_pengajuan, lampiran
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            '''
            waktu_pengajuan = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Modified execute with lampiran
            cursor.execute(insert_query, (
                nip, ruangan, tanggal, waktu_mulai, waktu_selesai, keperluan,
                'Menunggu', waktu_pengajuan, lampiran_filename
            ))
            conn.commit()
            conn.close()

            flash("Reservasi berhasil diajukan!", "success")

            # Kirim notifikasi ke semua admin
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT nama, no_wa FROM pegawai WHERE role = 'admin'")
            admin_list = cursor.fetchall()
            conn.close()

            for admin in admin_list:
                if admin['no_wa']:
                    pesan_admin = (
                        f"[NOTIFIKASI RESERVASI BARU]\n\n"
                        f"Ada pengajuan reservasi dari {session['nama']}:\n"
                        f"- Ruangan: {ruangan}\n"
                        f"- Tanggal: {tanggal}\n"
                        f"- Waktu: {waktu_mulai} - {waktu_selesai}\n"
                        f"- Keperluan: {keperluan}\n\n"
                        f"Silakan periksa dan setujui/tolak melalui panel admin."
                    )
                    kirim_wa(admin['no_wa'], pesan_admin)

            return redirect(url_for('dashboard_pegawai'))

        except Exception as e:
            print("[ERROR RESERVASI]:", e)
            flash("Terjadi kesalahan saat mengajukan reservasi.", "danger")
            return redirect(url_for('ajukan_reservasi'))

    return render_template('ajukan_reservasi.html')

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
        return redirect(url_for('kelola_reservasi'))  # <--- redirect ke kelola_reservasi

    # Update status menjadi Ditolak
    cursor.execute("UPDATE reservasi SET status = 'Ditolak' WHERE id = %s", (id,))
    conn.commit()
    conn.close()

    # Kirim WA jika nomor tersedia
    pesan = (
        f"Hai, {data['nama']}.\n\n"
        f"Reservasi Anda untuk ruang *{data['ruangan']}* pada "
        f"{data['tanggal']} pukul {data['waktu_mulai']} - {data['waktu_selesai']} "
        f"telah *DITOLAK* oleh admin.\n\n"
        f"Silakan ajukan kembali dengan waktu atau ruangan lain."
    )

    if data.get('no_wa'):
        kirim_wa(data['no_wa'], pesan)
    else:
        print("[INFO] Nomor WhatsApp kosong, tidak mengirim WA.")

    flash('Reservasi ditolak & notifikasi dikirim.', 'success')
    return redirect(url_for('kelola_reservasi'))  # <--- redirect ke kelola_reservasi

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
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT r.id, p.nama, r.ruangan as nama_ruangan, r.tanggal, r.waktu_mulai, r.waktu_selesai, r.keperluan as kegiatan, r.status
        FROM reservasi r
        JOIN pegawai p ON r.nip = p.nip
        ORDER BY r.tanggal DESC, r.waktu_mulai DESC
    """)
    reservasi = cursor.fetchall()
    conn.close()

    return render_template('kelola_reservasi.html', reservasi=reservasi)

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
    return redirect(url_for('dashboard_admin'))

@app.route('/kirim-pengingat-sekarang', methods=['POST'])
@admin_required
def kirim_pengingat_sekarang():
    jumlah = kirim_notifikasi_otomatis()
    flash(f'Notifikasi pengingat dikirim ke {jumlah} pegawai.', 'success')
    return redirect(url_for('kelola_reservasi'))

@app.route('/kirim-pengingat-terpilih', methods=['POST'])
@admin_required
def kirim_pengingat_terpilih():
    ids = request.form.getlist('ids')
    if not ids:
        flash('Tidak ada reservasi yang dipilih.', 'danger')
        return redirect(url_for('kelola_reservasi'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    format_strings = ','.join(['%s'] * len(ids))
    cursor.execute(f"""
        SELECT r.*, p.nama, p.no_wa
        FROM reservasi r
        JOIN pegawai p ON r.nip = p.nip
        WHERE r.id IN ({format_strings}) AND r.status = 'Disetujui'
    """, tuple(ids))
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    jumlah_dikirim = 0
    for row in data:
        pesan = (
            f"Hai, {row['nama']}!\n\n"
            f"Ini adalah pengingat bahwa Anda memiliki jadwal di ruang *{row['ruangan']}* "
            f"pada {row['tanggal']} pukul {row['waktu_mulai']} - {row['waktu_selesai']}.\n\n"
            f"> _Dikirim oleh adm. KOMNAS HAM RI_"
        )
        if row['no_wa']:
            kirim_wa(row['no_wa'], pesan)
            jumlah_dikirim += 1

    flash(f'Pengingat dikirim ke {jumlah_dikirim} pegawai.', 'success')
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

def jadwal_pagi_kirim_notifikasi():
    with app.app_context():
        kirim_notifikasi_otomatis()

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

if __name__ == '__main__':
    app.run(debug=True)
