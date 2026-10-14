"""Opening and closing cards for the all-songs video (1080x1920, same look as the song cards)."""
import os
from PIL import Image, ImageDraw, ImageFilter
from make import F, W, H, L, R, INK, PAPER, MUTED, BRAND, BRAND_HI, GOLD, SONGS, OUT

def base():
    im = Image.new("RGB", (W, H), INK)
    glow = Image.new("RGB", (W, H), INK); g = ImageDraw.Draw(glow)
    g.ellipse((-300, 650, 1100, 1750), fill="#4A2414")
    g.ellipse((500, -200, 1400, 700), fill="#2E1E12")
    return Image.blend(im, glow.filter(ImageFilter.GaussianBlur(220)), 1.0)

def pill(d, y, txt):
    f = F("Hanken-700.ttf", 34); tw = d.textlength(txt, font=f)
    d.rounded_rectangle((L, y, L + tw + 56, y + 70), radius=35, outline=BRAND_HI, width=3)
    d.text((L + 28, y + 35), txt, font=f, fill=BRAND_HI, anchor="lm")

def intro():
    im = base(); d = ImageDraw.Draw(im)
    pill(d, 190, "NEW MUSIC · OUT NOW")
    d.text((L - 6, 300), "MP", font=F("Fraunces-700.ttf", 300), fill=GOLD, anchor="lt")
    d.text((L, 640), "Ten new songs", font=F("Fraunces-600.ttf", 96), fill=PAPER, anchor="lt")
    d.text((L, 760), "from McLearn Media", font=F("Hanken-500.ttf", 46), fill=MUTED, anchor="lt")
    d.line((L, 860, R, 860), fill="#43362A", width=3)
    nf, tf = F("Hanken-600.ttf", 34), F("Hanken-600.ttf", 40)
    y = 900
    for i, (t, _, _) in enumerate(SONGS, 1):
        d.text((L, y), f"{i:02d}", font=nf, fill=BRAND_HI, anchor="lt")
        d.text((L + 80, y - 3), t, font=tf, fill=PAPER, anchor="lt")
        y += 58
    return im

def outro():
    im = base(); d = ImageDraw.Draw(im)
    pill(d, 190, "THANKS FOR LISTENING")
    d.text((L - 6, 320), "MP", font=F("Fraunces-700.ttf", 300), fill=GOLD, anchor="lt")
    y = 680
    for ln in ("Hear the full", "songs everywhere", "you stream"):
        d.text((L, y), ln, font=F("Fraunces-600.ttf", 96), fill=PAPER, anchor="lt"); y += 122
    d.text((L, y + 40), "Search  MP  on Spotify, Apple Music", font=F("Hanken-600.ttf", 40), fill=PAPER, anchor="lt")
    d.text((L, y + 96), "and every streaming app", font=F("Hanken-600.ttf", 40), fill=PAPER, anchor="lt")
    d.rounded_rectangle((L, y + 190, L + 470, y + 290), radius=50, fill=BRAND)
    d.text((L + 235, y + 240), "Link in bio", font=F("Hanken-700.ttf", 46), fill=PAPER, anchor="mm")
    d.text((L, y + 340), "McLearn Media", font=F("Fraunces-600.ttf", 40), fill=MUTED, anchor="lt")
    return im

if __name__ == "__main__":
    intro().save(os.path.join(OUT, "_intro.png")); outro().save(os.path.join(OUT, "_outro.png"))
    print("ok")
