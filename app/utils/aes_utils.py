import os
import binascii
from Crypto.Cipher import AES

def pad_text(plaintext):
    """Menambahkan padding pada plaintext agar panjangnya kelipatan 16."""
    padding_length = 16 - (len(plaintext) % 16)
    return plaintext + (chr(padding_length) * padding_length)

def encrypt_aes(plaintext, key):
    """Mengenkripsi plaintext menggunakan AES."""
    # Validasi panjang kunci - harus persis 16 karakter
    if len(key) != 16:
        raise ValueError(f"Panjang kunci harus 16 karakter, bukan {len(key)}.")
    
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