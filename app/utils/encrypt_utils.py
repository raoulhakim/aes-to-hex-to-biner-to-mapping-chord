import os
import binascii
import numpy as np
import json
import struct
import wave
import uuid
import logging
import hashlib
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
    
    if len(key) != 16:
        raise ValueError(f"Panjang kunci harus 16 karakter, bukan {len(key)}.")
    
    padded_text = pad_text(plaintext)
    logger.info(f"[ENCRYPT_AES] Plaintext dengan padding: '{padded_text}'")
    
    cipher = AES.new(key.encode(), AES.MODE_ECB)
    logger.info(f"[ENCRYPT_AES] Cipher AES diinisialisasi dengan mode ECB")
    
    ciphertext = cipher.encrypt(padded_text.encode())
    logger.info(f"[ENCRYPT_AES] Plaintext berhasil dienkripsi")
    
    ciphertext_hex = binascii.hexlify(ciphertext).decode()
    logger.info(f"[ENCRYPT_AES] Ciphertext (hex): {ciphertext_hex}")
    logger.info("="*50 + "\n")
    
    return ciphertext_hex

def hex_to_binary(hex_string):
    """Mengkonversi string hex ke string biner."""
    logger.info(f"[HEX_TO_BINARY] Mengkonversi hex: {hex_string}")
    binary = bin(int(hex_string, 16))[2:]
    if len(binary) % 2 != 0:
        binary = '0' + binary
    logger.info(f"[HEX_TO_BINARY] Hasil konversi ke biner: {binary}")
    logger.info(f"[HEX_TO_BINARY] Panjang biner: {len(binary)} bit")
    return binary

def prepare_song_with_binary(binary_string):
    """Menyiapkan pola lagu dengan memetakan segmen biner ke nada yang ditentukan."""
    logger.info("\n" + "="*50)
    logger.info(f"[PREPARE_SONG] Memulai persiapan pola lagu dengan biner: {binary_string[:20]}...")
    
    binary_segments = [binary_string[i:i+2] for i in range(0, len(binary_string), 2)]
    logger.info(f"[PREPARE_SONG] Binary string dibagi menjadi {len(binary_segments)} segmen 2-bit")
    
    binary_to_note = {binary: chord_file.split('-')[0] for binary, chord_file in binary_to_chord.items()}
    logger.info(f"[PREPARE_SONG] Mapping biner ke nada: {binary_to_note}")
    
    melody_notes = [note for note, _ in mary_had_a_little_lamb]
    melody_durations = [duration for _, duration in mary_had_a_little_lamb]
    melody_length = len(melody_notes)
    
    song_pattern = []
    chord_positions_by_index = [None] * len(binary_segments)
    
    iteration = 0
    iterations_data = []
    current_segment_index = 0
    
    while current_segment_index < len(binary_segments):
        segment_mapped = False
        binary_segment = binary_segments[current_segment_index]
        target_note = binary_to_note.get(binary_segment)
        
        for iter_idx, iter_data in enumerate(iterations_data):
            positions_used = iter_data['positions_used']
            start_pos = iter_data['start_pos']
            
            for pos, note in enumerate(iter_data['notes']):
                if note == target_note and not positions_used[pos]:
                    chord_idx_position = start_pos + pos
                    positions_used[pos] = True
                    chord_positions_by_index[current_segment_index] = chord_idx_position
                    segment_mapped = True
                    break
            if segment_mapped:
                break
        
        if not segment_mapped:
            if iteration > 0:
                song_pattern.append(("PAUSE", 4.0, None))
            
            iteration_start_pos = len(song_pattern)
            positions_used = [False] * melody_length
            
            iterations_data.append({
                'start_pos': iteration_start_pos,
                'positions_used': positions_used,
                'notes': melody_notes.copy()
            })
            
            position_found = False
            for pos, note in enumerate(melody_notes):
                if note == target_note:
                    chord_idx_position = iteration_start_pos + pos
                    positions_used[pos] = True
                    chord_positions_by_index[current_segment_index] = chord_idx_position
                    position_found = True
                    break
            
            if not position_found:
                current_segment_index += 1
                continue
            
            for pos, note in enumerate(melody_notes):
                bin_segment_for_note = binary_segment if positions_used[pos] else None
                song_pattern.append((note, melody_durations[pos], bin_segment_for_note))
            
            iteration += 1
        
        current_segment_index += 1

    chord_positions = [pos for pos in chord_positions_by_index if pos is not None]
    logger.info(f"[PREPARE_SONG] Pola lagu selesai. Total nada: {len(song_pattern)}, Perulangan: {iteration}")
    logger.info("="*50 + "\n")
    return song_pattern, chord_positions, {}

def generate_music_from_prepared_song(song_pattern, chord_dir):
    """Membuat musik dari pola lagu yang telah disiapkan dengan biner."""
    logger.info("\n" + "="*50)
    logger.info("[GENERATE_MUSIC] Memulai pembuatan musik dari pola lagu")
    sample_rate = 44100
    audio_segments = []

    nonce = os.urandom(16)
    nonce_samples = np.frombuffer(nonce, dtype=np.int16) // 20
    audio_segments.append(nonce_samples)
    logger.info(f"[GENERATE_MUSIC] Nonce unik disematkan ke audio.")

    for note, duration, _ in song_pattern:
        if note == "PAUSE":
            pause_duration = int(sample_rate * 0.5 * duration)
            audio_segments.append(np.zeros(pause_duration, dtype=np.int16))
            continue
            
        chord_filename = f"{note}-PianoChord.wav"
        chord_path = os.path.join(chord_dir, chord_filename)
        
        if not os.path.exists(chord_path):
            logger.warning(f"[GENERATE_MUSIC] File chord {chord_path} tidak ditemukan, dilewati.")
            continue
        
        try:
            rate, audio = wavfile.read(chord_path)
            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=1).astype(np.int16)
            
            beat_duration = int(sample_rate * 0.5 * duration)
            
            if len(audio) > beat_duration:
                adjusted_audio = audio[:beat_duration]
            else:
                padding = np.zeros(beat_duration - len(audio), dtype=audio.dtype)
                adjusted_audio = np.concatenate([audio, padding])
            
            audio_segments.append(adjusted_audio)
        except Exception as e:
            logger.error(f"[GENERATE_MUSIC] Error saat memproses {chord_path}: {e}")
    
    if not audio_segments:
        raise ValueError("Gagal membuat segmen audio.")
    
    combined_audio = np.concatenate(audio_segments)
    logger.info(f"[GENERATE_MUSIC] Audio berhasil digabungkan. Total durasi: {len(combined_audio)/sample_rate:.2f}s")
    logger.info("="*50 + "\n")
    return combined_audio, sample_rate, []

def create_audio_fingerprint(file_path):
    """Membaca bagian dari file audio dan membuat hash unik sebagai fingerprint."""
    try:
        samplerate, data = wavfile.read(file_path)
        chunk_size = 4096
        if len(data) < chunk_size:
            data_sample = data.tobytes()
        else:
            start_chunk = data[:chunk_size].tobytes()
            end_chunk = data[-chunk_size:].tobytes()
            data_sample = start_chunk + end_chunk
        fingerprint = hashlib.sha256(data_sample).hexdigest()[:16]
        logger.info(f"[FINGERPRINT_AUDIO] Fingerprint audio dibuat dari {file_path}: {fingerprint}")
        return fingerprint
    except Exception as e:
        logger.error(f"[FINGERPRINT_AUDIO] Gagal membuat fingerprint audio: {e}")
        raise IOError(f"Tidak dapat membuat fingerprint dari file audio: {e}")

def binary_to_audio(hex_string, key, output_dir="app/static/uploads", chord_dir="Chord"):
    """Fungsi utama untuk konversi hex ke audio steganografi."""
    logger.info("\n" + "="*50)
    logger.info("[BINARY_TO_AUDIO] Memulai konversi hex ke audio steganografi")
    
    ciphertext_binary = hex_to_binary(hex_string)
    _, temp_chord_positions, _ = prepare_song_with_binary(ciphertext_binary)
    
    temp_chord_positions_str = ",".join(map(str, temp_chord_positions))
    combined_key = key + temp_chord_positions_str
    internal_fingerprint_hex = hashlib.sha256(combined_key.encode()).hexdigest()[:8]
    internal_fingerprint_binary = bin(int(internal_fingerprint_hex, 16))[2:].zfill(32)
    logger.info(f"[BINARY_TO_AUDIO] Generated internal fingerprint: {internal_fingerprint_hex}")

    binary_with_fingerprint = internal_fingerprint_binary + ciphertext_binary
    final_song_pattern, final_chord_positions, _ = prepare_song_with_binary(binary_with_fingerprint)
    final_chord_positions_str = ",".join(map(str, final_chord_positions))

    audio_data, sample_rate, _ = generate_music_from_prepared_song(final_song_pattern, chord_dir)
    
    output_filename = f"stegano_{uuid.uuid4().hex[:8]}.wav"
    output_path = os.path.join(output_dir, output_filename)
    os.makedirs(output_dir, exist_ok=True)
    wavfile.write(output_path, sample_rate, audio_data)
    logger.info(f"[BINARY_TO_AUDIO] Audio berhasil disimpan ke: {output_path}")

    try:
        audio_key = create_audio_fingerprint(output_path)
    except IOError as e:
        logger.error(f"[BINARY_TO_AUDIO] Gagal menghasilkan Kunci Audio: {e}")
        raise

    logger.info(f"[BINARY_TO_AUDIO] PENTING: Kunci Audio (Password 2): {audio_key}")

    metadata_filename = os.path.splitext(output_path)[0] + '_metadata.json'
    with open(metadata_filename, 'w') as f:
        json.dump({
            'internal_fingerprint': internal_fingerprint_hex,
            'chord_positions': final_chord_positions_str
        }, f)
    logger.info(f"[BINARY_TO_AUDIO] Metadata dekripsi disimpan ke: {metadata_filename}")

    return output_filename, { "audio_key": audio_key } 