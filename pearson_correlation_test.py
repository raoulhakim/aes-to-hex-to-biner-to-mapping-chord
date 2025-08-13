#!/usr/bin/env python3
import os
import sys
import base64
import binascii
import numpy as np
import argparse
from scipy.stats import pearsonr
from Crypto.Cipher import AES
from app.utils.encrypt_utils import encrypt_aes
from app.utils.decrypt_utils import decrypt_aes

def pad_text(plaintext):
    """Menambahkan padding pada plaintext agar panjangnya kelipatan 16."""
    padding_length = 16 - (len(plaintext) % 16)
    return plaintext + (chr(padding_length) * padding_length)

def calculate_pearson_correlation(text1, text2):
    """Menghitung korelasi Pearson berdasarkan nilai ASCII karakter."""
    print(f"Teks 1: {text1}")
    print(f"Teks 2: {text2}")
    
    ascii1 = [ord(char) for char in text1]
    ascii2 = [ord(char) for char in text2]
    
    min_len = min(len(ascii1), len(ascii2))
    ascii1 = ascii1[:min_len]
    ascii2 = ascii2[:min_len]
    
    print(f"ASCII 1 (dipotong): {ascii1[:10]}...")
    print(f"ASCII 2 (dipotong): {ascii2[:10]}...")
    
    correlation, _ = pearsonr(ascii1, ascii2)
    return correlation

def text_to_binary(text):
    """Mengubah teks ke representasi biner berbasis byte (UTF-8)."""
    byte_data = text.encode('utf-8')
    return ''.join(format(b, '08b') for b in byte_data)

def hex_to_binary(hex_string):
    """Mengubah ciphertext hex ke representasi biner berbasis byte."""
    try:
        byte_data = binascii.unhexlify(hex_string)
    except binascii.Error:
        return ''
    return ''.join(format(b, '08b') for b in byte_data)

def summarize_binary(binary_string):
    n = len(binary_string)
    if n <= 80:
        return binary_string
    first_part = binary_string[:9999999]
    # last_part = binary_string[-40:]
    return f"{first_part}"

def calculate_binary_pearson(plaintext_text, ciphertext_hex):
    """Menghitung korelasi Pearson antara biner plaintext dan biner AES ciphertext (bytes)."""
    bin_plain = [int(b) for b in text_to_binary(plaintext_text)]
    bin_cipher = [int(b) for b in hex_to_binary(ciphertext_hex)]

    if not bin_plain or not bin_cipher:
        raise ValueError("Representasi biner kosong. Periksa input plaintext atau ciphertext hex.")

    min_len = min(len(bin_plain), len(bin_cipher))
    bin_plain = bin_plain[:min_len]
    bin_cipher = bin_cipher[:min_len]

    correlation, _ = pearsonr(bin_plain, bin_cipher)
    return correlation

def encrypt_text_with_aes(plaintext, key):
    """Mengenkripsi teks menggunakan AES dan mengembalikan ciphertext."""
    try:
        # Gunakan fungsi dari encrypt_utils
        ciphertext_hex = encrypt_aes(plaintext, key)
        
        # Konversi hex ke bytes dan kemudian ke base64
        ciphertext_bytes = binascii.unhexlify(ciphertext_hex)
        ciphertext_base64 = base64.b64encode(ciphertext_bytes).decode()
        
        return ciphertext_base64, ciphertext_hex
    except Exception as e:
        print(f"Error saat enkripsi: {str(e)}")
        return None, None

def manual_encrypt_aes(plaintext, key):
    """Implementasi enkripsi AES manual untuk verifikasi."""
    # Padding plaintext
    padded_text = pad_text(plaintext)
    
    # Inisialisasi cipher
    cipher = AES.new(key.encode(), AES.MODE_ECB)
    
    # Enkripsi
    ciphertext = cipher.encrypt(padded_text.encode())
    
    # Konversi ke base64
    ciphertext_base64 = base64.b64encode(ciphertext).decode()
    
    # Konversi ke hex
    ciphertext_hex = binascii.hexlify(ciphertext).decode()
    
    return ciphertext_base64, ciphertext_hex

def test_correlation(messages, passwords):
    """Menguji korelasi antara plaintext dan ciphertext."""
    results = []
    
    print("\n" + "="*80)
    print("PENGUJIAN KORELASI PEARSON".center(80))
    print("="*80)
    
    for i, (message, password) in enumerate(zip(messages, passwords)):
        print(f"\nUji #{i+1}:")
        print(f"Pesan: {message}")
        print(f"Password: {password}")
        
        # Enkripsi menggunakan AES
        ciphertext_base64, ciphertext_hex = encrypt_text_with_aes(message, password)
        
        if not ciphertext_base64:
            print("Gagal mengenkripsi pesan.")
            continue
        
        # Verifikasi dengan enkripsi manual
        manual_base64, manual_hex = manual_encrypt_aes(message, password)
        
        # print(f"Ciphertext (Base64): {ciphertext_base64}")
        # print(f"Ciphertext (Hex): {ciphertext_hex[:30]}...")
        
        # Hitung korelasi Biner antara plaintext dan AES ciphertext (bytes)
        print("\nKorelasi Biner (Plaintext vs AES Biner):")
        try:
            # Representasi biner dari plaintext (berbasis byte)
            plaintext_binary = text_to_binary(message)

            # Representasi biner dari ciphertext AES (dari bytes, sumber: hex)
            aes_binary = hex_to_binary(ciphertext_hex)

            print(f"Plaintext (binary): {summarize_binary(plaintext_binary)}")
            print(f"AES Ciphertext (binary): {summarize_binary(aes_binary)}")

            # Korelasi Pearson antara dua deret biner
            binary_correlation = calculate_binary_pearson(message, ciphertext_hex)
            print(f"Korelasi Pearson (Biner): {binary_correlation:.6f}")
        except Exception as e:
            print(f"Error pada perhitungan korelasi Biner: {str(e)}")
            binary_correlation = None
        
        # Simpan hasil
        results.append({
            'message': message,
            'password': password,
            'ciphertext_base64': ciphertext_base64,
            'ciphertext_hex': ciphertext_hex,
            'binary_correlation': binary_correlation
        })
        
        print("-"*80)
    
    # Tampilkan ringkasan
    print("\n" + "="*80)
    print("RINGKASAN HASIL KORELASI PEARSON".center(80))
    print("="*80)
    print(f"{'#':<3} {'Panjang':<10} {'Binary Correlation':<20}")
    print("-"*80)
    
    for i, result in enumerate(results):
        msg_len = len(result['message'])
        binary_corr = result['binary_correlation']
        
        binary_str = f"{binary_corr:.6f}" if binary_corr is not None else "N/A"
        
        print(f"{i+1:<3} {msg_len:<10} {binary_str:<20}")
    
    print("="*80)
    
    return results

def main():
    """Fungsi utama untuk menjalankan pengujian korelasi."""
    parser = argparse.ArgumentParser(description="Uji Korelasi Pearson untuk Enkripsi AES")
    parser.add_argument('--custom', action='store_true', help="Gunakan input kustom alih-alih preset")
    args = parser.parse_args()
    
    if args.custom:
        # Gunakan input kustom
        messages = []
        passwords = []
        
        num_tests = int(input("Masukkan jumlah pengujian: "))
        
        for i in range(num_tests):
            print(f"\nPengujian #{i+1}:")
            message = input("Masukkan pesan: ")
            password = input("Masukkan password (16 karakter): ")
            
            # Validasi password
            while len(password) != 16:
                print("Password harus tepat 16 karakter!")
                password = input("Masukkan password (16 karakter): ")
            
            messages.append(message)
            passwords.append(password)
    else:
        # Gunakan preset untuk pengujian
        messages = [
            "iaH",
            "Hai123",
            "TestPassword1234",
            "4321drowssaPtseT",
            "5",                    # 3 karakter
            # "Sampai jumpa besok",                                                     # 16 karakter
            # "Terima kasih atas bantuannya kemarin",                                   # 30 karakter
            # "Saya sedang mengerjakan tugas kuliah tentang steganografi audio dan enkripsi data",  # 75 karakter
            # "Akhir pekan ini saya berencana mengunjungi pantai di Bali. Cuacanya diperkirakan cerah dengan sedikit awan. Kita bisa menikmati matahari terbenam sambil makan malam."  # 150 karakter
        ]
        
        passwords = [
            "TestPassword1234",
            "TestPassword1234",
            "TestPassword1234",
            "TestPassword1234",
            "5555555555555555"
        ]
    
    # Jalankan pengujian
    test_correlation(messages, passwords)

if __name__ == "__main__":
    main() 