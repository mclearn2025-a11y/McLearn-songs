"""Feed (4:5, 1080x1350) and widescreen (16:9, 1920x1080) versions of the MP song videos.
Same look as the vertical TikTok cards; layout recomposed for each frame."""
import os, sys, subprocess
from PIL import Image, ImageDraw, ImageFilter
from make import F, SONGS, SRC, INK, PAPER, MUTED, BRAND, BRAND_HI, GOLD, wrap

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out_formats"); os.makedirs(OUT, exist_ok=True)

LAYOUTS = {
    # name: canvas, text column, wave box, bar y, footer y, type sizes
    "feed": dict(W=1080, H=1350, L=80, R=1000, top=90, mp=120, title=(150, 132, 116, 100), tmax=2,
                 wave=(80, 830, 920, 200), bar=1110, foot=1150, label="Feed 4x5"),
    "wide": dict(W=1920, H=1080, L=110, R=1100, top=110, mp=130, title=(150, 132, 116, 100), tmax=2,
                 wave=(1180, 330, 640, 340), bar=880, foot=920, label="Wide 16x9"),
}

PILL = "NEW MUSIC · OUT NOW"
FOOT1 = "Full song on every streaming app"
FOOT2 = "Search  MP {title}"

def background(title, genre, c):
    W, H, L, R = c["W"], c["H"], c["L"], c["R"]
    im = Image.new("RGB", (W, H), INK)
    glow = Image.new("RGB", (W, H), INK); g = ImageDraw.Draw(glow)
    g.ellipse((-W * .3, H * .35, W * .9, H * 1.3), fill="#4A2414")
    g.ellipse((W * .5, -H * .25, W * 1.3, H * .45), fill="#2E1E12")
    im = Image.blend(im, glow.filter(ImageFilter.GaussianBlur(min(W, H) // 6)), 1.0)
    d = ImageDraw.Draw(im)

    pf = F("Hanken-700.ttf", 30); txt = PILL; tw = d.textlength(txt, font=pf)
    y = c["top"]
    d.rounded_rectangle((L, y, L + tw + 50, y + 62), radius=31, outline=BRAND_HI, width=3)
    d.text((L + 25, y + 31), txt, font=pf, fill=BRAND_HI, anchor="lm")
    y += 95
    d.text((L - 4, y), "MP", font=F("Fraunces-700.ttf", c["mp"]), fill=GOLD, anchor="lt")
    y += int(c["mp"] * 1.05) + 26

    for size in c["title"]:
        tf = F("Fraunces-600.ttf", size)
        lines = wrap(d, title, tf, R - L)
        if len(lines) <= c["tmax"] and all(d.textlength(l, font=tf) <= R - L for l in lines): break
    for ln in lines:
        d.text((L, y), ln, font=tf, fill=PAPER, anchor="lt"); y += int(size * 1.02)
    d.text((L, y + 22), genre, font=F("Hanken-500.ttf", 40), fill=MUTED, anchor="lt")

    bx = L if c["W"] < c["H"] * 1.2 else L
    bw = (c["wave"][0] + c["wave"][2]) - L if c["W"] > c["H"] else R - L
    d.rounded_rectangle((bx, c["bar"], bx + bw, c["bar"] + 10), radius=5, fill="#43362A")
    d.text((L, c["foot"]), FOOT1, font=F("Hanken-600.ttf", 38), fill=PAPER, anchor="lt")
    d.text((L, c["foot"] + 54), FOOT2.format(title=title), font=F("Hanken-500.ttf", 34), fill=MUTED, anchor="lt")
    if c["W"] > c["H"]:
        d.text((bx + bw, c["foot"] + 54), "McLearn Media", font=F("Fraunces-600.ttf", 34), fill=MUTED, anchor="rt")
    return im, bx, bw

def render(kind, title, genre, slug):
    c = LAYOUTS[kind]
    im, bx, bw = background(title, genre, c)
    bg = os.path.join(OUT, f"_{kind}-{slug}.png"); im.save(bg)
    out = os.path.join(OUT, f"MP - {title.replace('?','')} - {c['label']}.mp4")
    wx, wy, ww, wh = c["wave"]; dur = 45.0
    fc = (
        f"[1:a]afade=t=in:d=0.4,afade=t=out:st={dur-1.8}:d=1.8,loudnorm=I=-14:TP=-1.0:LRA=11,"
        f"aresample=44100,asplit=2[aout][aviz];"
        f"[aviz]showwaves=s={ww}x{wh}:mode=cline:rate=30:scale=sqrt:draw=full:"
        f"colors=0x{BRAND_HI[1:]},format=rgba,colorkey=black:0.08:0.0[wave];"
        f"color=c=0x{BRAND[1:]}:s={bw}x10:r=30,format=rgba[fillc];"
        f"color=c=black@0.0:s={bw}x10:r=30,format=rgba[empty];"
        f"[fillc][empty]hstack,crop=w={bw}:h=10:x='{bw}-{bw}*min(t/{dur},1)':y=0[prog];"
        f"[0:v][wave]overlay=x={wx}:y={wy}:shortest=1[v1];"
        f"[v1][prog]overlay=x={bx}:y={c['bar']}:shortest=1,"
        f"fade=t=in:d=0.4,fade=t=out:st={dur-0.8}:d=0.8,format=yuv420p[v]"
    )
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-loop", "1", "-framerate", "30", "-i", bg, "-i", os.path.join(SRC, f"{slug}.mp3"),
                    "-filter_complex", fc, "-map", "[v]", "-map", "[aout]", "-t", str(dur), "-r", "30",
                    "-c:v", "libx264", "-profile:v", "high", "-preset", "medium", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
                    "-movflags", "+faststart", out], check=True)
    return out

if __name__ == "__main__":
    kinds = [a for a in sys.argv[1:] if a in LAYOUTS] or list(LAYOUTS)
    picks = [a for a in sys.argv[1:] if a not in LAYOUTS]
    for k in kinds:
        for t, g, s in SONGS:
            if not picks or s in picks:
                print(render(k, t, g, s))
