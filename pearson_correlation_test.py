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
    """Mengubah teks ke representasi biner."""
    return ''.join(format(ord(c), '08b') for c in text)

def summarize_binary(binary_string):
    """Meringkas string biner dengan mengambil bagian awal dan akhir."""
    first_part = binary_string[:80]  # 10 karakter x 8 bit
    last_part = binary_string[-40:]  # 5 karakter x 8 bit
    return f"{first_part}...{last_part}"

def calculate_binary_pearson(text1, text2):
    """Menghitung korelasi Pearson berdasarkan representasi biner."""
    bin1 = [int(b) for b in text_to_binary(text1)]
    bin2 = [int(b) for b in text_to_binary(text2)]
    
    min_len = min(len(bin1), len(bin2))
    bin1 = bin1[:min_len]
    bin2 = bin2[:min_len]
    
    correlation, _ = pearsonr(bin1, bin2)
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
        
        print(f"Ciphertext (Base64): {ciphertext_base64}")
        print(f"Ciphertext (Hex): {ciphertext_hex[:30]}...")
        
        # Hitung korelasi ASCII menggunakan representasi Base64
        print("\nKorelasi ASCII (menggunakan Base64):")
        try:
            # Gunakan string Base64 langsung untuk perbandingan
            ascii_correlation = calculate_pearson_correlation(message, ciphertext_base64)
            print(f"Korelasi Pearson (ASCII dengan Base64): {ascii_correlation:.6f}")
        except Exception as e:
            print(f"Error pada perhitungan korelasi ASCII: {str(e)}")
            ascii_correlation = None
        
        # Hitung korelasi Biner menggunakan representasi biner langsung
        print("\nKorelasi Biner:")
        try:
            # Representasi biner dari plaintext
            plaintext_binary = text_to_binary(message)
            
            # Representasi biner dari Base64 ciphertext
            base64_binary = text_to_binary(ciphertext_base64)
            
            print(f"Plaintext (binary): {summarize_binary(plaintext_binary)}")
            print(f"Base64 Ciphertext (binary): {summarize_binary(base64_binary)}")
            
            # Hitung korelasi antara representasi biner plaintext dan Base64 ciphertext
            binary_correlation = calculate_binary_pearson(message, ciphertext_base64)
            print(f"Korelasi Pearson (Biner dengan Base64): {binary_correlation:.6f}")
        except Exception as e:
            print(f"Error pada perhitungan korelasi Biner: {str(e)}")
            binary_correlation = None
        
        # Simpan hasil
        results.append({
            'message': message,
            'password': password,
            'ciphertext_base64': ciphertext_base64,
            'ciphertext_hex': ciphertext_hex,
            'ascii_correlation': ascii_correlation,
            'binary_correlation': binary_correlation
        })
        
        print("-"*80)
    
    # Tampilkan ringkasan
    print("\n" + "="*80)
    print("RINGKASAN HASIL KORELASI PEARSON".center(80))
    print("="*80)
    print(f"{'#':<3} {'Panjang':<10} {'ASCII Correlation':<20} {'Binary Correlation':<20}")
    print("-"*80)
    
    for i, result in enumerate(results):
        msg_len = len(result['message'])
        ascii_corr = result['ascii_correlation']
        binary_corr = result['binary_correlation']
        
        ascii_str = f"{ascii_corr:.6f}" if ascii_corr is not None else "N/A"
        binary_str = f"{binary_corr:.6f}" if binary_corr is not None else "N/A"
        
        print(f"{i+1:<3} {msg_len:<10} {ascii_str:<20} {binary_str:<20}")
    
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
            "Hai",                                                                    # 3 karakter
            "Sampai jumpa besok",                                                     # 16 karakter
            "Terima kasih atas bantuannya kemarin",                                   # 30 karakter
            "Saya sedang mengerjakan tugas kuliah tentang steganografi audio dan enkripsi data",  # 75 karakter
            "Akhir pekan ini saya berencana mengunjungi pantai di Bali. Cuacanya diperkirakan cerah dengan sedikit awan. Kita bisa menikmati matahari terbenam sambil makan malam."  # 150 karakter
        ]
        
        passwords = [
            "TestPassword1234",
            "Stegano123Audio4",
            "AudioSecret12345",
            "Sec#Audio@123456",
            "PesanRahasia2023"
        ]
    
    # Jalankan pengujian
    test_correlation(messages, passwords)

if __name__ == "__main__":
    main() 