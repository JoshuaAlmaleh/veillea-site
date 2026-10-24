"""Weekly per-trade pages of OPEN SEAO tenders (FR only): /fr/appels-offres-cette-semaine/<trade>.html + hub.
Data: SEAO open data on Données Québec (OCDS JSON, monthly + weekly files), fetched directly so it runs unattended
(GitHub Actions, weekly). Writes scripts/weekly_manifest.json; refreshes sitemap.xml when tender-seo is available.
Run:  python scripts/build_weekly.py [--cache .cache/seao] [--days 150]   (stdlib + markdown for build_pages import)"""
import html, json, re, sys, unicodedata, urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_pages as B  # noqa: E402  (head/header/footer/JSON-LD helpers; same look and checks as other pages)

ROOT = B.ROOT
ARG = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
CACHE = Path(ARG("--cache", ROOT / ".cache" / "seao"))
DAYS = int(ARG("--days", 150))
TZ = ZoneInfo("America/Toronto")
CKAN = "https://www.donneesquebec.ca/recherche/api/3/action/package_show?id=systeme-electronique-dappel-doffres-seao"
UA = {"User-Agent": "veillea-site-weekly/1.0 (+https://veillea.ca)"}
HUB = "/fr/appels-offres-cette-semaine/"
MANIFEST = ROOT / "scripts" / "weekly_manifest.json"

# Trade rules: title keywords (accent-insensitive, word-start) and/or UNSPSC prefixes; `cat` = OCDS mainProcurementCategory.
# `not_` keywords in the title exclude. `sector` = existing FR sector page that links here.
TRADES = [
 dict(slug="entretien-menager", name="entretien ménager", label="Entretien ménager", sector="appels-offres-entretien-menager",
      kw=["entretien menager", "conciergerie", "menage", "lavage de vitres", "lavage des vitres", "nettoyage des locaux", "nettoyage de locaux",
          "nettoyage d'immeubles", "nettoyage des immeubles", "nettoyage de bureaux", "nettoyage des bureaux", "entretien sanitaire"],
      unspsc=["76111"], not_=["produits", "egout", "pompage", "aqueduc"]),
 dict(slug="toiture", name="toiture", label="Toiture", sector=None,
      kw=["toiture", "toitures", "toit", "toits", "couvreur", "bardeaux"], unspsc=[], not_=["deneigement"]),
 dict(slug="deneigement", name="déneigement", label="Déneigement", sector="appels-offres-deneigement",
      kw=["deneigement", "deglacage", "transport de neige", "soufflage", "epandage d'abrasif", "abrasifs", "sel de deglacage", "sel de voirie", "fondants"],
      unspsc=[], not_=["remorquage"]),
 dict(slug="construction", name="construction", label="Construction", sector="appels-offres-construction-quebec",
      kw=["construction", "agrandissement", "renovation", "refection", "reamenagement", "travaux de", "pavage", "demolition", "maconnerie"],
      unspsc=["72"], not_=[]),
 dict(slug="informatique", name="informatique et TI", label="Informatique / TI", sector="appels-offres-informatique-quebec",
      kw=["informatique", "informatiques", "logiciel", "logiciels", "infonuagique", "ti", "technologies de l'information", "serveurs", "reseautique",
          "cybersecurite", "cyberdefense", "progiciel", "telephonie ip", "stockage"],
      unspsc=["4321", "4322", "4323", "8111", "8116"], not_=[]),
 dict(slug="securite-gardiennage", name="sécurité et gardiennage", label="Sécurité / gardiennage", sector="appels-offres-securite-gardiennage",
      kw=["gardiennage", "agents de securite", "agent de securite", "securite evenementielle", "service de securite", "services de securite",
          "patrouille de securite", "controle d'acces", "agence de securite"], unspsc=["9212"], not_=["camera", "incendie"]),
 dict(slug="transport", name="transport", label="Transport", sector="appels-offres-transport",
      kw=["transport scolaire", "transport adapte", "transport collectif", "transport des usagers", "transport d'usagers", "transport des eleves",
          "transport des equipes", "transport de personnes", "autobus", "taxi", "nolisement", "demenagement", "messagerie", "transport de", "transport entre"],
      unspsc=[], not_=["achat d'autobus", "acquisition d'autobus", "transport de neige", "location de vehicules"]),
 dict(slug="genie-architecture", name="génie et architecture", label="Génie / architecture", sector="appels-offres-genie-architecture",
      kw=["ingenierie", "genie", "ingenieurs", "ingenieurs-conseils", "architecture", "architectes", "architecte", "plans et devis",
          "surveillance des travaux", "geotechnique", "arpentage", "hygiene industrielle"], unspsc=["8110"], not_=["genie logiciel", "analyste"]),
 dict(slug="services-professionnels", name="services professionnels", label="Services professionnels", sector="appels-offres-services-professionnels",
      kw=["services professionnels", "services-conseils", "firmes-conseils", "consultant", "consultation", "accompagnement", "audit", "etude de", "etudes",
          "evaluation", "formation"],
      unspsc=["80", "86"], not_=["ingenierie", "ingenieurs", "architecture", "plans et devis", "surveillance des travaux", "informatique",
                                   "technologies de l'information", "fourniture", "achat", "acquisition"]),
 dict(slug="fournitures", name="fournitures et équipement", label="Fournitures / équipement", sector="appels-offres-fournitures-equipement",
      kw=[], unspsc=[], not_=[]),
]


def norm(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return re.sub(r"[^a-z0-9' -]+", " ", "".join(c for c in s if not unicodedata.combining(c))).replace("’", "'")


def hit(words, text):
    return [w for w in words if re.search(r"(?<![a-z0-9])" + re.escape(w) + r"(?![a-z0-9])", text)]


def classify(t):
    """Title keywords decide; UNSPSC codes count only on service contracts (codes on SEAO notices are often generic)."""
    title = norm(t["title"])
    out = []
    for tr in TRADES:
        if hit(tr["not_"], title):
            continue
        kw = hit(tr["kw"], title)
        code = any(c.startswith(p) for c in t["unspsc"] for p in tr["unspsc"])
        if tr["slug"] == "construction":
            ok = t["cat"] == "works" and (bool(kw) or code)
        elif tr["slug"] == "fournitures":
            ok = t["cat"] == "goods"
        else:
            ok = bool(kw) or (code and t["cat"] == "services")
        if ok:
            out.append(tr["slug"])
    return out


def get(url, dest=None, timeout=300):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    if dest:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    return data


def files(today):
    res = json.loads(get(CKAN, timeout=60))["result"]["resources"]
    rx = re.compile(r"^(hebdo|mensuel)_(\d{8})_(\d{8})\.json$", re.I)
    since = today - timedelta(days=DAYS)
    out = []
    for r in res:
        m = rx.match(r.get("name", ""))
        if m:
            out.append((m.group(1).lower(), datetime.strptime(m.group(2), "%Y%m%d").date(), datetime.strptime(m.group(3), "%Y%m%d").date(), r["name"], r["url"]))
    monthly = sorted((x for x in out if x[0] == "mensuel" and x[2] >= since), key=lambda x: x[1])
    until = max((x[2] for x in monthly), default=since - timedelta(days=1))
    weekly = sorted((x for x in out if x[0] == "hebdo" and x[2] > until), key=lambda x: x[1])
    seen, chosen = set(), []
    for x in monthly + weekly:
        if x[3] not in seen:
            seen.add(x[3]); chosen.append(x)
    return chosen


def load(today):
    chosen = files(today)
    latest = {}
    data_end = max(x[2] for x in chosen)
    for kind, s, e, name, url in chosen:
        p = CACHE / name
        fresh = p.exists() and (e < today - timedelta(days=14) or datetime.now().timestamp() - p.stat().st_mtime < 86400)
        if not fresh:
            print("download", name, file=sys.stderr)
            get(url, p)
        for rel in json.loads(p.read_text(encoding="utf-8")).get("releases", []):
            oc = rel.get("ocid")
            if not oc:
                continue
            key = (rel.get("date") or "", rel.get("id") or "")
            if oc not in latest or key >= latest[oc][0]:
                latest[oc] = (key, rel)
    # keep the cache small: drop files no longer selected
    for f in CACHE.glob("*.json"):
        if f.name not in {x[3] for x in chosen}:
            f.unlink()
    return [r for _, r in latest.values()], data_end


def dt(s):
    try:
        d = datetime.fromisoformat(s)
        return d if d.tzinfo else d.replace(tzinfo=TZ)
    except Exception:
        return None


def to_rows(rels, now):
    rows = []
    for rel in rels:
        t = rel.get("tender") or {}
        tags = rel.get("tag") or []
        end, start = dt((t.get("tenderPeriod") or {}).get("endDate")), dt((t.get("tenderPeriod") or {}).get("startDate"))
        if t.get("status") != "active" or "tenderCancellation" in tags or not end or end <= now:
            continue
        party = next((p for p in rel.get("parties", []) if "buyer" in (p.get("roles") or [])), {})
        addr = party.get("address") or {}
        codes = []
        for it in t.get("items") or []:
            for c in [it.get("classification") or {}] + list(it.get("additionalClassifications") or []):
                if c.get("id"):
                    codes.append(str(c["id"]))
        url = next((d.get("url") for d in t.get("documents") or [] if (d.get("url") or "").startswith("https://")), None)
        title = re.sub(r"\s+", " ", (t.get("title") or "")).strip()
        if not title or not url:
            continue
        rows.append(dict(id=rel["ocid"], num=t.get("id") or "", title=title, buyer=(rel.get("buyer") or {}).get("name") or party.get("name") or "",
                         city=(addr.get("locality") or "").strip().title() if (addr.get("locality") or "").isupper() else (addr.get("locality") or "").strip(),
                         region=addr.get("region") or "", published=start, closing=end, url=url, unspsc=codes, cat=t.get("mainProcurementCategory") or ""))
    return rows


def fr_date(d, time=False):
    d = d.astimezone(TZ)
    s = f"{d.day}{'er' if d.day == 1 else ''} {B.MONTHS['fr'][d.month - 1]} {d.year}"
    return s + (f", {d.hour} h {d.minute:02d}" if time else "")


def footer():
    """Same footer as the rest of the site, taken from the built /fr/ page (B.footer needs the tender-seo sources,
    which are not in this repo / not available in GitHub Actions)."""
    t = (ROOT / "fr" / "index.html").read_text(encoding="utf-8")
    return re.search(r"<footer>.*?</footer>", t, re.S).group(0)


MOIS = "janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split()


def week_label(updated):
    """Monday of the week of the data refresh (Montréal time), e.g. '12 octobre 2026'. Deterministic for a given refresh."""
    d = updated.astimezone(TZ).date()
    m = d - timedelta(days=d.weekday())
    return f"{'1er' if m.day == 1 else m.day} {MOIS[m.month - 1]} {m.year}"


MOIS_ABR = "janv. févr. mars avr. mai juin juil. août sept. oct. nov. déc.".split()
SEO_META = {  # trade slug -> (title template, meta description)
    "entretien-menager": ("Appel d'offres entretien ménager Québec : semaine du {d}",
                          "Appels d'offres en entretien ménager ouverts cette semaine au SEAO : organisme, ville, date de clôture. Recevez-les par alerte : essai 14 jours, sans carte."),
    "construction": ("Appels d'offres construction Québec : semaine du {d}",
                     "Appels d'offres en construction ouverts cette semaine au SEAO : organisme, ville, date de clôture, lien officiel. Alertes : essai 14 jours, sans carte."),
    "fournitures": ("Appels d'offres fournitures Québec : semaine du {d}",
                    "Appels d'offres en fournitures et équipement ouverts cette semaine au SEAO : organisme, ville, clôture. Recevez-les par alerte : essai 14 jours, sans carte."),
    "informatique": ("Appels d'offres TI et informatique Québec : {d}",
                     "Appels d'offres en informatique et TI ouverts cette semaine au SEAO : organisme, ville, date de clôture. Alertes selon profil : essai 14 jours, sans carte."),
}


def week_short(updated):
    """Monday of the refresh week as '{day} {abbreviated month}', e.g. '19 oct.' (same Monday as week_label)."""
    d = updated.astimezone(TZ).date()
    m = d - timedelta(days=d.weekday())
    return f"{'1er' if m.day == 1 else m.day} {MOIS_ABR[m.month - 1]}"


def page(tr, items, updated, data_end):
    url = f"{B.SITE}{HUB}{tr['slug']}"
    n = len(items)
    wk = week_label(updated)
    title = next(t for t in (f"Appels d'offres {tr['name']}, semaine du {wk} | Veillea", f"Appels d'offres {tr['name']}, semaine du {wk}",
                             f"AO {tr['name']}, semaine du {wk}") if len(t) <= 60)
    desc = next(d for d in (
        f"Appels d'offres SEAO en {tr['name']} ouverts la semaine du {wk} : organisme, ville, dates de clôture et lien vers l'avis officiel.",
        f"Appels d'offres SEAO en {tr['name']}, semaine du {wk} : organisme, ville, clôture et lien vers l'avis officiel.",
        f"SEAO, {tr['name']}, semaine du {wk} : appels d'offres ouverts, organismes, dates de clôture.") if len(d) <= 160)
    if tr["slug"] in SEO_META:  # Tender SEO handoff (items 1-2-5): title template with the current week's Monday, fixed description
        t_tpl, d_fix = SEO_META[tr["slug"]]
        t_new = t_tpl.format(d=week_short(updated))
        if len(t_new) <= 60:  # else keep the generic title (e.g. 2-digit day + "sept." would exceed 60 characters)
            title = t_new
        desc = d_fix
    assert len(title) <= 60 and 70 <= len(desc) <= 160, (tr["slug"], len(title), len(desc))
    crumbs = [("Accueil", f"{B.SITE}/fr/"), ("Appels d'offres cette semaine", B.SITE + HUB), (tr["label"], url)]
    lds = B.ld(B.crumbs_ld(crumbs))
    if items:
        lds += B.ld({"@context": "https://schema.org", "@type": "ItemList", "name": f"Appels d'offres ouverts en {tr['name']}",
                     "numberOfItems": n, "itemListElement": [{"@type": "ListItem", "position": i, "url": r["url"], "name": r["title"][:150]}
                                                             for i, r in enumerate(items[:50], 1)]})
    alts = f'<link rel="alternate" hreflang="fr-CA" href="{url}"><link rel="alternate" hreflang="x-default" href="{url}">'
    out = B.head("fr", title, desc, url, lds, alts)
    rows = "".join(
        f'<tr><td><a href="{html.escape(r["url"])}" rel="nofollow noopener" target="_blank">{html.escape(r["title"])}</a>'
        f'{f"<small>{html.escape(r["num"])}</small>" if r["num"] else ""}</td><td>{html.escape(r["buyer"])}</td>'
        f'<td>{html.escape(r["city"] or "—")}</td><td>{fr_date(r["published"]) if r["published"] else "—"}</td>'
        f'<td><b>{fr_date(r["closing"])}</b></td></tr>' for r in items)
    table = (f'<div class="cmpwrap wk"><table class="cmp wk-t"><thead><tr><th scope="col">Appel d\'offres</th><th scope="col">Organisme</th>'
             f'<th scope="col">Ville</th><th scope="col">Publié</th><th scope="col">Clôture</th></tr></thead><tbody>{rows}</tbody></table></div>'
             if items else '<p class="note">Aucun appel d\'offres ouvert dans cette catégorie pour le moment. Revenez la semaine prochaine.</p>')
    sec = f' Voir aussi notre page <a href="/fr/{tr["sector"]}">appels d\'offres en {tr["name"]}</a>.' if tr["sector"] else ""
    cta = (f'<div class="wk-cta"><div><h2>Recevez ces avis automatiquement</h2><p>Veillea surveille le SEAO et 13 autres sources et vous envoie '
           f'les nouveaux appels d\'offres en {tr["name"]} selon vos mots-clés et vos régions. Essai gratuit de 14 jours, sans carte de crédit.</p></div>'
           f'<p class="ctas"><a class="btn" href="{B.APP_URL}/signup?plan=team&amp;interval=monthly&amp;lang=fr">Essai gratuit 14 jours</a>'
           f'<a class="btn ghost" href="{B.APP_URL}/signup?plan=free&amp;interval=monthly&amp;lang=fr">Alerte hebdo gratuite</a></p></div>')
    body = (f'{B.crumbs_html("fr", crumbs)}<h1>Appels d\'offres {tr["name"]} — semaine du {wk}</h1>'
            f'<p class="wk-meta">Mis à jour le {fr_date(updated)} · Données ouvertes SEAO jusqu\'au {fr_date(datetime.combine(data_end, datetime.min.time(), TZ))} · '
            f'<b>{n}</b> appel{"s" if n != 1 else ""} d\'offres ouvert{"s" if n != 1 else ""}</p>'
            f'<p>Liste des appels d\'offres publics du SEAO (Québec) encore ouverts dans la catégorie {tr["name"]}, triés par date de clôture. '
            f'Chaque titre mène à l\'avis officiel sur le SEAO, où se trouvent les documents et les modalités de dépôt.{sec}</p>'
            + cta + table +
            '<p class="small">Classement automatique selon le titre et les codes UNSPSC de l\'avis; une catégorie peut contenir des avis connexes. '
            'Source : données ouvertes du SEAO (Données Québec), mises à jour chaque semaine. Vérifiez toujours l\'avis officiel avant de soumissionner.</p>'
            f'<p><a href="{HUB}">← Toutes les catégories cette semaine</a></p>')
    out += B.no_pair_switch(B.header("fr"), "fr") + f'<main class="landing"><div class="wrap prose">{body}</div></main>' + footer() + B.CF_BEACON + "</body></html>\n"
    assert "<!--" not in out.replace(B.CF_BEACON, "")
    return out


def hub(counts, updated):
    url = B.SITE + HUB
    wk = week_label(updated)
    title = f"Appels d'offres par métier, semaine du {wk} | Veillea"
    if len(title) > 60:
        title = f"Appels d'offres par métier, semaine du {wk}"
    desc = (f"Appels d'offres SEAO ouverts la semaine du {wk}, par métier : entretien ménager, toiture, déneigement, construction, "
            "informatique, etc.")
    assert len(title) <= 60 and len(desc) <= 160, (len(title), len(desc))
    crumbs = [("Accueil", f"{B.SITE}/fr/"), ("Appels d'offres cette semaine", url)]
    out = B.head("fr", title, desc, url, B.ld(B.crumbs_ld(crumbs)), f'<link rel="alternate" hreflang="fr-CA" href="{url}"><link rel="alternate" hreflang="x-default" href="{url}">')
    cards = "".join(f'<a class="card wk-card" href="{HUB}{t["slug"]}"><b>{counts[t["slug"]]}</b><span>{t["label"]}</span></a>' for t in TRADES)
    body = (f'{B.crumbs_html("fr", crumbs)}<h1>Appels d\'offres ouverts — semaine du {wk}</h1><p class="wk-meta">Mis à jour le {fr_date(updated)}</p>'
            '<p>Les appels d\'offres publics du SEAO encore ouverts, classés par métier. Chaque page liste le titre, l\'organisme, la ville, '
            'les dates de publication et de clôture, avec un lien vers l\'avis officiel.</p>'
            f'<div class="wk-grid">{cards}</div>'
            f'<p class="ctas"><a class="btn" href="{B.APP_URL}/signup?plan=team&amp;interval=monthly&amp;lang=fr">Essai gratuit 14 jours</a></p>')
    out += B.no_pair_switch(B.header("fr"), "fr") + f'<main class="landing"><div class="wrap prose">{body}</div></main>' + footer() + B.CF_BEACON + "</body></html>\n"
    return out


def main():
    now = datetime.now(timezone.utc)
    rels, data_end = load(date.today())
    rows = to_rows(rels, now)
    print(f"{len(rels)} releases, {len(rows)} open SEAO tenders (data to {data_end})", file=sys.stderr)
    by = {t["slug"]: [] for t in TRADES}
    for r in rows:
        for s in classify(r):
            by[s].append(r)
    outdir = ROOT / HUB.strip("/")
    outdir.mkdir(parents=True, exist_ok=True)
    for f in outdir.glob("*.html"):
        f.unlink()
    for t in TRADES:
        items = sorted(by[t["slug"]], key=lambda r: (r["closing"], r["title"]))
        (outdir / f"{t['slug']}.html").write_text(page(t, items, now, data_end), encoding="utf-8")
    counts = {t["slug"]: len(by[t["slug"]]) for t in TRADES}
    (outdir / "index.html").write_text(hub(counts, now), encoding="utf-8")
    MANIFEST.write_text(json.dumps({"hub": HUB, "updated": now.astimezone(TZ).date().isoformat(), "week": week_label(now), "pages": [{"slug": t["slug"], "label": t["label"], "sector": t["sector"], "count": counts[t["slug"]]}
                                                       for t in TRADES]}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if B.SEO.exists():  # the URL set is fixed (TRADES), so the committed sitemap stays valid when sources are absent
        B.sitemap()
    print(json.dumps(counts, ensure_ascii=False))


if __name__ == "__main__":
    main()
