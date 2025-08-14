#!/usr/bin/env python3
import binascii
import argparse
from scipy.stats import pearsonr
from app.utils.encrypt_utils import encrypt_aes

 

def text_to_binary(text):
    byte_data = text.encode('utf-8')
    return ''.join(format(b, '08b') for b in byte_data)

def hex_to_binary(hex_string):
    try:
        byte_data = binascii.unhexlify(hex_string)
    except binascii.Error:
        return ''
    return ''.join(format(b, '08b') for b in byte_data)

def summarize_binary(binary_string):
    n = len(binary_string)
    if n <= 80:
        return binary_string
    first_part = binary_string[:80]
    last_part = binary_string[-40:]
    return f"{first_part}...{last_part}"

def calculate_binary_pearson(plaintext_text, ciphertext_hex):
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
    try:
        ciphertext_hex = encrypt_aes(plaintext, key)
        return ciphertext_hex
    except Exception as e:
        print(f"Error saat enkripsi: {str(e)}")
        return None

 

def test_correlation(messages, passwords):
    results = []
    
    print("\n" + "="*80)
    print("PENGUJIAN KORELASI PEARSON".center(80))
    print("="*80)
    
    for i, (message, password) in enumerate(zip(messages, passwords)):
        print(f"\nUji #{i+1}:")
        print(f"Pesan: {message}")
        print(f"Password: {password}")
        
        ciphertext_hex = encrypt_text_with_aes(message, password)
        
        if not ciphertext_hex:
            print("Gagal mengenkripsi pesan.")
            continue
        
        
        print("\nKorelasi Biner (Plaintext vs AES Biner):")
        try:
            plaintext_binary = text_to_binary(message)

            aes_binary = hex_to_binary(ciphertext_hex)

            print(f"Plaintext (binary): {summarize_binary(plaintext_binary)}")
            print(f"AES Ciphertext (binary): {summarize_binary(aes_binary)}")

            binary_correlation = calculate_binary_pearson(message, ciphertext_hex)
            print(f"Korelasi Pearson (Biner): {binary_correlation:.6f}")
        except Exception as e:
            print(f"Error pada perhitungan korelasi Biner: {str(e)}")
            binary_correlation = None
        
        results.append({
            'message': message,
            'password': password,
            'ciphertext_hex': ciphertext_hex,
            'binary_correlation': binary_correlation
        })
        
        print("-"*80)
    
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
    parser = argparse.ArgumentParser(description="Uji Korelasi Pearson untuk Enkripsi AES")
    parser.add_argument('--custom', action='store_true', help="Gunakan input kustom alih-alih preset")
    args = parser.parse_args()
    
    if args.custom:
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
        messages = [
            "Hai",
            "iaH",
            "Hai123",
            "TestPassword1234",
            "4321drowssaPtseT",
            "5",
            "Sampai jumpa besok",
            "Terima kasih atas bantuannya kemarin",
            "Saya sedang mengerjakan tugas kuliah tentang steganografi audio dan enkripsi data",
            "Akhir pekan ini saya berencana mengunjungi pantai di Bali. Cuacanya diperkirakan cerah dengan sedikit awan. Kita bisa menikmati matahari terbenam sambil makan malam."
        ]
        
        passwords = [
            "TestPassword1234",
            "TestPassword1234",
            "TestPassword1234",
            "TestPassword1234",
            "TestPassword1234",
            "5555555555555555",
            "TestPassword1234",
            "TestPassword1234",
            "TestPassword1234",
            "TestPassword1234",
        ]
    
    # Jalankan pengujian
    test_correlation(messages, passwords)

if __name__ == "__main__":
    main() 