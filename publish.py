"""Pubblica su Instagram i post in coda la cui ora è arrivata.

Variabili richieste (segreti di GitHub):
  IG_USER_ID     id numerico dell'account Instagram professionale
  IG_TOKEN       token di accesso della Pagina Facebook collegata (non scade)
  IMAGE_BASE_URL indirizzo pubblico della cartella images (impostato dal workflow)
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

API = "https://graph.facebook.com/v21.0"
HERE = os.path.dirname(os.path.abspath(__file__))
MAX_PER_RUN = 3


def call(path, params, method="POST"):
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path}"
    if method == "GET":
        url, data = f"{url}?{data.decode()}", None
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Errore Instagram {e.code}: {e.read().decode()}") from None


def publish(post, user_id, token, base_url):
    image_url = f"{base_url}/{post['id']}.png"
    c = call(f"{user_id}/media", {"image_url": image_url, "caption": post.get("caption", ""),
                                  "access_token": token})
    cid = c["id"]
    for _ in range(20):
        s = call(cid, {"fields": "status_code", "access_token": token}, method="GET")
        if s.get("status_code") == "FINISHED":
            break
        if s.get("status_code") == "ERROR":
            raise RuntimeError(f"Instagram non ha accettato l'immagine {image_url}")
        time.sleep(5)
    return call(f"{user_id}/media_publish", {"creation_id": cid, "access_token": token})["id"]


def main():
    user_id, token, base = os.environ["IG_USER_ID"], os.environ["IG_TOKEN"], os.environ["IMAGE_BASE_URL"]
    path = os.path.join(HERE, "posts.json")
    with open(path, encoding="utf-8") as f:
        posts = json.load(f)
    now = datetime.now(timezone.utc)
    done, failed = 0, 0
    for p in sorted(posts, key=lambda p: p["publish_at"]):
        if p.get("status") != "queued" or datetime.fromisoformat(p["publish_at"]) > now:
            continue
        if done >= MAX_PER_RUN:
            break
        try:
            p["media_id"] = publish(p, user_id, token, base)
            p["status"] = "published"
            p["published_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            done += 1
            print("pubblicato", p["id"])
        except Exception as e:  # il post resta in coda e viene riprovato
            p["last_error"] = str(e)[:500]
            failed += 1
            print("ERRORE", p["id"], e, file=sys.stderr)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"pubblicati {done}, errori {failed}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
