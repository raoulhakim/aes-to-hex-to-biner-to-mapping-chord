import os
import wave
import struct
import json
import binascii
import numpy as np
import logging
from scipy.io import wavfile
from Crypto.Cipher import AES

# Setup logging
logger = logging.getLogger(__name__)

# Pemetaan biner ke nama file chord untuk referensi saat dekripsi
binary_to_chord = {
    "00": "C-PianoChord.wav",
    "01": "D-PianoChord.wav", 
    "10": "E-PianoChord.wav",
    "11": "G-PianoChord.wav"
}

# Pemetaan nama chord ke biner
chord_to_binary = {chord_name.split("-")[0]: binary for binary, chord_name in binary_to_chord.items()}

# Definisi pola lagu Mary Had a Little Lamb dengan nada dan ketukan
mary_had_a_little_lamb = [
    ("E", 1.6), ("D", 0.5), ("C", 1.0), ("D", 1.0), ("E", 1), ("E", 1.0), ("E", 2.2),
    ("D", 1.0), ("D", 1.0), ("D", 2.4), ("E", 1.0), ("G", 1.0), ("G", 2.2),
    ("E", 1.6), ("D", 0.5), ("C", 1.0), ("D", 1.0), ("E", 1), ("E", 1.0), ("E", 1.0),
    ("C", 1.1), ("D", 1.1), ("D", 1.1), ("E", 1.1), ("D", 1.1), ("C", 2.2)
]

def binary_to_hex(binary_string):
    """Mengkonversi string biner ke string hex."""
    logger.info("\n" + "="*50)
    logger.info(f"[BINARY_TO_HEX] Mengkonversi string biner: {binary_string[:50]}...")
    logger.info(f"[BINARY_TO_HEX] Panjang string biner: {len(binary_string)} bit")
    
    try:
        # Bersihkan string biner dari karakter yang tidak valid
        binary_string = ''.join(c for c in binary_string if c in '01')
        
        if not binary_string:
            logger.error(f"[BINARY_TO_HEX] ERROR: String biner kosong setelah pembersihan")
            raise ValueError("String biner tidak valid")
        
        # Konversi biner ke hex tanpa awalan '0x'
        hex_string = format(int(binary_string, 2), 'x')
        
        # Pastikan panjang hex genap (untuk format AES)
        if len(hex_string) % 2 != 0:
            hex_string = '0' + hex_string
            logger.info(f"[BINARY_TO_HEX] Menambahkan '0' di awal untuk memastikan panjang hex genap")
        
        # Pastikan panjang hex adalah 32 karakter (16 bytes) untuk AES
        if len(hex_string) < 32:
            padding_zeros = '0' * (32 - len(hex_string))
            hex_string = padding_zeros + hex_string
            logger.info(f"[BINARY_TO_HEX] Menambahkan {len(padding_zeros)} '0' di awal untuk mencapai 32 karakter")
        
        logger.info(f"[BINARY_TO_HEX] Hasil konversi ke hex: {hex_string[:50]}...")
        logger.info(f"[BINARY_TO_HEX] Panjang string hex: {len(hex_string)} karakter")
        logger.info("="*50 + "\n")
        
        return hex_string
    
    except Exception as e:
        logger.error(f"[BINARY_TO_HEX] ERROR saat konversi biner ke hex: {str(e)}")
        raise ValueError(f"Error saat konversi biner ke hex: {str(e)}")

def decrypt_aes(ciphertext_hex, key, expected_key_length=16):
    """Mendekripsi ciphertext menggunakan AES."""
    logger.info("\n" + "="*50)
    logger.info("[DECRYPT_AES] Memulai proses dekripsi AES")
    logger.info(f"[DECRYPT_AES] Ciphertext hex: {ciphertext_hex[:50]}...")
    logger.info(f"[DECRYPT_AES] Panjang ciphertext hex: {len(ciphertext_hex)} karakter")
    logger.info(f"[DECRYPT_AES] Kunci: '{key}'")
    
    try:
        # Validasi panjang kunci - harus persis 16 karakter 
        if len(key) != expected_key_length:
            logger.error(f"[DECRYPT_AES] ERROR: Panjang kunci tidak valid")
            raise ValueError(f"Password harus persis {expected_key_length} karakter, bukan {len(key)} karakter")
        
        # Konversi ciphertext hex ke bytes
        try:
            ciphertext = binascii.unhexlify(ciphertext_hex)
            logger.info(f"[DECRYPT_AES] Ciphertext hex berhasil dikonversi ke bytes (panjang: {len(ciphertext)} bytes)")
        except binascii.Error as e:
            logger.error(f"[DECRYPT_AES] ERROR: Format hex tidak valid: {str(e)}")
            # Pastikan string hex memiliki panjang genap
            if len(ciphertext_hex) % 2 != 0:
                ciphertext_hex = '0' + ciphertext_hex
                logger.info(f"[DECRYPT_AES] Menambahkan '0' di awal untuk memastikan panjang hex genap")
                try:
                    ciphertext = binascii.unhexlify(ciphertext_hex)
                    logger.info(f"[DECRYPT_AES] Ciphertext hex berhasil dikonversi ke bytes (panjang: {len(ciphertext)} bytes)")
                except binascii.Error:
                    raise ValueError(f"Format hex tidak valid bahkan setelah perbaikan")
            else:
                raise ValueError(f"Format hex tidak valid: {str(e)}")
        
        # Inisialisasi cipher
        cipher = AES.new(key.encode(), AES.MODE_ECB)
        logger.info(f"[DECRYPT_AES] Cipher AES diinisialisasi dengan mode ECB")
        
        # Dekripsi
        try:
            decrypted_padded = cipher.decrypt(ciphertext)
            logger.info(f"[DECRYPT_AES] Ciphertext berhasil didekripsi dengan padding")
        except Exception as e:
            logger.error(f"[DECRYPT_AES] ERROR saat dekripsi: {str(e)}")
            raise ValueError(f"Error saat dekripsi AES: {str(e)}")
        
        try:
            # Validasi padding
            padding_length = decrypted_padded[-1]
            logger.info(f"[DECRYPT_AES] Panjang padding terdeteksi: {padding_length}")
            
            # Validasi padding - jika padding tidak valid, kemungkinan password salah
            if padding_length > 16 or padding_length < 1:
                logger.error(f"[DECRYPT_AES] ERROR: Padding tidak valid (nilai: {padding_length})")
                raise ValueError("Password salah atau chord positions tidak sesuai. Padding tidak valid.")
            
            # Cek padding konsistensi
            for i in range(1, padding_length + 1):
                if decrypted_padded[-i] != padding_length:
                    logger.error(f"[DECRYPT_AES] ERROR: Padding tidak konsisten pada posisi -{i}")
                    raise ValueError("Password salah atau chord positions tidak sesuai. Padding tidak konsisten.")
                
            # Hapus padding
            decrypted = decrypted_padded[:-padding_length]
            logger.info(f"[DECRYPT_AES] Padding berhasil dihapus, panjang plaintext: {len(decrypted)} bytes")
            
            # Konversi ke string
            try:
                result = decrypted.decode('utf-8')
                logger.info(f"[DECRYPT_AES] Hasil dekripsi: '{result}'")
                logger.info("="*50 + "\n")
                return result
            except UnicodeDecodeError as e:
                logger.error(f"[DECRYPT_AES] ERROR: Hasil dekripsi tidak dapat dikonversi ke teks: {str(e)}")
                # Tambahan: coba check bytes hasil dekripsi untuk debugging
                logger.error(f"[DECRYPT_AES] Bytes hasil dekripsi: {decrypted}")
                raise ValueError("Password salah atau chord positions tidak sesuai. Hasil dekripsi tidak dapat dikonversi ke teks.")
        
        except IndexError:
            logger.error(f"[DECRYPT_AES] ERROR: Hasil dekripsi kosong atau terlalu pendek")
            raise ValueError("Password salah atau chord positions tidak sesuai. Hasil dekripsi kosong atau terlalu pendek.")
    
    except binascii.Error:
        logger.error(f"[DECRYPT_AES] ERROR: Format hex tidak valid")
        raise ValueError("Format hex tidak valid")
    except UnicodeDecodeError:
        logger.error(f"[DECRYPT_AES] ERROR: Hasil dekripsi tidak dapat dikonversi ke teks")
        raise ValueError("Password salah atau chord positions tidak sesuai. Hasil dekripsi tidak dapat dikonversi ke teks.")


def extract_binary_from_exact_positions(chord_positions):
    """Ekstrak biner dari posisi chord dengan urutan yang tepat seperti saat enkripsi."""
    logger.info("\n" + "="*50)
    logger.info(f"[EXTRACT_BINARY] Mengekstrak biner dari posisi chord dengan urutan asli")
    
    try:
        # Definisi pola lagu Mary Had a Little Lamb
        melody_notes = [note for note, _ in mary_had_a_little_lamb]
        melody_length = len(melody_notes)
        logger.info(f"[EXTRACT_BINARY] Total {melody_length} nada dalam pola lagu asli")
        
        # Rekonstruksi pola lagu
        song_pattern = []
        pattern_debugger = []
        current_perulangan = 0
        position_counter = 0
        max_pos = max(chord_positions)
        
        # Mapping nada ke biner - HARUS SAMA DENGAN YANG DI encrypt_utils.py
        note_to_binary = {
            "C": "00", 
            "D": "01",
            "E": "10",
            "G": "11"
        }
        
        # Debug original melody pattern
        logger.info(f"[EXTRACT_BINARY] Pola melodi asli: {melody_notes}")
        
        # Rekonstruksi pola lagu untuk mendapatkan nada di posisi tertentu
        while position_counter <= max_pos:
            # Tambahkan jeda antar perulangan (kecuali pada perulangan pertama)
            if current_perulangan > 0:
                song_pattern.append("PAUSE")
                pattern_debugger.append(f"{position_counter}: PAUSE")
                # PENTING: Jeda ini menambah 1 posisi, sehingga perulangan berikutnya dimulai dari chord_idx+1
                logger.info(f"[EXTRACT_BINARY] Menambahkan jeda di posisi {position_counter} (ini menyebabkan perulangan berikutnya dimulai dari chord_idx {position_counter+1})")
                position_counter += 1
            
            # Tambahkan satu perulangan lagu Mary Had a Little Lamb
            for note in melody_notes:
                song_pattern.append(note)
                pattern_debugger.append(f"{position_counter}: {note}")
                position_counter += 1
            
            current_perulangan += 1
            logger.info(f"[EXTRACT_BINARY] Perulangan {current_perulangan} selesai, total posisi: {position_counter}")
            logger.info(f"[EXTRACT_BINARY] Jika ada perulangan berikutnya, akan dimulai dari chord_idx {position_counter}")
            
            # Debug jika diperlukan
            if position_counter > max_pos + 100:  # Prevent infinite loops
                logger.error(f"[EXTRACT_BINARY] ERROR: Kemungkinan infinite loop pada rekonstruksi pola lagu")
                break
        
        # Ekstrak biner dari posisi chord - MENGGUNAKAN URUTAN YANG SAMA PERSIS
        binary_segments = []
        logger.info(f"[EXTRACT_BINARY] Pemetaan posisi chord ke biner (sesuai urutan enkripsi):")
        
        # Debug untuk melihat mapping
        logger.info(f"[EXTRACT_BINARY] 5 nada pertama: {[song_pattern[i] for i in range(min(5, len(song_pattern)))]}")
        
        # Debug beberapa posisi penting
        for debug_pos in [0, 1, 2, 15, 26]:
            if debug_pos < len(song_pattern):
                logger.info(f"[EXTRACT_BINARY] Posisi {debug_pos}: {song_pattern[debug_pos]}")
            else:
                logger.info(f"[EXTRACT_BINARY] Posisi {debug_pos}: di luar jangkauan")
        
        # Proses setiap posisi chord sesuai urutan yang diberikan
        for pos in chord_positions:
            if pos < len(song_pattern):
                note = song_pattern[pos]
                if note == "PAUSE":
                    # Abaikan PAUSE dalam rekonstruksi biner
                    logger.info(f"[EXTRACT_BINARY] Chord_idx {pos}: {note} -> Mengabaikan (bukan data)")
                    continue
                else:
                    # Pastikan kita menggunakan pemetaan yang konsisten dengan enkripsi
                    binary = note_to_binary.get(note, "00")
                    logger.info(f"[EXTRACT_BINARY] Chord_idx {pos}: Nada {note} -> Biner {binary}")
                    binary_segments.append(binary)
            else:
                logger.error(f"[EXTRACT_BINARY] ERROR: Chord_idx {pos} di luar jangkauan pola lagu")
                raise ValueError(f"Posisi chord {pos} di luar jangkauan pola lagu (panjang {len(song_pattern)})")
        
        # Gabung semua segmen biner
        binary_sequence = "".join(binary_segments)
        logger.info(f"[EXTRACT_BINARY] Hasil rekonstruksi biner: {binary_sequence}")
        logger.info(f"[EXTRACT_BINARY] Panjang biner: {len(binary_sequence)} bit")
        logger.info("="*50 + "\n")
        
        return binary_sequence
    
    except Exception as e:
        logger.error(f"[EXTRACT_BINARY] ERROR saat ekstraksi biner: {str(e)}")
        raise ValueError(f"Error saat ekstraksi biner: {str(e)}")

def extract_binary_from_audio(audio_path, chord_positions_str):
    """Ekstrak data biner dari file audio steganografi menggunakan password kedua (posisi chord)."""
    logger.info("\n" + "="*50)
    logger.info(f"[EXTRACT_BINARY] Memulai ekstraksi biner dari file audio: {audio_path}")
    
    if not chord_positions_str or not chord_positions_str.strip():
        logger.error(f"[EXTRACT_BINARY] ERROR: Posisi chord tidak disediakan")
        raise ValueError("Posisi chord (password kedua) harus disediakan untuk dekripsi")
    
    try:
        logger.info(f"[EXTRACT_BINARY] Menggunakan posisi chord yang disediakan pengguna: {chord_positions_str}")
        
        # Parse input chord positions - MENGGUNAKAN URUTAN YANG SAMA PERSIS SEPERTI DARI ENKRIPSI
        chord_positions = []
        for pos in chord_positions_str.split(','):
            pos = pos.strip()
            if pos:  # Pastikan bukan string kosong
                try:
                    chord_positions.append(int(pos))
                except ValueError:
                    logger.warning(f"[EXTRACT_BINARY] PERINGATAN: Mengabaikan posisi tidak valid: {pos}")
        
        if not chord_positions:
            logger.error(f"[EXTRACT_BINARY] ERROR: Tidak ada posisi chord yang valid")
            raise ValueError("Tidak ada posisi chord yang valid ditemukan")
        
        # SANGAT PENTING: JANGAN urutkan chord positions, karena urutannya harus sama dengan saat enkripsi
        logger.info(f"[EXTRACT_BINARY] Posisi chord yang akan digunakan (urutan asli dari enkripsi): {chord_positions}")
        
        # Ekstrak biner dari posisi chord - MENGGUNAKAN URUTAN YANG SAMA PERSIS
        binary_sequence = extract_binary_from_exact_positions(chord_positions)
        
        # Konversi biner ke hex
        hex_string = binary_to_hex(binary_sequence)
        
        logger.info(f"[EXTRACT_BINARY] Ekstraksi biner selesai, hasil hex: {hex_string}")
        logger.info(f"[EXTRACT_BINARY] Panjang hex: {len(hex_string)} karakter")
        logger.info("="*50 + "\n")
        
        return hex_string
    
    except ValueError as e:
        logger.error(f"[EXTRACT_BINARY] ERROR saat parsing posisi chord: {str(e)}")
        raise ValueError(f"Format posisi chord tidak valid: {str(e)}") 