# Premium Quiz Studio V2

## Yang ditingkatkan
- Dashboard edit kuis Inggris/Indonesia.
- Empat tema warna dan pilihan resolusi 9:16.
- Scene hook, pertanyaan, countdown per detik, reveal jawaban, fakta, dan CTA.
- Upload gambar objek sendiri dan opsi upload musik.
- Opsi voice-over TTS melalui edge-tts (butuh internet).
- Export MP4 H.264 dan ZIP berisi PNG tiap scene.
- Tetap memakai bank kuis bilingual `quiz_bank.json`.

## Update repository GitHub yang sudah ada
1. Buka repository `3Dgokil/quiz_studio`.
2. Upload dan replace `app.py`, `requirements.txt`, dan `README_ID.md` dari ZIP ini.
3. Tambahkan file baru `packages.txt` (isi satu baris: `ffmpeg`).
4. Jangan hapus `quiz_bank.json` yang sudah ada. Bank dari ZIP ini bisa dipakai jika ingin mengganti seluruh bank.
5. Commit perubahan ke branch `main`.
6. Tunggu Streamlit Cloud redeploy, lalu refresh aplikasi.

## Catatan deployment
- Streamlit Community Cloud membaca `packages.txt` untuk apt packages seperti FFmpeg.
- Jika voice-over diaktifkan, `edge-tts` menggunakan koneksi internet. Jika gagal, matikan opsi TTS dan render video tanpa suara, lalu coba lagi.
- MP4 adalah video slide grafis dengan countdown per detik; bukan animasi karakter 3D penuh.
- Upload gambar yang kamu punya hak untuk gunakan. Periksa fakta dan jawaban sebelum publikasi.

## Menjalankan lokal di Termux
```bash
pkg update
pkg install python ffmpeg
pip install -r requirements.txt
streamlit run app.py --server.address 0.0.0.0
```
