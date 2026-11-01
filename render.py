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
import wave
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import numpy as np

from PIL import Image, ImageDraw, ImageFont

POST_SIZE, TALL_SIZE = (1080, 1350), (1080, 1920)
CREMA, NERO, ARANCIO, GRIGIO = "#F4EDE1", "#14110F", "#E8571F", "#8A8178"
HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 30
SR = 44100
ROME = ZoneInfo("Europe/Rome")

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



# ---------- suono firma "quasi inviato" (generato qui, nessun diritto d'autore) ----------

def _env(n, attack, release):
    e = np.ones(n)
    a, r = int(attack * SR), int(release * SR)
    if a:
        e[:a] = np.linspace(0, 1, a)
    if r:
        e[-r:] *= np.linspace(1, 0, r)
    return e


def _pad(duration, seed=0):
    """Tappeto morbido: accordo di La minore 9 con tremolo lento."""
    t = np.arange(int(duration * SR)) / SR
    notes = [110.0, 164.81, 196.0, 246.94, 261.63]
    out = np.zeros_like(t)
    rng = np.random.default_rng(seed)
    for i, f in enumerate(notes):
        detune = 1 + rng.uniform(-0.002, 0.002)
        trem = 0.75 + 0.25 * np.sin(2 * np.pi * (0.15 + 0.05 * i) * t + i)
        out += trem * (np.sin(2 * np.pi * f * detune * t) + 0.25 * np.sin(4 * np.pi * f * detune * t)) / (i + 1.5)
    return 0.18 * out / np.max(np.abs(out)) * _env(len(t), 1.2, 1.5)


def _click(rng, pitch=1.0):
    n = int(0.018 * SR)
    noise = rng.standard_normal(n)
    noise = np.diff(np.concatenate([[0], noise]))  # toglie i bassi
    tone = np.sin(2 * np.pi * 2200 * pitch * np.arange(n) / SR) * 0.3
    return (noise * 0.6 + tone) * np.exp(-np.arange(n) / (0.003 * SR)) * rng.uniform(0.5, 1.0)


def _blip(freq, length=0.14):
    t = np.arange(int(length * SR)) / SR
    return 0.35 * np.sin(2 * np.pi * freq * t) * np.exp(-t / 0.05)


def make_audio(events, duration, path, seed=0):
    """events: lista di (secondi, tipo) con tipo in type | delete | dot | end."""
    rng = np.random.default_rng(seed)
    out = _pad(duration, seed)
    def put(sig, at):
        i = int(at * SR)
        j = min(len(out), i + len(sig))
        if i < len(out):
            out[i:j] += sig[: j - i]
    for at, kind in events:
        if kind == "type":
            put(0.35 * _click(rng), at)
        elif kind == "delete":
            put(0.16 * _click(rng, pitch=0.7), at)
        elif kind == "dot":
            put(_blip(rng.choice([659.25, 783.99, 880.0])) * 0.5, at)
        elif kind == "end":
            put(_blip(659.25, 0.5), at)
            put(_blip(987.77, 0.7), at + 0.12)
    out = np.clip(out / max(1e-6, np.max(np.abs(out))) * 0.8, -1, 1)
    pcm = (out * 32767).astype(np.int16)
    stereo = np.column_stack([pcm, pcm]).ravel()
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(stereo.tobytes())


def encode(frames, events, out_path, seed=0):
    tmp = tempfile.mkdtemp()
    try:
        prev = None
        for idx, img in enumerate(frames):
            dst = os.path.join(tmp, f"f{idx:05d}.png")
            if img is prev:
                shutil.copy(os.path.join(tmp, f"f{idx - 1:05d}.png"), dst)
            else:
                img.save(dst)
            prev = img
        wav = os.path.join(tmp, "audio.wav")
        make_audio(events, len(frames) / FPS, wav, seed)
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(tmp, "f%05d.png"),
            "-i", wav, "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high",
            "-r", str(FPS), "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out_path], check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def render_reel(post, out_path):
    """Video: scrive la frase, tre puntini che pulsano, cancella, chiude con 'quasi inviato.'"""
    text, theme = post["text"], post.get("theme", "night")
    n = len(plain(text))
    frames, events = [], []
    kw = dict(theme=theme, size_wh=TALL_SIZE, time_label=post.get("time_label"), handle=post.get("handle"))

    def add(img, count=1, event=None):
        if event:
            events.append((len(frames) / FPS, event))
        frames.extend([img] * count)

    add(draw_frame(text, visible_chars=0, cursor=True, **kw), 12)
    for i in range(1, n + 1):                       # scrittura, 30 caratteri al secondo
        ch = plain(text)[i - 1]
        add(draw_frame(text, visible_chars=i, cursor=True, **kw), 1, None if ch == " " else "type")
    post["thumb_offset"] = int(len(frames) / FPS * 1000) + 500  # copertina: la frase intera
    add(draw_frame(text, **kw), 45)                 # pausa per leggere
    for k in range(3):                              # "sta scrivendo..." che pulsa
        for lit in range(3):
            dots = [GRIGIO if j != lit else ARANCIO for j in range(3)]
            add(draw_frame(text, dots=dots, **kw), 7, "dot")
    for i in range(n, -1, -3):                      # cancellazione veloce
        add(draw_frame(text, visible_chars=i, cursor=True, **kw), 1, "delete")
    add(draw_frame("*quasi* inviato.", **kw), 60, "end")
    encode(frames, events, out_path, seed=sum(map(ord, post["id"])))


def render_story_video(post, out_path):
    """Storia video di 6 secondi: la frase, i tre puntini che pulsano, il suono firma."""
    kw = dict(theme=post.get("theme"), size_wh=TALL_SIZE, time_label=post.get("time_label"),
              handle=post.get("handle"))
    frames, events = [], []
    base = draw_frame(post["text"], **kw)
    frames.extend([base] * 20)
    for k in range(6):
        for lit in range(3):
            events.append((len(frames) / FPS, "dot"))
            dots = [GRIGIO if j != lit else ARANCIO for j in range(3)]
            frames.extend([draw_frame(post["text"], dots=dots, **kw)] * 9)
    frames.extend([base] * 15)
    encode(frames, events, out_path, seed=sum(map(ord, post["id"])))


def media_files(post):
    """Nomi dei file da pubblicare per un post."""
    t = post.get("type") or ("carousel" if post.get("slides") else "post")
    if t == "carousel":
        return [f"{post['id']}-{i + 1}.png" for i in range(len(post["slides"]))]
    if t == "reel" or (t == "story" and post.get("format") != "image"):
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
    elif t == "story" and files[0].endswith(".mp4"):
        render_reel(post, files[0])  # stessa sequenza e stesso suono del Reel
    elif t == "story":
        draw_frame(post["text"], size_wh=TALL_SIZE, time_label=post.get("time_label"), **kw).save(files[0])
    elif t == "reel":
        render_reel(post, files[0])
    else:
        draw_frame(post["text"], size_wh=POST_SIZE, time_label=post.get("time_label"), **kw).save(files[0])
    return files


def due_posts(posts, now=None):
    """Post da pubblicare adesso (o quelli indicati in PROVA)."""
    prova = [x for x in os.environ.get("PROVA", "").split(",") if x]
    if prova:
        return [p for p in posts if p["id"] in prova]
    now = now or datetime.now(timezone.utc)
    return [p for p in posts if p.get("status") == "queued" and datetime.fromisoformat(p["publish_at"]) <= now]


def main():
    path = os.path.join(HERE, "posts.json")
    with open(path, encoding="utf-8") as f:
        posts = json.load(f)
    os.makedirs(os.path.join(HERE, "images"), exist_ok=True)
    if "--due" in sys.argv:
        # L'orario sull'immagine è l'ora reale di uscita: lo scriviamo adesso, al momento della pubblicazione.
        todo = due_posts(posts)
        # Griglia a scacchiera: ogni contenuto della griglia ha il fondo opposto al precedente.
        grid = [p for p in posts if p.get("status") == "published" and p.get("type") != "story"]
        last = max(grid, key=lambda p: p.get("published_at", ""), default=None)
        next_theme = "day" if not last or last.get("theme") == "night" else "night"
        for p in sorted(todo, key=lambda p: p["publish_at"]):
            if p.get("type") != "story" and not p.get("keep_theme"):
                p["theme"], next_theme = next_theme, ("night" if next_theme == "day" else "day")
        for p in todo:
            t = p.get("type") or ("carousel" if p.get("slides") else "post")
            delay = 3 if t == "reel" or (t == "story" and p.get("format") != "image") else 2 if t == "carousel" else 1
            p["time_label"] = (datetime.now(ROME) + timedelta(minutes=delay)).strftime("%H:%M")
        with open(os.path.join(HERE, ".due"), "w") as f:
            f.write(",".join(p["id"] for p in todo))
    else:
        only = set(sys.argv[1:])
        todo = [p for p in posts if p["id"] in only] if only else \
            [p for p in posts if p.get("status") != "published"]
    for p in todo:
        for out in render(p):
            print("creato", os.path.basename(out))
    if "--due" in sys.argv:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
            f.write("\n")


if __name__ == "__main__":
    main()
