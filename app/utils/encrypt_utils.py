import os
import binascii
import numpy as np
import json
import struct
import wave
import uuid
import logging
from scipy.io import wavfile
from Crypto.Cipher import AES
import time

# Setup logging
logger = logging.getLogger(__name__)

# Pemetaan biner ke nama file chord
binary_to_chord = {
    "00": "C-PianoChord.wav",
    "01": "D-PianoChord.wav", 
    "10": "E-PianoChord.wav",
    "11": "G-PianoChord.wav"
}

# Definisi pola lagu Mary Had a Little Lamb dengan nada dan ketukan
mary_had_a_little_lamb = [
    ("E", 1.6), ("D", 0.5), ("C", 1.0), ("D", 1.0), ("E", 1), ("E", 1.0), ("E", 2.2),
    ("D", 1.0), ("D", 1.0), ("D", 2.4), ("E", 1.0), ("G", 1.0), ("G", 2.2),
    ("E", 1.6), ("D", 0.5), ("C", 1.0), ("D", 1.0), ("E", 1), ("E", 1.0), ("E", 1.0),
    ("C", 1.1), ("D", 1.1), ("D", 1.1), ("E", 1.1), ("D", 1.1), ("C", 2.2)
]

def pad_text(plaintext):
    """Menambahkan padding pada plaintext agar panjangnya kelipatan 16."""
    padding_length = 16 - (len(plaintext) % 16)
    logger.info(f"[PAD_TEXT] Plaintext asli: '{plaintext}' dengan panjang {len(plaintext)}")
    logger.info(f"[PAD_TEXT] Menambahkan padding sebanyak {padding_length} karakter")
    return plaintext + (chr(padding_length) * padding_length)

def encrypt_aes(plaintext, key):
    """Mengenkripsi plaintext menggunakan AES."""
    logger.info("\n" + "="*50)
    logger.info("[ENCRYPT_AES] Memulai proses enkripsi AES")
    logger.info(f"[ENCRYPT_AES] Plaintext: '{plaintext}'")
    logger.info(f"[ENCRYPT_AES] Kunci: '{key}'")
    
    # Validasi panjang kunci - harus persis 16 karakter
    if len(key) != 16:
        raise ValueError(f"Panjang kunci harus 16 karakter, bukan {len(key)}.")
    
    # Padding plaintext
    padded_text = pad_text(plaintext)
    logger.info(f"[ENCRYPT_AES] Plaintext dengan padding: '{padded_text}'")
    
    # Inisialisasi cipher
    cipher = AES.new(key.encode(), AES.MODE_ECB)
    logger.info(f"[ENCRYPT_AES] Cipher AES diinisialisasi dengan mode ECB")
    
    # Enkripsi
    ciphertext = cipher.encrypt(padded_text.encode())
    logger.info(f"[ENCRYPT_AES] Plaintext berhasil dienkripsi")
    
    # Konversi ke hex
    ciphertext_hex = binascii.hexlify(ciphertext).decode()
    logger.info(f"[ENCRYPT_AES] Ciphertext (hex): {ciphertext_hex}")
    logger.info("="*50 + "\n")
    
    return ciphertext_hex

def hex_to_binary(hex_string):
    """Mengkonversi string hex ke string biner."""
    logger.info(f"[HEX_TO_BINARY] Mengkonversi hex: {hex_string}")
    binary = bin(int(hex_string, 16))[2:]
    
    # Pastikan panjang biner adalah kelipatan 2
    if len(binary) % 2 != 0:
        binary = '0' + binary
        logger.info(f"[HEX_TO_BINARY] Menambahkan '0' di awal untuk memastikan panjang kelipatan 2")
    
    logger.info(f"[HEX_TO_BINARY] Hasil konversi ke biner: {binary}")
    logger.info(f"[HEX_TO_BINARY] Panjang biner: {len(binary)} bit")
    return binary

def map_binary_to_chords(binary_string):
    """Memetakan string biner ke daftar nama file chord."""
    logger.info(f"[MAP_BINARY] Memetakan string biner: {binary_string}")
    chord_files = []
    
    # Pastikan panjang string biner adalah kelipatan 2
    if len(binary_string) % 2 != 0:
        binary_string = '0' + binary_string
        logger.info(f"[MAP_BINARY] Menambahkan '0' di awal biner untuk memastikan panjang kelipatan 2")
    
    # Pemetakan setiap 2 bit ke chord yang sesuai
    for i in range(0, len(binary_string), 2):
        binary_segment = binary_string[i:i+2]
        chord_file = binary_to_chord.get(binary_segment)
        if chord_file:
            chord_files.append(chord_file)
            logger.info(f"[MAP_BINARY] Segmen '{binary_segment}' dipetakan ke chord '{chord_file}'")
    
    logger.info(f"[MAP_BINARY] Total {len(chord_files)} chord dihasilkan")
    return chord_files

def prepare_song_with_binary(binary_string):
    """Menyiapkan pola lagu dengan memetakan segmen biner ke nada yang ditentukan."""
    logger.info("\n" + "="*50)
    logger.info(f"[PREPARE_SONG] Memulai persiapan pola lagu dengan biner: {binary_string[:20]}...")
    
    # Bagi binary string menjadi segmen 2-bit
    binary_segments = [binary_string[i:i+2] for i in range(0, len(binary_string), 2)]
    logger.info(f"[PREPARE_SONG] Binary string dibagi menjadi {len(binary_segments)} segmen 2-bit")
    
    # Membuat mapping dari segmen biner ke nada
    binary_to_note = {}
    for binary, chord_file in binary_to_chord.items():
        note = chord_file.split('-')[0]  # Misalnya, "C" dari "C-PianoChord.wav"
        binary_to_note[binary] = note
    
    logger.info(f"[PREPARE_SONG] Mapping biner ke nada: {binary_to_note}")
    
    # Definisi pola lagu Mary Had a Little Lamb
    melody_notes = [note for note, _ in mary_had_a_little_lamb]
    melody_durations = [duration for _, duration in mary_had_a_little_lamb]
    melody_length = len(melody_notes)
    logger.info(f"[PREPARE_SONG] Total {melody_length} nada dalam pola lagu asli")
    
    # Inisialisasi variabel untuk hasil
    song_pattern = []
    chord_positions_by_index = [None] * len(binary_segments)
    position_mapping = {}
    
    # Variabel untuk melacak iterasi
    iteration = 0
    iterations_data = []  # Menyimpan data tentang setiap iterasi
    
    # Proses semua segmen biner
    current_segment_index = 0
    
    while current_segment_index < len(binary_segments):
        # Coba cari di iterasi yang sudah ada terlebih dahulu
        segment_mapped = False
        binary_segment = binary_segments[current_segment_index]
        target_note = binary_to_note.get(binary_segment)
        
        # Cek di semua iterasi yang sudah ada
        for iter_idx, iter_data in enumerate(iterations_data):
            positions_used = iter_data['positions_used']
            iter_notes = iter_data['notes']
            start_pos = iter_data['start_pos']
            
            # Cari posisi yang cocok dan belum digunakan
            for pos, note in enumerate(iter_notes):
                if note == target_note and not positions_used[pos]:
                    # Posisi ditemukan di iterasi yang sudah ada
                    absolute_position = start_pos + pos
                    positions_used[pos] = True  # Tandai posisi ini sudah digunakan
                    
                    # Simpan mapping
                    chord_positions_by_index[current_segment_index] = absolute_position
                    position_mapping[absolute_position] = {
                        "binary": binary_segment,
                        "note": note,
                        "iteration": iter_idx,
                        "relative_position": pos,
                        "segment_index": current_segment_index
                    }
                    
                    logger.info(f"[PREPARE_SONG] Memetakan '{binary_segment}' \u2192 Nada {note} di posisi {pos} (absolut: {absolute_position}, segmen_idx: {current_segment_index}) [MENGISI POSISI KOSONG DI ITERASI {iter_idx+1}]")
                    
                    segment_mapped = True
                    break
            
            if segment_mapped:
                break
        
        # Jika tidak menemukan posisi di iterasi yang ada, buat iterasi baru
        if not segment_mapped:
            # Tambahkan jeda antar iterasi kecuali di putaran pertama
            if iteration > 0:
                logger.info(f"[PREPARE_SONG] Menambahkan jeda setelah iterasi ke-{iteration}")
                song_pattern.append(("PAUSE", 4.0, None))
            
            logger.info(f"[PREPARE_SONG] Memulai iterasi ke-{iteration+1}")
            
            # Posisi awal absolut untuk iterasi ini
            iteration_start_pos = len(song_pattern)
            
            # Buat array untuk melacak posisi yang sudah digunakan
            positions_used = [False] * len(melody_notes)
            
            # Simpan informasi iterasi ini
            iterations_data.append({
                'start_pos': iteration_start_pos,
                'positions_used': positions_used,
                'notes': melody_notes.copy()
            })
            
            # Cari posisi yang cocok di iterasi baru ini
            position_found = False
            for pos, note in enumerate(melody_notes):
                if note == target_note:
                    # Posisi ditemukan
                    absolute_position = iteration_start_pos + pos
                    positions_used[pos] = True  # Tandai posisi ini sudah digunakan
                    
                    # Simpan mapping
                    chord_positions_by_index[current_segment_index] = absolute_position
                    position_mapping[absolute_position] = {
                        "binary": binary_segment,
                        "note": note,
                        "iteration": iteration,
                        "relative_position": pos,
                        "segment_index": current_segment_index
                    }
                    
                    logger.info(f"[PREPARE_SONG] Memetakan '{binary_segment}' \u2192 Nada {note} di posisi {pos} (absolut: {absolute_position}, segmen_idx: {current_segment_index})")
                    
                    position_found = True
                    break
            
            if not position_found:
                logger.warning(f"[PREPARE_SONG] Tidak menemukan posisi untuk segmen '{binary_segment}' di iterasi baru, ini tidak seharusnya terjadi!")
                # Skip segmen ini jika tidak menemukan posisi (seharusnya tidak terjadi)
                current_segment_index += 1
                continue
            
            # Buat pola lagu untuk iterasi ini
            for pos, note in enumerate(melody_notes):
                absolute_pos = iteration_start_pos + pos
                is_used = positions_used[pos]
                
                if is_used:
                    segment_info = position_mapping.get(absolute_pos)
                    bin_segment = segment_info.get("binary") if segment_info else None
                    song_pattern.append((note, melody_durations[pos], bin_segment))
                else:
                    song_pattern.append((note, melody_durations[pos], None))
            
            # Debug info
            logger.info(f"[PREPARE_SONG] Iterasi {iteration+1}: Berhasil memetakan 1 segmen biner")
            logger.info(f"[PREPARE_SONG] Total kemajuan: {current_segment_index+1}/{len(binary_segments)} segmen")
            
            # Verifikasi pola melodi untuk debug
            pattern_notes = [item[0] for item in song_pattern[-melody_length:] if item[0] != "PAUSE"]
            logger.info("[PREPARE_SONG] Pola melodi dalam iterasi ini:")
            logger.info(f"[PREPARE_SONG] Pola aktual: {', '.join([str(n) for n in pattern_notes if n is not None])}")
            logger.info(f"[PREPARE_SONG] Pola asli: {', '.join([str(n) for n in melody_notes])}")
            
            iteration += 1
        
        # Lanjut ke segmen berikutnya
        current_segment_index += 1
        
        # Keamanan agar tidak loop tanpa akhir
        if iteration > 100:
            logger.error("[PREPARE_SONG] Terlalu banyak iterasi, menghentikan proses.")
            break
    
    logger.info(f"[PREPARE_SONG] Pola lagu selesai dibuat dengan {len(song_pattern)} nada")
    logger.info(f"[PREPARE_SONG] Lagu diulang sebanyak {iteration} kali")
    logger.info(f"[PREPARE_SONG] Total {current_segment_index}/{len(binary_segments)} segmen biner berhasil dipetakan")
    
    # Bangun daftar chord_positions sesuai urutan asli segmen biner
    chord_positions = [pos for pos in chord_positions_by_index if pos is not None]
    
    # Tulis urutan chord position sesuai indeks segmen untuk debugging
    logger.info(f"[PREPARE_SONG] Urutan segmen biner (untuk debugging): {binary_segments[:10]}...")
    logger.info(f"[PREPARE_SONG] Chord positions (ordered by segment index): {chord_positions}")
    logger.info("="*50 + "\n")
    
    return song_pattern, chord_positions, position_mapping

def generate_music_from_prepared_song(song_pattern, chord_dir):
    """Membuat musik dari pola lagu yang telah disiapkan dengan biner."""
    logger.info("\n" + "="*50)
    logger.info("[GENERATE_MUSIC] Memulai pembuatan musik dari pola lagu")
    sample_rate = 44100
    audio_segments = []
    note_positions = [0]
    position = 0
    
    # Debug: Tampilkan pola lagu yang akan diproses
    logger.info("[GENERATE_MUSIC] Pola lagu yang akan diproses:")
    current_iteration = 0
    iteration_start = 0
    
    for i, (note, duration, binary) in enumerate(song_pattern):
        if note == "PAUSE":
            logger.info(f"[GENERATE_MUSIC] --- Akhir iterasi {current_iteration+1} ---")
            # Bandingkan dengan pola Mary Had a Little Lamb
            if i > iteration_start:
                original_pattern = ", ".join([f"{note}" for note, _ in mary_had_a_little_lamb])
                actual_pattern = ", ".join([f"{note}" for note, _, _ in song_pattern[iteration_start:i]])
                logger.info(f"[GENERATE_MUSIC] Pola asli: {original_pattern}")
                logger.info(f"[GENERATE_MUSIC] Pola aktual: {actual_pattern}")
            
            iteration_start = i + 1
            current_iteration += 1
        else:
            logger.info(f"[GENERATE_MUSIC] Nada {i}: {note} (durasi {duration}, biner {binary})")
    
    # Selalu gunakan mono untuk ukuran file yang lebih kecil
    channels = 1  # Tetapkan channels ke 1 (mono) untuk semua audio
    logger.info(f"[GENERATE_MUSIC] Menggunakan format audio mono untuk menghemat ukuran file")
    
    logger.info(f"[GENERATE_MUSIC] Memproses {len(song_pattern)} nada dalam pola lagu")
    
    # Verifikasi jika pola sesuai dengan Mary Had a Little Lamb
    # Jika tidak ada nada dalam pola pertama, gunakan pola Mary Had a Little Lamb asli
    first_iteration_empty = True
    for i, (note, duration, binary) in enumerate(song_pattern):
        if note == "PAUSE":
            break
        if note != "PAUSE":
            first_iteration_empty = False
    
    # Jika tidak ada nada yang dimainkan dalam iterasi pertama, gunakan pola asli
    if first_iteration_empty:
        logger.warning("[GENERATE_MUSIC] PERINGATAN: Iterasi pertama kosong, menggunakan pola lagu asli")
        # Buat mapping sederhana dari nada ke biner
        note_to_binary = {"C": "00", "D": "01", "E": "10", "G": "11"}
        # Tambahkan pola lagu asli ke awal song_pattern
        original_pattern = [(note, duration, note_to_binary.get(note, "00")) 
                           for note, duration in mary_had_a_little_lamb]
        song_pattern = original_pattern + song_pattern
    
    # Iterasi melalui pola lagu
    for i, (note, duration, binary) in enumerate(song_pattern):
        # Jika ini adalah jeda, tambahkan keheningan
        if note == "PAUSE":
            # Tambahkan keheningan sesuai durasi
            pause_duration = int(sample_rate * 0.5 * duration)  # 0.5 detik per unit durasi
            logger.info(f"[GENERATE_MUSIC] Menambahkan jeda dengan durasi {duration} unit ({pause_duration/sample_rate:.2f} detik)")
            
            # Buat keheningan mono
            silence = np.zeros(pause_duration, dtype=np.int16)
                
            audio_segments.append(silence)
            
            # Catat posisi untuk position_data
            note_positions.append(position + len(silence))
            position += len(silence)
            continue
            
        # Tentukan file chord berdasarkan nada
        chord_prefix = note
        chord_filename = f"{chord_prefix}-PianoChord.wav"
        chord_path = os.path.join(chord_dir, chord_filename)
        
        if not os.path.exists(chord_path):
            # Coba gunakan file alternatif berdasarkan binary mapping
            chord_filename = binary_to_chord.get(binary, "C-PianoChord.wav")  # Default ke C jika tidak ada
            chord_path = os.path.join(chord_dir, chord_filename)
            logger.warning(f"[GENERATE_MUSIC] File chord untuk nada {note} tidak ditemukan, menggunakan alternatif: {chord_filename}")
            
            if not os.path.exists(chord_path):
                logger.warning(f"[GENERATE_MUSIC] PERINGATAN: File chord alternatif juga tidak ditemukan, melewati nada ini")
                continue
        
        try:
            # Baca file chord
            rate, audio = wavfile.read(chord_path)
            
            # Konversi stereo ke mono jika diperlukan
            if len(audio.shape) > 1:  # Jika stereo
                audio = np.mean(audio, axis=1).astype(np.int16)  # Konversi ke mono dengan mengambil rata-rata
                logger.info(f"[GENERATE_MUSIC] Mengkonversi audio stereo ke mono untuk {chord_filename}")
            
            logger.info(f"[GENERATE_MUSIC] Membaca chord: {chord_filename} (rate={rate}Hz, panjang={len(audio)})")
            
            # Hitung durasi berdasarkan ketukan (1.0 = 0.5 detik)
            beat_duration = int(sample_rate * 0.5 * duration)
            
            # Sesuaikan audio dengan durasi
            if len(audio) > beat_duration:
                adjusted_audio = audio[:beat_duration]
                logger.info(f"[GENERATE_MUSIC] Memotong audio ke durasi {duration} unit ({beat_duration/sample_rate:.2f} detik)")
            else:
                # Buat padding mono
                padding = np.zeros(beat_duration - len(audio), dtype=audio.dtype)
                adjusted_audio = np.concatenate([audio, padding])
                logger.info(f"[GENERATE_MUSIC] Menambahkan padding ke audio untuk durasi {duration} unit ({beat_duration/sample_rate:.2f} detik)")
            
            # Catat posisi untuk position_data
            note_positions.append(position + len(adjusted_audio))
            position += len(adjusted_audio)
            
            # Tambahkan ke segmen audio
            audio_segments.append(adjusted_audio)
            
        except Exception as e:
            logger.error(f"[GENERATE_MUSIC] Error saat membaca {chord_path}: {e}")
    
    if not audio_segments:
        raise ValueError("Tidak ada segmen audio yang valid!")
    
    # Gabungkan semua segmen audio
    try:
        combined_audio = np.concatenate(audio_segments)
        logger.info(f"[GENERATE_MUSIC] Berhasil menggabungkan {len(audio_segments)} segmen audio")
        logger.info(f"[GENERATE_MUSIC] Total durasi audio: {len(combined_audio)/sample_rate:.2f} detik")
        logger.info(f"[GENERATE_MUSIC] Format audio: mono (1 channel)")
        logger.info("="*50 + "\n")
        return combined_audio, sample_rate, note_positions
    except ValueError as e:
        raise ValueError(f"Error saat menggabungkan audio: {e}")

def binary_to_audio(hex_string, output_dir="app/static/uploads", chord_dir="Chord"):
    """Fungsi utama untuk konversi hex ke audio steganografi."""
    logger.info("\n" + "="*50)
    logger.info("[BINARY_TO_AUDIO] Memulai konversi hex ke audio steganografi")
    logger.info(f"[BINARY_TO_AUDIO] Hex string: {hex_string[:20]}... (panjang: {len(hex_string)})")
    
    # Konversi hex ke biner
    binary = hex_to_binary(hex_string)
    
    # Debug - log binary string yang akan digunakan
    logger.info(f"[BINARY_TO_AUDIO] Binary string yang akan digunakan: {binary}")
    logger.info(f"[BINARY_TO_AUDIO] Panjang binary string: {len(binary)} bit")
    
    # Log segmen 2-bit untuk debugging
    binary_segments = [binary[i:i+2] for i in range(0, len(binary), 2)]
    logger.info(f"[BINARY_TO_AUDIO] Segmen 2-bit: {binary_segments[:10]}... (total {len(binary_segments)} segmen)")
    
    # Siapkan pola lagu berdasarkan segmen biner
    song_pattern, chord_positions, position_mapping = prepare_song_with_binary(binary)
    
    # Buat audio dari pola lagu
    output_filename = f"stegano_{uuid.uuid4().hex[:8]}.wav"
    output_path = os.path.join(output_dir, output_filename)
    
    # Pastikan direktori output ada
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate musik dan simpan ke file
    audio_data, sample_rate, note_positions = generate_music_from_prepared_song(song_pattern, chord_dir)
    
    # Simpan file audio
    wavfile.write(output_path, sample_rate, audio_data)
    logger.info(f"[BINARY_TO_AUDIO] Audio berhasil disimpan ke: {output_path}")
    
    # Format kunci dekripsi yang dikembalikan ke routes.py
    decryption_key = {
        "chord_positions": chord_positions,
        "chord_positions_str": ",".join(map(str, chord_positions))
    }
    
    # Hitung jumlah iterasi lagu dari song_pattern
    iteration_count = 1  # Minimal 1 iterasi
    for note, _, _ in song_pattern:
        if note == "PAUSE":
            iteration_count += 1
    
    logger.info(f"[BINARY_TO_AUDIO] Nama file output: {output_filename}")
    logger.info("[BINARY_TO_AUDIO] Proses konversi hex ke audio steganografi selesai")
    logger.info(f"[BINARY_TO_AUDIO] Lagu Mary Had a Little Lamb diulang sebanyak {iteration_count} kali")
    logger.info(f"[BINARY_TO_AUDIO] PENTING: Password kedua (posisi chord): {chord_positions}")
    logger.info("[BINARY_TO_AUDIO] Pastikan pengguna menyimpan posisi chord ini untuk dekripsi!")
    logger.info("="*50 + "\n")
    
    return output_filename, decryption_key 