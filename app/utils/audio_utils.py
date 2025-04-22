import os
import wave
import struct
import json
import numpy as np
from scipy.io import wavfile
import uuid
from app.utils.aes_utils import hex_to_binary, binary_to_hex

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
    """Menyiapkan pola lagu dengan memetakan segmen biner ke nada yang ditentukan."""
    # Bagi binary string menjadi segmen 2-bit
    binary_segments = [binary_string[i:i+2] for i in range(0, len(binary_string), 2)]
    
    song_pattern = []
    binary_mapping = {}
    used_binary = []
    
    song_repeat_count = 0
    binary_index = 0
    
    # Iterasi melalui semua segmen biner menggunakan pola lagu yang berulang
    while binary_index < len(binary_segments):
        # Reset jika mencapai akhir pola lagu
        if song_repeat_count > 0:
            # Tambahkan jeda 2 detik di antara perulangan
            song_pattern.append(("PAUSE", 4.0, "00"))  # 4.0 durasi = 2 detik (karena 1.0 = 0.5 detik)
        
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
                
            binary_index += 1
            
        song_repeat_count += 1
    
    return song_pattern, binary_mapping, "".join(used_binary)

def generate_music_from_prepared_song(song_pattern, chord_dir):
    """Membuat musik dari pola lagu yang telah disiapkan dengan biner."""
    sample_rate = 44100
    audio_segments = []
    note_positions = [0]
    position = 0
    
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
            continue
            
        # Tentukan file chord berdasarkan nada
        chord_prefix = note
        chord_filename = f"{chord_prefix}-PianoChord.wav"
        chord_path = os.path.join(chord_dir, chord_filename)
        
        if not os.path.exists(chord_path):
            # Coba gunakan file alternatif berdasarkan binary mapping
            chord_filename = binary_to_chord.get(binary, "C-PianoChord.wav")  # Default ke C jika tidak ada
            chord_path = os.path.join(chord_dir, chord_filename)
            
            if not os.path.exists(chord_path):
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
            
        except Exception as e:
            print(f"Error saat membaca {chord_path}: {e}")
    
    if not audio_segments:
        raise ValueError("Tidak ada segmen audio yang valid!")
    
    # Gabungkan semua segmen audio
    try:
        combined_audio = np.concatenate(audio_segments)
        return combined_audio, sample_rate, note_positions
    except ValueError as e:
        raise ValueError(f"Error saat menggabungkan audio: {e}")

def add_metadata_to_wav(audio_data, sample_rate, metadata, output_file):
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

def binary_to_audio(hex_string, output_dir="app/static/uploads", chord_dir="Chord"):
    """Fungsi utama untuk konversi hex ke audio steganografi."""
    # Konversi hex ke biner
    binary = hex_to_binary(hex_string)
    
    # Menyiapkan pola lagu dengan pemetaan biner
    song_pattern, binary_mapping, used_binary = prepare_song_with_binary(binary)
    
    # Membuat musik dari pola lagu yang telah disiapkan
    audio_data, sample_rate, note_positions = generate_music_from_prepared_song(song_pattern, chord_dir)
    
    # Buat metadata
    metadata = {
        "song_type": "mary_had_a_little_lamb_prepared",
        "song_name": "stegano_music_prepared",
        "note_positions": note_positions,
        "binary_mapping": binary_mapping,
        "cipher_binary": binary,
        "key_length": 16
    }
    
    # Buat nama file unik
    output_filename = f"stegano_{uuid.uuid4().hex[:8]}.wav"
    output_path = os.path.join(output_dir, output_filename)
    
    # Pastikan direktori output ada
    os.makedirs(output_dir, exist_ok=True)
    
    # Simpan musik dengan metadata
    add_metadata_to_wav(audio_data, sample_rate, metadata, output_path)
    
    return output_filename

def extract_binary_from_audio(audio_path):
    """Ekstrak data biner dari file audio steganografi."""
    # Ekstrak metadata
    metadata = extract_metadata_from_wav(audio_path)
    
    # Dapatkan urutan biner dari metadata
    binary_sequence = get_binary_sequence_from_metadata(metadata)
    
    # Konversi biner ke hex
    hex_string = binary_to_hex(binary_sequence)
    
    return hex_string 