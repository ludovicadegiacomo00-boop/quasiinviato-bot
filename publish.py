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

from render import image_files

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


def wait_ready(cid, token):
    for _ in range(24):
        s = call(cid, {"fields": "status_code", "access_token": token}, method="GET")
        if s.get("status_code") == "FINISHED":
            return
        if s.get("status_code") == "ERROR":
            raise RuntimeError(f"Instagram non ha accettato il contenuto {cid}")
        time.sleep(5)
    raise RuntimeError(f"Instagram non ha finito di elaborare {cid}")


def publish(post, user_id, token, base_url):
    urls = [f"{base_url}/{name}" for name in image_files(post)]
    caption = post.get("caption", "")
    if len(urls) == 1:
        cid = call(f"{user_id}/media", {"image_url": urls[0], "caption": caption,
                                        "access_token": token})["id"]
    else:
        children = []
        for url in urls[:10]:  # Instagram accetta al massimo 10 slide
            child = call(f"{user_id}/media", {"image_url": url, "is_carousel_item": "true",
                                              "access_token": token})["id"]
            wait_ready(child, token)
            children.append(child)
        cid = call(f"{user_id}/media", {"media_type": "CAROUSEL", "children": ",".join(children),
                                        "caption": caption, "access_token": token})["id"]
    wait_ready(cid, token)
    return call(f"{user_id}/media_publish", {"creation_id": cid, "access_token": token})["id"]


def main():
    user_id = os.environ["IG_USER_ID"].strip().strip("\"'")
    token = os.environ["IG_TOKEN"].strip().strip("\"'")
    base = os.environ["IMAGE_BASE_URL"]
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
