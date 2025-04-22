import os
import wave
import struct
import json
import binascii
from Crypto.Cipher import AES

# Pemetaan biner ke nama file chord untuk referensi saat dekripsi
binary_to_chord = {
    "00": "C-PianoChord.wav",
    "01": "D-PianoChord.wav", 
    "10": "E-PianoChord.wav",
    "11": "G-PianoChord.wav"
}

# Pemetaan nama chord ke biner
chord_to_binary = {chord_name.split("-")[0]: binary for binary, chord_name in binary_to_chord.items()}

def binary_to_hex(binary_string):
    """Mengkonversi string biner ke string hex."""
    # Pastikan panjang string biner adalah kelipatan 4
    padding = 4 - (len(binary_string) % 4) if len(binary_string) % 4 != 0 else 0
    binary_string = '0' * padding + binary_string
    
    # Konversi biner ke hex
    hex_string = hex(int(binary_string, 2))[2:]
    
    return hex_string

def decrypt_aes(ciphertext_hex, key, expected_key_length=16):
    """Mendekripsi ciphertext menggunakan AES."""
    try:
        # Validasi panjang kunci - harus persis 16 karakter 
        if len(key) != expected_key_length:
            raise ValueError(f"Password harus persis {expected_key_length} karakter, bukan {len(key)} karakter")
        
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
            raise ValueError("Password salah. Padding tidak valid.")
        
        # Cek padding konsistensi
        for i in range(1, padding_length + 1):
            if decrypted_padded[-i] != padding_length:
                raise ValueError("Password salah. Padding tidak konsisten.")
                
        # Hapus padding
        decrypted = decrypted_padded[:-padding_length]
        
        # Konversi ke string
        result = decrypted.decode('utf-8')
        return result
    
    except binascii.Error:
        raise ValueError("Format hex tidak valid")
    except UnicodeDecodeError:
        raise ValueError("Password salah. Hasil dekripsi tidak dapat dikonversi ke teks.")

def extract_metadata_from_wav(wav_path):
    """Mengekstrak metadata dari file WAV."""
    try:
        with open(wav_path, 'rb') as f:
            content = f.read()
            
        # Cari marker metadata 'META'
        meta_index = content.find(b'META')
        
        if meta_index == -1:
            # Coba cari metadata di akhir file jika tidak menemukan marker
            potential_json_start = content.find(b'{')
            potential_json_end = content.rfind(b'}')
            
            if potential_json_start > 0 and potential_json_end > potential_json_start:
                # Coba parse JSON dari posisi yang ditemukan
                try:
                    potential_json = content[potential_json_start:potential_json_end+1]
                    metadata = json.loads(potential_json.decode('utf-8'))
                    if metadata:
                        return metadata
                except:
                    pass
            
            raise ValueError("Metadata tidak ditemukan dalam file")
        
        # Ekstrak metadata
        meta_len_bytes = content[meta_index+4:meta_index+8]
        meta_len = struct.unpack('<I', meta_len_bytes)[0]
        
        meta_json = content[meta_index+8:meta_index+8+meta_len]
        
        try:
            # Coba decode metadata
            json_str = meta_json.decode('utf-8')
            metadata = json.loads(json_str)
            return metadata
        except json.JSONDecodeError as e:
            # Coba bersihkan string JSON
            json_str = json_str.strip()
            # Cari awal dan akhir objek JSON yang valid
            start_idx = json_str.find('{')
            end_idx = json_str.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                try:
                    cleaned_json = json_str[start_idx:end_idx]
                    metadata = json.loads(cleaned_json)
                    return metadata
                except:
                    raise ValueError("Format metadata tidak valid setelah pembersihan")
            
            raise ValueError("Format metadata tidak valid")
            
    except Exception as e:
        raise ValueError(f"Error saat membaca file WAV: {str(e)}")

def get_binary_sequence_from_metadata(metadata):
    """Mendapatkan urutan biner dari metadata."""
    if not metadata:
        raise ValueError("Metadata tidak ditemukan")
    
    # Metode 1: Gunakan urutan biner yang disimpan dalam metadata
    if "cipher_binary" in metadata:
        return metadata["cipher_binary"]
    
    # Metode 2: Rekonstruksi urutan biner dari chord yang digunakan dan posisi note
    elif "note_positions" in metadata and "binary_mapping" in metadata:
        try:
            note_positions = metadata["note_positions"]
            binary_mapping = metadata["binary_mapping"]
            
            # Reverse mapping - dari file chord ke nilai biner
            rev_mapping = {}
            for chord, binary in binary_mapping.items():
                rev_mapping[chord] = binary
            
            # Membangun kembali urutan biner dari posisi note
            binary_sequence = ""
            
            # Asumsi bahwa semua chord yang digunakan adalah C-PianoChord.wav (00), D-PianoChord.wav (01), dll.
            chord_keys = list(binary_mapping.keys())
            if not chord_keys:
                raise ValueError("Binary mapping kosong")
                
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
                return binary_sequence
            else:
                raise ValueError("Gagal merekonstruksi urutan biner")
        
        except Exception as e:
            raise ValueError(f"Error saat merekonstruksi urutan biner: {str(e)}")
    
    else:
        missing = []
        if "cipher_binary" not in metadata:
            missing.append("cipher_binary")
        if "note_positions" not in metadata:
            missing.append("note_positions")
        if "binary_mapping" not in metadata:
            missing.append("binary_mapping")
            
        raise ValueError(f"Informasi yang diperlukan tidak ditemukan dalam metadata: {', '.join(missing)}")

def extract_binary_from_audio(audio_path):
    """Ekstrak data biner dari file audio steganografi."""
    # Ekstrak metadata
    metadata = extract_metadata_from_wav(audio_path)
    
    # Dapatkan urutan biner dari metadata
    binary_sequence = get_binary_sequence_from_metadata(metadata)
    
    # Konversi biner ke hex
    hex_string = binary_to_hex(binary_sequence)
    
    return hex_string 