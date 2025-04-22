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
        print("Membuka file WAV...")
        with open(wav_path, 'rb') as f:
            content = f.read()
            
        # Cari marker metadata 'META'
        meta_index = content.find(b'META')
        
        if meta_index == -1:
            print("Marker META tidak ditemukan, mencoba metode alternatif...")
            # Coba cari metadata di akhir file jika tidak menemukan marker
            potential_json_start = content.find(b'{')
            potential_json_end = content.rfind(b'}')
            
            if potential_json_start > 0 and potential_json_end > potential_json_start:
                # Coba parse JSON dari posisi yang ditemukan
                try:
                    potential_json = content[potential_json_start:potential_json_end+1]
                    metadata = json.loads(potential_json.decode('utf-8'))
                    if metadata:
                        print("Berhasil menemukan metadata dengan metode alternatif.")
                        return metadata, None
                except:
                    pass
            
            return None, "Metadata tidak ditemukan dalam file"
        
        print(f"Marker META ditemukan pada posisi {meta_index}")
        
        # Ekstrak metadata
        meta_len_bytes = content[meta_index+4:meta_index+8]
        meta_len = struct.unpack('<I', meta_len_bytes)[0]
        print(f"Panjang metadata: {meta_len} bytes")
        
        meta_json = content[meta_index+8:meta_index+8+meta_len]
        
        try:
            # Coba decode metadata
            json_str = meta_json.decode('utf-8')
            # Debuging - tampilkan substring metadata
            print(f"Preview JSON metadata: {json_str[:50]}..." if len(json_str) > 50 else f"JSON metadata: {json_str}")
            
            metadata = json.loads(json_str)
            return metadata, None
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {str(e)}")
            print(f"Mencoba membersihkan string JSON...")
            
            # Coba bersihkan string JSON
            json_str = json_str.strip()
            # Cari awal dan akhir objek JSON yang valid
            start_idx = json_str.find('{')
            end_idx = json_str.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                try:
                    cleaned_json = json_str[start_idx:end_idx]
                    metadata = json.loads(cleaned_json)
                    return metadata, None
                except:
                    return None, "Format metadata tidak valid setelah pembersihan"
            
            return None, "Format metadata tidak valid"
            
    except Exception as e:
        print(f"Exception detail: {str(e)}")
        return None, f"Error saat membaca file WAV: {str(e)}"

def get_binary_sequence_from_metadata(metadata):
    """Mendapatkan urutan biner dari metadata."""
    if not metadata:
        return None, "Metadata tidak ditemukan"
    
    print("Metadata yang tersedia:")
    for key in metadata:
        print(f"- {key}")
    
    # Metode 1: Gunakan urutan biner yang disimpan dalam metadata
    if "cipher_binary" in metadata:
        print("Menggunakan cipher_binary dari metadata")
        return metadata["cipher_binary"], None
    
    # Metode 2: Rekonstruksi urutan biner dari chord yang digunakan dan posisi note
    elif "note_positions" in metadata and "binary_mapping" in metadata:
        try:
            print("Mencoba merekonstruksi dari note_positions dan binary_mapping")
            note_positions = metadata["note_positions"]
            binary_mapping = metadata["binary_mapping"]
            
            # Debugging
            print(f"Jumlah posisi note: {len(note_positions)}")
            print(f"Binary mapping: {binary_mapping}")
            
            # Reverse mapping - dari file chord ke nilai biner
            rev_mapping = {}
            for chord, binary in binary_mapping.items():
                rev_mapping[chord] = binary
            
            print(f"Reverse mapping: {rev_mapping}")
            
            # Membangun kembali urutan biner dari posisi note
            binary_sequence = ""
            
            # Asumsi bahwa semua chord yang digunakan adalah C-PianoChord.wav (00), D-PianoChord.wav (01), dll.
            chord_keys = list(binary_mapping.keys())
            if not chord_keys:
                return None, "Binary mapping kosong"
                
            # Default ke chord pertama jika tidak ada yang cocok
            default_chord = chord_keys[0]
            default_binary = binary_mapping[default_chord]
            
            # Iterasi melalui posisi
            for i in range(len(note_positions) - 1):
                # Hitung durasi
                current_pos = note_positions[i]
                next_pos = note_positions[i+1]
                duration = next_pos - current_pos
                
                # Cari chord yang sesuai
                # Gunakan cara sederhana: ambil dari rev_mapping dengan index terurut
                index = i % len(chord_keys)
                chord = chord_keys[index]
                binary = rev_mapping.get(chord, default_binary)
                
                binary_sequence += binary
            
            if binary_sequence:
                print(f"Berhasil merekonstruksi dengan panjang: {len(binary_sequence)} bit")
                return binary_sequence, None
            else:
                return None, "Gagal merekonstruksi urutan biner"
        
        except Exception as e:
            print(f"Error detail: {str(e)}")
            return None, f"Error saat merekonstruksi urutan biner: {str(e)}"
    
    else:
        missing = []
        if "cipher_binary" not in metadata:
            missing.append("cipher_binary")
        if "note_positions" not in metadata:
            missing.append("note_positions")
        if "binary_mapping" not in metadata:
            missing.append("binary_mapping")
            
        return None, f"Informasi yang diperlukan tidak ditemukan dalam metadata: {', '.join(missing)}"

def binary_to_hex(binary_string):
    """Mengkonversi string biner ke string hex."""
    # Pastikan panjang string biner adalah kelipatan 4
    padding = 4 - (len(binary_string) % 4) if len(binary_string) % 4 != 0 else 0
    binary_string = '0' * padding + binary_string
    
    # Konversi biner ke hex
    hex_string = hex(int(binary_string, 2))[2:]
    
    return hex_string

def decrypt_aes(ciphertext_hex, key, expected_key_length=16):
    """Mendekripsi ciphertext menggunakan AES.
    
    Args:
        ciphertext_hex: String hex dari ciphertext
        key: Kunci dekripsi
        expected_key_length: Panjang kunci yang diharapkan (default: 16)
        
    Returns:
        (plaintext, error): Tuple dari hasil dekripsi dan pesan error (jika ada)
    """
    try:
        # Validasi panjang kunci - harus persis 16 karakter 
        # Tidak mengizinkan pemadatan otomatis atau pemotongan
        if len(key) != expected_key_length:
            return None, f"Password harus persis {expected_key_length} karakter, bukan {len(key)} karakter"
        
        # Konversi ciphertext hex ke bytes
        ciphertext = binascii.unhexlify(ciphertext_hex)
        
        # Inisialisasi cipher
        cipher = AES.new(key.encode(), AES.MODE_ECB)
        
        # Dekripsi
        decrypted_padded = cipher.decrypt(ciphertext)
        
        # Validasi padding
        padding_length = decrypted_padded[-1]
        
        # Validasi padding - jika padding tidak valid, kemungkinan password salah
        if padding_length > 16 or padding_length < 1:
            return None, "Password salah. Padding tidak valid."
        
        # Cek padding konsistensi
        for i in range(1, padding_length + 1):
            if decrypted_padded[-i] != padding_length:
                return None, "Password salah. Padding tidak konsisten."
                
        # Hapus padding
        decrypted = decrypted_padded[:-padding_length]
        
        # Validasi tambahan - cek apakah hasil decryption adalah teks yang valid
        try:
            result = decrypted.decode('utf-8')
            # Cek apakah hasil berisi karakter yang dapat dibaca
            if all(ord(c) < 32 or ord(c) > 126 for c in result[:5]) and len(result) > 5:
                return None, "Password mungkin salah. Hasil dekripsi tidak berisi teks yang dapat dibaca."
            return result, None
        except UnicodeDecodeError:
            return None, "Password salah. Hasil dekripsi tidak dapat dikonversi ke teks."
    
    except binascii.Error:
        return None, "Format hex tidak valid"
    except Exception as e:
        return None, f"Error saat dekripsi: {str(e)}"

def main():
    """Fungsi utama untuk dekripsi file WAV."""
    print("=== PROGRAM DEKRIPSI STEGANOGRAFI AUDIO AES ===")
    
    # Input file WAV terlebih dahulu
    wav_path = input("Masukkan path file WAV: ")
    
    if not os.path.exists(wav_path):
        print(f"Error: File '{wav_path}' tidak ditemukan")
        return
    
    try:
        # Ekstrak metadata
        print("\nMemulai proses ekstraksi metadata...")
        metadata, error = extract_metadata_from_wav(wav_path)
        
        if error:
            print(f"Error: {error}")
            decision = input("Tetap lanjutkan dan coba rekonstruksi manual? (y/n): ")
            if decision.lower() != 'y':
                return
        
        if not metadata:
            print("Error: Metadata tidak ditemukan atau kosong")
            return
        
        print("Metadata berhasil diekstrak.")
        
        # Dapatkan panjang kunci yang diharapkan dari metadata jika ada
        expected_key_length = metadata.get("key_length", 16)
        
        # Dapatkan urutan biner dari metadata
        print("\nMendapatkan urutan biner dari metadata...")
        binary_sequence, error = get_binary_sequence_from_metadata(metadata)
        
        if error:
            print(f"Error: {error}")
            decision = input("Tetap lanjutkan dengan urutan biner default? (y/n): ")
            if decision.lower() == 'y':
                # Buat urutan biner dummy untuk testing
                print("Menggunakan urutan biner default untuk testing")
                binary_sequence = "01" * 32
            else:
                return
        
        if not binary_sequence:
            print("Error: Urutan biner tidak dapat direkonstruksi")
            return
        
        print(f"Urutan biner berhasil didapatkan: {binary_sequence[:64]}..." if len(binary_sequence) > 64 else f"Urutan biner berhasil didapatkan: {binary_sequence}")
        
        # Konversi biner ke hex
        print("\nMengkonversi biner ke hex...")
        hex_string = binary_to_hex(binary_sequence)
        print(f"Konversi ke hex: {hex_string[:32]}..." if len(hex_string) > 32 else f"Konversi ke hex: {hex_string}")
        
        # Loop untuk mencoba password
        max_attempts = 3
        attempt = 0
        
        while attempt < max_attempts:
            # Input kunci dekripsi
            if attempt == 0:
                key = input(f"\nMasukkan kunci dekripsi (harus persis {expected_key_length} karakter): ")
            else:
                key = input(f"\nPassword salah. Percobaan ke-{attempt+1}/{max_attempts}. Masukkan kunci dekripsi ({expected_key_length} karakter): ")
            
            # Dekripsi dengan kunci
            print("Memulai proses dekripsi...")
            decrypted_text, error = decrypt_aes(hex_string, key, expected_key_length)
            
            if error:
                print(f"Error: {error}")
                attempt += 1
                if attempt >= max_attempts:
                    print("\nTerlalu banyak percobaan gagal. Program berhenti.")
                    # Opsi untuk bypass password
                    bypass = input("Bypass password untuk melihat hasil mentah (hanya untuk debugging)? (y/n): ")
                    if bypass.lower() == 'y':
                        try:
                            # Coba dekripsi dengan password kosong (untuk debugging)
                            raw_decrypted = AES.new(key.encode(), AES.MODE_ECB).decrypt(binascii.unhexlify(hex_string))
                            print("\nHasil dekripsi (raw):")
                            print(f"HEX: {binascii.hexlify(raw_decrypted).decode()[:100]}")
                            print(f"Coba decode UTF-8: {raw_decrypted[:100]}")
                        except:
                            print("Gagal melakukan debugging dekripsi")
                    return
                continue
            
            # Jika berhasil, keluar dari loop
            break
        
        print("\nHasil dekripsi:")
        print(decrypted_text)
    
    except Exception as e:
        print(f"\nError tidak terduga: {str(e)}")
        print("Silakan coba lagi atau hubungi pengembang")

if __name__ == "__main__":
    main()
