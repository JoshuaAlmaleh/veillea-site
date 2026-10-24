"""Build static, pre-rendered pages: /fr/, /en/ (from tender-seo landing markdown), 404.html, sitemap.xml,
robots.txt, and pre-fill the root index.html with static French text (i18n.js still switches languages).
Run:  python scripts/build_pages.py [--seo-dir ../tender-seo]   (needs `pip install markdown`, node)"""
import html, json, os, re, subprocess, sys
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import markdown

ROOT = Path(__file__).resolve().parent.parent
SEO = Path(sys.argv[sys.argv.index("--seo-dir") + 1]) if "--seo-dir" in sys.argv else ROOT.parent / "tender-seo"
SITE = "https://veillea.ca"
APP_URL = "https://app.veillea.ca"   # keep in sync with APP_URL in i18n.js
FONTS = ''  # fonts are self-hosted via @font-face in style.css
# Cloudflare Web Analytics (cookieless); Cloudflare's snippet as given, placed before </body> on every page
CF_BEACON = '''<!-- Cloudflare Web Analytics --><script type='module' src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{"token": "0db15ef9766647029a30dadef264f5ba"}'></script><!-- End Cloudflare Web Analytics -->'''
ICONS = '<link rel="icon" href="/favicon.ico" sizes="48x48"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="/apple-touch-icon.png"><link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png"><link rel="manifest" href="/site.webmanifest"><meta name="theme-color" content="#3e1a24">'
HREFLANG = (f'<link rel="alternate" hreflang="fr-CA" href="{SITE}/fr/"><link rel="alternate" hreflang="en-CA" href="{SITE}/en/">'
            f'<link rel="alternate" hreflang="x-default" href="{SITE}/">')  # / is the language-neutral x-default
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


LEGAL = {"fr": "Veillea est une entreprise individuelle exploitée par Joshua Almaleh · NEQ 2282674748 · C.P. 311, Hudson (Québec) J0P 0A9", "en": "Veillea is a sole proprietorship operated by Joshua Almaleh · Quebec Enterprise Number (NEQ) 2282674748 · PO Box 311, Hudson, Quebec J0P 0A9"}


def footer(lang):
    d = L[lang]
    return (f'<footer><div class="wrap grid g3"><div><a class="brand" href="/{lang}/"><span class="seal">V</span>Veillea</a><p>{d["tag"]}</p></div>'
            f'<div><p><b>{"Secteurs" if lang=="fr" else "Sectors"}</b><br>' + " · ".join(
                f'<a href="/{lang}/{x[2] if lang=="fr" else x[4]}">{x[5] if lang=="fr" else x[6]}</a>' for x in SECTORS) + f'</p><p><b>{"Ressources" if lang=="fr" else "Resources"}</b><br>' + " · ".join(
                f'<a href="{u}">{t}</a>' for u, t in resources(lang)) + '<br>' + " · ".join(
                f'<a href="{u}">{t}</a>' for u, t in hub_links(lang)) + f'</p><p>{d["ind"]}</p></div>'
            f'<div><p>© 2026 Veillea · Montréal, QC<br><a href="mailto:bonjour@veillea.ca">bonjour@veillea.ca</a><br>'
            + " · ".join(f'<a href="{u}">{t}</a>' for u, t in legal_links(lang)) + '</p></div></div>'
            f'<div class="wrap ft-legal"><p>{LEGAL[lang]} · <a href="mailto:bonjour@veillea.ca">bonjour@veillea.ca</a></p></div></footer>')


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


# Batch 3 (tender-seo/batch3): sectors, regions, guides. Each file also declares its breadcrumb ("**Fil d'Ariane / Breadcrumb :**").
BATCH3 = [(f"batch3/{f}", f"batch3/{e}", k) for f, e, k in [
    ("deneigement-fr", "deneigement-en", "sector"),
    ("entretien-menager-fr", "entretien-menager-en", "sector"),
    ("fournitures-equipement-fr", "fournitures-equipement-en", "sector"),
    ("genie-architecture-fr", "genie-architecture-en", "sector"),
    ("securite-gardiennage-fr", "securite-gardiennage-en", "sector"),
    ("services-professionnels-fr", "services-professionnels-en", "sector"),
    ("transport-fr", "transport-en", "sector"),
    ("region-quebec-fr", "region-quebec-en", "region"),
    ("region-laval-fr", "region-laval-en", "region"),
    ("region-gatineau-fr", "region-gatineau-en", "region"),
    ("region-longueuil-fr", "region-longueuil-en", "region"),
    ("region-sherbrooke-fr", "region-sherbrooke-en", "region"),
    ("region-trois-rivieres-fr", "region-trois-rivieres-en", "region"),
    ("guide-lire-avis-seao-fr", "guide-read-seao-notice-en", "guide"),
    ("guide-modes-fr", "guide-modes-en", "guide"),
    ("guide-neq-rbq-fr", "guide-neq-rbq-en", "guide"),
    ("guide-autorisation-amp-fr", "guide-amp-authorization-en", "guide"),
    ("guide-gagner-appel-offres-fr", "guide-how-to-win-tender-en", "guide"),
    ("guide-entretien-menager-fr", "guide-cleaning-tenders-en", "guide"),
    ("guide-hydro-quebec-2026-fr", "guide-hydro-quebec-2026-en", "guide"),
]]
PAGES = BATCH2 + BATCH3


def md_path(name):  # "batch3/x" or a bare batch2 name
    return SEO / f"{name if '/' in name else 'batch2/' + name}.md"


def file_crumbs(name):
    """[(label, absolute url)] from the file's breadcrumb line; the last item is the page itself."""
    src = md_path(name).read_text(encoding="utf-8")
    line = re.search(r"\*\*Fil d'Ariane[^*]*\*\*\s*(.+)", src).group(1).strip()
    out = []
    for part in [x.strip() for x in line.split(">")]:
        m = re.fullmatch(r"\[([^\]]+)\]\(([^)]+)\)", part)
        out.append((m.group(1), SITE + m.group(2)) if m else (part, SITE + b2_slug(name)))
    return out


def b2_slug(name):
    return re.search(r"\*\*Slug\s*:\*\*\s*`([^`]+)`", md_path(name).read_text(encoding="utf-8")).group(1)


def crumb_name(md):
    t = re.search(r"\*\*Title tag[^*]*\*\*\s*(.+)", Path(md).read_text(encoding="utf-8")).group(1).strip()
    return re.sub(r"\s*\|\s*Veillea$", "", t)


def b2_h1(name):
    return re.search(r"^# (.+)$", md_path(name).read_text(encoding="utf-8"), re.M).group(1).strip()


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
    for frs, ens, kind in PAGES:
        fs, es = b2_slug(frs), b2_slug(ens)
        fr_url, en_url = SITE + fs, SITE + es
        alts = hreflang(fr_url, en_url)
        for lg, src, sl, url in (("fr", frs, fs, fr_url), ("en", ens, es, en_url)):
            out = ROOT / (sl.lstrip("/") + ".html")
            out.parent.mkdir(parents=True, exist_ok=True)
            md = md_path(src)
            cr = (hub_crumbs(kind, lg, file_crumbs(src)[-1][0], url) if kind in ("sector", "region")
                  else file_crumbs(src) if src.startswith("batch3/") else [("Veillea", f"{SITE}/{lg}/")] + ([("Guides", f"{SITE}/{lg}/guide/")] if kind == "guide" else []) + [(crumb_name(md), url)])
            print(lg, landing(lg, md, out, url, alts, "sector", cr))
            t = out.read_text(encoding="utf-8")
            t = t.replace('<a href="/fr/" class', f'<a href="{fs}" class', 1).replace('<a href="/en/" class', f'<a href="{es}" class', 1)
            out.write_text(t, encoding="utf-8")


HUBS = {  # key: (fr path, en path, fr (title, desc, h1, intro), en (...))
    "guide": ("/fr/guide/", "/en/guide/",
              ("Guides : appels d'offres publics au Québec | Veillea",
               "Guides pratiques sur le SEAO, AchatsCanada et les seuils d'appels d'offres au Québec : comment trouver les avis, soumissionner et quoi surveiller.",
               "Guides pour soumissionner aux appels d'offres publics",
               "Des guides pratiques, mis à jour, pour comprendre le SEAO, AchatsCanada et les règles des marchés publics au Québec."),
              ("Guides: Québec & Canada Public Tenders | Veillea",
               "Practical guides to SEAO, CanadaBuys and Québec tender thresholds: how to find notices, how to bid, and what to watch for, in plain English.",
               "Guides to bidding on public tenders",
               "Practical, up-to-date guides to SEAO, CanadaBuys and Québec public procurement rules, in plain English.")),
    "sector": ("/fr/secteurs/", "/en/sectors/",
               ("Appels d'offres par secteur au Québec | Veillea",
                "Appels d'offres publics au Québec par secteur : construction, TI, entretien ménager, déneigement, génie, transport et plus, via le SEAO et AchatsCanada.",
                "Appels d'offres par secteur",
                "Veillea surveille le SEAO et AchatsCanada et classe chaque avis selon votre secteur. Choisissez le vôtre pour voir les acheteurs, les types de contrats et les conseils propres à votre domaine."),
               ("Quebec Public Tenders by Sector | Veillea",
                "Québec public tenders by sector: construction, IT, cleaning, snow removal, engineering, transportation and more, from SEAO and CanadaBuys, in English.",
                "Public tenders by sector",
                "Veillea monitors SEAO and CanadaBuys and ranks every notice for your line of business. Pick your sector to see the buyers, contract types and tips that apply to it.")),
    "region": ("/fr/regions/", "/en/regions/",
               ("Appels d'offres par région au Québec | Veillea",
                "Appels d'offres publics par région : Montréal, Québec, Laval, Gatineau, Longueuil, Sherbrooke et Trois-Rivières. Veille SEAO et AchatsCanada, dès 0 $.",
                "Appels d'offres par région",
                "Les villes et organismes publics de chaque région publient leurs appels d'offres au SEAO. Choisissez votre région pour voir les principaux acheteurs et comment Veillea les surveille."),
               ("Quebec Public Tenders by Region | Veillea",
                "Public tenders by Québec region: Montréal, Québec City, Laval, Gatineau, Longueuil, Sherbrooke and Trois-Rivières. SEAO and CanadaBuys, from $0.",
                "Public tenders by region",
                "Cities and public bodies in every Québec region post their tenders on SEAO. Pick your region to see the main buyers and how Veillea tracks them, in English.")),
}
# the original 8 sector pages: Montréal is a region; construction, IT and Hydro-Québec (energy buyer) go under sectors
SECTOR_KIND = {"construction": "sector", "hydro": "sector", "it": "sector", "montreal": "region"}


def meta_desc(md):
    return re.search(r"\*\*Meta description[^*]*\*\*\s*(.+)", Path(md).read_text(encoding="utf-8")).group(1).strip()


def hub_items(key, lang):
    """[(path, name, description)] for one hub, in display order (original pages first)."""
    i = 0 if lang == "fr" else 1
    items = []
    for k, frs, frslug, ens, enslug, frl, enl in SECTORS:
        if SECTOR_KIND[k] == key:
            md = SEO / "sectors" / f"{frs if lang == 'fr' else ens}.md"
            items.append((f"/{lang}/{frslug if lang == 'fr' else enslug}", frl if lang == "fr" else enl, meta_desc(md)))
    for x in PAGES:
        if x[2] == key:
            n = x[i]
            name = file_crumbs(n)[-1][0] if n.startswith("batch3/") and key != "guide" else b2_h1(n)
            items.append((b2_slug(n), name, meta_desc(md_path(n))))
    return items


def hubs():
    for key, (fp, ep, frt, ent) in HUBS.items():
        alts = hreflang(SITE + fp, SITE + ep)
        for lg, path, (title, desc, h1, intro) in (("fr", fp, frt), ("en", ep, ent)):
            url, items = SITE + path, hub_items(key, lg)
            lst = {"@context": "https://schema.org", "@type": "CollectionPage", "name": h1, "url": url, "inLanguage": f"{lg}-CA",
                   "isPartOf": {"@id": f"{SITE}/#website"}, "publisher": {"@id": ORG_ID},
                   "mainEntity": {"@type": "ItemList", "itemListElement": [
                       {"@type": "ListItem", "position": k, "url": SITE + u, "name": t} for k, (u, t, _) in enumerate(items, 1)]}}
            crumbs = [("Veillea", f"{SITE}/{lg}/"), (h1 if key != "guide" else "Guides", url)]
            body = (crumbs_html(lg, crumbs) + f"<h1>{html.escape(h1)}</h1><p>{html.escape(intro)}</p>"
                    + "".join(f'<h2><a href="{u}">{html.escape(t)}</a></h2><p>{html.escape(d)}</p>' for u, t, d in items))
            out = head(lg, title, desc, url, ld(lst) + ld(crumbs_ld(crumbs)), alts)
            out += header(lg) + f'<main class="landing"><div class="wrap prose">{body}</div></main>' + footer(lg) + CF_BEACON + "</body></html>\n"
            out = out.replace('<a href="/fr/" class', f'<a href="{fp}" class', 1).replace('<a href="/en/" class', f'<a href="{ep}" class', 1)
            assert "<!--" not in out.replace(CF_BEACON, "")
            target = ROOT / path.strip("/") / "index.html"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(out, encoding="utf-8")


def hub_crumbs(kind, lang, name, url):
    """Home › Secteurs/Sectors (or Régions/Regions) hub › page, for every sector and region page."""
    hub = HUBS[kind][0 if lang == "fr" else 1]
    label = {("sector", "fr"): "Secteurs", ("sector", "en"): "Sectors", ("region", "fr"): "Régions", ("region", "en"): "Regions"}[kind, lang]
    return [("Accueil" if lang == "fr" else "Home", f"{SITE}/{lang}/"), (label, SITE + hub), (name, url)]


def hub_links(lang):
    lab = {"fr": ("Tous les secteurs", "Toutes les régions", "Tous les guides"), "en": ("All sectors", "All regions", "All guides")}[lang]
    out = [(HUBS[k][0 if lang == "fr" else 1], l) for k, l in zip(("sector", "region", "guide"), lab)]
    out.append(B4["fr" if lang == "fr" else "en"][1:3])
    if lang == "fr" and WEEKLY:
        out.append((WEEKLY["hub"], "Appels d'offres cette semaine"))
    return out


# Batch 4 (tender-seo/batch4): "tender scanner" pair. lang: (source, url path, footer label)
B4 = {"fr": ("batch4/scanner-appels-offres-fr", "/fr/scanner-appels-offres", "Scanner d'appels d'offres"),
      "en": ("batch4/tender-scanner-en", "/en/tender-scanner", "Tender scanner")}
# Weekly open-tender pages (FR only), written by scripts/build_weekly.py; the manifest keeps this build reproducible.
_WM = ROOT / "scripts" / "weekly_manifest.json"
WEEKLY = json.loads(_WM.read_text(encoding="utf-8")) if _WM.exists() else None


def faq_ld(src, lang):
    sec = re.search(r"^## (?:Frequently asked questions|Questions fréquentes)\s*$(.*?)(?=^## )", src, re.M | re.S).group(1)
    qa = re.findall(r"^### (.+?)\s*\n(.+?)(?=^### |\Z)", sec, re.M | re.S)
    clean = lambda x: re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", re.sub(r"\*\*?", "", x)).strip()
    assert len(qa) >= 3, "FAQ not found"
    return {"@type": "FAQPage", "inLanguage": f"{lang}-CA", "mainEntity": [
        {"@type": "Question", "name": clean(q), "acceptedAnswer": {"@type": "Answer", "text": clean(" ".join(a.split()))}} for q, a in qa]}


def batch4():
    import tempfile
    fr_url, en_url = SITE + B4["fr"][1], SITE + B4["en"][1]
    alts = hreflang(fr_url, en_url)
    for lg in ("fr", "en"):
        name, path, _ = B4[lg]
        src = md_path(name).read_text(encoding="utf-8")
        sw = software_ld(lg)
        sw.pop("@context")
        sw["url"] = SITE + path
        data = {"@context": "https://schema.org", "@graph": [faq_ld(src, lg), sw]}
        with tempfile.TemporaryDirectory() as td:  # JSON-LD built here (from the file's notes), appended after the closing ---
            tmp = Path(td) / "page.md"
            tmp.write_text(src + '\n\n<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + "</script>\n", encoding="utf-8")
            out = ROOT / (path.lstrip("/") + ".html")
            print(lg, landing(lg, tmp, out, SITE + path, alts, "sector", file_crumbs(name)))
        t = out.read_text(encoding="utf-8")
        t = t.replace('<a href="/fr/" class', f'<a href="{B4["fr"][1]}" class', 1).replace('<a href="/en/" class', f'<a href="{B4["en"][1]}" class', 1)
        out.write_text(t, encoding="utf-8")


def weekly_links():
    """Link each FR sector page to its weekly open-tender page (idempotent: sector pages are regenerated first)."""
    if not WEEKLY:
        return
    for p in WEEKLY["pages"]:
        if not p["sector"]:
            continue
        f = ROOT / "fr" / f"{p['sector']}.html"
        t = f.read_text(encoding="utf-8")
        link = (f'<p class="wk-link"><a href="{WEEKLY["hub"]}{p["slug"]}">Voir les appels d\'offres ouverts cette semaine en '
                f'{html.escape(p["label"].lower())} →</a></p>')
        t = re.sub(r'<p class="wk-link">.*?</p>', "", t, flags=re.S)
        t = t.replace("</nav><h1>", "</nav>", 1) if False else t
        t = re.sub(r"(</h1>)", r"\1" + link.replace("\\", "\\\\"), t, count=1)
        f.write_text(t, encoding="utf-8")


def hreflang(fr_url, en_url):
    return (f'<link rel="alternate" hreflang="fr-CA" href="{fr_url}"><link rel="alternate" hreflang="en-CA" href="{en_url}">'
            f'<link rel="alternate" hreflang="x-default" href="{fr_url}">')  # x-default = the French version


OG_IMAGE = f"{SITE}/og-image.png"   # 1200x630, generated by scripts/make_og_image.py
OG_ALT = {"fr": "Veillea : veille d'appels d'offres SEAO et AchatsCanada", "en": "Veillea: SEAO and CanadaBuys tender monitoring"}
ORG_ID = f"{SITE}/#org"
# Organization + WebSite on every page. No sameAs (no verified profiles yet) and no aggregateRating (no real reviews).
SITE_LD = {"@context": "https://schema.org", "@graph": [
    {"@type": "Organization", "@id": ORG_ID, "name": "Veillea", "url": f"{SITE}/",
     "logo": {"@type": "ImageObject", "url": f"{SITE}/icon-512.png", "width": 512, "height": 512},
     "email": "bonjour@veillea.ca",
     "address": {"@type": "PostalAddress", "addressLocality": "Montréal", "addressRegion": "QC", "addressCountry": "CA"}},
    {"@type": "WebSite", "@id": f"{SITE}/#website", "name": "Veillea", "alternateName": ["Veillea.ca"], "url": f"{SITE}/",
     "inLanguage": ["fr-CA", "en-CA"], "publisher": {"@id": ORG_ID}}]}


def ld(obj):
    txt = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    json.loads(txt)
    return f'<script type="application/ld+json">{txt.replace("</", "<\\/")}</script>'


def social(lang, title, desc, canonical, og_type="website", extra_meta=""):
    """Open Graph + Twitter tags (escaped)."""
    t, ds = html.escape(re.sub(r"\s*\|\s*Veillea$", "", title)), html.escape(desc)
    alt = f'<meta property="og:locale:alternate" content="{L[L[lang]["other"]]["locale"]}">' if lang in L else ""
    return (f'<meta property="og:type" content="{og_type}"><meta property="og:site_name" content="Veillea"><meta property="og:title" content="{t}">'
            f'<meta property="og:description" content="{ds}"><meta property="og:url" content="{canonical}"><meta property="og:locale" content="{L.get(lang, L["fr"])["locale"]}">{alt}'
            f'<meta property="og:image" content="{OG_IMAGE}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
            f'<meta property="og:image:alt" content="{html.escape(OG_ALT.get(lang, OG_ALT["fr"]))}">{extra_meta}'
            f'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{t}">'
            f'<meta name="twitter:description" content="{ds}"><meta name="twitter:image" content="{OG_IMAGE}">')


def crumbs_ld(crumbs):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i, "name": n, "item": u} for i, (n, u) in enumerate(crumbs, 1)]}


def crumbs_html(lang, crumbs):
    lab = "Fil d'Ariane" if lang == "fr" else "Breadcrumb"
    items = [f'<a href="{u.replace(SITE, "")}">{html.escape(n)}</a>' for n, u in crumbs[:-1]] + [f'<span aria-current="page">{html.escape(crumbs[-1][0])}</span>']
    return f'<nav class="crumbs" aria-label="{lab}">' + ' <span aria-hidden="true">›</span> '.join(items) + '</nav>'


def software_ld(lang):
    """SoftwareApplication with offers from plans.json (single source of truth for prices)."""
    P = json.loads((ROOT / "plans.json").read_text(encoding="utf-8"))
    cur, url = P["currency"], f"{SITE}/{lang}/" if lang else f"{SITE}/"
    by = {p["key"]: p for p in P["plans"]}
    offers = []
    for k in P["order"]:
        p = by[k]
        name = p["name_fr"] if lang == "fr" else p["name_en"] if lang == "en" else (p["name_fr"] if p["name_fr"] == p["name_en"] else f'{p["name_fr"]} / {p["name_en"]}')
        o = {"@type": "Offer", "name": name, "price": str(p["monthly_cad"]), "priceCurrency": cur, "url": url + "#pricing-plans"}
        if p["monthly_cad"]:
            frm = {"fr": "À partir de", "en": "From"}.get(lang, "From / à partir de") if p.get("quote") else None
            spec = []
            for unit, v in (("MON", p["monthly_cad"]), ("ANN", p["annual_cad"])):
                x = {"@type": "UnitPriceSpecification", "price": str(v), "priceCurrency": cur, "unitCode": unit,
                     "referenceQuantity": {"@type": "QuantitativeValue", "value": 1, "unitCode": unit}, "valueAddedTaxIncluded": False}
                if frm:
                    x["description"] = frm
                spec.append(x)
            o["priceSpecification"] = spec
        offers.append(o)
    desc = {"fr": "Veille d'appels d'offres SEAO et AchatsCanada avec résumés bilingues pour les PME. Prix fixe, non par utilisateur.",
            "en": "SEAO and CanadaBuys tender monitoring with bilingual summaries for SMBs. Flat pricing, not per user.",
            "": "Veille bilingue d'appels d'offres publics canadiens (SEAO, AchatsCanada) pour les PME. Bilingual Canadian public tender monitoring for SMBs."}[lang]
    return {"@context": "https://schema.org", "@type": "SoftwareApplication", "name": "Veillea", "url": url,
            "applicationCategory": "BusinessApplication", "operatingSystem": "Web",
            "inLanguage": {"fr": "fr-CA", "en": "en-CA"}.get(lang, ["fr-CA", "en-CA"]), "description": desc,
            "image": OG_IMAGE, "publisher": {"@id": ORG_ID}, "offers": offers}


def head(lang, title, desc, canonical, extra="", alts=None, og_type="website", og_extra=""):
    t, ds = html.escape(title), html.escape(desc)
    return (f'<!doctype html><html lang="{lang}-CA"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{t}</title><meta name="description" content="{ds}"><link rel="canonical" href="{canonical}">{alts or HREFLANG}'
            + social(lang, title, desc, canonical, og_type, og_extra) +
            f'{FONTS}<link rel="stylesheet" href="/style.css?v=w17">{ICONS}{ld(SITE_LD)}{extra}</head><body>')


MONTHS = {"fr": "janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split(),
          "en": "January February March April May June July August September October November December".split()}


def nice_date(d, lang):
    y, m, dd = (int(x) for x in d[:10].split("-"))
    return f"{dd}{'er' if dd == 1 else ''} {MONTHS['fr'][m-1]} {y}" if lang == "fr" else f"{MONTHS['en'][m-1]} {dd}, {y}"


def iso_dt(d):  # date-only -> 09:00 Montréal time
    return d if "T" in d else f"{d}T09:00:00-04:00"


def landing(lang, src_path=None, out_path=None, canonical=None, alts=None, shots="home", crumbs=None):
    src = Path(src_path or SEO / f"landing-{lang}.md").read_text(encoding="utf-8")
    src = re.sub(r"\A(\s*<!--.*?-->\s*)+", "", src, flags=re.S)  # strip the source/notes comments at the top
    title = re.search(r"\*\*Title tag[^*]*\*\*\s*(.+)", src).group(1).strip()
    desc = re.search(r"\*\*Meta description[^*]*\*\*\s*(.+)", src).group(1).strip()
    jsonld = re.search(r"<script type=\"application/ld\+json\">(.*?)</script>", src, re.S).group(1).strip()
    data = json.loads(jsonld)  # validate
    canonical = canonical or f"{SITE}/{lang}/"
    og_type, og_extra, dates = "website", "", ""
    if crumbs and "@graph" in data:  # breadcrumbs are generated from the file's breadcrumb line (single source)
        data["@graph"] = [n for n in data["@graph"] if n.get("@type") != "BreadcrumbList"]
    for n in data.get("@graph", [data]):
        if n.get("@type") == "Article":  # guides: image, author url, publisher logo (via #org), full timestamps
            n["datePublished"], n["dateModified"] = iso_dt(n["datePublished"]), iso_dt(n.get("dateModified", n["datePublished"]))
            n["image"] = [OG_IMAGE]
            n["author"] = {"@type": "Organization", "name": "Veillea", "url": f"{SITE}/"}
            n["publisher"] = {"@id": ORG_ID}
            n["mainEntityOfPage"] = {"@type": "WebPage", "@id": canonical}
            og_type = "article"
            og_extra = (f'<meta property="article:published_time" content="{n["datePublished"]}">'
                        f'<meta property="article:modified_time" content="{n["dateModified"]}">')
            pub, upd = nice_date(n["datePublished"], lang), nice_date(n["dateModified"], lang)
            dates = (f'<p class="dates"><time datetime="{n["datePublished"]}">{"Publié le" if lang == "fr" else "Published"} {pub}</time> · '
                     f'<time datetime="{n["dateModified"]}">{"Mis à jour le" if lang == "fr" else "Updated"} {upd}</time></p>')
    blocks = ld(data)
    if crumbs:
        blocks += ld(crumbs_ld(crumbs))
    if src_path is None:  # /fr/ and /en/ home pages
        blocks += ld(software_ld(lang))
    body = src.split("\n---\n", 1)[1].rsplit("\n---\n", 1)[0]
    if crumbs:  # the markdown breadcrumb line is replaced by the generated <nav class="crumbs">
        body = re.sub(r"^\[[^\]]+\]\(/(?:fr|en)/\) >.*\n", "", body, count=1, flags=re.M)
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
    if dates:
        h = re.sub(r"(</h1>)", r"\1" + dates, h, count=1)
    out = head(lang, title, desc, canonical, blocks, alts, og_type, og_extra)
    out += header(lang) + f'<main class="landing"><div class="wrap prose">{crumbs_html(lang, crumbs) if crumbs else ""}{h}</div></main>' + footer(lang) + CF_BEACON + "</body></html>\n"
    assert "<!--" not in out.replace(CF_BEACON, ""), "HTML comment left in page"  # only the Cloudflare snippet's own comments are allowed
    target = Path(out_path or ROOT / lang / "index.html")
    target.parent.mkdir(exist_ok=True)
    target.write_text(out, encoding="utf-8")
    return title


def sectors():
    for key, frs, frslug, ens, enslug, *_ in SECTORS:
        fr_url, en_url = f"{SITE}/fr/{frslug}", f"{SITE}/en/{enslug}"
        alts = hreflang(fr_url, en_url)
        for lg, src, sl, url in (("fr", frs, frslug, fr_url), ("en", ens, enslug, en_url)):
            md = SEO / "sectors" / f"{src}.md"
            print(lg, landing(lg, md, ROOT / lg / f"{sl}.html", url, alts, "sector", hub_crumbs(SECTOR_KIND[key], lg, crumb_name(md), url)))
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
        '<p class="ctas"><a class="btn ghost" href="/en/">English home page</a></p></div></main>') + footer("fr") + CF_BEACON + "</body></html>\n"
    (ROOT / "404.html").write_text(out, encoding="utf-8")


def lastmod(url):
    """Weekly pages: date of the SEAO data refresh (manifest). Other pages: git last-commit date (ET) of the built file;
    if the file differs from HEAD (about to be committed), the date it was last written. Deterministic for a given tree."""
    path = url[len(SITE):]
    if WEEKLY and path.startswith(WEEKLY["hub"]) and WEEKLY.get("updated"):
        return WEEKLY["updated"]
    rel = "index.html" if path == "/" else path.strip("/") + ("/index.html" if path.endswith("/") else ".html")
    git = ["git", "-C", str(ROOT)]
    if subprocess.run(git + ["diff", "--quiet", "HEAD", "--", rel]).returncode == 0:
        out = subprocess.run(git + ["log", "-1", "--format=%cd", "--date=format-local:%Y-%m-%d", "--", rel],
                             capture_output=True, text=True, env={**os.environ, "TZ": "America/Toronto"}).stdout.strip()
        if out:
            return out
    return datetime.fromtimestamp((ROOT / rel).stat().st_mtime, ZoneInfo("America/Toronto")).date().isoformat()


LEGAL_PAGES = {  # key: {lang: (path, md file, title, description)}
    "privacy": {"fr": ("/fr/confidentialite", "privacy-fr", "Politique de confidentialité | Veillea",
                       "Comment Veillea recueille, utilise et protège vos renseignements personnels : Loi 25, LPRPDE, fournisseurs, témoins, conservation et droits."),
                "en": ("/en/privacy", "privacy-en", "Privacy Policy | Veillea",
                       "How Veillea collects, uses and protects your personal information: Quebec Law 25, PIPEDA, service providers, cookies, retention and your rights.")},
    "terms": {"fr": ("/fr/conditions", "terms-fr", "Conditions d'utilisation | Veillea",
                     "Conditions d'utilisation de Veillea : service, comptes, forfaits en dollars canadiens, essai gratuit, annulation, usage acceptable et droit applicable."),
              "en": ("/en/terms", "terms-en", "Terms of Service | Veillea",
                     "Veillea Terms of Service: the service, accounts, plans in Canadian dollars, free trial, billing, cancellation, acceptable use and governing law.")},
}


def legal_links(lang):
    return [(LEGAL_PAGES[k][lang][0], LEGAL_PAGES[k][lang][2].split(" | ")[0]) for k in ("privacy", "terms")]


def legal():
    for key, langs in LEGAL_PAGES.items():
        a = "".join(f'<link rel="alternate" hreflang="{h}" href="{SITE}{langs[l][0]}">' for h, l in (("fr-CA", "fr"), ("en-CA", "en"))) + \
            f'<link rel="alternate" hreflang="x-default" href="{SITE}{langs["fr"][0]}">'
        for lang, (path, src, title, desc) in langs.items():
            assert len(title) <= 60 and 140 <= len(desc) <= 160, (path, len(title), len(desc))
            url = SITE + path
            crumbs = [("Accueil" if lang == "fr" else "Home", f"{SITE}/{lang}/"), (title.split(" | ")[0], url)]
            body = markdown.markdown((ROOT / "legal" / f"{src}.md").read_text(encoding="utf-8"), extensions=["tables"], output_format="html")
            out = head(lang, title, desc, url, ld(crumbs_ld(crumbs)), a) + header(lang)
            out += f'<main class="landing"><div class="wrap prose legal-doc">{crumbs_html(lang, crumbs)}{body}</div></main>' + footer(lang) + CF_BEACON + "</body></html>\n"
            (ROOT / (path.strip("/") + ".html")).write_text(out, encoding="utf-8")


TRIAL_TXT = {"fr": "Essai gratuit 14 jours, sans carte de crédit", "en": "14-day free trial, no credit card"}
# Above-the-fold trial CTA on the key landings: built page path -> utm_campaign slug (/ is in index.html: "home")
TRIAL_CTA = {"fr/index.html": "home-fr", "en/index.html": "home-en",
             "fr/scanner-appels-offres.html": "tender-scanner-fr", "en/tender-scanner.html": "tender-scanner-en",
             "fr/alternative-alertes-seao.html": "seao-alerts-fr", "en/seao-alerts-alternative.html": "seao-alerts-en",
             "fr/appels-offres-construction-quebec.html": "construction-qc-fr", "en/construction-tenders-quebec.html": "construction-qc-en",
             "fr/guide/soumissionner-achatscanada.html": "canadabuys-guide-fr", "en/guide/how-to-bid-canadabuys.html": "canadabuys-guide-en"}


def trial_url(lang, campaign):
    assert re.fullmatch(r"[a-z0-9-]{1,80}", campaign), campaign
    return f"{APP_URL}/signup?plan=solo&lang={lang}&utm_source=veillea.ca&utm_medium=cta&utm_campaign={campaign}"


def trial_cta(lang, campaign):
    return f'<a class="btn trial-cta" href="{html.escape(trial_url(lang, campaign))}">{TRIAL_TXT[lang]}</a>'


CTA_ROW = re.compile(r'<p class="ctas"><a class="btn" (href="[^"]*plan=free[^"]*")>([^<]*)</a> <a class="btn ghost" href="[^"]*plan=team[^"]*">[^<]*</a></p>')
SWITCH = re.compile(r'(<div class="lang"><a href=")[^"]*(" class="[^"]*" hreflang="fr-CA">FR</a><a href=")[^"]*(")')


def finalize_pages():
    """Post-build passes on generated FR/EN pages (idempotent):
    (a) the FR/EN switch links to the paired page, taken from the page's own hreflang links;
    (b) the trial CTA above the fold on TRIAL_CTA pages (replaces the top free/team button row, or is added after the intro)."""
    for f in sorted(list((ROOT / "fr").rglob("*.html")) + list((ROOT / "en").rglob("*.html"))):
        rel = f.relative_to(ROOT).as_posix()
        if rel.startswith("fr/appels-offres-cette-semaine/"):
            continue  # FR-only weekly pages (built by build_weekly.py)
        s = o = f.read_text(encoding="utf-8")
        alt = dict(re.findall(r'<link rel="alternate" hreflang="(fr-CA|en-CA)" href="https://veillea\.ca([^"]*)">', s))
        if "fr-CA" in alt and "en-CA" in alt:
            s = SWITCH.sub(lambda m: m.group(1) + alt["fr-CA"] + m.group(2) + alt["en-CA"] + m.group(3), s, count=1)
        if rel in TRIAL_CTA and "trial-cta" not in s:
            lang, btn, i = rel[:2], trial_cta(rel[:2], TRIAL_CTA[rel]), s.index("</h1>")
            m = CTA_ROW.search(s, i)
            if m and m.start() - i < 2500:
                s = s[:m.start()] + f'<p class="ctas">{btn} <a class="btn ghost" {m.group(1)}>{m.group(2)}</a></p>' + s[m.end():]
            else:
                j = s.index("</p>", re.compile(r"<p>").search(s, i).start()) + 4
                s = s[:j] + f'\n<p class="ctas">{btn}</p>' + s[j:]
        if s != o:
            f.write_text(s, encoding="utf-8")


# /fr/ in-place FR/EN toggle (same behaviour as the root page). The static /fr/ HTML stays French; the English version of its
# <main> (rendered from i18n/landing-fr.en.md, a faithful translation of tender-seo/landing-fr.md) and the header/footer
# string map go to /fr/index.en.json, loaded by /fr-toggle.js only when the visitor switches to English.
FR_TOGGLE_SRC = ROOT / "i18n" / "landing-fr.en.md"
FR_TOGGLE_LANG = ('<div class="lang" role="group" aria-label="Langue / Language"><button type="button" data-l="fr" class="on" aria-pressed="true" '
                  'lang="fr">FR</button><button type="button" data-l="en" aria-pressed="false" lang="en">EN</button></div>')
FR_TOGGLE_JS = '<script src="/fr-toggle.js?v=w18" defer></script>'


def _main_of(t):
    return re.search(r"<main[^>]*>.*</main>", t, re.S).group(0)


def fr_toggle():
    import tempfile
    fr_path = ROOT / "fr" / "index.html"
    fr = fr_path.read_text(encoding="utf-8")
    src = FR_TOGGLE_SRC.read_text(encoding="utf-8")
    title = re.search(r"\*\*Title tag[^*]*\*\*\s*(.+)", src).group(1).strip()
    desc = re.search(r"\*\*Meta description[^*]*\*\*\s*(.+)", src).group(1).strip()
    with tempfile.TemporaryDirectory() as td:
        md, out = Path(td) / "en.md", Path(td) / "en.html"
        md.write_text(src.rstrip() + '\n\n```html\n<script type="application/ld+json">\n{"@context": "https://schema.org", "@type": "WebPage"}\n</script>\n```\n', encoding="utf-8")
        landing("en", md, out, f"{SITE}/fr/", HREFLANG)
        en_main = _main_of(out.read_text(encoding="utf-8"))
    # same above-the-fold trial CTA as finalize_pages() puts on /fr/ (campaign of the page, link and text in English)
    btn, i = trial_cta("en", TRIAL_CTA["fr/index.html"]), en_main.index("</h1>")
    m = CTA_ROW.search(en_main, i)
    assert m and m.start() - i < 2500
    en_main = en_main[:m.start()] + f'<p class="ctas">{btn} <a class="btn ghost" {m.group(1)}>{m.group(2)}</a></p>' + en_main[m.end():]
    fr_main = _main_of(fr)
    for tag in ("<h1", "<h2", "<h3", "<tr", "<li", "<table", "<a ", "<img"):  # the translation must mirror the French page
        assert fr_main.count(tag) == en_main.count(tag), ("fr/en toggle out of sync", tag, fr_main.count(tag), en_main.count(tag))
    assert "<!--" not in en_main
    # header/footer strings, FR -> EN (exact text nodes)
    tmap = {"Forfaits": "Pricing", L["fr"]["login"]: L["en"]["login"], L["fr"]["trial"]: L["en"]["trial"], L["fr"]["tag"]: L["en"]["tag"],
            "Secteurs": "Sectors", "Ressources": "Resources", L["fr"]["ind"]: L["en"]["ind"],
            "Appels d'offres cette semaine": "Open tenders this week (in French)"}
    tmap.update({x[5]: x[6] for x in SECTORS})
    tmap.update({a: b for (_, a), (_, b) in zip(resources("fr"), resources("en"))})
    tmap.update({a: b for (_, a), (_, b) in zip(hub_links("fr"), hub_links("en"))})
    tmap.update({a: b for (_, a), (_, b) in zip(legal_links("fr"), legal_links("en"))})
    tmap[LEGAL["fr"] + " · "] = LEGAL["en"] + " · "
    tmap = {k: v for k, v in tmap.items() if k != v}
    (ROOT / "fr" / "index.en.json").write_text(json.dumps({"lang": "en-CA", "title": title, "desc": desc, "main": en_main, "map": tmap},
                                                         ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    # /fr/: FR/EN buttons instead of links, and the toggle script (idempotent)
    fr = re.sub(r'<div class="lang"[^>]*>.*?</div>', FR_TOGGLE_LANG, fr, count=1, flags=re.S)
    if FR_TOGGLE_JS not in fr:
        fr = fr.replace("</body>", FR_TOGGLE_JS + "</body>", 1)
    fr_path.write_text(fr, encoding="utf-8")


def sitemap():
    alt = "".join(f'<xhtml:link rel="alternate" hreflang="{h}" href="{SITE}/{p}{"/" if p else ""}"/>' for h, p in (("fr-CA", "fr"), ("en-CA", "en"), ("x-default", "")))
    urls = "".join(f"<url><loc>{SITE}/{p}/</loc>{alt}<changefreq>weekly</changefreq><priority>{pr}</priority></url>"
                   for p, pr in (("fr", "1.0"), ("en", "0.9")))
    for key, frs, frslug, ens, enslug, *_ in SECTORS:
        a = "".join(f'<xhtml:link rel="alternate" hreflang="{h}" href="{u}"/>' for h, u in
                    (("fr-CA", f"{SITE}/fr/{frslug}"), ("en-CA", f"{SITE}/en/{enslug}"), ("x-default", f"{SITE}/fr/{frslug}")))
        urls += "".join(f"<url><loc>{u}</loc>{a}<changefreq>monthly</changefreq><priority>0.8</priority></url>"
                        for u in (f"{SITE}/fr/{frslug}", f"{SITE}/en/{enslug}"))
    for frs, ens, kind in PAGES:
        fu, eu = SITE + b2_slug(frs), SITE + b2_slug(ens)
        a = "".join(f'<xhtml:link rel="alternate" hreflang="{h}" href="{u}"/>' for h, u in (("fr-CA", fu), ("en-CA", eu), ("x-default", fu)))
        urls += "".join(f"<url><loc>{u}</loc>{a}<changefreq>monthly</changefreq><priority>0.7</priority></url>" for u in (fu, eu))
    for fp, ep, *_ in HUBS.values():
        a = "".join(f'<xhtml:link rel="alternate" hreflang="{h}" href="{u}"/>' for h, u in
                    (("fr-CA", SITE + fp), ("en-CA", SITE + ep), ("x-default", SITE + fp)))
        urls += "".join(f"<url><loc>{u}</loc>{a}<changefreq>monthly</changefreq><priority>0.6</priority></url>" for u in (SITE + fp, SITE + ep))
    a = "".join(f'<xhtml:link rel="alternate" hreflang="{h}" href="{u}"/>' for h, u in
                (("fr-CA", SITE + B4["fr"][1]), ("en-CA", SITE + B4["en"][1]), ("x-default", SITE + B4["fr"][1])))
    urls += "".join(f"<url><loc>{SITE + B4[l][1]}</loc>{a}<changefreq>monthly</changefreq><priority>0.8</priority></url>" for l in ("fr", "en"))
    if WEEKLY:
        for u in [WEEKLY["hub"]] + [WEEKLY["hub"] + p["slug"] for p in WEEKLY["pages"]]:
            urls += f'<url><loc>{SITE}{u}</loc><xhtml:link rel="alternate" hreflang="fr-CA" href="{SITE}{u}"/><xhtml:link rel="alternate" hreflang="x-default" href="{SITE}{u}"/><changefreq>weekly</changefreq><priority>0.6</priority></url>'
    for langs in LEGAL_PAGES.values():
        a = "".join(f'<xhtml:link rel="alternate" hreflang="{h}" href="{SITE}{langs[l][0]}"/>' for h, l in (("fr-CA", "fr"), ("en-CA", "en"), ("x-default", "fr")))
        urls += "".join(f"<url><loc>{SITE}{langs[l][0]}</loc>{a}<changefreq>yearly</changefreq><priority>0.3</priority></url>" for l in ("fr", "en"))
    urls += f"<url><loc>{SITE}/</loc>{alt}<changefreq>weekly</changefreq><priority>0.8</priority></url>"
    urls = re.sub(r"<loc>([^<]+)</loc>", lambda m: f"<loc>{m.group(1)}</loc><lastmod>{lastmod(m.group(1))}</lastmod>", urls)
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
           + '<br><b lang="en">Resources</b>: ' + " · ".join(f'<a href="{u}" hreflang="en-CA">{t}</a>' for u, t in resources("en"))
           + '<br><b>Explorer</b> : ' + " · ".join(f'<a href="{u}">{t}</a>' for u, t in hub_links("fr"))
           + '<br><b lang="en">Browse</b>: ' + " · ".join(f'<a href="{u}" hreflang="en-CA">{t}</a>' for u, t in hub_links("en")) + "</p>")
    s = re.sub(r'<p class="resources">.*?</p>', "", s, flags=re.S)
    s = re.sub(r'(<p class="sectors">.*?</p>)', lambda m: m.group(1) + res, s, count=1, flags=re.S)
    # head of / (x-default landing): lang, title, description, canonical + hreflang, OG/Twitter, JSON-LD. Idempotent rewrite.
    title = "Veillea | Veille d'appels d'offres SEAO et AchatsCanada"
    desc = ("Veillea surveille le SEAO et AchatsCanada et vous envoie les appels d'offres pertinents, résumés en français et en anglais. "
            "Forfait gratuit, essai 14 jours.")
    assert len(title) <= 60 and 140 <= len(desc) <= 160, (len(title), len(desc))
    s = re.sub(r'<html lang="[^"]*"', '<html lang="fr-CA"', s, count=1)
    s = re.sub(r'<link rel="canonical"[^>]*>|<link rel="alternate" hreflang[^>]*>|<meta property="(?:og|article):[^>]*>|<meta name="twitter:[^>]*>'
               r'|<meta name="description"[^>]*>|<title>.*?</title>|<script type="application/ld\+json">.*?</script>'
               r'|<link rel="icon" type="image/png" sizes="192x192"[^>]*>', "", s, flags=re.S)
    s = s.replace("<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">",
                  "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
                  f'<title>{html.escape(title, quote=False)}</title><meta name="description" content="{html.escape(desc)}">'
                  f'<link rel="canonical" href="{SITE}/">{HREFLANG}' + social("fr", title, desc, f"{SITE}/")
                  + ld(SITE_LD) + ld(software_ld("")), 1)
    s = s.replace('<link rel="manifest"', '<link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png"><link rel="manifest"', 1)
    s = re.sub(r"\n{2,}", "\n", s)
    p.write_text(s, encoding="utf-8")


REDIRECTS = {"fr/tarifs.html": ("fr", "/#pricing", "Voir les tarifs de Veillea"), "en/pricing.html": ("en", "/?lang=en#pricing", "See Veillea pricing"),
             "fr/guide/seuils-appels-offresquebec-2026-2027.html": ("fr", "/fr/guide/seuils-appels-offres-quebec-2026-2027", "Seuils des appels d'offres au Québec 2026-2027")}


def redirect_stubs():
    """Redirect stubs (not in the sitemap): no standalone pricing page, pricing lives in /#pricing."""
    for rel, (lang, target, label) in REDIRECTS.items():
        t = html.escape(target)
        (ROOT / rel).write_text(
            f'<!doctype html><html lang="{lang}-CA"><head><meta charset="utf-8"><title>{label}</title>'
            f'<meta name="robots" content="noindex"><link rel="canonical" href="{SITE}{target if target.startswith('/fr/') else '/'}">'
            f'<meta http-equiv="refresh" content="0; url={t}"><script>location.replace({json.dumps(target)})</script></head>'
            f'<body><p><a href="{t}">{label}</a></p></body></html>\n', encoding="utf-8")


if __name__ == "__main__":
    for lg in ("fr", "en"):
        print(lg, landing(lg))
    sectors(); batch2(); batch4(); weekly_links(); hubs(); legal(); page_404(); finalize_pages(); fr_toggle(); sitemap(); prerender_root(); redirect_stubs(); print("ok")
