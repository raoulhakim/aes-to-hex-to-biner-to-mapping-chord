from Crypto.Cipher import AES
import binascii
import os
from scipy.io.wavfile import write
from scipy.io.wavfile import read  
import numpy as np


def pad(text):
    # Padding agar panjangnya kelipatan 16
    while len(text) % 16 != 0:
        text += " "
    return text

def encrypt_aes(plaintext, key):
    cipher = AES.new(key.encode(), AES.MODE_ECB)
    padded_text = pad(plaintext)
    ciphertext = cipher.encrypt(padded_text.encode())
    return binascii.hexlify(ciphertext).decode()

def hex_to_binary(hex_string):
    return bin(int(hex_string, 16))[2:].zfill(len(hex_string) * 4)

def binary_to_music(binary_string, chord_folder):
    note_mapping = {
    "0000": "F-PianoChord.wav",
    "0001": "Fm-PianoChord.wav",
    "0010": "G-PianoChord.wav",
    "0011": "Gm-PianoChord.wav",
    "0100": "A-PianoChord.wav",
    "0101": "Am-PianoChord.wav",
    "0110": "B-PianoChord.wav",
    "0111": "Bm-PianoChord.wav",
    "1000": "C-PianoChord.wav",
    "1001": "Cm-PianoChord.wav",
    "1010": "D-PianoChord.wav",
    "1011": "Dm-PianoChord.wav",
    "1100": "E-PianoChord.wav",
    "1101": "Em-PianoChord.wav",
    "1110": "F#-PianoChord.wav",
    "1111": "F#m-PianoChord.wav",

    # "00": "DA.wav",
    # "01": "MA.wav",
    # "11": "NA.wav",
    # "10": "TI.wav",

    # "0000": "12.wav",
    # "0001": "5.wav",
    # "0010": "16.wav",
    # "0011": "7.wav",
    # "0100": "2.wav",
    # "0101": "11.wav",
    # "0110": "4.wav",
    # "0111": "15.wav",
    # "1000": "9.wav",
    # "1001": "6.wav",
    # "1010": "13.wav",
    # "1011": "3.wav",
    # "1100": "14.wav",
    # "1101": "1.wav",
    # "1110": "10.wav",
    # "1111": "8.wav",
    }

    audio_files = []
    print("\n=== Pemetaan Biner ke Nada ===")
    
    for i in range(0, len(binary_string), 4):
        binary_segment = binary_string[i:i+4]
        if binary_segment in note_mapping:
            audio_file = os.path.join(chord_folder, note_mapping[binary_segment])
            audio_files.append(audio_file)
            print(f"{binary_segment} -> {note_mapping[binary_segment]}")
        else:
            print(f"{binary_segment} -> [Nada tidak tersedia]")
    return audio_files

def generate_wave_file(audio_files, output_file):
    sample_rate = 44100
    combined_audio = np.array([], dtype=np.int16)
    
    for file in audio_files:
        if os.path.exists(file):
            _, data = read(file)
            if len(data.shape) > 1:
                data = data[:, 0]
            combined_audio = np.append(combined_audio, data)
        else:
            print(f"Warning: {file} tidak ditemukan!")
    
    write(output_file, sample_rate, combined_audio)
    print(f"File audio berhasil dibuat: {output_file}")

# Data awal
plaintext = "Ramadan"
key = "passwordpassword"  # 16-byte key
chord_folder = "C:\\Users\\raoulhakim\\OneDrive\\Documents\\SEMPROOOOOOOOOOOO\\dummystegano\\aes to hex to biner to mapping chord\\Chord"
output_audio = "output_music.wav"

# Enkripsi AES
cipher_hex = encrypt_aes(plaintext, key)
print(f"Hasil Enkripsi (HEX): {cipher_hex}")

# Konversi ke biner
cipher_binary = hex_to_binary(cipher_hex)
print(f"Hasil Enkripsi (Biner): {cipher_binary}")

# Konversi ke tangga nada
audio_files = binary_to_music(cipher_binary, chord_folder)

# Generate file wave
generate_wave_file(audio_files, output_audio)
