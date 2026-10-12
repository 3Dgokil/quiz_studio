import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
from pathlib import Path
import json, os, shutil, subprocess, tempfile, zipfile, re, time

ROOT = Path(__file__).parent
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)
BANK_PATH = ROOT / "quiz_bank.json"
DATA = json.loads(BANK_PATH.read_text(encoding="utf-8")) if BANK_PATH.exists() else []

st.set_page_config(page_title="Premium Quiz Studio V2", page_icon="🎯", layout="wide")
st.title("🎯 Premium Quiz Studio")
st.caption("Satu dashboard • mode Kids & 18+ • Indonesia/English • countdown • export MP4")

with st.sidebar:
    st.header("⚙️ Pengaturan")
    mode = st.radio("Pilih mode channel", ["KIDS", "NON-KIDS (18+)"], help="Pilih mode untuk menyesuaikan bank soal dan gaya visual.")
    bank_path = ROOT / ("quiz_bank.json" if mode == "KIDS" else "adult_quiz_bank.json")
    try:
        DATA = json.loads(bank_path.read_text(encoding="utf-8"))
    except Exception:
        DATA = []
    language = st.selectbox("Bahasa / Language", ["Indonesia", "English"])
    if not DATA:
        st.error(f"Bank kuis untuk mode {mode} tidak ditemukan. Pastikan file {bank_path.name} ada di repository.")
        st.stop()
    category = st.selectbox("Kategori", sorted(set(q.get("category", "General") for q in DATA)))
    theme_options = ["Kids Pop", "Ocean Blue", "Candy 3D"] if mode == "KIDS" else ["Premium Purple", "Neon Arcade", "Midnight Gold"]
    theme = st.selectbox("Tema visual", theme_options)
    resolution_label = st.selectbox("Resolusi", ["1080 × 1920 (Full HD)", "720 × 1280 (Preview cepat)"])
    width, height = (1080, 1920) if resolution_label.startswith("1080") else (720, 1280)
    fps = st.selectbox("FPS", [24, 25, 30], index=2)
    question_seconds = st.slider("Durasi pertanyaan (detik)", 3, 8, 5)
    countdown_seconds = st.slider("Durasi countdown", 3, 5, 5)
    reveal_seconds = st.slider("Durasi jawaban/fakta", 3, 7, 5)
    make_voice = st.checkbox("Buat voice-over otomatis (butuh koneksi internet)", value=False)
    voice_gender = st.selectbox("Gaya suara TTS", ["Female", "Male"])
    add_music = st.checkbox("Tambahkan musik latar dari file sendiri", value=False)

themes = {
    "Kids Pop": {"bg": (19, 105, 174), "accent": (48, 191, 142), "yellow": (255, 207, 61), "ink": (28, 28, 66)},
    "Ocean Blue": {"bg": (5, 74, 125), "accent": (27, 153, 190), "yellow": (255, 214, 82), "ink": (13, 54, 88)},
    "Candy 3D": {"bg": (103, 57, 174), "accent": (255, 105, 170), "yellow": (255, 226, 93), "ink": (48, 28, 83)},
    "Premium Purple": {"bg": (35, 28, 105), "accent": (111, 75, 230), "yellow": (255, 207, 64), "ink": (31, 26, 77)},
    "Neon Arcade": {"bg": (13, 15, 38), "accent": (126, 48, 220), "yellow": (0, 245, 210), "ink": (20, 20, 44)},
    "Midnight Gold": {"bg": (18, 19, 27), "accent": (179, 128, 45), "yellow": (246, 205, 96), "ink": (36, 34, 30)}
}
T = themes[theme]

def get_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    for fp in candidates:
        if os.path.exists(fp):
            try: return ImageFont.truetype(fp, size)
            except: pass
    return ImageFont.load_default()

def wrap_lines(draw, text, fnt, max_w):
    lines = []
    for paragraph in str(text).split("\n"):
        words = paragraph.split()
        line = ""
        for word in words:
            candidate = (line + " " + word).strip()
            if draw.textbbox((0,0), candidate, font=fnt)[2] <= max_w:
                line = candidate
            else:
                if line: lines.append(line)
                line = word
        if line: lines.append(line)
        if not words: lines.append("")
    return lines

def draw_centered(draw, text, center_y, fnt, fill, max_w, stroke_width=0, stroke_fill=(0,0,0)):
    lines = wrap_lines(draw, text, fnt, max_w)
    line_h = int(fnt.size * 1.25)
    y = int(center_y - (len(lines) * line_h) / 2)
    for line in lines:
        box = draw.textbbox((0,0), line, font=fnt, stroke_width=stroke_width)
        x = (width - (box[2]-box[0])) // 2
        draw.text((x,y), line, font=fnt, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)
        y += line_h

def crop_image(source, target_size):
    im = source.convert("RGB")
    return ImageOps.fit(im, target_size, method=Image.Resampling.LANCZOS, centering=(0.5,0.45))

def make_scene(kind, title, subtitle="", options=None, answer="", fact="", uploaded_img=None, count=None, episode=1):
    im = Image.new("RGB", (width,height), T["bg"])
    d = ImageDraw.Draw(im)
    # decorative blobs, dots and rays
    d.ellipse((int(width*.68), -int(height*.06), int(width*1.13), int(height*.20)), fill=T["accent"])
    d.ellipse((-int(width*.19), int(height*.74), int(width*.28), int(height*1.02)), fill=T["accent"])
    for x,y,r in [(0.15,.22,.012),(.83,.28,.009),(.78,.68,.014),(.18,.80,.008),(.84,.83,.007)]:
        cx,cy,rr=int(width*x),int(height*y),int(width*r)
        d.ellipse((cx-rr,cy-rr,cx+rr,cy+rr),fill=T["yellow"])
    # main card
    d.rounded_rectangle((int(width*.055),int(height*.055),int(width*.945),int(height*.945)), radius=int(width*.055), fill=(250,249,255), outline=T["yellow"], width=max(3,width//220))
    d.rounded_rectangle((int(width*.10),int(height*.08),int(width*.90),int(height*.145)), radius=int(width*.025), fill=T["ink"])
    label = {"hook":"QUIZ TIME • WAKTUNYA KUIS","question":"CHOOSE YOUR ANSWER","countdown":"TIME'S UP SOON!","answer":"ANSWER REVEAL","fact":"DID YOU KNOW?","cta":"PLAY AGAIN!"}.get(kind,"PREMIUM QUIZ")
    draw_centered(d, label, int(height*.112), get_font(int(width*.031),True), (255,255,255), int(width*.72))
    d.rounded_rectangle((int(width*.76),int(height*.16),int(width*.88),int(height*.195)), radius=14, fill=T["yellow"])
    d.text((int(width*.775),int(height*.166)), f"#{episode:03d}", font=get_font(int(width*.021),True), fill=T["ink"])

    # Optional uploaded subject image gets a large rounded-ish panel area
    image_y0, image_y1 = int(height*.25), int(height*.56)
    if uploaded_img is not None and kind in ("question","answer","fact"):
        target_w = int(width*.66); target_h = int(height*.30)
        try:
            pic = crop_image(uploaded_img, (target_w,target_h))
            x0=(width-target_w)//2; y0=image_y0
            im.paste(pic,(x0,y0))
            d=ImageDraw.Draw(im)
            d.rounded_rectangle((x0,y0,x0+target_w,y0+target_h), radius=int(width*.035), outline=T["yellow"], width=max(3,width//180))
        except Exception:
            pass

    if kind == "hook":
        draw_centered(d, title, int(height*.36), get_font(int(width*.068),True), T["ink"], int(width*.72), 2, (255,255,255))
        draw_centered(d, subtitle, int(height*.48), get_font(int(width*.036),True), T["bg"], int(width*.70))
        # playful decorative badge
        d.rounded_rectangle((int(width*.20),int(height*.61),int(width*.80),int(height*.70)), radius=int(width*.04), fill=T["yellow"])
        draw_centered(d, "LET'S PLAY! • AYO MAIN!", int(height*.655), get_font(int(width*.035),True), T["ink"], int(width*.55))
    elif kind == "question":
        title_y = int(height*.22) if uploaded_img is not None else int(height*.32)
        draw_centered(d, title, title_y, get_font(int(width*.052),True), T["ink"], int(width*.72), 2, (255,255,255))
        if options:
            start_y = int(height*.60) if uploaded_img is not None else int(height*.48)
            row_h = int(height*.073)
            for i,opt in enumerate(options[:4]):
                yy = start_y + i*int(height*.083)
                d.rounded_rectangle((int(width*.14),yy,int(width*.86),yy+row_h), radius=int(width*.026), fill=(255,255,255), outline=T["accent"], width=max(2,width//320))
                color = [(237,72,76),(46,115,240),(255,190,35),(48,174,96)][i]
                d.ellipse((int(width*.17),yy+int(row_h*.13),int(width*.17)+int(row_h*.72),yy+int(row_h*.72)),fill=color)
                d.text((int(width*.17)+int(row_h*.22), yy+int(row_h*.18)), "ABCD"[i], font=get_font(int(width*.027), True), fill=(255,255,255))
                f=get_font(int(width*.031),True)
                lines=wrap_lines(d,opt,f,int(width*.50))
                d.text((int(width*.28),yy+int(row_h*.20)),lines[0][:36],font=f,fill=T["ink"])
    elif kind == "countdown":
        draw_centered(d, title, int(height*.30), get_font(int(width*.050),True), T["ink"], int(width*.74))
        circle_r=int(width*.20); cx=width//2; cy=int(height*.52)
        d.ellipse((cx-circle_r,cy-circle_r,cx+circle_r,cy+circle_r), fill=T["yellow"], outline=T["accent"], width=max(6,width//90))
        draw_centered(d, str(count if count is not None else "3"), cy, get_font(int(width*.20),True), T["ink"], int(width*.35))
        draw_centered(d, subtitle, int(height*.75), get_font(int(width*.034),True), T["bg"], int(width*.72))
    elif kind == "answer":
        draw_centered(d, title, int(height*.22), get_font(int(width*.055),True), T["ink"], int(width*.72))
        d.rounded_rectangle((int(width*.13),int(height*.60),int(width*.87),int(height*.70)), radius=int(width*.04), fill=(45,177,92))
        draw_centered(d, f"✓ {answer}", int(height*.65), get_font(int(width*.045),True), (255,255,255), int(width*.66))
        draw_centered(d, "GREAT JOB! • HEBAT!", int(height*.77), get_font(int(width*.035),True), T["bg"], int(width*.70))
    elif kind == "fact":
        draw_centered(d, title, int(height*.22), get_font(int(width*.05),True), T["ink"], int(width*.72))
        draw_centered(d, fact, int(height*.67 if uploaded_img is not None else height*.48), get_font(int(width*.036),True), T["ink"], int(width*.70))
    elif kind == "cta":
        draw_centered(d, title, int(height*.37), get_font(int(width*.065),True), T["ink"], int(width*.72))
        draw_centered(d, subtitle, int(height*.53), get_font(int(width*.037),True), T["bg"], int(width*.70))
        d.rounded_rectangle((int(width*.18),int(height*.66),int(width*.82),int(height*.75)), radius=int(width*.035), fill=(236,63,72))
        draw_centered(d, "SUBSCRIBE • IKUTI!", int(height*.705), get_font(int(width*.034),True), (255,255,255), int(width*.58))
    d.text((int(width*.12),int(height*.91)), ("QUIZ STUDIO • KIDS" if mode == "KIDS" else "QUIZ STUDIO • BRAIN CHALLENGE"), font=get_font(int(width*.018),True), fill=(105,100,130))
    return im

filtered = [q for q in DATA if q.get("category","General") == category]
def question_text(q):
    return q["en_question"] if language == "English" else q["id_question"]
titles = [f'{q["id"]:03d} • {question_text(q)}' for q in filtered]
idx = st.selectbox("Pilih template kuis", range(len(filtered)), format_func=lambda i: titles[i])
q = filtered[idx]

if language == "English":
    default_question, opts, correct, fact = q["en_question"], q["en_options"], q["en_answer"], q["en_fact"]
    hook_default = "Can you guess it before time runs out?" if mode == "KIDS" else "Think fast. Can you solve this challenge?"
    cta_default = "Comment your answer and subscribe for the next quiz!"
else:
    default_question, opts, correct, fact = q["id_question"], q["id_options"], q["id_answer"], q["id_fact"]
    hook_default = "Bisakah kamu menebak sebelum waktunya habis?" if mode == "KIDS" else "Asah otakmu. Bisa pecahkan tantangan ini?"
    cta_default = "Tulis jawabanmu dan ikuti untuk kuis berikutnya!"

st.subheader("1) Edit konten")
left, right = st.columns([1,1])
with left:
    hook = st.text_input("Hook / pembuka", hook_default)
    question = st.text_area("Pertanyaan", default_question, height=90)
    options_text = st.text_area("Pilihan jawaban (satu per baris)", "\n".join(opts), height=120)
    options = [x.strip() for x in options_text.splitlines() if x.strip()][:4]
    answer = st.text_input("Jawaban benar", correct)
    fact_text = st.text_area("Fakta menarik", fact, height=90)
    cta = st.text_input("CTA", cta_default)
    uploaded = st.file_uploader("Upload gambar objek kuis (opsional, JPG/PNG)", type=["jpg","jpeg","png"])
    uploaded_img = Image.open(uploaded).convert("RGB") if uploaded else None
    music_file = st.file_uploader("Upload musik latar (opsional, MP3/WAV)", type=["mp3","wav","m4a"]) if add_music else None
with right:
    st.markdown("#### Preview pertanyaan")
    preview = make_scene("question", question, options=options, uploaded_img=uploaded_img, episode=q["id"])
    st.image(preview, use_container_width=True)
    st.caption("Untuk gambar objek yang lebih bagus, upload ilustrasi milikmu sendiri. Jika tidak ada gambar, template tetap bisa dirender.")

st.subheader("2) Export video")
st.caption("Video berisi hook, pertanyaan, countdown, jawaban, fakta, dan CTA. Visual saat ini grafis 2D, belum animasi karakter 3D.")
if mode == "KIDS":
    st.info("Mode Kids: soal sederhana dan warna cerah. Pastikan pengaturan audiens YouTube sesuai jika konten memang ditujukan untuk anak.")
else:
    st.info("Mode Non-Kids (18+): teka-teki otak, logika angka, dan pengetahuan umum dengan tema lebih gelap. Label ini bukan berarti konten dewasa eksplisit.")
if st.button("🎬 Generate MP4 + PNG scenes", type="primary", use_container_width=True):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        st.error("FFmpeg belum tersedia di server. Pastikan repository memiliki packages.txt berisi: ffmpeg, lalu tunggu Streamlit selesai redeploy.")
        st.stop()
    if len(options) < 2:
        st.error("Masukkan minimal dua pilihan jawaban.")
        st.stop()
    # map answer text or letter to the displayed option
    answer_clean = answer.strip()
    if answer_clean.upper() in ["A","B","C","D"]:
        letter = answer_clean.upper()
        answer_display = options["ABCD".index(letter)] if "ABCD".index(letter) < len(options) else answer_clean
    else:
        answer_display = answer_clean
    if uploaded_img is None:
        # allow no-upload fallback; scene remains designed, but use simple icon only
        image_for_scenes = None
    else:
        image_for_scenes = uploaded_img

    scenes = []
    durations = []
    def add(im, dur):
        scenes.append(im); durations.append(float(dur))
    add(make_scene("hook", hook, "A quick challenge for curious minds!" if language=="English" else "Tantangan singkat untuk kamu!", uploaded_img=image_for_scenes, episode=q["id"]), 2.5)
    add(make_scene("question", question, options=options, uploaded_img=image_for_scenes, episode=q["id"]), float(question_seconds))
    for n in range(countdown_seconds,0,-1):
        add(make_scene("countdown", "LOCK IN YOUR ANSWER!" if language=="English" else "PILIH JAWABANMU!", "Choose now! • Pilih sekarang!", count=n, episode=q["id"]), 1.0)
    add(make_scene("answer", "THE ANSWER IS..." if language=="English" else "JAWABANNYA ADALAH...", answer=answer_display, uploaded_img=image_for_scenes, episode=q["id"]), float(reveal_seconds))
    add(make_scene("fact", "DID YOU KNOW?" if language=="English" else "TAHUKAH KAMU?", fact=fact_text, uploaded_img=image_for_scenes, episode=q["id"]), 4.0)
    add(make_scene("cta", "YOU DID GREAT!" if language=="English" else "KAMU HEBAT!", cta, episode=q["id"]), 3.5)

    stem = f"quiz_{'kids' if mode == 'KIDS' else 'nonkids'}_{q['id']:03d}_{language.lower()}"
    png_paths=[]
    for i, im in enumerate(scenes,1):
        p=OUT/f"{stem}_scene{i:02d}.png"
        im.save(p)
        png_paths.append(p)
    concat = OUT/f"{stem}_concat.txt"
    with concat.open("w",encoding="utf-8") as f:
        for p,dur in zip(png_paths,durations):
            f.write(f"file '{p.resolve().as_posix()}'\n")
            f.write(f"duration {dur}\n")
        f.write(f"file '{png_paths[-1].resolve().as_posix()}'\n")
    video = OUT/f"{stem}.mp4"
    cmd=[ffmpeg,"-y","-f","concat","-safe","0","-i",str(concat),"-vf",f"fps={fps},format=yuv420p","-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p",str(video)]
    result=subprocess.run(cmd,capture_output=True,text=True)
    if result.returncode != 0:
        st.error("Render video gagal.")
        st.code(result.stderr[-2500:])
        st.stop()

    # Optional TTS narration using edge-tts, then mux voice and optional music.
    voice_path = OUT/f"{stem}_voice.mp3"
    final_video = video
    voice_status = "Voice-over belum dibuat."
    if make_voice:
        edge = shutil.which("edge-tts")
        if not edge:
            st.warning("edge-tts belum terpasang. Tambahkan edge-tts di requirements.txt dan redeploy.")
        else:
            voice = "en-US-AriaNeural" if language=="English" and voice_gender=="Female" else \
                    "en-US-GuyNeural" if language=="English" else \
                    "id-ID-GadisNeural" if voice_gender=="Female" else "id-ID-ArdiNeural"
            narration = f"{hook}. {question}. Options: " + ", ".join(options) + f". The answer is {answer_display}. {fact_text}. {cta}" if language=="English" else f"{hook}. {question}. Pilihannya: " + ", ".join(options) + f". Jawabannya {answer_display}. {fact_text}. {cta}"
            tts = subprocess.run([edge,"--voice",voice,"--text",narration,"--write-media",str(voice_path)],capture_output=True,text=True)
            if tts.returncode == 0 and voice_path.exists():
                voiced = OUT/f"{stem}_voiced.mp4"
                muxcmd=[ffmpeg,"-y","-i",str(video),"-i",str(voice_path),"-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","160k","-shortest",str(voiced)]
                mux=subprocess.run(muxcmd,capture_output=True,text=True)
                if mux.returncode == 0:
                    final_video=voiced; voice_status="Voice-over otomatis berhasil dibuat."
                else:
                    st.warning("TTS selesai tetapi audio belum berhasil digabungkan.")
            else:
                st.warning("TTS gagal. Periksa koneksi cloud atau log Streamlit.")
    if add_music and music_file is not None:
        music_path=OUT/f"{stem}_music.{music_file.name.split('.')[-1].lower()}"
        music_path.write_bytes(music_file.getvalue())
        mixed=OUT/f"{stem}_final.mp4"
        if final_video == video:
            mixcmd=[ffmpeg,"-y","-i",str(video),"-i",str(music_path),"-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-filter:a","volume=0.15","-shortest",str(mixed)]
        else:
            mixcmd=[ffmpeg,"-y","-i",str(final_video),"-i",str(music_path),"-filter_complex","[0:a]volume=1.0[v];[1:a]volume=0.12[m];[v][m]amix=inputs=2:duration=first:dropout_transition=2[a]","-map","0:v:0","-map","[a]","-c:v","copy","-c:a","aac","-shortest",str(mixed)]
        mix=subprocess.run(mixcmd,capture_output=True,text=True)
        if mix.returncode == 0: final_video=mixed
        else: st.warning("Musik gagal digabung. Video tanpa musik tetap tersedia.")
    st.success(f"Render selesai. {voice_status}")
    st.video(str(final_video))
    st.download_button("⬇️ Download MP4", data=final_video.read_bytes(), file_name=final_video.name, mime="video/mp4", use_container_width=True)
    zip_path=OUT/f"{stem}_scenes.zip"
    with zipfile.ZipFile(zip_path,"w",zipfile.ZIP_DEFLATED) as z:
        for p in png_paths: z.write(p,p.name)
    st.download_button("⬇️ Download semua PNG scene", data=zip_path.read_bytes(), file_name=zip_path.name, mime="application/zip", use_container_width=True)
    st.info("Catatan: desain menggunakan grafis Pillow. Untuk hasil paling kaya, upload gambar objek yang sesuai. TTS memerlukan koneksi internet; suara/intonasi perlu diperiksa sebelum publikasi.")

st.subheader("3) Bank kuis")
st.write(f"Mode **{mode}**: **{len(DATA)} soal** tersedia. Ini jumlah soal di bank, bukan jumlah desain visual unik. Pilih bahasa dan kategori, edit teks, lalu render.")
st.download_button("⬇️ Download bank kuis JSON", data=json.dumps(DATA,ensure_ascii=False,indent=2), file_name=f"quiz_bank_{'kids' if mode == 'KIDS' else 'nonkids'}.json", mime="application/json")
