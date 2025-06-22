# Black Box Testing - Sistem Reservasi Ruangan Rapat

## 1. Autentikasi dan Manajemen Akun

### 1.1 Login
| ID | Test Case | Input | Expected Output | Status |
|----|-----------|-------|----------------|--------|
| TC-1.1.1 | Login dengan kredensial valid | Username: admin, Password: admin123 | Berhasil login dan redirect ke dashboard admin | |
| TC-1.1.2 | Login dengan kredensial invalid | Username: admin, Password: wrongpass | Pesan error "Username atau password salah" | |
| TC-1.1.3 | Login dengan field kosong | Username: "", Password: "" | Pesan error "Username dan password harus diisi" | |
| TC-1.1.4 | Login dengan username kosong | Username: "", Password: admin123 | Pesan error "Username harus diisi" | |
| TC-1.1.5 | Login dengan password kosong | Username: admin, Password: "" | Pesan error "Password harus diisi" | |

### 1.2 Pengajuan Akun
| ID | Test Case | Input | Expected Output | Status |
|----|-----------|-------|----------------|--------|
| TC-1.2.1 | Pengajuan akun dengan data valid | Nama: John Doe, Email: john@example.com, Jabatan: Staff IT | Berhasil mengajukan akun, status pending | |
| TC-1.2.2 | Pengajuan akun dengan email sudah terdaftar | Nama: Jane Doe, Email: admin@example.com, Jabatan: Staff HR | Pesan error "Email sudah terdaftar" | |
| TC-1.2.3 | Pengajuan akun dengan field kosong | Semua field kosong | Pesan error "Semua field harus diisi" | |
| TC-1.2.4 | Pengajuan akun dengan format email invalid | Nama: John Doe, Email: invalid-email, Jabatan: Staff IT | Pesan error "Format email tidak valid" | |

### 1.3 Kelola Pengajuan Akun (Admin)
| ID | Test Case | Input | Expected Output | Status |
|----|-----------|-------|----------------|--------|
| TC-1.3.1 | Menyetujui pengajuan akun | Klik tombol "Setuju" pada pengajuan | Status berubah menjadi "Disetujui" | |
| TC-1.3.2 | Menolak pengajuan akun | Klik tombol "Tolak" pada pengajuan | Status berubah menjadi "Ditolak" | |
| TC-1.3.3 | Melihat detail pengajuan | Klik tombol "Lihat" pada pengajuan | Menampilkan detail pengajuan | |
| TC-1.3.4 | Filter pengajuan berdasarkan status | Pilih filter "Pending" | Menampilkan hanya pengajuan dengan status pending | |

## 2. Manajemen Reservasi

### 2.1 Pengajuan Reservasi
| ID | Test Case | Input | Expected Output | Status |
|----|-----------|-------|----------------|--------|
| TC-2.1.1 | Pengajuan reservasi dengan data valid | Ruangan: Meeting A, Tanggal: 20/03/2024, Waktu: 09:00-11:00 | Berhasil mengajukan reservasi | |
| TC-2.1.2 | Pengajuan reservasi dengan ruangan sudah dipesan | Ruangan: Meeting A, Tanggal: 20/03/2024, Waktu: 09:00-11:00 | Pesan error "Ruangan sudah dipesan pada waktu tersebut" | |
| TC-2.1.3 | Pengajuan reservasi dengan tanggal lampau | Ruangan: Meeting A, Tanggal: 01/01/2024, Waktu: 09:00-11:00 | Pesan error "Tanggal tidak valid" | |
| TC-2.1.4 | Pengajuan reservasi dengan waktu tidak valid | Ruangan: Meeting A, Tanggal: 20/03/2024, Waktu: 23:00-01:00 | Pesan error "Waktu tidak valid" | |

### 2.2 Kelola Reservasi (Admin)
| ID | Test Case | Input | Expected Output | Status |
|----|-----------|-------|----------------|--------|
| TC-2.2.1 | Menyetujui reservasi | Klik tombol "Setuju" pada reservasi | Status berubah menjadi "Disetujui" | |
| TC-2.2.2 | Menolak reservasi | Klik tombol "Tolak" pada reservasi | Status berubah menjadi "Ditolak" | |
| TC-2.2.3 | Melihat detail reservasi | Klik tombol "Lihat" pada reservasi | Menampilkan detail reservasi | |
| TC-2.2.4 | Filter reservasi berdasarkan status | Pilih filter "Pending" | Menampilkan hanya reservasi dengan status pending | |

### 2.3 Daftar Reservasi (Pegawai)
| ID | Test Case | Input | Expected Output | Status |
|----|-----------|-------|----------------|--------|
| TC-2.3.1 | Melihat daftar reservasi | Klik menu "Daftar Reservasi" | Menampilkan daftar reservasi yang diajukan | |
| TC-2.3.2 | Filter reservasi berdasarkan status | Pilih filter "Disetujui" | Menampilkan hanya reservasi yang disetujui | |
| TC-2.3.3 | Mencari reservasi | Masukkan kata kunci pencarian | Menampilkan reservasi yang sesuai dengan kata kunci | |

## 3. Manajemen Ruangan

### 3.1 Tambah Ruangan (Admin)
| ID | Test Case | Input | Expected Output | Status |
|----|-----------|-------|----------------|--------|
| TC-3.1.1 | Menambah ruangan dengan data valid | Nama: Meeting C, Kapasitas: 20 | Berhasil menambah ruangan | |
| TC-3.1.2 | Menambah ruangan dengan nama sudah ada | Nama: Meeting A, Kapasitas: 15 | Pesan error "Nama ruangan sudah ada" | |
| TC-3.1.3 | Menambah ruangan dengan field kosong | Nama: "", Kapasitas: "" | Pesan error "Semua field harus diisi" | |
| TC-3.1.4 | Menambah ruangan dengan kapasitas invalid | Nama: Meeting D, Kapasitas: -5 | Pesan error "Kapasitas harus lebih dari 0" | |

### 3.2 Edit Ruangan (Admin)
| ID | Test Case | Input | Expected Output | Status |
|----|-----------|-------|----------------|--------|
| TC-3.2.1 | Mengedit ruangan dengan data valid | Nama: Meeting A, Kapasitas: 25 | Berhasil mengedit ruangan | |
| TC-3.2.2 | Mengedit ruangan dengan nama sudah ada | Nama: Meeting B, Kapasitas: 15 | Pesan error "Nama ruangan sudah ada" | |
| TC-3.2.3 | Mengedit ruangan dengan field kosong | Nama: "", Kapasitas: "" | Pesan error "Semua field harus diisi" | |

## 4. Laporan

### 4.1 Generate Laporan PDF
| ID | Test Case | Input | Expected Output | Status |
|----|-----------|-------|----------------|--------|
| TC-4.1.1 | Generate laporan dengan filter tanggal | Tanggal awal: 01/03/2024, Tanggal akhir: 31/03/2024 | File PDF berhasil diunduh | |
| TC-4.1.2 | Generate laporan tanpa filter | Klik "Generate Laporan" | File PDF berhasil diunduh dengan semua data | |
| TC-4.1.3 | Generate laporan dengan tanggal tidak valid | Tanggal awal: 31/03/2024, Tanggal akhir: 01/03/2024 | Pesan error "Tanggal tidak valid" | |

### 4.2 Lihat Jadwal
| ID | Test Case | Input | Expected Output | Status |
|----|-----------|-------|----------------|--------|
| TC-4.2.1 | Melihat jadwal dengan filter ruangan | Pilih ruangan: Meeting A | Menampilkan jadwal untuk ruangan tersebut | |
| TC-4.2.2 | Melihat jadwal dengan filter tanggal | Pilih tanggal: 20/03/2024 | Menampilkan jadwal untuk tanggal tersebut | |
| TC-4.2.3 | Melihat jadwal tanpa filter | Klik "Lihat Jadwal" | Menampilkan semua jadwal | |

## 5. Navigasi dan UI

### 5.1 Navigasi Menu
| ID | Test Case | Input | Expected Output | Status |
|----|-----------|-------|----------------|--------|
| TC-5.1.1 | Navigasi ke dashboard admin | Klik menu "Dashboard" | Berhasil menampilkan dashboard admin | |
| TC-5.1.2 | Navigasi ke dashboard pegawai | Klik menu "Dashboard" | Berhasil menampilkan dashboard pegawai | |
| TC-5.1.3 | Logout | Klik tombol "Logout" | Berhasil logout dan redirect ke halaman login | |

### 5.2 Responsivitas
| ID | Test Case | Input | Expected Output | Status |
|----|-----------|-------|----------------|--------|
| TC-5.2.1 | Tampilan di desktop | Buka di browser desktop | Layout sesuai dengan desain | |
| TC-5.2.2 | Tampilan di tablet | Buka di browser tablet | Layout menyesuaikan ukuran layar | |
| TC-5.2.3 | Tampilan di mobile | Buka di browser mobile | Layout menyesuaikan ukuran layar | |