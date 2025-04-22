from Crypto.Cipher import AES
import binascii
import os
from scipy.io.wavfile import write, read
import numpy as np

# Fungsi padding untuk AES
def pad(text):
    while len(text) % 16 != 0:
        text += " "
    return text

# Fungsi enkripsi AES (ECB Mode)
def encrypt_aes(plaintext, key):
    cipher = AES.new(key.encode(), AES.MODE_ECB)
    padded_text = pad(plaintext)
    ciphertext = cipher.encrypt(padded_text.encode())
    return binascii.hexlify(ciphertext).decode()

# Konversi HEX ke Biner
def hex_to_binary(hex_string):
    return bin(int(hex_string, 16))[2:].zfill(len(hex_string) * 4)

# Mapping nada lagu Mary Had a Little Lamb dengan ketukan
song_notes = [
    ("E", 1), ("D", 0.5), ("C", 0.5), ("D", 0.5), ("E", 0.5), ("E", 0.5), ("E", 2),
    ("D", 1), ("D", 1), ("D", 2), ("E", 1), ("G", 1), ("G", 2),
    ("E", 1), ("D", 1), ("C", 1), ("D", 1), ("E", 1), ("E", 1), ("E", 2)
]

# Pemetaan nada ke kode biner
note_mapping = {
    "C-PianoChord": "00",
    "D-PianoChord": "01",
    "E-PianoChord": "10",
    "G-PianoChord": "11"
}

# Reverse mapping untuk menemukan nada berdasarkan biner
binary_to_note = {v: k for k, v in note_mapping.items()}

# Fungsi menyisipkan pesan ke dalam nada lagu dengan perulangan dan ketukan yang sesuai
def map_message_to_song(binary_message):
    binary_pairs = [binary_message[i:i+2] for i in range(0, len(binary_message), 2)]
    mapped_notes = []
    
    print("\n=== Pemetaan Pesan ke Lagu ===")
    
    song_length = len(song_notes)
    repeat_count = 0
    i = 0
    
    for binary_pair in binary_pairs:
        note_index = i % song_length  # Looping jika melebihi panjang lagu
        note, duration = song_notes[note_index]  # Ambil nada dan ketukannya
        
        if note_index == 0 and i != 0:
            repeat_count += 1
            print(f"\n--- Lagu Diulang (ke-{repeat_count}) ---")
        
        if binary_pair in binary_to_note:
            mapped_notes.append((binary_pair, duration))  # Simpan biner + durasi
            print(f"{binary_pair} -> {note} (Ketukan: {duration})")
        else:
            print(f"{binary_pair} -> [Tidak cocok, dilewati]")
        
        i += 1

    return mapped_notes

# Fungsi untuk membangun file audio berdasarkan pemetaan biner dan ketukan
def generate_wave_file(mapped_notes, chord_folder, output_file):
    sample_rate = 44100
    combined_audio = np.array([], dtype=np.int16)

    for binary_pair, duration in mapped_notes:
        if binary_pair in binary_to_note:
            note = binary_to_note[binary_pair]
            audio_file = os.path.join(chord_folder, f"{note}.wav")
            
            if os.path.exists(audio_file):
                _, data = read(audio_file)
                if len(data.shape) > 1:
                    data = data[:, 0]

                # Sesuaikan durasi berdasarkan ketukan (misalnya, 1 beat = 0.5 detik)
                beat_duration = int(sample_rate * 0.5 * duration)
                if len(data) > beat_duration:
                    data = data[:beat_duration]  # Potong jika terlalu panjang
                else:
                    silence = np.zeros(beat_duration - len(data), dtype=np.int16)
                    data = np.concatenate((data, silence))  # Tambahkan silence jika kurang
                
                combined_audio = np.append(combined_audio, data)
            else:
                print(f"Warning: {audio_file} tidak ditemukan!")

    write(output_file, sample_rate, combined_audio)
    print(f"File audio berhasil dibuat: {output_file}")

# Data awal
plaintext = "Ramadan"
key = "passwordpassword"  # 16-byte key
chord_folder = "C:\\Users\\raoulhakim\\OneDrive\\Documents\\SEMPROOOOOOOOOOOO\\dummystegano\\aes to hex to biner to mapping chord\\Chord"
output_audio = "output_music_mhal.wav"

# Enkripsi AES
cipher_hex = encrypt_aes(plaintext, key)
print(f"Hasil Enkripsi (HEX): {cipher_hex}")

# Konversi ke biner
cipher_binary = hex_to_binary(cipher_hex)
print(f"Hasil Enkripsi (Biner): {cipher_binary}")

# Pemetaan biner ke lagu Mary Had a Little Lamb dengan ketukan yang sesuai
mapped_notes = map_message_to_song(cipher_binary)

# Generate file wave dengan hasil steganografi
generate_wave_file(mapped_notes, chord_folder, output_audio)
