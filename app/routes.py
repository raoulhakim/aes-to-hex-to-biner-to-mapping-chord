import os
from flask import render_template, flash, redirect, url_for, request, send_file
from werkzeug.utils import secure_filename
from datetime import datetime
from app import app
from app.utils.aes_utils import encrypt_aes, decrypt_aes
from app.utils.audio_utils import binary_to_audio, extract_binary_from_audio

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
            
            # Buat audio steganografi
            output_filename = binary_to_audio(ciphertext_hex, 
                                             app.config['UPLOAD_FOLDER'], 
                                             app.config['CHORD_FOLDER'])
            
            # Tampilkan hasil
            return render_template('encrypt_result.html', 
                                  title='Hasil Enkripsi',
                                  plaintext=plaintext,
                                  key=key,
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
            # Ekstrak hex dari file audio
            hex_string = extract_binary_from_audio(filepath)
            
            # Dekripsi hex
            decrypted_text = decrypt_aes(hex_string, key)
            
            # Tampilkan hasil
            return render_template('decrypt_result.html',
                                  title='Hasil Dekripsi',
                                  decrypted_text=decrypted_text,
                                  key=key,
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