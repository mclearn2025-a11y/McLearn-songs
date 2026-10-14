"""Build TikTok-ready 1080x1920 videos for MP songs.
Safe zone: keep text clear of TikTok's top bar (~150px), right-side buttons (~140px)
and the bottom caption/sound area (~420px)."""
import subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "..", "audio")  # the 45-second clips in this repo
OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
W, H = 1080, 1920
INK, PAPER, MUTED, BRAND, BRAND_HI, GOLD = "#15100C", "#FAF1E5", "#C9B6A1", "#C45D34", "#E8835A", "#E4B458"
F = lambda n, s: ImageFont.truetype(os.path.join(HERE, "fonts", n), s)

SONGS = [
    ("These Regrets", "Southern Soul", "these-regrets"),
    ("Who Got Your Back", "Soul / Rap", "who-got-your-back"),
    ("Can I?", "Southern Soul", "can-i"),
    ("Rain and You", "Slow Ballad", "rain-and-you"),
    ("TEA", "Slow Jam", "tea"),
    ("I See You", "Southern Soul", "i-see-you"),
    ("Who Am I", "Slow Ballad", "who-am-i"),
    ("Hey You", "Rhythm & Soul", "hey-you"),
    ("I Can't Tell", "Southern Soul", "i-cant-tell"),
    ("Thank You", "Trap-Soul Duet", "thank-you-remix"),
]

L, R = 72, 940          # left edge / right limit of the safe zone
WAVE_Y, WAVE_H = 1080, 260
BAR_Y = 1400

def wrap(draw, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= maxw: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur); return lines

def background(title, genre):
    im = Image.new("RGB", (W, H), INK)
    glow = Image.new("RGB", (W, H), INK); g = ImageDraw.Draw(glow)
    g.ellipse((-300, 650, 1100, 1750), fill="#4A2414")
    g.ellipse((500, -200, 1400, 700), fill="#2E1E12")
    im = Image.blend(im, glow.filter(ImageFilter.GaussianBlur(220)), 1.0)
    d = ImageDraw.Draw(im)

    # top: label pill
    pill = F("Hanken-700.ttf", 34); txt = "NEW MUSIC · OUT NOW"
    tw = d.textlength(txt, font=pill)
    d.rounded_rectangle((L, 190, L + tw + 56, 190 + 70), radius=35, outline=BRAND_HI, width=3)
    d.text((L + 28, 225), txt, font=pill, fill=BRAND_HI, anchor="lm")

    # artist
    d.text((L, 330), "MP", font=F("Fraunces-700.ttf", 150), fill=GOLD, anchor="lt")

    # title, sized to fit
    for size in (190, 170, 150, 130, 112, 96):
        tf = F("Fraunces-600.ttf", size)
        lines = wrap(d, title, tf, R - L)
        if len(lines) <= 3 and all(d.textlength(l, font=tf) <= R - L for l in lines): break
    y = 540
    for ln in lines:
        d.text((L, y), ln, font=tf, fill=PAPER, anchor="lt"); y += int(size * 1.02)

    d.text((L, y + 30), genre, font=F("Hanken-500.ttf", 44), fill=MUTED, anchor="lt")

    # progress track (fill is animated in ffmpeg)
    d.rounded_rectangle((L, BAR_Y, R, BAR_Y + 10), radius=5, fill="#43362A")

    # footer inside safe zone
    d.text((L, BAR_Y + 44), "Full song on every streaming app", font=F("Hanken-600.ttf", 40), fill=PAPER, anchor="lt")
    sf = F("Hanken-500.ttf", 36)
    for size in (36, 32, 28):
        sf = F("Hanken-500.ttf", size)
        if d.textlength(f"Search  MP {title}", font=sf) <= R - L: break
    d.text((L, BAR_Y + 100), f"Search  MP {title}", font=sf, fill=MUTED, anchor="lt")
    return im

def render(title, genre, slug):
    bg = os.path.join(OUT, f"{slug}.png"); background(title, genre).save(bg)
    out = os.path.join(OUT, f"MP - {title.replace('?','')} - TikTok.mp4")
    dur = 45.0
    fc = (
        f"[1:a]afade=t=in:d=0.4,afade=t=out:st={dur-1.8}:d=1.8,loudnorm=I=-14:TP=-1.0:LRA=11,"
        f"aresample=44100,asplit=2[aout][aviz];"
        f"[aviz]showwaves=s={R-L}x{WAVE_H}:mode=cline:rate=30:scale=sqrt:draw=full:"
        f"colors=0x{BRAND_HI[1:]},format=rgba,colorkey=black:0.08:0.0[wave];"
        f"color=c=0x{BRAND[1:]}:s={R-L}x10:r=30,format=rgba[fillc];"
        f"color=c=black@0.0:s={R-L}x10:r=30,format=rgba[empty];"
        f"[fillc][empty]hstack,crop=w={R-L}:h=10:x='{R-L}-{R-L}*min(t/{dur},1)':y=0[prog];"
        f"[0:v][wave]overlay=x={L}:y={WAVE_Y}:shortest=1[v1];"
        f"[v1][prog]overlay=x={L}:y={BAR_Y}:shortest=1,"
        f"fade=t=in:d=0.4,fade=t=out:st={dur-0.8}:d=0.8,format=yuv420p[v]"
    )
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-loop", "1", "-framerate", "30", "-i", bg,
           "-i", os.path.join(SRC, f"{slug}.mp3"),
           "-filter_complex", fc, "-map", "[v]", "-map", "[aout]",
           "-t", str(dur), "-r", "30",
           "-c:v", "libx264", "-profile:v", "high", "-level", "4.1", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
           "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    return out

if __name__ == "__main__":
    pick = sys.argv[1:]
    for t, g, s in SONGS:
        if not pick or s in pick:
            print(render(t, g, s))
