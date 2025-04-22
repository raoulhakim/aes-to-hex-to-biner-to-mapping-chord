/**
 * main.js - Fitur-fitur JavaScript dasar untuk aplikasi Noiseless Steganografi
 */

document.addEventListener('DOMContentLoaded', function() {
    // Animasi logo saat halaman dimuat
    const logo = document.querySelector('.app-logo');
    if (logo) {
        logo.style.transition = 'transform 0.5s ease-in-out';
        logo.style.transform = 'scale(1.1)';
        
        setTimeout(() => {
            logo.style.transform = 'scale(1)';
        }, 300);
    }
    
    // Tooltips Bootstrap (jika diperlukan nanti)
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}); 