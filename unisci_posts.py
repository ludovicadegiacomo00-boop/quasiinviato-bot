"""Porta su main le voci di posts.json scritte da una sessione cloud (ramo claude/*).

Dall'app di Claude (scheda Code) Claude lavora su un ramo separato: qui lo uniamo a main
in automatico, ma solo se tocca soltanto posts.json e se le voci sono valide.
Altrimenti il ramo resta dov'è e va rivisto a mano.
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROME = ZoneInfo("Europe/Rome")
TYPES = {"post", "carousel", "story", "reel"}
ALLOWED = {"id", "type", "text", "slides", "caption", "publish_at", "status", "theme", "keep_theme",
           "format", "label", "handle"}


def normalize(p):
    """Controlla una voce scritta da fuori e la riporta al formato della coda."""
    if not isinstance(p, dict):
        raise ValueError("voce non valida")
    pid = p.get("id")
    if not isinstance(pid, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", pid):
        raise ValueError(f"id non valido: {pid!r}")
    t = p.get("type") or ("carousel" if p.get("slides") else "post")
    if t not in TYPES:
        raise ValueError(f"{pid}: tipo sconosciuto {t!r}")
    if t == "carousel":
        s = p.get("slides")
        if not isinstance(s, list) or not 1 <= len(s) <= 10 or not all(isinstance(x, str) and x for x in s):
            raise ValueError(f"{pid}: un carosello ha da 1 a 10 slide di testo")
    elif not isinstance(p.get("text"), str) or not p["text"].strip():
        raise ValueError(f"{pid}: manca il testo")
    if t != "story" and not str(p.get("caption", "")).strip():
        raise ValueError(f"{pid}: manca la didascalia")
    try:
        dt = datetime.fromisoformat(p["publish_at"])
    except Exception:
        raise ValueError(f"{pid}: publish_at non valido") from None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ROME)
    out = {k: v for k, v in p.items() if k in ALLOWED}
    out["publish_at"] = dt.isoformat(timespec="seconds")
    out["status"] = "queued"
    return out


def merge(base, ours, theirs):
    """Applica a `ours` (main) ciò che `theirs` ha cambiato rispetto a `base`."""
    b = {p["id"]: p for p in base}
    t = {p["id"]: p for p in theirs}
    result = list(ours)
    pos = {p["id"]: i for i, p in enumerate(result)}
    log = []
    for pid, p in t.items():
        if pid not in b:                                    # voce nuova
            if pid in pos:
                raise ValueError(f"{pid}: esiste già in coda")
            result.append(normalize(p))
            log.append(f"+ {pid}")
        elif p != b[pid]:                                   # voce modificata
            if pid in pos and result[pos[pid]].get("status") == "queued":
                result[pos[pid]] = normalize(p)
                log.append(f"~ {pid}")
            else:
                log.append(f"! {pid}: già pubblicato o assente, modifica ignorata")
    for pid in b:                                           # voce cancellata
        if pid not in t and pid in pos and result[pos[pid]].get("status") == "queued":
            result[pos[pid]] = None
            log.append(f"- {pid}")
    return [p for p in result if p is not None], log


def git(*args, check=True):
    r = subprocess.run(["git", *args], cwd=HERE, capture_output=True, text=True, encoding="utf-8")
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout.strip()


def main():
    branches = git("for-each-ref", "--sort=committerdate", "--format=%(refname:short)",
                   "refs/remotes/origin/claude/").split()
    merged = []
    path = os.path.join(HERE, "posts.json")
    for br in branches:
        base = git("merge-base", "HEAD", br)
        files = set(git("diff", "--name-only", base, br).split())
        if files - {"posts.json"}:
            print(f"salto {br}: tocca anche {sorted(files - {'posts.json'})}, va rivisto a mano")
            continue
        if files:
            try:
                with open(path, encoding="utf-8") as f:
                    ours = json.load(f)
                result, log = merge(json.loads(git("show", f"{base}:posts.json")), ours,
                                    json.loads(git("show", f"{br}:posts.json")))
            except (ValueError, KeyError, json.JSONDecodeError) as e:
                print(f"salto {br}: {e}")
                continue
            with open(path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                f.write("\n")
            git("add", "posts.json")
            git("commit", "-m", f"Programma dal telefono ({br.split('/', 1)[1]})")
            print(f"unito {br}: " + "; ".join(log))
        merged.append(br)
    if not merged:
        return
    if git("rev-list", "--count", "origin/main..HEAD") != "0":
        git("push", "origin", "HEAD:main")
    for br in merged:
        git("push", "origin", "--delete", br.split("/", 1)[1], check=False)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # non deve mai bloccare la pubblicazione dei post in coda
        print("unione dal telefono non riuscita:", e, file=sys.stderr)
