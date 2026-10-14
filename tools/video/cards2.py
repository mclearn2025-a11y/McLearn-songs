"""Opening and closing cards for the Feed 4:5 and Wide 16:9 all-songs videos."""
import os
from PIL import Image, ImageDraw, ImageFilter
from make import F, SONGS, INK, PAPER, MUTED, BRAND, BRAND_HI, GOLD

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out_formats")

def base(W, H):
    im = Image.new("RGB", (W, H), INK)
    glow = Image.new("RGB", (W, H), INK); g = ImageDraw.Draw(glow)
    g.ellipse((-W * .3, H * .35, W * .9, H * 1.3), fill="#4A2414")
    g.ellipse((W * .5, -H * .25, W * 1.3, H * .45), fill="#2E1E12")
    return Image.blend(im, glow.filter(ImageFilter.GaussianBlur(min(W, H) // 6)), 1.0)

def pill(d, x, y, txt):
    f = F("Hanken-700.ttf", 30); tw = d.textlength(txt, font=f)
    d.rounded_rectangle((x, y, x + tw + 50, y + 62), radius=31, outline=BRAND_HI, width=3)
    d.text((x + 25, y + 31), txt, font=f, fill=BRAND_HI, anchor="lm")

def tracklist(d, x, y, step, size=36):
    nf, tf = F("Hanken-600.ttf", size - 6), F("Hanken-600.ttf", size)
    for i, (t, _, _) in enumerate(SONGS, 1):
        d.text((x, y), f"{i:02d}", font=nf, fill=BRAND_HI, anchor="lt")
        d.text((x + 72, y - 3), t, font=tf, fill=PAPER, anchor="lt"); y += step

def outro_block(d, x, y, head):
    for ln in ("Hear the full songs", "everywhere you stream"):
        d.text((x, y), ln, font=F("Fraunces-600.ttf", head), fill=PAPER, anchor="lt"); y += int(head * 1.2)
    d.text((x, y + 26), "Search  MP  on Spotify, Apple Music and every streaming app",
           font=F("Hanken-600.ttf", 34), fill=PAPER, anchor="lt")
    d.rounded_rectangle((x, y + 100, x + 520, y + 190), radius=45, fill=BRAND)
    d.text((x + 260, y + 145), "MP fan page · link below", font=F("Hanken-700.ttf", 36), fill=PAPER, anchor="mm")
    d.text((x, y + 230), "McLearn Media", font=F("Fraunces-600.ttf", 36), fill=MUTED, anchor="lt")

def feed():
    W, H, L = 1080, 1350, 80
    a = base(W, H); d = ImageDraw.Draw(a)
    pill(d, L, 90, "NEW MUSIC · OUT NOW")
    d.text((L - 6, 180), "MP", font=F("Fraunces-700.ttf", 230), fill=GOLD, anchor="lt")
    d.text((L, 450), "Ten new songs", font=F("Fraunces-600.ttf", 84), fill=PAPER, anchor="lt")
    d.text((L, 556), "from McLearn Media", font=F("Hanken-500.ttf", 40), fill=MUTED, anchor="lt")
    d.line((L, 640, W - L, 640), fill="#43362A", width=3)
    tracklist(d, L, 680, 58)
    b = base(W, H); d = ImageDraw.Draw(b)
    pill(d, L, 90, "THANKS FOR LISTENING")
    d.text((L - 6, 190), "MP", font=F("Fraunces-700.ttf", 230), fill=GOLD, anchor="lt")
    outro_block(d, L, 500, 84)
    return a, b

def wide():
    W, H, L = 1920, 1080, 110
    a = base(W, H); d = ImageDraw.Draw(a)
    pill(d, L, 110, "NEW MUSIC · OUT NOW")
    d.text((L - 6, 210), "MP", font=F("Fraunces-700.ttf", 260), fill=GOLD, anchor="lt")
    d.text((L, 520), "Ten new songs", font=F("Fraunces-600.ttf", 96), fill=PAPER, anchor="lt")
    d.text((L, 640), "from McLearn Media", font=F("Hanken-500.ttf", 42), fill=MUTED, anchor="lt")
    d.line((1080, 150, 1080, 930), fill="#43362A", width=3)
    tracklist(d, 1160, 170, 76, 42)
    b = base(W, H); d = ImageDraw.Draw(b)
    pill(d, L, 110, "THANKS FOR LISTENING")
    d.text((L - 6, 210), "MP", font=F("Fraunces-700.ttf", 260), fill=GOLD, anchor="lt")
    outro_block(d, L, 520, 96)
    return a, b

if __name__ == "__main__":
    for name, fn in (("feed", feed), ("wide", wide)):
        a, b = fn()
        a.save(os.path.join(OUT, f"_intro-{name}.png")); b.save(os.path.join(OUT, f"_outro-{name}.png"))
    print("ok")
