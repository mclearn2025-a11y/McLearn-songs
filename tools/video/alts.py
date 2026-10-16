"""Videos for the two second versions, in all three shapes (both are out on every app).
Who Got Your Back (Flow Mix, Remastered) is labelled as the featured release.
Usage: python3 alts.py OUTDIR"""
import os, sys, shutil
import make, formats

ALTS = [("Who Got Your Back", "Flow Mix · Remastered", "who-got-your-back-flow", "FEATURED RELEASE"),
        ("I See You", "Alternate Version · Southern Soul", "i-see-you-alt", "NEW MUSIC · OUT NOW")]
OUT = os.path.abspath(sys.argv[1]); os.makedirs(OUT, exist_ok=True)
for title, genre, slug, pill in ALTS:
    for m in (make, formats):
        m.PILL = pill
        m.FOOT1 = "Full song on every streaming app"
        m.FOOT2 = "Search  MP {title}"
    p = make.render(title, genre, slug); shutil.move(p, os.path.join(OUT, f"mp-{slug}-tiktok.mp4")); print("tall", slug, flush=True)
    for kind, suffix in (("feed", "feed-4x5"), ("wide", "wide-16x9")):
        p = formats.render(kind, title, genre, slug); shutil.move(p, os.path.join(OUT, f"mp-{slug}-{suffix}.mp4")); print(kind, slug, flush=True)
print("ALLDONE", flush=True)
