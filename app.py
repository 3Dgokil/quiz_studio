import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import json, os, random, subprocess, shutil, textwrap, tempfile
from pathlib import Path

ROOT = Path(__file__).parent
DATA = json.loads((ROOT / "quiz_bank.json").read_text(encoding="utf-8"))
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)

st.set_page_config(page_title="Premium Quiz Studio", page_icon="🎯", layout="wide")
st.title("🎯 Premium Quiz Studio")
st.caption("120+ bilingual quiz prompts • template designer • MP4 slide-video generator")
st.info("Membuat video kuis berbasis slide 9:16. Video hasil render memakai teks dan bentuk grafis; gambar karakter/objek bisa ditambahkan sebagai aset sendiri.")

with st.sidebar:
    st.header("⚙️ Pengaturan")
    lang = st.selectbox("Language / Bahasa", ["English", "Indonesia", "Bilingual"])
    category = st.selectbox("Category / Kategori", sorted(set(q["category"] for q in DATA)))
    theme = st.selectbox("Theme / Tema", ["Premium Purple", "Kids 3D Colors", "Neon Arcade", "Ocean Blue"])
    duration = st.slider("Durasi tiap scene (detik)", 2, 8, 4)
    fps = st.selectbox("FPS", [24, 25, 30], index=2)
    size = st.selectbox("Video size", ["1080 × 1920 (Shorts)", "720 × 1280 (Fast preview)"])
    width, height = (1080,1920) if size.startswith("1080") else (720,1280)

palette = {
    "Premium Purple": ((35, 28, 105), (111, 75, 230), (255, 207, 64), (255,255,255)),
    "Kids 3D Colors": ((17, 110, 176), (52, 190, 135), (255, 205, 55), (255,255,255)),
    "Neon Arcade": ((13, 15, 38), (110, 45, 210), (0, 245, 210), (255,255,255)),
    "Ocean Blue": ((5, 74, 125), (27, 153, 190), (255, 214, 82), (255,255,255))
}
bg, accent, highlight, white = palette[theme]

def font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"
    ]
    for f in candidates:
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()

def centered(draw, text, y, fnt, fill, max_width, stroke_width=0, stroke_fill=(0,0,0)):
    words = str(text).split()
    lines, line = [], ""
    for word in words:
        test = (line + " " + word).strip()
        if draw.textbbox((0,0), test, font=fnt, stroke_width=stroke_width)[2] <= max_width:
            line = test
        else:
            if line: lines.append(line)
            line = word
    if line: lines.append(line)
    line_h = fnt.size + 18
    for ln in lines:
        box = draw.textbbox((0,0), ln, font=fnt, stroke_width=stroke_width)
        x = (width - (box[2]-box[0]))//2
        draw.text((x,y), ln, font=fnt, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)
        y += line_h
    return y

def make_scene(title, subtitle="", options=None, footer="PREMIUM QUIZ STUDIO", reveal=None, number=None):
    im = Image.new("RGB", (width,height), bg)
    d = ImageDraw.Draw(im)
    # soft graphic rings and card
    d.ellipse((width*0.68,-height*0.04,width*1.12,height*0.20), fill=accent)
    d.ellipse((-width*0.18,height*0.73,width*0.28,height*1.02), fill=accent)
    d.rounded_rectangle((width*.055,height*.08,width*.945,height*.92), radius=int(width*.06), fill=(248,247,255), outline=highlight, width=max(3,width//180))
    d.rounded_rectangle((width*.10,height*.105,width*.90,height*.18), radius=int(width*.025), fill=accent)
    centered(d, "KIDS QUIZ • QUIZ ANAK", int(height*.125), font(int(width*.034),True), white, int(width*.72))
    if number:
        d.rounded_rectangle((width*.78,height*.205,width*.88,height*.245), radius=16, fill=highlight)
        d.text((width*.80,height*.211), f"#{number:03d}", font=font(int(width*.022),True), fill=bg)
    y = int(height*.24)
    y = centered(d, title, y, font(int(width*.065),True), bg, int(width*.72))
    if subtitle:
        y += int(height*.025)
        y = centered(d, subtitle, y, font(int(width*.038)), (75,74,100), int(width*.72))
    if options:
        y = max(y+int(height*.045), int(height*.48))
        for i,opt in enumerate(options):
            yy = y + i*int(height*.095)
            d.rounded_rectangle((width*.15,yy,width*.85,yy+int(height*.073)), radius=int(width*.025), fill=(255,255,255), outline=accent, width=max(2,width//300))
            d.ellipse((width*.18,yy+int(height*.012),width*.23,yy+int(height*.062)), fill=highlight)
            d.text((width*.193,yy+int(height*.018)), "ABCD"[i], font=font(int(width*.025),True), fill=bg)
            d.text((width*.26,yy+int(height*.018)), str(opt), font=font(int(width*.032),True), fill=bg)
    if reveal:
        d.rounded_rectangle((width*.13,height*.73,width*.87,height*.82), radius=int(width*.03), fill=highlight)
        centered(d, reveal, int(height*.755), font(int(width*.043),True), bg, int(width*.66))
    d.text((width*.12,height*.875), footer, font=font(int(width*.021),True), fill=(95,90,120))
    return im

st.subheader("1) Choose a quiz")
filtered = [q for q in DATA if q["category"] == category]
titles = [f'{q["id"]:03d} • {q["en_question"] if lang=="English" else q["id_title"]}' for q in filtered]
selected_idx = st.selectbox("Quiz template", range(len(filtered)), format_func=lambda i: titles[i])
q = filtered[selected_idx]
if lang == "English":
    question, options, answer, fact = q["en_question"], q["en_options"], q["en_answer"], q["en_fact"]
elif lang == "Indonesia":
    question, options, answer, fact = q["id_question"], q["id_options"], q["id_answer"], q["id_fact"]
else:
    question, options, answer, fact = q["en_question"] + "\n" + q["id_question"], q["en_options"], q["en_answer"] + " / " + q["id_answer"], q["en_fact"] + "\n" + q["id_fact"]

c1,c2 = st.columns([1,1])
with c1:
    st.markdown("#### Edit konten")
    question = st.text_area("Question / Pertanyaan", question, height=90)
    option_text = st.text_area("Options (one per line)", "\n".join(options), height=120)
    answer = st.text_input("Correct answer / Jawaban", answer)
    fact = st.text_area("Fun fact / Fakta menarik", fact, height=90)
    hook = st.text_input("Hook / Pembuka", "Can you get this right? / Bisa jawab dengan benar?")
    cta = st.text_input("CTA", "Comment your answer & subscribe! / Tulis jawabanmu & subscribe!")
with c2:
    st.markdown("#### Preview")
    preview = make_scene(hook, "A quick challenge for curious minds!", footer="PREMIUM QUIZ STUDIO", number=q["id"])
    st.image(preview, use_container_width=True)
    st.caption("Preview adalah contoh layout; MP4 terdiri dari scene hook, pertanyaan, countdown, jawaban, fakta, dan CTA.")

st.subheader("2) Export")
if st.button("🎬 Generate MP4 + PNG scene", type="primary", use_container_width=True):
    opts = [x.strip() for x in option_text.splitlines() if x.strip()][:4]
    if len(opts) < 2:
        st.error("Masukkan minimal dua pilihan jawaban.")
    else:
        scenes = [
            make_scene(hook, "READY? LET'S PLAY!", footer="HOOK • HOOK PEMBUKA", number=q["id"]),
            make_scene(question, "Choose the best answer / Pilih jawaban terbaik", opts, footer="QUESTION • PERTANYAAN", number=q["id"]),
            make_scene("5  •  4  •  3  •  2  •  1", "Lock in your answer! / Kunci jawabanmu!", footer="COUNTDOWN • HITUNG MUNDUR"),
            make_scene("ANSWER REVEAL", "", opts, footer="ANSWER • JAWABAN", reveal=answer),
            make_scene("DID YOU KNOW? / TAHUKAH KAMU?", fact, footer="FUN FACT • FAKTA MENARIK"),
            make_scene("YOU DID GREAT! / KAMU HEBAT!", cta, footer="CTA • AJAKAN")
        ]
        stem = f"quiz_{q['id']:03d}"
        frame_paths=[]
        for i,im in enumerate(scenes,1):
            p=OUT/f"{stem}_scene{i:02d}.png"; im.save(p); frame_paths.append(p)
        video_path=OUT/f"{stem}.mp4"
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            st.error("FFmpeg belum ditemukan. Install FFmpeg lalu jalankan ulang aplikasi.")
        else:
            # Create slideshow with concat demuxer; images become video, silent by design.
            concat = OUT/f"{stem}_concat.txt"
            with concat.open("w",encoding="utf-8") as f:
                for p in frame_paths:
                    f.write(f"file '{p.as_posix()}'\n")
                    f.write(f"duration {duration}\n")
                f.write(f"file '{frame_paths[-1].as_posix()}'\n")
            cmd=[ffmpeg,"-y","-f","concat","-safe","0","-i",str(concat),"-vf",f"fps={fps},format=yuv420p","-c:v","libx264","-pix_fmt","yuv420p",str(video_path)]
            result=subprocess.run(cmd,capture_output=True,text=True)
            if result.returncode == 0:
                st.success("MP4 dan PNG scene berhasil dibuat. Video ini belum memiliki voice-over atau musik.")
                st.video(str(video_path))
                st.download_button("⬇️ Download MP4", data=video_path.read_bytes(), file_name=video_path.name, mime="video/mp4")
                zpath=OUT/f"{stem}_scenes.zip"
                import zipfile
                with zipfile.ZipFile(zpath,"w",zipfile.ZIP_DEFLATED) as z:
                    for p in frame_paths: z.write(p,p.name)
                st.download_button("⬇️ Download semua PNG scene", data=zpath.read_bytes(), file_name=zpath.name, mime="application/zip")
            else:
                st.error("Render gagal. Pastikan FFmpeg mendukung libx264.")
                st.code(result.stderr[-2500:])

st.subheader("3) Batch template bank")
st.write(f"Template bank berisi **{len(DATA)} kuis** dalam kategori bilingual. Pilih kuis dari menu, edit teks, lalu generate.")
bank = [{"id":q["id"],"category":q["category"],"title":q["id_title"],"question_en":q["en_question"],"question_id":q["id_question"],"options_en":q["en_options"],"options_id":q["id_options"],"answer_en":q["en_answer"],"answer_id":q["id_answer"]} for q in DATA]
st.download_button("⬇️ Download bank kuis JSON", json.dumps(bank,ensure_ascii=False,indent=2), file_name="quiz_bank_bilingual.json", mime="application/json")
