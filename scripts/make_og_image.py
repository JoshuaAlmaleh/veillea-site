"""Generate /og-image.png (1200x630, burgundy + copper share image). Run: python3 scripts/make_og_image.py (needs Pillow).
Deterministic: same fonts -> same bytes. Fonts: Source Serif Pro + IBM Plex Mono (falls back to DejaVu)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OX, OX2, CU, PEACH, OXT = "#3e1a24", "#57263a", "#b8561d", "#f0b58b", "#f3e6dc"


def font(cands, size):
    for c in cands:
        try:
            return ImageFont.truetype(c, size)
        except OSError:
            pass
    return ImageFont.load_default(size)


SERIF = ["/usr/share/fonts/truetype/sand-box/custom/Source Serif Pro/SourceSerifPro-Bold.ttf", "DejaVuSerif-Bold.ttf"]
MONO = ["/usr/share/fonts/truetype/sand-box/google/IBM Plex Mono/IBMPlexMono-SemiBold.ttf", "DejaVuSansMono-Bold.ttf"]
SANS = ["/usr/share/fonts/truetype/sand-box/custom/Source Serif Pro/SourceSerifPro-Regular.ttf", "DejaVuSerif.ttf"]

im = Image.new("RGB", (1200, 630), OX)
d = ImageDraw.Draw(im)
for y in range(31, 630, 32):  # ruled-paper lines like the site hero
    d.line([(0, y), (1200, y)], fill="#45202b")
d.rectangle([0, 600, 1200, 630], fill=CU)
cx, cy, r = 160, 250, 74  # copper seal
d.ellipse([cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8], outline="#7a3a22", width=2)
d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=CU, width=6)
d.text((cx, cy + 4), "V", font=font(SERIF, 96), fill=CU, anchor="mm")
d.text((270, 250), "Veillea", font=font(SERIF, 120), fill="#ffffff", anchor="lm")
d.text((90, 400), "Veille d'appels d'offres SEAO et AchatsCanada", font=font(SANS, 44), fill=OXT)
d.text((90, 460), "Public tender alerts for Québec & Canada, in French and English", font=font(SANS, 32), fill=PEACH)
d.text((90, 540), "VEILLEA.CA", font=font(MONO, 26), fill=CU)
im.save(ROOT / "og-image.png", optimize=True)
print("og-image.png", (ROOT / "og-image.png").stat().st_size)
