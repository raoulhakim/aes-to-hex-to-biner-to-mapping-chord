import os
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
            
            # Buat audio steganografi dan dapatkan chord positions
            output_filename, decryption_key = binary_to_audio(ciphertext_hex, 
                                             app.config['UPLOAD_FOLDER'], 
                                             app.config['CHORD_FOLDER'])
            
            # Ekstrak chord positions untuk password kedua
            chord_positions = decryption_key.get("chord_positions", [])
            chord_positions_str = ",".join(map(str, chord_positions))
            
            # Tampilkan hasil
            return render_template('encrypt_result.html', 
                                  title='Hasil Enkripsi',
                                  plaintext=plaintext,
                                  key=key,
                                  chord_positions=chord_positions_str,
                                  audio_file=output_filename)
                                  
        except Exception as e:
            flash(f'Error saat enkripsi: {str(e)}', 'danger')
            return redirect(url_for('encrypt'))
            
    return render_template('encrypt.html', title='Enkripsi Pesan')

@app.route('/decrypt', methods=['GET', 'POST'])
def decrypt():
    """Halaman dekripsi audio."""
    if request.method == 'POST':
        key = request.form.get('key', '')
        chord_positions = request.form.get('chord_positions', '')
        
        # Validasi key
        if not key or len(key) != 16:
            flash('Kunci dekripsi harus tepat 16 karakter.', 'warning')
            return redirect(url_for('decrypt'))
            
        # Validasi chord positions
        if not chord_positions or chord_positions.strip() == '':
            flash('Posisi chord (password kedua) harus diisi.', 'warning')
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
            # Ekstrak hex dari file audio (dengan chord positions yang diwajibkan)
            hex_string = extract_binary_from_audio(filepath, chord_positions)
            
            # Dekripsi hex
            decrypted_text = decrypt_aes(hex_string, key)
            
            # Tampilkan hasil
            return render_template('decrypt_result.html',
                                  title='Hasil Dekripsi',
                                  decrypted_text=decrypted_text,
                                  key=key,
                                  chord_positions=chord_positions,
                                  timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                                  
        except Exception as e:
            flash(f'Error saat dekripsi: {str(e)}', 'danger')
            return redirect(url_for('decrypt'))
            
    return render_template('decrypt.html', title='Dekripsi Audio')

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
    
    return render_template('admin_logs.html', logs=logs) 