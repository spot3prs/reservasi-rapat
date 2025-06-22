-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jun 15, 2025 at 10:40 AM
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
  `nip` varchar(18) NOT NULL,
  `password` varchar(100) NOT NULL,
  `nama` varchar(100) DEFAULT NULL,
  `no_wa` varchar(20) DEFAULT NULL,
  `role` enum('pegawai','admin') NOT NULL DEFAULT 'pegawai'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `pegawai`
--

INSERT INTO `pegawai` (`id`, `nip`, `password`, `nama`, `no_wa`, `role`) VALUES
(1, '199009032019031001', 'pratama030903', 'Pratama, Komnas HAM', '6281290097308', 'admin'),
(2, '199812122020101002', '1122', 'daffa, Komnas HAM', '6285774451688', 'pegawai'),
(3, '199707152021041003', '918871', 'arif, Komnas HAM', '6285771735834', 'pegawai'),
(4, '199511282022021004', 'reza123', 'reza, Komnas HAM', '62895324876603', 'pegawai'),
(5, '199403192019121005', 'Ari123', 'Ari, Komnas HAM', '6281808075566', 'pegawai'),
(6, '199206102018071006', 'dipa123', 'dipa, Komnas HAM', '6281546850859', 'pegawai'),
(8, '199511202020101007', 'gilang123', 'gilang, Komnas HAM', '6285814530903', 'pegawai'),
(10, '199305112021051008', '12345', 'Arbi, Komnas HAM ', '6285887524049', 'pegawai'),
(11, '199101012017121009', '12345', 'Ridwan, FOTOCOPY', '6281219183725', 'pegawai'),
(12, '444444444444444444', '12345', 'Rira,pantry', '6281381710344', 'pegawai'),
(23, '432', '12345', 'nama', '6281290097308', 'pegawai');

-- --------------------------------------------------------

--
-- Table structure for table `pengajuan_akun`
--

CREATE TABLE `pengajuan_akun` (
  `id` int(11) NOT NULL,
  `nip` varchar(18) NOT NULL,
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
(10, '66666666', 'Ridwan, FOTOCOPY', '6281219183725', 'arip mau ngetest', 'Disetujui', '2025-06-02 16:24:25', '20250602_162425_ridwan.pdf'),
(11, '34563', 'fufufafa', '6281290097308', 'Pengajuan akun baru.', 'Menunggu', '2025-06-10 00:23:23', NULL),
(12, '432', 'nama', '6281290097308', 'Pengajuan akun baru.', 'Disetujui', '2025-06-10 00:28:49', NULL),
(16, '444444444444444444', 'Rira,pantry', '6281381710344', 'Pengajuan akun baru.', 'Disetujui', '2025-06-10 15:48:51', 'surat_anak_pantry.pdf'),
(17, '123456789123456789', 'dipa,baru', '6282211522242', 'Pengajuan akun baru.', 'Ditolak', '2025-06-12 00:14:06', 'surat_pengajuan_123456789123456789.pdf'),
(18, '123456789123456789', 'dipa, baruuu', '6282211522242', 'Pengajuan akun baru.', 'Ditolak', '2025-06-12 00:19:53', 'surat_pengajuan_123456789123456789-2.pdf');

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
(80, '199511282022021004', 'Ruang Rapat Kelompok', '2025-06-11', '16:00:00', '16:45:00', 'coba', 'Disetujui', '2025-06-11 15:28:19', 0, 0, NULL),
(82, '199206102018071006', 'Ruang Rapat Kelompok', '2025-06-12', '10:00:00', '15:00:00', 'rapat dengan BPK', 'Ditolak', '2025-06-11 23:53:12', 0, 0, NULL),
(83, '199403192019121005', 'Ruang Rapat Pleno 1', '2025-06-12', '16:30:00', '17:30:00', 'tes', 'Disetujui', '2025-06-12 16:23:58', 0, 0, NULL),
(84, '199511202020101007', 'Ruang Rapat Pleno 2', '2025-06-13', '10:00:00', '12:00:00', 'tes tgl 13', 'Disetujui', '2025-06-12 16:33:55', 0, 0, NULL),
(85, '199305112021051008', 'Ruang Rapat Pleno 2', '2025-06-13', '13:00:00', '15:00:00', 'coba tgl 13', 'Disetujui', '2025-06-12 16:35:21', 0, 0, NULL),
(86, '199707152021041003', 'Ruang Rapat Pleno 2', '2025-06-13', '16:00:00', '18:00:00', 'coba tgl 13.', 'Disetujui', '2025-06-12 16:36:27', 0, 0, NULL),
(87, '199812122020101002', 'Ruang Rapat Kelompok', '2025-06-14', '10:00:00', '12:00:00', 'magang', 'Disetujui', '2025-06-13 23:21:48', 0, 0, NULL),
(89, '199812122020101002', 'Ruang Rapat Kelompok', '2025-06-15', '13:00:00', '10:00:00', 'au dah', 'Disetujui', '2025-06-13 23:24:45', 0, 0, NULL),
(90, '199812122020101002', 'Ruang Rapat Pleno 2', '2025-06-15', '12:00:00', '15:00:00', 'magang', 'Disetujui', '2025-06-13 23:32:22', 0, 0, '20250613_233222_219_D_ERP_Pratama_Rafli_Syachdan_pert6.pdf');

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
  ADD UNIQUE KEY `nip` (`nip`),
  ADD UNIQUE KEY `nip_2` (`nip`);

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
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=24;

--
-- AUTO_INCREMENT for table `pengajuan_akun`
--
ALTER TABLE `pengajuan_akun`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19;

--
-- AUTO_INCREMENT for table `reservasi`
--
ALTER TABLE `reservasi`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=91;

--
-- AUTO_INCREMENT for table `ruangan`
--
ALTER TABLE `ruangan`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
