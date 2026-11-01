"""Crea le immagini dei post nello stile Quasi inviato (1080x1350).

La parola tra asterischi (*parola*) viene scritta in corsivo arancio.
"""
import json
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
CREMA, NERO, ARANCIO, GRIGIO = "#F4EDE1", "#14110F", "#E8571F", "#8A8178"
HERE = os.path.dirname(os.path.abspath(__file__))

FONT_CANDIDATES = {
    "serif": ["fonts/PlayfairDisplay.ttf", "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"],
    "italic": ["fonts/PlayfairDisplay-Italic.ttf", "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"],
    "sans": ["fonts/Inter.ttf", "/usr/share/fonts/opentype/inter/Inter-Medium.otf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
}


def font(kind, size):
    for path in FONT_CANDIDATES[kind]:
        full = path if os.path.isabs(path) else os.path.join(HERE, path)
        if os.path.exists(full):
            f = ImageFont.truetype(full, size)
            if "Playfair" in full:
                try:
                    f.set_variation_by_axes([400])
                except Exception:
                    pass
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
        f = ita if hl else reg
        ww = f.getlength(w)
        if line and lw + space + ww > max_w:
            lines.append((line, lw))
            line, lw = [], 0
        lw += (space if line else 0) + ww
        line.append((w, hl, ww))
    if line:
        lines.append((line, lw))
    return lines, reg, ita, space


def render(post, out_path):
    night = post.get("theme") == "night"
    bg, fg = (NERO, CREMA) if night else (CREMA, NERO)
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)

    words = tokens(post["text"])
    max_w, size = 820, 76
    while True:
        lines, reg, ita, space = layout(words, size, max_w)
        line_h = int(size * 1.32)
        if len(lines) * line_h <= 720 or size <= 44:
            break
        size -= 4

    y = (H - len(lines) * line_h) // 2 - 30
    for line, lw in lines:
        x = (W - lw) / 2
        for w, hl, ww in line:
            d.text((x, y), w, font=ita if hl else reg, fill=ARANCIO if hl else fg)
            x += ww + space
        y += line_h

    small = font("sans", 30)
    if post.get("time_label"):
        d.text((64, 56), post["time_label"], font=small, fill=GRIGIO)

    cy, r, gap = H - 150, 9, 34
    for i, color in enumerate([GRIGIO, GRIGIO, ARANCIO]):
        cx = W / 2 + (i - 1) * gap
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
    handle = post.get("handle") or os.environ.get("IG_HANDLE", "@quasiinviato")
    hf = font("sans", 26)
    d.text(((W - hf.getlength(handle)) / 2, cy + 30), handle, font=hf, fill=GRIGIO)

    img.save(out_path, "PNG")


def main():
    with open(os.path.join(HERE, "posts.json"), encoding="utf-8") as f:
        posts = json.load(f)
    only = set(sys.argv[1:])
    os.makedirs(os.path.join(HERE, "images"), exist_ok=True)
    for p in posts:
        if only and p["id"] not in only:
            continue
        path = os.path.join(HERE, "images", f"{p['id']}.png")
        if p.get("status") == "published" and os.path.exists(path):
            continue
        render(p, path)
        print("creata", path)


if __name__ == "__main__":
    main()
