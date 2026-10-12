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


# App screenshots: img/<name>.png is French, img/<name>-en.png is English (taken with the app UI in that language).
# Static pages reference the file for their own language directly in the HTML (no JS swap needed).
SHOTS = {  # name: (fr alt, en alt)
    "01_dashboard": ("Tableau de bord Veillea : avis ouverts, échéances de la semaine et nouveaux matches",
                     "Veillea dashboard: open notices, deadlines this week and new matches"),
    "08_profile_matches": ("Correspondances classées par score pour un profil, avec résumés FR/EN",
                           "Matches ranked by score for a profile, with EN/FR summaries"),
    "04_tender_detail_seao": ("Fiche d'un avis SEAO avec résumé bilingue et score du profil",
                              "SEAO notice detail with bilingual summary and profile score"),
    "02_tender_list": ("Liste des avis ouverts avec badges d'échéance", "Open notice list with deadline badges"),
}
SHOT_SETS = {"home": ["01_dashboard", "08_profile_matches", "04_tender_detail_seao"], "sector": ["08_profile_matches", "02_tender_list"]}


def shot_src(name, lang):
    return f"/img/{name}{'-en' if lang == 'en' else ''}.png"


def shots_html(lang, which="home"):
    head_ = "Aperçu du produit" if lang == "fr" else "Product screenshots"
    figs = "".join(f'<figure><img class="shot" src="{shot_src(n, lang)}" alt="{html.escape(SHOTS[n][0 if lang == "fr" else 1])}" loading="lazy">'
                   f'<figcaption>{html.escape(SHOTS[n][0 if lang == "fr" else 1])}</figcaption></figure>' for n in SHOT_SETS[which])
    return f'<section class="shots" id="screenshots"><h2>{head_}</h2>{figs}</section>'


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
            f'<div><p><b>{"Secteurs" if lang=="fr" else "Sectors"}</b><br>' + " · ".join(
                f'<a href="/{lang}/{x[2] if lang=="fr" else x[4]}">{x[5] if lang=="fr" else x[6]}</a>' for x in SECTORS) + f'</p><p><b>{"Ressources" if lang=="fr" else "Resources"}</b><br>' + " · ".join(
                f'<a href="{u}">{t}</a>' for u, t in resources(lang)) + f'</p><p>{d["ind"]}</p></div>'
            f'<div><p>© 2026 Veillea · Montréal, QC<br><a href="mailto:bonjour@veillea.ca">bonjour@veillea.ca</a></p></div></div></footer>')


SECTORS = [  # (key, fr source, fr slug, en source, en slug, fr label, en label)
    ("construction", "construction-fr", "appels-offres-construction-quebec", "construction-en", "construction-tenders-quebec", "Construction", "Construction"),
    ("hydro", "hydro-quebec-fr", "appels-offres-hydro-quebec", "hydro-quebec-en", "hydro-quebec-tenders", "Hydro-Québec", "Hydro-Québec"),
    ("montreal", "montreal-fr", "appels-offres-montreal", "montreal-en", "montreal-tenders", "Montréal", "Montréal"),
    ("it", "informatique-fr", "appels-offres-informatique-quebec", "it-en", "it-tenders-quebec", "Informatique / TI", "IT & software"),
]


# Batch 2 (tender-seo/batch2): comparison pages and guides. Each source file declares its slug ("**Slug :** `/fr/...`").
BATCH2 = [  # (fr source, en source, kind)
    ("meilleurs-outils-veille-appels-offres-fr", "best-tender-alert-services-canada-en", "roundup"),
    ("alternative-alertes-seao-fr", "seao-alerts-alternative-en", "compare"),
    ("alternative-merx-fr", "merx-alternative-en", "compare"),
    ("alternative-seaoalerte-fr", "seaoalerte-alternative-en", "compare"),
    ("alternative-tenderscan-fr", "tenderscan-alternative-en", "compare"),
    ("guide-comment-fonctionne-seao-fr", "guide-how-seao-works-en", "guide"),
    ("guide-seuils-appels-offres-quebec-fr", "guide-quebec-tender-thresholds-en", "guide"),
    ("guide-soumissionner-achatscanada-fr", "guide-how-to-bid-canadabuys-en", "guide"),
]


def b2_slug(name):
    return re.search(r"\*\*Slug\s*:\*\*\s*`([^`]+)`", (SEO / "batch2" / f"{name}.md").read_text(encoding="utf-8")).group(1)


def b2_h1(name):
    return re.search(r"^# (.+)$", (SEO / "batch2" / f"{name}.md").read_text(encoding="utf-8"), re.M).group(1).strip()


RES_LABELS = {  # short footer labels
    "meilleurs-outils-veille-appels-offres-fr": "Comparatif des outils de veille", "best-tender-alert-services-canada-en": "Tender alert services compared",
    "guide-comment-fonctionne-seao-fr": "Guide du SEAO", "guide-how-seao-works-en": "How SEAO works",
    "guide-seuils-appels-offres-quebec-fr": "Seuils 2026-2027", "guide-quebec-tender-thresholds-en": "Québec thresholds 2026-2027",
    "guide-soumissionner-achatscanada-fr": "Soumissionner sur AchatsCanada", "guide-how-to-bid-canadabuys-en": "Bidding on CanadaBuys",
}


def resources(lang):
    i = 0 if lang == "fr" else 1
    return [(b2_slug(x[i]), RES_LABELS[x[i]]) for x in BATCH2 if x[2] in ("roundup", "guide")]


def batch2():
    for frs, ens, kind in BATCH2:
        fs, es = b2_slug(frs), b2_slug(ens)
        fr_url, en_url = SITE + fs, SITE + es
        alts = hreflang(fr_url, en_url)
        for lg, src, sl, url in (("fr", frs, fs, fr_url), ("en", ens, es, en_url)):
            out = ROOT / (sl.lstrip("/") + ".html")
            out.parent.mkdir(parents=True, exist_ok=True)
            print(lg, landing(lg, SEO / "batch2" / f"{src}.md", out, url, alts, "sector"))
            t = out.read_text(encoding="utf-8")
            t = t.replace('<a href="/fr/" class', f'<a href="{fs}" class', 1).replace('<a href="/en/" class', f'<a href="{es}" class', 1)
            out.write_text(t, encoding="utf-8")


def hreflang(fr_url, en_url):
    return (f'<link rel="alternate" hreflang="fr-CA" href="{fr_url}"><link rel="alternate" hreflang="en-CA" href="{en_url}">'
            f'<link rel="alternate" hreflang="x-default" href="{fr_url}">')


def head(lang, title, desc, canonical, extra="", alts=None):
    t, ds = html.escape(title), html.escape(desc)
    return (f'<!doctype html><html lang="{lang}-CA"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{t}</title><meta name="description" content="{ds}"><link rel="canonical" href="{canonical}">{alts or HREFLANG}'
            f'<meta property="og:type" content="website"><meta property="og:site_name" content="Veillea"><meta property="og:title" content="{t}">'
            f'<meta property="og:description" content="{ds}"><meta property="og:url" content="{canonical}"><meta property="og:locale" content="{L[lang]["locale"]}">'
            f'<meta property="og:locale:alternate" content="{L[L[lang]["other"]]["locale"]}"><meta property="og:image" content="{SITE}/icon-512.png">'
            f'<meta name="twitter:card" content="summary">{FONTS}<link rel="stylesheet" href="/style.css">{ICONS}{extra}</head><body>')


def landing(lang, src_path=None, out_path=None, canonical=None, alts=None, shots="home"):
    src = Path(src_path or SEO / f"landing-{lang}.md").read_text(encoding="utf-8")
    src = re.sub(r"\A(\s*<!--.*?-->\s*)+", "", src, flags=re.S)  # strip the source/notes comments at the top
    title = re.search(r"\*\*Title tag[^*]*\*\*\s*(.+)", src).group(1).strip()
    desc = re.search(r"\*\*Meta description[^*]*\*\*\s*(.+)", src).group(1).strip()
    jsonld = re.search(r"<script type=\"application/ld\+json\">(.*?)</script>", src, re.S).group(1).strip()
    json.loads(jsonld)  # validate
    body = src.split("\n---\n", 1)[1].rsplit("\n---\n", 1)[0]
    d = L[lang]
    cta = (f'<p class="ctas"><a class="btn" href="{signup(lang, "free")}">{d["free"]}</a> '
           f'<a class="btn ghost" href="{signup(lang, "team")}">{d["trial"]}</a></p><p class="small">')
    body = re.sub(r"^\*\*\[([^\]]+)\](?:\([^)]*\))?\*\*\s*·\s*(.+)$", lambda m: cta + m.group(2) + "</p>", body, flags=re.M)
    h = markdown.markdown(body, extensions=["tables"], output_format="html")
    h = re.sub(r"<table>", '<div class="cmpwrap"><table class="cmp">', h).replace("</table>", "</table></div>")
    # anchors for the plan table and FAQ section
    h = re.sub(r"<h2>([^<]*(?:forfaits|plans|Pricing)[^<]*)</h2>", r'<h2 id="pricing-plans">\1</h2>', h, count=1, flags=re.I)
    h = re.sub(r"<h2>(Questions fréquentes|Frequently asked questions|FAQ[^<]*)</h2>", r'<h2 id="faq">\1</h2>', h, count=1, flags=re.I)
    # product screenshots in the page's own language, just before the pricing section (or at the end)
    block = shots_html(lang, shots)
    h = h.replace('<h2 id="pricing-plans">', block + '<h2 id="pricing-plans">', 1) if 'id="pricing-plans"' in h else h + block
    canonical = canonical or f"{SITE}/{lang}/"
    out = head(lang, title, desc, canonical, f'<script type="application/ld+json">{jsonld}</script>', alts)
    out += header(lang) + f'<main class="landing"><div class="wrap prose">{h}</div></main>' + footer(lang) + "</body></html>\n"
    assert "<!--" not in out, "HTML comment left in page"
    target = Path(out_path or ROOT / lang / "index.html")
    target.parent.mkdir(exist_ok=True)
    target.write_text(out, encoding="utf-8")
    return title


def sectors():
    for key, frs, frslug, ens, enslug, *_ in SECTORS:
        fr_url, en_url = f"{SITE}/fr/{frslug}", f"{SITE}/en/{enslug}"
        alts = hreflang(fr_url, en_url)
        print("fr", landing("fr", SEO / "sectors" / f"{frs}.md", ROOT / "fr" / f"{frslug}.html", fr_url, alts, "sector"))
        print("en", landing("en", SEO / "sectors" / f"{ens}.md", ROOT / "en" / f"{enslug}.html", en_url, alts, "sector"))
        for f in (ROOT / "fr" / f"{frslug}.html", ROOT / "en" / f"{enslug}.html"):  # FR/EN switch -> counterpart page
            t = f.read_text(encoding="utf-8")
            t = t.replace('<a href="/fr/" class', f'<a href="/fr/{frslug}" class', 1).replace('<a href="/en/" class', f'<a href="/en/{enslug}" class', 1)
            f.write_text(t, encoding="utf-8")


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
    for key, frs, frslug, ens, enslug, *_ in SECTORS:
        a = "".join(f'<xhtml:link rel="alternate" hreflang="{h}" href="{u}"/>' for h, u in
                    (("fr-CA", f"{SITE}/fr/{frslug}"), ("en-CA", f"{SITE}/en/{enslug}"), ("x-default", f"{SITE}/fr/{frslug}")))
        urls += "".join(f"<url><loc>{u}</loc>{a}<changefreq>monthly</changefreq><priority>0.8</priority></url>"
                        for u in (f"{SITE}/fr/{frslug}", f"{SITE}/en/{enslug}"))
    for frs, ens, kind in BATCH2:
        fu, eu = SITE + b2_slug(frs), SITE + b2_slug(ens)
        a = "".join(f'<xhtml:link rel="alternate" hreflang="{h}" href="{u}"/>' for h, u in (("fr-CA", fu), ("en-CA", eu), ("x-default", fu)))
        urls += "".join(f"<url><loc>{u}</loc>{a}<changefreq>monthly</changefreq><priority>0.7</priority></url>" for u in (fu, eu))
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
    # screenshots: French file + French alt in the static HTML (i18n.js swaps to -en.png and the EN alt)
    s = re.sub(r'(<img [^>]*\bdata-shot="(\w+)"[^>]*\bdata-alt="(\w+)"[^>]*>)',
               lambda m: re.sub(r'(?<=\s)alt="[^"]*"', f'alt="{html.escape(fr[m.group(3)])}"', re.sub(r'(?<=\s)src="[^"]*"', f'src="img/{m.group(2)}.png"', m.group(1))), s)
    # Resources links (FR + EN) in the root footer, after the sectors paragraph; regenerated on every build
    res = ('<p class="resources"><b>Ressources</b> : ' + " · ".join(f'<a href="{u}">{t}</a>' for u, t in resources("fr"))
           + '<br><b lang="en">Resources</b>: ' + " · ".join(f'<a href="{u}" hreflang="en-CA">{t}</a>' for u, t in resources("en")) + "</p>")
    s = re.sub(r'<p class="resources">.*?</p>', "", s, flags=re.S)
    s = re.sub(r'(<p class="sectors">.*?</p>)', lambda m: m.group(1) + res, s, count=1, flags=re.S)
    if 'rel="canonical"' not in s:
        s = s.replace("<title>", f'<link rel="canonical" href="{SITE}/">{HREFLANG}<title>', 1)
    p.write_text(s, encoding="utf-8")


if __name__ == "__main__":
    for lg in ("fr", "en"):
        print(lg, landing(lg))
    sectors(); batch2(); page_404(); sitemap(); prerender_root(); print("ok")
