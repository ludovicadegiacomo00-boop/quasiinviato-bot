"""Crea immagini e video nello stile Quasi inviato.

Tipi di contenuto (campo "type" in posts.json):
  post      immagine singola 1080x1350 (predefinito)
  carousel  più immagini 1080x1350, una per elemento di "slides"
  story     immagine verticale 1080x1920
  reel      video verticale 1080x1920: la frase si scrive, appaiono i tre puntini,
            poi si cancella ("quasi inviato")
La parola tra asterischi (*parola*) viene scritta in corsivo arancio.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

POST_SIZE, TALL_SIZE = (1080, 1350), (1080, 1920)
CREMA, NERO, ARANCIO, GRIGIO = "#F4EDE1", "#14110F", "#E8571F", "#8A8178"
HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 30

FONT_CANDIDATES = {
    "serif": ["fonts/PlayfairDisplay.ttf", "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"],
    "italic": ["fonts/PlayfairDisplay-Italic.ttf", "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"],
    "sans": ["fonts/Inter.ttf", "/usr/share/fonts/opentype/inter/Inter-Medium.otf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
}
_font_cache = {}


def font(kind, size):
    key = (kind, size)
    if key in _font_cache:
        return _font_cache[key]
    for path in FONT_CANDIDATES[kind]:
        full = path if os.path.isabs(path) else os.path.join(HERE, path)
        if os.path.exists(full):
            f = ImageFont.truetype(full, size)
            if "Playfair" in full:
                try:
                    f.set_variation_by_axes([400])
                except Exception:
                    pass
            _font_cache[key] = f
            return f
    raise FileNotFoundError(f"Nessun font trovato per {kind}")


def tokens(text):
    """Divide la frase in parole, segnando quelle evidenziate."""
    out = []
    for part in re.split(r"(\*[^*]+\*)", text):
        hl = part.startswith("*") and part.endswith("*")
        for w in part.strip("*").split():
            out.append((w, hl))
    return out


def layout(words, size, max_w):
    reg, ita = font("serif", size), font("italic", size)
    space = reg.getlength(" ")
    lines, line, lw = [], [], 0
    for w, hl in words:
        ww = (ita if hl else reg).getlength(w)
        if line and lw + space + ww > max_w:
            lines.append((line, lw))
            line, lw = [], 0
        lw += (space if line else 0) + ww
        line.append((w, hl, ww))
    if line:
        lines.append((line, lw))
    return lines, reg, ita, space


def fit(words, size_wh):
    W, H = size_wh
    size = 76 if H < 1600 else 84
    while True:
        lines, reg, ita, space = layout(words, size, 820)
        line_h = int(size * 1.32)
        if len(lines) * line_h <= H * 0.53 or size <= 44:
            return lines, reg, ita, space, line_h
        size -= 4


def draw_frame(text, theme, size_wh, time_label=None, counter=None, handle=None,
               visible_chars=None, dots=None, cursor=False):
    """Disegna un fotogramma. visible_chars limita i caratteri mostrati (per il Reel)."""
    W, H = size_wh
    night = theme == "night"
    bg, fg = (NERO, CREMA) if night else (CREMA, NERO)
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)

    lines, reg, ita, space, line_h = fit(tokens(text), size_wh)
    y = (H - len(lines) * line_h) // 2 - 30
    budget = visible_chars
    last_xy = None
    for line, lw in lines:
        x = (W - lw) / 2
        for w, hl, ww in line:
            f = ita if hl else reg
            shown = w if budget is None else w[:max(0, budget)]
            if shown:
                d.text((x, y), shown, font=f, fill=ARANCIO if hl else fg)
                last_xy = (x + f.getlength(shown), y)
            if budget is not None:
                budget -= len(w) + 1
            x += ww + space
        y += line_h
    if cursor:
        cx, cy = last_xy if last_xy else (W / 2, (H - line_h) // 2)
        d.rectangle((cx + 6, cy + 12, cx + 10, cy + line_h - 18), fill=ARANCIO)

    small = font("sans", 30)
    top = 56 if H < 1600 else 220  # nelle storie stiamo lontani dalla barra di Instagram
    if time_label:
        d.text((64, top), time_label, font=small, fill=GRIGIO)
    if counter:
        d.text((W - 64 - small.getlength(counter), top), counter, font=small, fill=GRIGIO)

    cy = H - (150 if H < 1600 else 380)
    r, gap = 9, 34
    colors = dots or [GRIGIO, GRIGIO, ARANCIO]
    for i, color in enumerate(colors):
        if color:
            cx = W / 2 + (i - 1) * gap
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
    handle = handle or os.environ.get("IG_HANDLE") or "@quasiinviato"
    hf = font("sans", 26)
    d.text(((W - hf.getlength(handle)) / 2, cy + 30), handle, font=hf, fill=GRIGIO)
    return img


def plain(text):
    return text.replace("*", "")


def render_reel(post, out_path):
    """Video: scrive la frase, tre puntini che pulsano, cancella, chiude con 'quasi inviato.'"""
    text, theme = post["text"], post.get("theme", "night")
    n = len(plain(text))
    frames = []
    kw = dict(theme=theme, size_wh=TALL_SIZE, time_label=post.get("time_label"))

    def add(img, count=1):
        frames.extend([img] * count)

    add(draw_frame(text, visible_chars=0, cursor=True, **kw), 12)
    for i in range(1, n + 1):                       # scrittura, 30 caratteri al secondo
        add(draw_frame(text, visible_chars=i, cursor=True, **kw), 1)
    full = draw_frame(text, **kw)
    add(full, 45)                                   # pausa per leggere
    for k in range(3):                              # "sta scrivendo..." che pulsa
        for lit in range(3):
            dots = [GRIGIO if j != lit else ARANCIO for j in range(3)]
            add(draw_frame(text, dots=dots, **kw), 7)
    for i in range(n, -1, -3):                      # cancellazione veloce
        add(draw_frame(text, visible_chars=i, cursor=True, **kw), 1)
    end = draw_frame("*quasi* inviato.", **kw)
    add(end, 45)

    tmp = tempfile.mkdtemp()
    try:
        last, idx = None, 0
        for img in frames:
            img.save(os.path.join(tmp, f"f{idx:05d}.png")) if img is not last else \
                shutil.copy(os.path.join(tmp, f"f{idx - 1:05d}.png"), os.path.join(tmp, f"f{idx:05d}.png"))
            last, idx = img, idx + 1
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(tmp, "f%05d.png"),
            "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high", "-r", str(FPS),
            "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out_path], check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def media_files(post):
    """Nomi dei file da pubblicare per un post."""
    t = post.get("type") or ("carousel" if post.get("slides") else "post")
    if t == "carousel":
        return [f"{post['id']}-{i + 1}.png" for i in range(len(post["slides"]))]
    if t == "reel":
        return [f"{post['id']}.mp4"]
    return [f"{post['id']}.png"]


image_files = media_files  # nome usato dalle versioni precedenti


def render(post):
    t = post.get("type") or ("carousel" if post.get("slides") else "post")
    files = [os.path.join(HERE, "images", f) for f in media_files(post)]
    kw = dict(theme=post.get("theme"), handle=post.get("handle"))
    if t == "carousel":
        n = len(post["slides"])
        for i, (text, path) in enumerate(zip(post["slides"], files)):
            draw_frame(text, size_wh=POST_SIZE, time_label=post.get("time_label") if i == 0 else None,
                       counter=f"{i + 1}/{n}", **kw).save(path)
    elif t == "story":
        draw_frame(post["text"], size_wh=TALL_SIZE, time_label=post.get("time_label"), **kw).save(files[0])
    elif t == "reel":
        render_reel(post, files[0])
    else:
        draw_frame(post["text"], size_wh=POST_SIZE, time_label=post.get("time_label"), **kw).save(files[0])
    return files


def main():
    with open(os.path.join(HERE, "posts.json"), encoding="utf-8") as f:
        posts = json.load(f)
    only = set(sys.argv[1:])
    os.makedirs(os.path.join(HERE, "images"), exist_ok=True)
    for p in posts:
        if (only and p["id"] not in only) or (not only and p.get("status") == "published"):
            continue
        for path in render(p):
            print("creato", os.path.basename(path))


if __name__ == "__main__":
    main()
