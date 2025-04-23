import os
import binascii
import numpy as np
from scipy.io import wavfile
import wave
import struct
import json
from Crypto.Cipher import AES

# Pemetaan biner ke nama file chord
binary_to_chord = {
    "00": "C-PianoChord.wav",
    "01": "D-PianoChord.wav", 
    "10": "E-PianoChord.wav",
    "11": "G-PianoChord.wav"
}

# Pemetaan nama chord ke biner
chord_to_binary = {v.split("-")[0]: k for k, v in binary_to_chord.items()}

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
    return plaintext + (chr(padding_length) * padding_length)

def encrypt_aes(plaintext, key):
    """Mengenkripsi plaintext menggunakan AES."""
    # Validasi panjang kunci - harus persis 16 karakter
    if len(key) != 16:
        print(f"PERINGATAN: Panjang kunci harus 16 karakter, bukan {len(key)}.")
        print("Kunci akan disesuaikan otomatis untuk enkripsi ini.")
        
        if len(key) < 16:
            key = key.ljust(16)  # Tambahkan spasi jika terlalu pendek
            print(f"Kunci diperpanjang: '{key}'")
        else:
            key = key[:16]  # Potong jika terlalu panjang
            print(f"Kunci dipotong: '{key}'")
    
    # Padding plaintext
    padded_text = pad_text(plaintext)
    
    # Inisialisasi cipher
    cipher = AES.new(key.encode(), AES.MODE_ECB)
    
    # Enkripsi
    ciphertext = cipher.encrypt(padded_text.encode())
    
    # Konversi ke hex
    ciphertext_hex = binascii.hexlify(ciphertext).decode()
    
    return ciphertext_hex

def hex_to_binary(hex_string):
    """Mengkonversi string hex ke string biner."""
    binary = bin(int(hex_string, 16))[2:]
    
    # Pastikan panjang biner adalah kelipatan 2
    if len(binary) % 2 != 0:
        binary = '0' + binary
    
    return binary

def map_binary_to_chords(binary_string):
    """Memetakan string biner ke daftar nama file chord."""
    chord_files = []
    
    # Pastikan panjang string biner adalah kelipatan 2
    if len(binary_string) % 2 != 0:
        binary_string = '0' + binary_string
    
    # Pemetakan setiap 2 bit ke chord yang sesuai
    for i in range(0, len(binary_string), 2):
        binary_segment = binary_string[i:i+2]
        chord_file = binary_to_chord.get(binary_segment)
        if chord_file:
            chord_files.append(chord_file)
    
    return chord_files

def prepare_song_with_binary(binary_string):
    """Menyiapkan pola lagu dengan memetakan segmen biner ke nada yang ditentukan.
    
    Pendekatan ini menyiapkan terlebih dahulu musik Mary Had a Little Lamb,
    lalu memetakan biner ke nada-nada yang ditentukan.
    """
    # Bagi binary string menjadi segmen 2-bit
    binary_segments = [binary_string[i:i+2] for i in range(0, len(binary_string), 2)]
    
    song_pattern = []
    binary_mapping = {}
    used_binary = []
    
    print("\n=== Penyiapan Musik Mary Had a Little Lamb dengan Pemetaan Biner ===")
    print(f"Total segmen biner: {len(binary_segments)}")
    print(f"Total nada dalam pola lagu: {len(mary_had_a_little_lamb)}")
    
    song_repeat_count = 0
    binary_index = 0
    
    # Iterasi melalui semua segmen biner menggunakan pola lagu yang berulang
    while binary_index < len(binary_segments):
        # Reset jika mencapai akhir pola lagu
        if song_repeat_count > 0:
            print(f"\n--- Mengulang pola lagu (ke-{song_repeat_count}) ---")
            # Tambahkan jeda 2 detik di antara perulangan
            song_pattern.append(("PAUSE", 4.0, "00"))  # 4.0 durasi = 2 detik (karena 1.0 = 0.5 detik)
            print("Menambahkan jeda 2 detik...")
        
        # Iterasi melalui setiap nada dalam pola lagu
        for pattern_index, (note, duration) in enumerate(mary_had_a_little_lamb):
            if binary_index >= len(binary_segments):
                break
                
            binary_segment = binary_segments[binary_index]
            chord_file = binary_to_chord.get(binary_segment)
            
            # Simpan nada, durasi, dan segmen biner yang digunakan
            song_pattern.append((note, duration, binary_segment))
            
            # Catat pemetaan untuk metadata
            if chord_file:
                binary_mapping[chord_file] = binary_segment
                used_binary.append(binary_segment)
                
            print(f"Nada {pattern_index+1}: {note} (Durasi: {duration}) ← Biner: {binary_segment}")
            binary_index += 1
            
        song_repeat_count += 1
    
    return song_pattern, binary_mapping, "".join(used_binary)

def generate_music_from_prepared_song(song_pattern, chord_dir="Chord"):
    """Membuat musik dari pola lagu yang telah disiapkan dengan biner."""
    sample_rate = 44100
    audio_segments = []
    note_positions = [0]
    position = 0
    
    print("\n=== Pembuatan File Musik dari Pola Lagu ===")
    
    # Mencari tahu berapa dimensi audio yang digunakan (untuk memastikan jeda konsisten)
    channels = 1  # Default ke mono jika tidak ada file chord
    for note, _, binary in song_pattern:
        if note != "PAUSE":
            chord_prefix = note
            chord_filename = f"{chord_prefix}-PianoChord.wav"
            chord_path = os.path.join(chord_dir, chord_filename)
            if os.path.exists(chord_path):
                try:
                    rate, audio = wavfile.read(chord_path)
                    if len(audio.shape) > 1:
                        channels = audio.shape[1]  # Ambil jumlah kanal (1=mono, 2=stereo)
                    break
                except Exception:
                    pass
    
    # Iterasi melalui pola lagu
    for i, (note, duration, binary) in enumerate(song_pattern):
        # Jika ini adalah jeda, tambahkan keheningan
        if note == "PAUSE":
            # Tambahkan keheningan sesuai durasi
            pause_duration = int(sample_rate * 0.5 * duration)  # 0.5 detik per unit durasi
            
            # Buat keheningan dengan dimensi yang sama dengan audio
            if channels > 1:
                silence = np.zeros((pause_duration, channels), dtype=np.int16)
            else:
                silence = np.zeros(pause_duration, dtype=np.int16)
                
            audio_segments.append(silence)
            
            # Catat posisi untuk metadata
            note_positions.append(position + len(silence))
            position += len(silence)
            
            print(f"Jeda {i+1}: Durasi {duration * 0.5} detik (silence)")
            continue
            
        # Tentukan file chord berdasarkan nada
        chord_prefix = note
        chord_filename = f"{chord_prefix}-PianoChord.wav"
        chord_path = os.path.join(chord_dir, chord_filename)
        
        if not os.path.exists(chord_path):
            print(f"Warning: File chord '{chord_path}' tidak ditemukan, menggunakan chord alternatif...")
            # Coba gunakan file alternatif berdasarkan binary mapping
            chord_filename = binary_to_chord.get(binary, "C-PianoChord.wav")  # Default ke C jika tidak ada
            chord_path = os.path.join(chord_dir, chord_filename)
            
            if not os.path.exists(chord_path):
                print(f"Error: File alternatif '{chord_path}' juga tidak ditemukan, melewatkan...")
                continue
        
        try:
            # Baca file chord
            rate, audio = wavfile.read(chord_path)
            
            # Hitung durasi berdasarkan ketukan (1.0 = 0.5 detik)
            beat_duration = int(sample_rate * 0.5 * duration)
            
            # Sesuaikan audio dengan durasi
            if len(audio) > beat_duration:
                adjusted_audio = audio[:beat_duration]
            else:
                # Buat padding dengan dimensi yang tepat
                if len(audio.shape) > 1:  # Stereo
                    padding = np.zeros((beat_duration - len(audio), audio.shape[1]), dtype=audio.dtype)
                else:  # Mono
                    padding = np.zeros(beat_duration - len(audio), dtype=audio.dtype)
                adjusted_audio = np.concatenate([audio, padding])
            
            # Catat posisi untuk metadata
            note_positions.append(position + len(adjusted_audio))
            position += len(adjusted_audio)
            
            # Tambahkan ke segmen audio
            audio_segments.append(adjusted_audio)
            
            print(f"Nada {i+1}: {note} (Durasi: {duration}, Biner: {binary}) → {chord_filename}")
            
        except Exception as e:
            print(f"Error saat membaca {chord_path}: {e}")
    
    if not audio_segments:
        print("Error: Tidak ada segmen audio yang valid!")
        return None, None, None
    
    # Gabungkan semua segmen audio
    print("\nMenggabungkan semua segmen audio...")
    try:
        combined_audio = np.concatenate(audio_segments)
        print(f"Audio gabungan: {len(combined_audio)} sampel")
        return combined_audio, sample_rate, note_positions
    except ValueError as e:
        print(f"Error saat menggabungkan audio: {e}")
        print("Informasi dimensi audio segments:")
        for i, segment in enumerate(audio_segments):
            print(f"Segment {i}: shape {segment.shape}, type {segment.dtype}")
        return None, None, None

def add_metadata_to_wav(audio_data, sample_rate, metadata, output_file="output.wav"):
    """Menambahkan metadata ke file WAV."""
    # Simpan audio dalam format WAV
    wavfile.write(output_file, sample_rate, audio_data)
    
    print("\n=== Debug Metadata ===")
    print(f"Metadata yang akan disimpan: {json.dumps(metadata, indent=2)}")
    
    # Simpan metadata dalam format JSON
    metadata_json = json.dumps(metadata).encode('utf-8')
    
    # Tambahkan metadata ke file WAV
    with wave.open(output_file, 'rb') as wf:
        # Baca parameter file WAV
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        comp_type = wf.getcomptype()
        comp_name = wf.getcompname()
        
        # Baca semua frame audio
        frames = wf.readframes(n_frames)
    
    # Tambahkan metadata ke frame
    frames_with_meta = frames + b'META' + struct.pack('<I', len(metadata_json)) + metadata_json
    
    # Tulis kembali file WAV dengan metadata
    with wave.open(output_file, 'wb') as wf:
        wf.setparams((n_channels, sampwidth, framerate, n_frames, comp_type, comp_name))
        wf.writeframes(frames_with_meta)
    
    print(f"Metadata berhasil ditambahkan, ukuran metadata: {len(metadata_json)} bytes")
    
    return output_file

def main():
    """Fungsi utama untuk enkripsi teks dan pembuatan musik steganografi."""
    print("=== PROGRAM STEGANOGRAFI AUDIO DENGAN ENKRIPSI AES ===")
    
    # Input plaintext
    plaintext = input("Masukkan teks (plaintext): ")
    
    # Input kunci enkripsi
    key = input("Masukkan kunci enkripsi (harus persis 16 karakter): ")
    
    # Enkripsi plaintext menggunakan AES
    ciphertext_hex = encrypt_aes(plaintext, key)
    print(f"Hasil enkripsi AES (hex): {ciphertext_hex}")
    
    # Konversi hex ke biner
    binary = hex_to_binary(ciphertext_hex)
    print(f"Hasil konversi ke biner: {binary}")
    
    # Menyiapkan pola lagu dengan pemetaan biner
    print("\nMenyiapkan pola lagu Mary Had a Little Lamb dengan pemetaan biner...")
    song_pattern, binary_mapping, used_binary = prepare_song_with_binary(binary)
    
    # Membuat musik dari pola lagu yang telah disiapkan
    print("\nMembuat musik dari pola lagu...")
    audio_data, sample_rate, note_positions = generate_music_from_prepared_song(song_pattern, "Chord")
    
    if audio_data is None or sample_rate is None or note_positions is None:
        print("Error: Gagal membuat musik steganografi")
        return
    
    # Metadata hanya berisi cipher_binary dan key_length saja
    metadata = {
        "cipher_binary": binary,
        "key_length": 16
    }
    
    # Uji baca metadata sebelum disimpan ke file
    try:
        json_metadata = json.dumps(metadata)
        json.loads(json_metadata)
        print("Metadata valid dalam format JSON")
    except Exception as e:
        print(f"Error validasi metadata: {e}")
        return
    
    # Simpan musik dengan metadata
    output_file = "output_music_prepared.wav"
    output_file = add_metadata_to_wav(audio_data, sample_rate, metadata, output_file)
    
    print(f"\nProses selesai! File output: {output_file}")
    print("Coba dekripsi dengan menggunakan Decrypt.py")
    print(f"Pastikan menggunakan kunci yang sama persis: '{key}'")

if __name__ == "__main__":
    main()
