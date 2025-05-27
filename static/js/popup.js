// popup.js

document.addEventListener('DOMContentLoaded', function () {
    const popups = document.querySelectorAll('.popup');

    popups.forEach(function (popup) {
        // Tampilkan popup selama 4 detik lalu hilangkan
        setTimeout(function () {
            popup.classList.add('fade-out');
            // Hapus elemen dari DOM setelah transisi selesai
            setTimeout(function () {
                popup.remove();
            }, 1000);
        }, 4000);
    });
});
