"""Aggiunge un contenuto alla coda (posts.json) con i controlli giusti.

Esempi (ora di Roma):
  python3 aggiungi.py post --testo "Ti scrivo e *cancello.*" --caption "Hook...\\n#quasiinviato" --quando "2026-11-05 18:00"
  python3 aggiungi.py reel --testo "..." --caption "..." --quando ora
  python3 aggiungi.py carosello --slide "Titolo *qui*" --slide "Seconda" --caption "..." --quando 21:30
  python3 aggiungi.py storia --testo "..." --quando "2026-11-06 10:00"
  python3 aggiungi.py post --testo "..." --caption "..." --quando "2026-11-06 10:30" --giorno   # frase del giorno

--quando: "ora" | "HH:MM" (oggi, o domani se è già passata) | "AAAA-MM-GG HH:MM".
La parola tra *asterischi* diventa arancio corsivo. Colori crema/nero e orario li decide render.py.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta

from unisci_posts import ROME, normalize

HERE = os.path.dirname(os.path.abspath(__file__))
TIPI = {"post": "post", "reel": "reel", "storia": "story", "story": "story",
        "carosello": "carousel", "carousel": "carousel"}


def quando(s):
    now = datetime.now(ROME).replace(second=0, microsecond=0)
    if s == "ora":
        return now
    if len(s) <= 5:
        h, m = map(int, s.split(":"))
        dt = now.replace(hour=h, minute=m)
        return dt if dt >= now else dt + timedelta(days=1)
    return datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=ROME)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tipo", choices=sorted(TIPI))
    ap.add_argument("--testo")
    ap.add_argument("--slide", action="append")
    ap.add_argument("--caption", default="")
    ap.add_argument("--quando", required=True)
    ap.add_argument("--giorno", action="store_true", help="frase del giorno: in alto la data al posto dell'orario")
    ap.add_argument("--file", default=os.path.join(HERE, "posts.json"))
    a = ap.parse_args()

    t = TIPI[a.tipo]
    dt = quando(a.quando)
    base = {"post": "post", "reel": "reel", "story": "story", "carousel": "carosello"}[t]
    with open(a.file, encoding="utf-8") as f:
        posts = json.load(f)
    ids = {p["id"] for p in posts}
    pid = f"{base}-{dt:%m%d-%H%M}"
    n = 2
    while pid in ids:
        pid, n = f"{base}-{dt:%m%d-%H%M}-{n}", n + 1

    p = {"id": pid, "publish_at": dt.isoformat(timespec="seconds")}
    if t in ("reel", "story"):
        p["type"] = t
    if t == "carousel":
        p["slides"] = a.slide
    else:
        p["text"] = a.testo
    if t != "story":
        p["caption"] = a.caption.replace("\\n", "\n")
    if a.giorno:
        p["label"] = "date"
    try:
        p = normalize(p)
    except ValueError as e:
        sys.exit(f"Errore: {e}")
    posts.append(p)
    with open(a.file, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Aggiunto {pid}: esce {dt:%d/%m/%Y alle %H:%M} (ora di Roma), entro 5 minuti dall'orario.")


if __name__ == "__main__":
    main()
