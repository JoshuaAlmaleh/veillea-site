"""Build static, pre-rendered pages: /fr/, /en/ (from tender-seo landing markdown), 404.html, sitemap.xml,
robots.txt, and pre-fill the root index.html with static French text (i18n.js still switches languages).
Run:  python scripts/build_pages.py [--seo-dir ../tender-seo]   (needs `pip install markdown`, node)"""
import html, json, re, subprocess, sys
from pathlib import Path
import markdown

ROOT = Path(__file__).resolve().parent.parent
SEO = Path(sys.argv[sys.argv.index("--seo-dir") + 1]) if "--seo-dir" in sys.argv else ROOT.parent / "tender-seo"
SITE = "https://veillea.ca"
APP_URL = "https://app.veillea.ca"   # keep in sync with APP_URL in i18n.js
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;600&family=Source+Serif+4:wght@400;700&display=swap" rel="stylesheet">'
ICONS = '<link rel="icon" href="/favicon.ico" sizes="48x48"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="/apple-touch-icon.png"><link rel="manifest" href="/site.webmanifest"><meta name="theme-color" content="#3e1a24">'
HREFLANG = (f'<link rel="alternate" hreflang="fr-CA" href="{SITE}/fr/"><link rel="alternate" hreflang="en-CA" href="{SITE}/en/">'
            f'<link rel="alternate" hreflang="x-default" href="{SITE}/fr/">')
L = {
 "fr": dict(other="en", other_label="English", login="Connexion", trial="Essai gratuit 14 jours", free="Commencer gratuitement",
            ind="Veillea est un service indépendant, non affilié au SEAO, au gouvernement du Canada ni aux autres plateformes mentionnées.",
            tag="Veille bilingue d'appels d'offres publics pour les PME canadiennes.", locale="fr_CA", home="Accueil"),
 "en": dict(other="fr", other_label="Français", login="Log in", trial="Start 14-day free trial", free="Start free",
            ind="Veillea is an independent service, not affiliated with SEAO, the Government of Canada or any other platform mentioned.",
            tag="Bilingual public tender monitoring for Canadian SMBs.", locale="en_CA", home="Home"),
}


def signup(lang, plan="free", interval="monthly"):
    return f"{APP_URL}/signup?plan={plan}&amp;interval={interval}&amp;lang={lang}"


def header(lang):
    d = L[lang]
    return (f'<header><div class="wrap nav"><a class="brand" href="/{lang}/"><span class="seal">V</span>Veillea</a>'
            f'<nav class="links"><a href="/{lang}/#pricing-plans">{"Forfaits" if lang=="fr" else "Pricing"}</a><a href="/{lang}/#faq">FAQ</a></nav>'
            f'<div class="lang"><a href="/fr/" class="{"on" if lang=="fr" else ""}" hreflang="fr-CA">FR</a><a href="/en/" class="{"on" if lang=="en" else ""}" hreflang="en-CA">EN</a></div>'
            f'<a class="login" href="{APP_URL}/login?lang={lang}">{d["login"]}</a>'
            f'<a class="btn" href="{signup(lang, "team")}">{d["trial"]}</a></div></header>')


def footer(lang):
    d = L[lang]
    return (f'<footer><div class="wrap grid g3"><div><a class="brand" href="/{lang}/"><span class="seal">V</span>Veillea</a><p>{d["tag"]}</p></div>'
            f'<div><p>{d["ind"]}</p></div><div><p>© 2026 Veillea · Montréal, QC<br><a href="mailto:bonjour@veillea.ca">bonjour@veillea.ca</a></p></div></div></footer>')


def head(lang, title, desc, canonical, extra=""):
    t, ds = html.escape(title), html.escape(desc)
    return (f'<!doctype html><html lang="{lang}-CA"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{t}</title><meta name="description" content="{ds}"><link rel="canonical" href="{canonical}">{HREFLANG}'
            f'<meta property="og:type" content="website"><meta property="og:site_name" content="Veillea"><meta property="og:title" content="{t}">'
            f'<meta property="og:description" content="{ds}"><meta property="og:url" content="{canonical}"><meta property="og:locale" content="{L[lang]["locale"]}">'
            f'<meta property="og:locale:alternate" content="{L[L[lang]["other"]]["locale"]}"><meta property="og:image" content="{SITE}/icon-512.png">'
            f'<meta name="twitter:card" content="summary">{FONTS}<link rel="stylesheet" href="/style.css">{ICONS}{extra}</head><body>')


def landing(lang):
    src = (SEO / f"landing-{lang}.md").read_text(encoding="utf-8")
    title = re.search(r"\*\*Title tag[^*]*\*\*\s*(.+)", src).group(1).strip()
    desc = re.search(r"\*\*Meta description[^*]*\*\*\s*(.+)", src).group(1).strip()
    jsonld = re.search(r"<script type=\"application/ld\+json\">(.*?)</script>", src, re.S).group(1).strip()
    json.loads(jsonld)  # validate
    body = src.split("\n---\n", 1)[1].rsplit("\n---\n", 1)[0]
    d = L[lang]
    cta = (f'<p class="ctas"><a class="btn" href="{signup(lang, "free")}">{d["free"]}</a> '
           f'<a class="btn ghost" href="{signup(lang, "team")}">{d["trial"]}</a></p><p class="small">')
    body = re.sub(r"^\*\*\[([^\]]+)\]\*\*\s*·\s*(.+)$", lambda m: cta + m.group(2) + "</p>", body, flags=re.M)
    h = markdown.markdown(body, extensions=["tables"], output_format="html")
    h = re.sub(r"<table>", '<div class="cmpwrap"><table class="cmp">', h).replace("</table>", "</table></div>")
    # anchors for the plan table and FAQ section
    h = re.sub(r"<h2>([^<]*(?:forfaits|plans|Pricing)[^<]*)</h2>", r'<h2 id="pricing-plans">\1</h2>', h, count=1, flags=re.I)
    h = re.sub(r"<h2>(Questions fréquentes|Frequently asked questions|FAQ[^<]*)</h2>", r'<h2 id="faq">\1</h2>', h, count=1, flags=re.I)
    out = head(lang, title, desc, f"{SITE}/{lang}/", f'<script type="application/ld+json">{jsonld}</script>')
    out += header(lang) + f'<main class="landing"><div class="wrap prose">{h}</div></main>' + footer(lang) + "</body></html>\n"
    (ROOT / lang).mkdir(exist_ok=True)
    (ROOT / lang / "index.html").write_text(out, encoding="utf-8")
    return title


def page_404():
    out = head("fr", "Page introuvable / Page not found · Veillea", "Cette page n'existe pas. / This page does not exist.", f"{SITE}/404.html")
    out = out.replace('<link rel="canonical" href="https://veillea.ca/404.html">', '<meta name="robots" content="noindex">')
    out += header("fr") + (
        '<main class="landing"><div class="wrap prose nf"><p class="eyebrow">404</p>'
        '<h1>Page introuvable</h1><p>La page demandée n\'existe pas ou a été déplacée.</p>'
        '<p class="ctas"><a class="btn" href="/fr/">Accueil en français</a></p>'
        '<hr><h2 lang="en">Page not found</h2><p lang="en">The page you requested does not exist or has moved.</p>'
        '<p class="ctas"><a class="btn ghost" href="/en/">English home page</a></p></div></main>') + footer("fr") + "</body></html>\n"
    (ROOT / "404.html").write_text(out, encoding="utf-8")


def sitemap():
    alt = "".join(f'<xhtml:link rel="alternate" hreflang="{h}" href="{SITE}/{p}/"/>' for h, p in (("fr-CA", "fr"), ("en-CA", "en"), ("x-default", "fr")))
    urls = "".join(f"<url><loc>{SITE}/{p}/</loc>{alt}<changefreq>weekly</changefreq><priority>{pr}</priority></url>"
                   for p, pr in (("fr", "1.0"), ("en", "0.9")))
    urls += f"<url><loc>{SITE}/</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>"
    (ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
                                      f'xmlns:xhtml="http://www.w3.org/1999/xhtml">{urls}</urlset>\n', encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")


def prerender_root():
    """Fill every data-i element of index.html with its French string (static HTML; JS still switches)."""
    js = (ROOT / "i18n.js").read_text(encoding="utf-8")
    tdef = js[: js.index("/* App base URL")]
    T = json.loads(subprocess.check_output(["node", "-e", tdef + ";process.stdout.write(JSON.stringify(T))"]))
    fr = T["fr"]
    p = ROOT / "index.html"
    s = p.read_text(encoding="utf-8")
    s = re.sub(r'(<(\w+)[^>]*\bdata-i="(\w+)"[^>]*>)(.*?)(</\2>)',
               lambda m: m.group(1) + (fr[m.group(3)] if isinstance(fr.get(m.group(3)), str) else m.group(4)) + m.group(5), s, flags=re.S)
    s = re.sub(r'<a ([^>]*?)href="[^"]*"([^>]*?)data-app="(\w+)"(?: data-plan="(\w+)")?',
               lambda m: f'<a {m.group(1)}href="{APP_URL}/login?lang=fr"{m.group(2)}data-app="login"' if m.group(3) == "login"
               else f'<a {m.group(1)}href="{signup("fr", m.group(4) or "team")}"{m.group(2)}data-app="signup" data-plan="{m.group(4) or "team"}"', s)
    if 'rel="canonical"' not in s:
        s = s.replace("<title>", f'<link rel="canonical" href="{SITE}/">{HREFLANG}<title>', 1)
    p.write_text(s, encoding="utf-8")


if __name__ == "__main__":
    for lg in ("fr", "en"):
        print(lg, landing(lg))
    page_404(); sitemap(); prerender_root(); print("ok")
