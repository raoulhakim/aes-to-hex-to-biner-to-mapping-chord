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
    ("E", 2), ("D", 0.9), ("C", 1.4), ("D", 1.4), ("E", 1.2), ("E", 1.4), ("E", 2.6),
    ("D", 1.4), ("D", 1.4), ("D", 2.8), ("E", 1.4), ("G", 1.4), ("G", 2.6),
    ("E", 2), ("D", 0.7), ("C", 1.3), ("D", 1.1), ("E", 1.3), ("E", 1.3), ("E", 1.3),
    ("C", 1.5), ("D", 1.5), ("D", 1.5), ("E", 1.5), ("D", 1.5), ("C", 2.5)
]

def pad_text(plaintext):
    """Menambahkan padding pada plaintext agar panjangnya kelipatan 16."""
    padding_length = 16 - (len(plaintext) % 16)
    return plaintext + (chr(padding_length) * padding_length)

def encrypt_aes(plaintext, key):
    """Mengenkripsi plaintext menggunakan AES."""
    # Pastikan panjang kunci 16 karakter
    if len(key) < 16:
        key = key.ljust(16)
    elif len(key) > 16:
        key = key[:16]
    
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
            
        # Tambahkan jeda 2 detik setelah satu perulangan lagu selesai, kecuali ini perulangan terakhir
        if binary_index < len(binary_segments):
            # Gunakan "PAUSE" sebagai penanda jeda dan nilai biner terakhir yang digunakan sebagai placeholder
            last_binary = binary_segments[binary_index-1] if binary_index > 0 else "00"
            song_pattern.append(("PAUSE", 4.0, last_binary))  # 4.0 karena 1.0 = 0.5 detik, sehingga 4.0 = 2 detik
            print(f"Menambahkan jeda 2 detik setelah perulangan ke-{song_repeat_count}")
            
        song_repeat_count += 1
    
    return song_pattern, binary_mapping, "".join(used_binary)

def generate_music_from_prepared_song(song_pattern, chord_dir="Chord"):
    """Membuat musik dari pola lagu yang telah disiapkan dengan biner."""
    sample_rate = 44100
    audio_segments = []
    note_positions = [0]
    position = 0
    channels = None  # Untuk menyimpan jumlah channel dari file audio
    
    print("\n=== Pembuatan File Musik dari Pola Lagu ===")
    
    # Baca salah satu file untuk mendapatkan format (stereo/mono)
    # Cari file chord pertama yang valid
    for note, _, binary in song_pattern:
        if note != "PAUSE":
            # Coba baca salah satu file
            try:
                test_file = os.path.join(chord_dir, f"{note}-PianoChord.wav")
                if os.path.exists(test_file):
                    _, test_audio = wavfile.read(test_file)
                    if len(test_audio.shape) > 1:
                        channels = test_audio.shape[1]  # Stereo
                    else:
                        channels = 1  # Mono
                    break
            except Exception:
                pass
    
    # Default ke mono jika tidak ada file yang valid
    if channels is None:
        channels = 1
        
    # Iterasi melalui pola lagu
    for i, (note, duration, binary) in enumerate(song_pattern):
        # Cek apakah ini jeda
        if note == "PAUSE":
            # Buat segmen sunyi untuk jeda dengan dimensi yang sama
            pause_duration = int(sample_rate * 0.5 * duration)  # Durasi jeda dalam sampel
            
            if channels > 1:
                # Buat silence stereo jika audio adalah stereo
                silence = np.zeros((pause_duration, channels), dtype=np.int16)
            else:
                # Buat silence mono jika audio adalah mono
                silence = np.zeros(pause_duration, dtype=np.int16)
            
            # Catat posisi untuk metadata
            note_positions.append(position + len(silence))
            position += len(silence)
            
            # Tambahkan ke segmen audio
            audio_segments.append(silence)
            
            print(f"Nada {i+1}: JEDA (Durasi: {duration} = 2 detik)")
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
            
            # Simpan informasi channel untuk segmen jeda
            if channels is None and len(audio.shape) > 1:
                channels = audio.shape[1]
            
            # Hitung durasi berdasarkan ketukan (1.0 = 0.5 detik)
            beat_duration = int(sample_rate * 0.5 * duration)
            
            # Sesuaikan audio dengan durasi
            if len(audio) > beat_duration:
                adjusted_audio = audio[:beat_duration]
            else:
                    # Sesuaikan padding dengan dimensi audio
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
    combined_audio = np.concatenate(audio_segments)
    print(f"Audio gabungan: {len(combined_audio)} sampel")
    
    return combined_audio, sample_rate, note_positions

def add_metadata_to_wav(audio_data, sample_rate, metadata, output_file="output.wav"):
    """Menambahkan metadata ke file WAV."""
    # Simpan audio dalam format WAV
    wavfile.write(output_file, sample_rate, audio_data)
    
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
    
    return output_file

def main():
    """Fungsi utama untuk enkripsi teks dan pembuatan musik steganografi."""
    print("=== PROGRAM STEGANOGRAFI AUDIO DENGAN ENKRIPSI AES ===")
    
    # Input plaintext
    plaintext = input("Masukkan teks (plaintext): ")
    
    # Input kunci enkripsi
    key = input("Masukkan kunci enkripsi (16 karakter): ")
    
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
    
    if audio_data is None or sample_rate is None:
        print("Error: Gagal membuat musik steganografi")
        return
    
    # Buat metadata
    metadata = {
        "song_type": "mary_had_a_little_lamb_prepared",
        "song_name": "stegano_music_prepared",
        "note_positions": note_positions,
        "binary_mapping": binary_mapping,
        "cipher_binary": binary
    }
    
    # Simpan musik dengan metadata
    output_file = "output_music_prepared.wav"
    output_file = add_metadata_to_wav(audio_data, sample_rate, metadata, output_file)
    
    print(f"\nProses selesai! File output: {output_file}")

if __name__ == "__main__":
    main()
