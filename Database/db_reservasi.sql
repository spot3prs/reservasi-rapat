-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jun 05, 2025 at 03:58 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `db_reservasi`
--

-- --------------------------------------------------------

--
-- Table structure for table `pegawai`
--

CREATE TABLE `pegawai` (
  `id` int(11) NOT NULL,
  `nip` varchar(20) NOT NULL,
  `password` varchar(100) NOT NULL,
  `nama` varchar(100) DEFAULT NULL,
  `no_wa` varchar(20) DEFAULT NULL,
  `role` enum('pegawai','admin') DEFAULT 'pegawai'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `pegawai`
--

INSERT INTO `pegawai` (`id`, `nip`, `password`, `nama`, `no_wa`, `role`) VALUES
(1, '12345', 'pratama030903', 'Pratama, Komnas HAM', '6281290097308', 'admin'),
(2, '987654321987654321', 'daffa123', 'daffa, Komnas HAM', '6285774451688', 'pegawai'),
(3, '00000000', '918871', 'arif, Komnas HAM', '6285771735834', 'pegawai'),
(4, '11111111', 'reza123', 'reza, Komnas HAM', '62895324876603', 'pegawai'),
(5, '22222222', 'Ari123', 'Ari, Komnas HAM', '6281808075566', 'pegawai'),
(6, '33333333', 'dipa123', 'dipa, Komnas HAM', '6281546850859', 'pegawai'),
(8, '54321', 'gilang123', 'gilang, Komnas HAM', '6285814530903', 'pegawai'),
(10, '77777', '12345', 'Arbi, Komnas HAM ', '6285887524049', 'pegawai'),
(11, '66666666', '12345', 'Ridwan, FOTOCOPY', '6281219183725', 'pegawai');

-- --------------------------------------------------------

--
-- Table structure for table `pengajuan_akun`
--

CREATE TABLE `pengajuan_akun` (
  `id` int(11) NOT NULL,
  `nip` varchar(20) NOT NULL,
  `nama` varchar(100) NOT NULL,
  `no_wa` varchar(20) NOT NULL,
  `isi_surat` text NOT NULL,
  `status` enum('Menunggu','Disetujui','Ditolak') DEFAULT 'Menunggu',
  `tanggal_pengajuan` datetime DEFAULT current_timestamp(),
  `file_surat` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `pengajuan_akun`
--

INSERT INTO `pengajuan_akun` (`id`, `nip`, `nama`, `no_wa`, `isi_surat`, `status`, `tanggal_pengajuan`, `file_surat`) VALUES
(9, '77777', 'Arbi, Komnas HAM ', '6285887524049', 'test aju', 'Disetujui', '2025-05-29 17:14:57', '20250529_171457_surat_tes.pdf'),
(10, '66666666', 'Ridwan, FOTOCOPY', '6281219183725', 'arip mau ngetest', 'Disetujui', '2025-06-02 16:24:25', '20250602_162425_ridwan.pdf');

-- --------------------------------------------------------

--
-- Table structure for table `reservasi`
--

CREATE TABLE `reservasi` (
  `id` int(11) NOT NULL,
  `nip` varchar(20) DEFAULT NULL,
  `ruangan` varchar(100) DEFAULT NULL,
  `tanggal` date DEFAULT NULL,
  `waktu_mulai` time DEFAULT NULL,
  `waktu_selesai` time DEFAULT NULL,
  `keperluan` text DEFAULT NULL,
  `status` varchar(20) DEFAULT 'Menunggu',
  `waktu_pengajuan` datetime DEFAULT current_timestamp(),
  `notifikasi_dikirim` tinyint(1) DEFAULT 0,
  `notifikasi_terkirim` tinyint(1) DEFAULT 0,
  `lampiran` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `reservasi`
--

INSERT INTO `reservasi` (`id`, `nip`, `ruangan`, `tanggal`, `waktu_mulai`, `waktu_selesai`, `keperluan`, `status`, `waktu_pengajuan`, `notifikasi_dikirim`, `notifikasi_terkirim`, `lampiran`) VALUES
(56, '987654321987654321', 'Ruang Rapat Utama', '2025-05-25', '22:30:00', '23:30:00', 'coba yah yah yah', 'Disetujui', '2025-05-25 22:02:06', 0, 0, NULL),
(57, '00000000', 'Ruang Rapat Pleno 1', '2025-05-25', '23:00:00', '23:50:00', 'hai nak', 'Disetujui', '2025-05-25 22:42:15', 0, 0, NULL),
(58, '00000000', 'Ruang Rapat Kelompok', '2025-05-27', '09:00:00', '12:00:00', 'ngadem', 'Ditolak', '2025-05-26 12:14:29', 0, 0, NULL),
(59, '987654321987654321', 'Ruang Rapat Pleno 2', '2025-05-26', '15:00:00', '16:00:00', 'gagal tombol aksi disetujui', 'Disetujui', '2025-05-26 13:58:49', 0, 0, NULL),
(60, '00000000', 'Ruang Rapat Kelompok', '2025-05-26', '15:30:00', '16:00:00', 'tes tombol aksi gagal setujui', 'Disetujui', '2025-05-26 14:02:57', 0, 0, NULL),
(61, '987654321987654321', 'Ruang Rapat Utama', '2025-05-28', '12:00:00', '14:00:00', 'coba notif ke no admin', 'Ditolak', '2025-05-27 23:02:55', 0, 0, NULL),
(62, '00000000', 'Ruang Rapat Utama', '2025-06-02', '10:00:00', '12:00:00', 'coba jam 09:00', 'Disetujui', '2025-06-01 23:31:35', 0, 0, '219_D_ERP_Pratama_Rafli_Syachdan_pert5.pdf'),
(63, '33333333', 'Ruang Rapat Pleno 2', '2025-06-02', '13:00:00', '15:00:00', 'jam 09:00\r\n', 'Disetujui', '2025-06-01 23:33:54', 0, 0, '219_D_ERP_Pratama_Rafli_Syachdan_pert6.pdf'),
(64, '987654321987654321', 'Ruang Rapat Pleno 1', '2025-06-03', '23:30:00', '23:50:00', 'tidur di ruangan rapat', 'Ditolak', '2025-06-03 23:08:02', 0, 0, NULL),
(65, '987654321987654321', 'Ruang Rapat Pleno 1', '2025-06-03', '23:35:00', '23:45:00', 'ff yu', 'Disetujui', '2025-06-03 23:17:48', 0, 0, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `ruangan`
--

CREATE TABLE `ruangan` (
  `id` int(11) NOT NULL,
  `nama` varchar(100) NOT NULL,
  `lokasi` varchar(100) NOT NULL,
  `kapasitas` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `ruangan`
--

INSERT INTO `ruangan` (`id`, `nama`, `lokasi`, `kapasitas`) VALUES
(1, 'Ruang Rapat Utama', 'Lantai 2', 30),
(2, 'Ruang Rapat Pleno 1', 'Lantai 3', 20),
(3, 'Ruang Rapat Pleno 2', 'Lantai 3', 30),
(4, 'Ruang Rapat Kelompok', 'Lantai 3', 15);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `pegawai`
--
ALTER TABLE `pegawai`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `nip` (`nip`);

--
-- Indexes for table `pengajuan_akun`
--
ALTER TABLE `pengajuan_akun`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `reservasi`
--
ALTER TABLE `reservasi`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `ruangan`
--
ALTER TABLE `ruangan`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `pegawai`
--
ALTER TABLE `pegawai`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT for table `pengajuan_akun`
--
ALTER TABLE `pengajuan_akun`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `reservasi`
--
ALTER TABLE `reservasi`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=66;

--
-- AUTO_INCREMENT for table `ruangan`
--
ALTER TABLE `ruangan`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
