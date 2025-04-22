# Noiseless Steganografi Audio dengan Enkripsi AES

<p align="center">
  <img src="app/static/img/logo.svg" alt="Logo Noiseless Steganografi" width="300">
</p>

Aplikasi web untuk menyembunyikan pesan rahasia dalam file audio menggunakan teknik steganografi "noiseless" dan enkripsi AES. Aplikasi ini menghasilkan file audio yang terdengar natural dan musikal, menyembunyikan fakta bahwa audio tersebut mengandung pesan tersembunyi.

## ✨ Fitur Utama

- **Enkripsi AES-128** - Keamanan pesan menggunakan algoritma enkripsi standar industri
- **Pemetaan Musikal** - Konversi data terenkripsi ke nada musik dengan pola lagu "Mary Had a Little Lamb"
- **Steganografi Noiseless** - Output berupa musik yang terdengar natural, bukan noise yang mencurigakan
- **Antarmuka Web** - Interface berbasis web yang intuitif dan mudah digunakan
- **Visualisasi Proses** - Progress bar dengan perkiraan waktu untuk enkripsi dan dekripsi

## 🛠️ Teknologi

- **Backend**: Python, Flask
- **Enkripsi**: PyCryptodome (AES-128 ECB)
- **Manipulasi Audio**: NumPy, SciPy
- **Frontend**: HTML, CSS, JavaScript, Bootstrap

## 🚀 Instalasi

### Persiapan

```bash
# Clone repository
git clone https://github.com/raoulhakim/aes-to-hex-to-biner-to-mapping-chord.git

# Install dependencies
pip install -r requirements.txt
```

### Menjalankan Aplikasi

```bash
python run.py
```

Aplikasi akan berjalan di `http://127.0.0.1:5000/`

## 📋 Cara Penggunaan

### Enkripsi Pesan

1. Buka halaman "Enkripsi"
2. Masukkan pesan yang ingin dienkripsi
3. Masukkan kunci enkripsi (tepat 16 karakter)
4. Klik "Enkripsi & Buat Audio"
5. Tunggu hingga proses selesai
6. Download file audio yang berisi pesan tersembunyi

### Dekripsi Pesan

1. Buka halaman "Dekripsi"
2. Upload file audio yang berisi pesan tersembunyi
3. Masukkan kunci yang sama dengan yang digunakan untuk enkripsi
4. Klik "Dekripsi Audio"
5. Tunggu hingga proses selesai
6. Pesan asli akan ditampilkan pada halaman hasil

## 🗂️ Struktur Project

```
noiseless-steganografi/
├── app/                        # Folder utama aplikasi
│   ├── static/                 # Asset statis (CSS, JS, gambar)
│   ├── templates/              # Template HTML
│   ├── utils/                  # Utilitas untuk enkripsi/dekripsi
│   ├── __init__.py            # Inisialisasi aplikasi Flask
│   └── routes.py              # Route dan handler aplikasi
├── Chord/                      # Data audio untuk chord
├── run.py                      # Script untuk menjalankan aplikasi
└── requirements.txt            # Dependencies Python
```

## 🔒 Catatan Keamanan

- Kunci enkripsi harus dijaga kerahasiaannya
- Untuk keamanan maksimal, gunakan kunci yang kompleks dan unik
- Aplikasi ini dibuat untuk tujuan edukasi dan demonstrasi

## 📊 Batasan

- Panjang pesan optimal: 2000-5000 karakter
- Kunci enkripsi harus tepat 16 karakter karena AES-128
