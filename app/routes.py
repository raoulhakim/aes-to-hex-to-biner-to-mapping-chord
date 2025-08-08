import os
import time
from flask import render_template, flash, redirect, url_for, request, send_file, send_from_directory
from werkzeug.utils import secure_filename
from datetime import datetime
from app import app
from app.utils.encrypt_utils import encrypt_aes, binary_to_audio
from app.utils.decrypt_utils import decrypt_aes, extract_binary_from_audio
import json
import logging

# Konfigurasi logging
logging.basicConfig(
    filename='logs/app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a'
)

def allowed_file(filename):
    """Memeriksa apakah file yang diunggah diizinkan."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['wav']

@app.route('/')
def index():
    """Halaman utama aplikasi."""
    return render_template('index.html', title='Steganografi Audio AES', now=datetime.now())

@app.route('/encrypt', methods=['GET', 'POST'])
def encrypt():
    """Halaman enkripsi pesan."""
    if request.method == 'POST':
        plaintext = request.form.get('plaintext', '')
        key = request.form.get('key', '')
        
        # Validasi input
        if not plaintext:
            flash('Silakan masukkan pesan yang akan dienkripsi.', 'warning')
            return redirect(url_for('encrypt'))
            
        if not key or len(key) != 16:
            flash('Kunci enkripsi harus tepat 16 karakter.', 'warning')
            return redirect(url_for('encrypt'))
            
        try:
            # Mulai timing untuk proses enkripsi
            start_time = time.time()
            
            # Enkripsi pesan
            ciphertext_hex = encrypt_aes(plaintext, key)
            
            # Buat audio steganografi dan dapatkan chord positions
            output_filename, decryption_key = binary_to_audio(ciphertext_hex, key,
                                             app.config['UPLOAD_FOLDER'], 
                                             app.config['CHORD_FOLDER'])
            
            # Hitung waktu eksekusi
            end_time = time.time()
            execution_time = end_time - start_time
            seconds = int(execution_time)
            milliseconds = int((execution_time - seconds) * 1000)
            
            # Log untuk debug dengan timing
            logging.info(f"Enkripsi berhasil: pesan={plaintext}, kunci={key}, file={output_filename}")
            logging.info(f"Password AES dan chord positions: {decryption_key['aes_password']}, {decryption_key['chord_positions_str']}")
            logging.info(f"Waktu eksekusi enkripsi: {seconds}.{milliseconds:03d} detik")
            
            # Tampilkan hasil dengan kedua password
            return render_template('encrypt_result.html', 
                                  title='Hasil Enkripsi',
                                  plaintext=plaintext,
                                  aes_password=decryption_key['aes_password'],
                                  chord_positions=decryption_key['chord_positions_str'],
                                  audio_file=output_filename,
                                  now=datetime.now())
                                  
        except Exception as e:
            logging.error(f"Error saat enkripsi: {str(e)}")
            flash(f'Error saat enkripsi: {str(e)}', 'danger')
            return redirect(url_for('encrypt'))
            
    return render_template('encrypt.html', title='Enkripsi Pesan', now=datetime.now())

@app.route('/decrypt', methods=['GET', 'POST'])
def decrypt():
    """Halaman dekripsi audio."""
    if request.method == 'POST':
        key = request.form.get('key', '')
        
        # Validasi key
        if not key or len(key) != 16:
            flash('Kunci dekripsi harus tepat 16 karakter.', 'warning')
            return redirect(url_for('decrypt'))
            
        # Memeriksa apakah file audio yang diunggah valid
        if 'audio_file' not in request.files:
            flash('Tidak ada file yang diunggah.', 'warning')
            return redirect(url_for('decrypt'))
            
        file = request.files['audio_file']
        
        if file.filename == '':
            flash('Tidak ada file yang dipilih.', 'warning')
            return redirect(url_for('decrypt'))
            
        if not allowed_file(file.filename):
            flash('Hanya file WAV yang diizinkan.', 'warning')
            return redirect(url_for('decrypt'))
            
        # Simpan file yang diunggah
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Mulai timing untuk proses dekripsi
            start_time = time.time()
            
            # Baca metadata password AES (MD5) dari file
            from app.utils.decrypt_utils import read_metadata_from_wav
            import hashlib
            
            # Baca metadata password AES dari file
            stored_aes_md5 = read_metadata_from_wav(filepath)
            if not stored_aes_md5:
                flash('File audio tidak valid atau tidak memiliki metadata password AES.', 'danger')
                return redirect(url_for('decrypt'))
            
            # Validasi password AES dengan MD5
            input_aes_md5 = hashlib.md5(key.encode()).hexdigest()
            if stored_aes_md5 != input_aes_md5:
                flash('Password AES tidak sesuai dengan file audio.', 'danger')
                return redirect(url_for('decrypt'))
            
            # Ambil chord positions dari input user
            chord_positions = request.form.get('chord_positions', '')
            if not chord_positions:
                flash('Chord positions (password kedua) harus disediakan.', 'warning')
                return redirect(url_for('decrypt'))
            
            # Ekstrak hex dari file audio menggunakan chord positions
            hex_string = extract_binary_from_audio(filepath, chord_positions)
            
            # Dekripsi hex
            decrypted_text = decrypt_aes(hex_string, key)
            
            # Hitung waktu eksekusi
            end_time = time.time()
            execution_time = end_time - start_time
            seconds = int(execution_time)
            milliseconds = int((execution_time - seconds) * 1000)
            
            # Log untuk debug dengan timing
            logging.info(f"Dekripsi berhasil: file={filename}, kunci={key}")
            logging.info(f"Waktu eksekusi dekripsi: {seconds}.{milliseconds:03d} detik")
            
            # Tampilkan hasil
            return render_template('decrypt_result.html',
                                  title='Hasil Dekripsi',
                                  decrypted_text=decrypted_text,
                                  key=key,
                                  timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                  now=datetime.now())
                                  
        except Exception as e:
            logging.error(f"Error saat dekripsi: {str(e)}")
            flash(f'Error saat dekripsi: {str(e)}', 'danger')
            return redirect(url_for('decrypt'))
            
    return render_template('decrypt.html', title='Dekripsi Audio', now=datetime.now())

@app.route('/download/<filename>')
def download_file(filename):
    """Mengunduh file audio hasil enkripsi."""
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename),
                    as_attachment=True,
                    download_name=filename)

@app.route('/about')
def about():
    """Halaman informasi tentang aplikasi."""
    return render_template('about.html', title='Tentang Aplikasi', now=datetime.now())

# Rute untuk halaman admin log viewer
@app.route('/admin/logs')
def view_logs():
    log_file = 'logs/app.log'
    
    # Periksa apakah file log ada
    if not os.path.exists(log_file):
        with open(log_file, 'w') as f:
            f.write("# Log file initialized #\n")
    
    # Baca isi file log
    try:
        with open(log_file, 'r') as f:
            logs = f.readlines()
            # Ambil 3000 baris 
            if len(logs) > 3000:
                logs = logs[-3000:]
    except Exception as e:
        logs = [f"Error membaca log: {str(e)}"]
    
    return render_template('admin_logs.html', logs=logs, title='Log Admin', now=datetime.now()) 