import os
import wave
import struct
import json
import binascii
import numpy as np
from Crypto.Cipher import AES

# Pemetaan nama file chord ke biner
chord_to_binary = {
    "C-PianoChord.wav": "00",
    "D-PianoChord.wav": "01",
    "E-PianoChord.wav": "10",
    "G-PianoChord.wav": "11"
}

def extract_metadata_from_wav(wav_path):
    """Mengekstrak metadata dari file WAV."""
    try:
        with wave.open(wav_path, 'rb') as wf:
            # Baca semua frame
            frames = wf.readframes(wf.getnframes())
            
            # Cari marker metadata 'META'
            meta_index = frames.find(b'META')
            
            if meta_index == -1:
                return None, "Metadata tidak ditemukan dalam file"
            
            # Ekstrak metadata
            meta_len_bytes = frames[meta_index+4:meta_index+8]
            meta_len = struct.unpack('<I', meta_len_bytes)[0]
            
            meta_json = frames[meta_index+8:meta_index+8+meta_len]
            
            try:
                metadata = json.loads(meta_json.decode('utf-8'))
                return metadata, None
            except json.JSONDecodeError:
                return None, "Format metadata tidak valid"
            
    except Exception as e:
        return None, f"Error saat membaca file WAV: {str(e)}"

def get_binary_sequence_from_metadata(metadata):
    """Mendapatkan urutan biner dari metadata."""
    if not metadata:
        return None, "Metadata tidak ditemukan"
    
    # Metode 1: Gunakan urutan biner yang disimpan dalam metadata
    if "cipher_binary" in metadata:
        return metadata["cipher_binary"], None
    
    # Metode 2: Rekonstruksi urutan biner dari chord yang digunakan
    elif "note_positions" in metadata and "binary_mapping" in metadata:
        try:
            note_positions = metadata["note_positions"]
            binary_mapping = metadata["binary_mapping"]
            
            # Membangun kembali urutan biner dari posisi note
            binary_sequence = ""
            
            # Kita perlu memeriksa setiap pasangan posisi untuk mendapatkan durasi setiap chord
            for i in range(len(note_positions) - 2):  # -2 karena posisi terakhir adalah posisi akhir file
                start_pos = note_positions[i]
                end_pos = note_positions[i+1]
                
                # Hitung durasi
                duration = end_pos - start_pos
                
                # Temukan chord berdasarkan durasi (pendekatan sederhana)
                # Asumsi: kita memiliki cara mengidentifikasi chord berdasarkan durasi
                # Dalam implementasi nyata, ini mungkin memerlukan analisis yang lebih kompleks
                
                # Disini kita menggunakan pendekatan placeholder
                # Pada implementasi sebenarnya, kita perlu mengidentifikasi chord yang valid
                chord_name = "C-PianoChord.wav"  # Placeholder
                binary_value = binary_mapping.get(chord_name, "00")
                
                binary_sequence += binary_value
            
            return binary_sequence, None
        
        except Exception as e:
            return None, f"Error saat merekonstruksi urutan biner: {str(e)}"
    
    else:
        return None, "Informasi yang diperlukan tidak ditemukan dalam metadata"

def binary_to_hex(binary_string):
    """Mengkonversi string biner ke string hex."""
    # Pastikan panjang string biner adalah kelipatan 4
    padding = 4 - (len(binary_string) % 4) if len(binary_string) % 4 != 0 else 0
    binary_string = '0' * padding + binary_string
    
    # Konversi biner ke hex
    hex_string = hex(int(binary_string, 2))[2:]
    
    return hex_string

def decrypt_aes(ciphertext_hex, key):
    """Mendekripsi ciphertext menggunakan AES."""
    try:
        # Pastikan panjang kunci 16 karakter
        if len(key) < 16:
            key = key.ljust(16)
        elif len(key) > 16:
            key = key[:16]
        
        # Konversi ciphertext hex ke bytes
        ciphertext = binascii.unhexlify(ciphertext_hex)
        
        # Inisialisasi cipher
        cipher = AES.new(key.encode(), AES.MODE_ECB)
        
        # Dekripsi
        decrypted_padded = cipher.decrypt(ciphertext)
        
        # Hapus padding
        padding_length = decrypted_padded[-1]
        decrypted = decrypted_padded[:-padding_length]
        
        # Konversi bytes ke string
        return decrypted.decode('utf-8'), None
    
    except binascii.Error:
        return None, "Format hex tidak valid"
    except Exception as e:
        return None, f"Error saat dekripsi: {str(e)}"

def main():
    """Fungsi utama untuk dekripsi file WAV."""
    print("=== PROGRAM DEKRIPSI STEGANOGRAFI AUDIO AES ===")
    
    # Input file WAV
    wav_path = input("Masukkan path file WAV: ")
    
    if not os.path.exists(wav_path):
        print(f"Error: File '{wav_path}' tidak ditemukan")
        return
    
    # Ekstrak metadata
    metadata, error = extract_metadata_from_wav(wav_path)
    
    if error:
        print(f"Error: {error}")
        return
    
    if not metadata:
        print("Error: Metadata tidak ditemukan")
        return
    
    print("Metadata berhasil diekstrak.")
    
    # Dapatkan urutan biner dari metadata
    binary_sequence, error = get_binary_sequence_from_metadata(metadata)
    
    if error:
        print(f"Error: {error}")
        return
    
    if not binary_sequence:
        print("Error: Urutan biner tidak dapat direkonstruksi")
        return
    
    print(f"Urutan biner berhasil didapatkan: {binary_sequence[:64]}..." if len(binary_sequence) > 64 else f"Urutan biner berhasil didapatkan: {binary_sequence}")
    
    # Konversi biner ke hex
    hex_string = binary_to_hex(binary_sequence)
    print(f"Konversi ke hex: {hex_string[:32]}..." if len(hex_string) > 32 else f"Konversi ke hex: {hex_string}")
    
    # Input kunci dekripsi
    key = input("Masukkan kunci dekripsi (16 karakter): ")
    
    # Dekripsi
    decrypted_text, error = decrypt_aes(hex_string, key)
    
    if error:
        print(f"Error: {error}")
        return
    
    print("\nHasil dekripsi:")
    print(decrypted_text)

if __name__ == "__main__":
    main()
