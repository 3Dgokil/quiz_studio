# Premium Quiz Studio — Paket Bilingual

## Isi paket
- `app.py`: aplikasi Streamlit untuk memilih, mengedit, mem-preview, dan merender video kuis MP4.
- `quiz_bank.json`: 120 template kuis edukasi berbahasa Inggris dan Indonesia.
- `requirements.txt`: dependensi Python.
- `output/`: folder hasil video dan PNG.

## Jalankan di PC
1. Install Python 3.10+ dan FFmpeg.
2. Buka terminal di folder ini.
3. Jalankan:
   ```bash
   python -m venv .venv
   # Windows: .venv\\Scripts\\activate
   # macOS/Linux: source .venv/bin/activate
   pip install -r requirements.txt
   streamlit run app.py
   ```
4. Buka URL lokal yang ditampilkan Streamlit.
5. Pilih kategori dan template, edit pertanyaan/jawaban, lalu klik **Generate MP4 + PNG scene**.

## Jalankan di Termux Android
```bash
pkg update
pkg install python ffmpeg
pip install streamlit pillow
cd premium_quiz_studio
streamlit run app.py --server.address 0.0.0.0
```
Buka `http://127.0.0.1:8501` di browser Android.

## Catatan penting
- Aplikasi membuat video slideshow 9:16 dengan 6 scene grafis, serta file PNG tiap scene.
- MP4 awal tidak memiliki voice-over atau musik; tambahkan narasi/TTS dan musik bebas lisensi di editor video.
- Bank berisi 120 variasi kuis bilingual. Periksa fakta dan jawaban sebelum publikasi.
- Template ini menggunakan desain grafis generatif berbasis Pillow, bukan file Canva editable.
