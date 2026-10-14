#!/usr/bin/env python3
"""Submit changed veillea.ca URLs to IndexNow (api.indexnow.org, shared by Bing, Yandex, Seznam, Naver...).
Changed URLs = built .html files changed between two commits (--since SHA, default HEAD~1), limited to URLs in sitemap.xml.
Falls back to the whole sitemap when the diff is unavailable or --all is given. Stdlib only.
Run:  python scripts/indexnow.py [--since SHA | --all] [--dry-run]"""
import json, re, subprocess, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST, SITE = "veillea.ca", "https://veillea.ca"
KEY = next(p.stem for p in ROOT.glob("*.txt") if re.fullmatch(r"[0-9a-f]{32}", p.stem))


def sitemap_urls():
    return re.findall(r"<loc>([^<]+)</loc>", (ROOT / "sitemap.xml").read_text(encoding="utf-8"))


def to_url(f):
    if not f.endswith(".html"):
        return None
    p = f[:-5]
    p = "" if p == "index" else (p[: -len("index")] if p.endswith("/index") else p)
    return f"{SITE}/{p}"


def changed(since):
    out = subprocess.run(["git", "-C", str(ROOT), "diff", "--name-only", since, "HEAD"], capture_output=True, text=True)
    if out.returncode:
        return None
    return {u for u in map(to_url, out.stdout.split()) if u}


def main():
    args = sys.argv[1:]
    allu = sitemap_urls()
    urls = None
    if "--all" not in args:
        since = args[args.index("--since") + 1] if "--since" in args else "HEAD~1"
        ch = changed(since)
        if ch is not None:
            urls = [u for u in allu if u in ch]
    if urls is None:
        urls = allu
    if not urls:
        print("no changed URLs")
        return
    body = {"host": HOST, "key": KEY, "keyLocation": f"{SITE}/{KEY}.txt", "urlList": urls[:10000]}
    print(f"{len(urls)} URLs", *urls[:20], sep="\n")
    if "--dry-run" in args:
        return
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            print("IndexNow HTTP", r.status, r.read().decode()[:300])
    except urllib.error.HTTPError as e:
        print("IndexNow HTTP", e.code, e.read().decode()[:300])
        sys.exit(e.code not in (200, 202))


if __name__ == "__main__":
    main()
