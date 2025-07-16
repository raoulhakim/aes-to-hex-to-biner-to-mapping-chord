import os
from flask import render_template, flash, redirect, url_for, request, send_file, send_from_directory
from werkzeug.utils import secure_filename
from datetime import datetime
from app import app
from app.utils.encrypt_utils import encrypt_aes, binary_to_audio
from app.utils.decrypt_utils import decrypt_aes, get_decrypted_hex_from_audio
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
    return render_template('index.html', title='Steganografi Audio AES')

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
            # Enkripsi pesan
            ciphertext_hex = encrypt_aes(plaintext, key)
            
            # Buat audio steganografi dan dapatkan Kunci Audio
            output_filename, decryption_data = binary_to_audio(ciphertext_hex, 
                                             key,
                                             app.config['UPLOAD_FOLDER'], 
                                             app.config['CHORD_FOLDER'])
            
            # Ekstrak Kunci Audio untuk ditampilkan ke pengguna
            audio_key = decryption_data.get("audio_key")
            
            return render_template('encrypt_result.html', 
                                  title='Hasil Enkripsi',
                                  plaintext=plaintext,
                                  key=key,
                                  audio_key=audio_key,
                                  audio_file=output_filename)
                                  
        except Exception as e:
            flash(f'Error saat enkripsi: {str(e)}', 'danger')
            return redirect(url_for('encrypt'))
            
    return render_template('encrypt.html', title='Enkripsi Pesan')

@app.route('/decrypt', methods=['GET', 'POST'])
def decrypt():
    if request.method == 'POST':
        if 'audio_file' not in request.files:
            flash('Tidak ada file yang dipilih.', 'warning')
            return redirect(request.url)
        
        file = request.files['audio_file']
        key = request.form.get('key')
        audio_key = request.form.get('audio_key') # Kunci baru dari pengguna
        
        if file.filename == '':
            flash('Tidak ada file yang dipilih.', 'warning')
            return redirect(request.url)
        
        if not all([file, key, audio_key]):
            flash('Semua kolom (File Audio, Kunci AES, Kunci Audio) harus diisi.', 'warning')
            return redirect(request.url)

        try:
            filename = secure_filename(file.filename)
            audio_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(audio_path)
            
            # 1. Dapatkan ciphertext hex menggunakan alur verifikasi baru
            ciphertext_hex = get_decrypted_hex_from_audio(audio_path, key, audio_key)
            
            # 2. Dekripsi pesan dari ciphertext
            decrypted_message = decrypt_aes(ciphertext_hex, key)
            
            # 3. Hapus file metadata setelah berhasil
            metadata_path = os.path.splitext(audio_path)[0] + '_metadata.json'
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
            
            # Mendapatkan timestamp saat ini
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            return render_template('decrypt_result.html', 
                                   title='Hasil Dekripsi',
                                   decrypted_text=decrypted_message,
                                   key=key,
                                   audio_key=audio_key,
                                   timestamp=timestamp)

        except (ValueError, FileNotFoundError) as e:
            flash(f'Error dekripsi: {str(e)}', 'danger')
        except Exception as e:
            flash(f'Terjadi error yang tidak terduga: {str(e)}', 'danger')
        
        # Jika terjadi error, alihkan kembali ke halaman dekripsi
        return redirect(url_for('decrypt'))

    return render_template('decrypt.html', title='Dekripsi')

@app.route('/download/<filename>')
def download_file(filename):
    """Mengunduh file audio hasil enkripsi."""
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename),
                    as_attachment=True,
                    download_name=filename)

@app.route('/about')
def about():
    """Halaman informasi tentang aplikasi."""
    return render_template('about.html', title='Tentang Aplikasi')

# Rute untuk halaman admin log viewer
@app.route('/admin/logs')
def admin_logs():
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
    
    return render_template('admin_logs.html', logs=logs) 