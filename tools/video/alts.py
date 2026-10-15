"""Videos for the two alternate versions (fan page exclusives), in all three shapes.
Usage: python3 alts.py OUTDIR"""
import os, sys, shutil
import make, formats

ALTS = [("Who Got Your Back", "Flow Mix · Soul / Rap", "who-got-your-back-flow"),
        ("I See You", "Alternate Version · Southern Soul", "i-see-you-alt")]
OUT = os.path.abspath(sys.argv[1]); os.makedirs(OUT, exist_ok=True)
for m in (make, formats):
    m.PILL = "FAN PAGE EXCLUSIVE"
    m.FOOT1 = "Only on the MP fan page"
    m.FOOT2 = "Hear it free · link in bio"
for title, genre, slug in ALTS:
    p = make.render(title, genre, slug); shutil.move(p, os.path.join(OUT, f"mp-{slug}-tiktok.mp4")); print("tall", slug, flush=True)
    for kind, suffix in (("feed", "feed-4x5"), ("wide", "wide-16x9")):
        p = formats.render(kind, title, genre, slug); shutil.move(p, os.path.join(OUT, f"mp-{slug}-{suffix}.mp4")); print(kind, slug, flush=True)
print("ALLDONE", flush=True)
