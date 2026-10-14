"""TikTok 'pick your song' compilation: all 10 MP clips in one 9:16 video.

Every frame shows the full tracklist with each song's start time and the current song
lit up, so viewers can pause (tap) and jump (drag TikTok's progress bar) to any song.
Opens with a 2.5-second hook and ends with a comment prompt, the two things that most
help a TikTok travel. Text stays inside TikTok's safe zone (clear of the top bar, the
right-hand buttons and the caption area at the bottom).

Usage: python3 pick.py OUTDIR      (needs ffmpeg; about 10 minutes)
"""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter
from make import F, SONGS, SRC, INK, PAPER, MUTED, BRAND, BRAND_HI, GOLD, wrap

W, H = 1080, 1920
L, R = 72, 940                 # safe zone: left edge and right limit
CLIP = 45.0                    # every clip is 45 seconds
WAVE = (L, 600, R - L, 150)    # x, y, w, h
BAR_Y = 785
LIST_Y = 905
ROW = 50
PLATFORMS = ["Spotify", "Apple Music", "YouTube Music", "Amazon Music", "TIDAL", "Deezer", "Pandora", "TikTok"]
OUTRO_S = 8.0                  # closing card length
SKIP_Y = 818
OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "pick_out")
os.makedirs(OUT, exist_ok=True)

def stamp(i):
    s = int(i * CLIP); return f"{s // 60}:{s % 60:02d}"

def base():
    im = Image.new("RGB", (W, H), INK)
    glow = Image.new("RGB", (W, H), INK); g = ImageDraw.Draw(glow)
    g.ellipse((-300, 500, 1100, 1700), fill="#4A2414")
    g.ellipse((500, -250, 1400, 600), fill="#2E1E12")
    return Image.blend(im, glow.filter(ImageFilter.GaussianBlur(220)), 1.0)

def frame(n):
    title, genre, _ = SONGS[n]
    im = base(); d = ImageDraw.Draw(im)
    # top row: song counter + artist
    f = F("Hanken-700.ttf", 32); t = f"SONG {n + 1} OF {len(SONGS)}"; tw = d.textlength(t, font=f)
    d.rounded_rectangle((L, 165, L + tw + 52, 165 + 64), radius=32, fill=GOLD)
    d.text((L + 26, 197), t, font=f, fill=INK, anchor="lm")
    d.text((R, 197), "MP", font=F("Fraunces-700.ttf", 64), fill=GOLD, anchor="rm")
    # title
    for size in (150, 132, 116, 100):
        tf = F("Fraunces-600.ttf", size); lines = wrap(d, title, tf, R - L)
        if len(lines) <= 2 and all(d.textlength(l, font=tf) <= R - L for l in lines): break
    y = 268 if len(lines) == 2 else 330
    for ln in lines:
        d.text((L, y), ln, font=tf, fill=PAPER, anchor="lt"); y += int(size * 1.0)
    d.text((L, y + 18), genre, font=F("Hanken-500.ttf", 40), fill=MUTED, anchor="lt")
    # song progress track (fill animated in ffmpeg)
    d.rounded_rectangle((L, BAR_Y, R, BAR_Y + 10), radius=5, fill="#43362A")
    # skip button: shows the next song and where it starts (drag the bar there)
    f2 = F("Hanken-700.ttf", 30)
    d.rounded_rectangle((L, SKIP_Y, L + 176, SKIP_Y + 56), radius=28, fill=PAPER)
    x0 = L + 24; cy = SKIP_Y + 28
    d.polygon([(x0, cy - 13), (x0, cy + 13), (x0 + 16, cy)], fill=INK)
    d.polygon([(x0 + 16, cy - 13), (x0 + 16, cy + 13), (x0 + 32, cy)], fill=INK)
    d.rectangle((x0 + 33, cy - 13, x0 + 37, cy + 13), fill=INK)
    d.text((x0 + 52, cy), "SKIP", font=f2, fill=INK, anchor="lm")
    if n + 1 < len(SONGS):
        nxt = f"Next: {SONGS[n + 1][0]} at {stamp(n + 1)}"
    else:
        nxt = "Last song · drag back to replay any song"
    nf = F("Hanken-600.ttf", 32)
    while d.textlength(nxt, font=nf) > R - (L + 200) and nf.size > 24:
        nf = F("Hanken-600.ttf", nf.size - 2)
    d.text((L + 200, cy), nxt, font=nf, fill=PAPER, anchor="lm")
    # tracklist menu
    d.text((L, LIST_Y), "TAP TO PAUSE · DRAG THE BAR TO PICK A SONG", font=F("Hanken-700.ttf", 27), fill=BRAND_HI, anchor="lt")
    y = LIST_Y + 52
    for i, (t, _, _) in enumerate(SONGS):
        on = i == n
        if on:
            d.rounded_rectangle((L - 14, y - 8, R, y + ROW - 14), radius=14, fill=BRAND)
            d.polygon([(L + 2, y + 6), (L + 2, y + 32), (L + 24, y + 19)], fill=PAPER)
        tm = F("Hanken-700.ttf" if on else "Hanken-600.ttf", 31)
        d.text((L + 44, y + 17), stamp(i), font=tm, fill=PAPER if on else GOLD, anchor="lm")
        d.text((L + 150, y + 17), t, font=F("Hanken-700.ttf" if on else "Hanken-500.ttf", 33), fill=PAPER if on else MUTED, anchor="lm")
        y += ROW
    # where to get the full songs (names only: TikTok videos can't hold tappable links)
    line = "FULL SONGS: Spotify · Apple Music · YouTube · Amazon · TikTok"
    ff = F("Hanken-700.ttf", 26)
    while d.textlength(line, font=ff) > R - L and ff.size > 20:
        ff = F("Hanken-700.ttf", ff.size - 1)
    d.text((L, y + 6), line, font=ff, fill=GOLD, anchor="lt")
    return im

def outro_card():
    """Closing card: comment prompt, every platform with the full songs, fan page via bio link."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    y0, y1 = 300, 1190
    d.rounded_rectangle((L - 24, y0, R + 24, y1), radius=36, fill=(21, 16, 12, 255), outline=GOLD, width=4)
    cx = (L + R) // 2
    d.text((cx, y0 + 50), "Which one is your favorite?", font=F("Fraunces-600.ttf", 58), fill=PAPER, anchor="mt")
    d.text((cx, y0 + 140), "Comment 1 – 10", font=F("Hanken-700.ttf", 60), fill=GOLD, anchor="mt")
    d.line((L + 20, y0 + 240, R - 20, y0 + 240), fill="#43362A", width=3)
    d.text((cx, y0 + 270), "GET THE FULL SONGS ON", font=F("Hanken-700.ttf", 32), fill=BRAND_HI, anchor="mt")
    pf = F("Hanken-600.ttf", 40); colx = (L + 40, cx + 30); y = y0 + 340
    for i, p in enumerate(PLATFORMS):
        x = colx[i % 2]
        d.ellipse((x, y + 12, x + 16, y + 28), fill=GOLD)
        d.text((x + 32, y + 20), p, font=pf, fill=PAPER, anchor="lm")
        if i % 2: y += 66
    d.text((cx, y + 22), "Search  MP  + the song title", font=F("Hanken-500.ttf", 34), fill=MUTED, anchor="mt")
    d.rounded_rectangle((cx - 300, y + 92, cx + 300, y + 176), radius=42, fill=BRAND)
    d.text((cx, y + 134), "MP fan page · link in bio", font=F("Hanken-700.ttf", 38), fill=PAPER, anchor="mm")
    d.text((cx, y + 210), "Follow MP for new music", font=F("Hanken-600.ttf", 34), fill=MUTED, anchor="mt")
    return im

def card(lines, y0, y1):
    """Dark rounded card with stacked lines: (text, font, size, color)."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((L - 24, y0, R + 24, y1), radius=36, fill=(21, 16, 12, 238), outline=GOLD, width=4)
    y = y0 + 54
    for text, font, size, color, gap in lines:
        d.text((W // 2 - 70, y), text, font=F(font, size), fill=color, anchor="mt"); y += gap
    return im

def render_song(n, path):
    bg = os.path.join(OUT, f"_bg{n}.png"); frame(n).save(bg)
    wx, wy, ww, wh = WAVE; bw = R - L
    fc = (
        f"[1:a]afade=t=in:d=0.3,afade=t=out:st={CLIP-1.2}:d=1.2,loudnorm=I=-14:TP=-1.0:LRA=11,aresample=44100,asplit=2[aout][aviz];"
        f"[aviz]showwaves=s={ww}x{wh}:mode=cline:rate=30:scale=sqrt:draw=full:colors=0x{BRAND_HI[1:]},format=rgba,colorkey=black:0.08:0.0[wave];"
        f"color=c=0x{GOLD[1:]}:s={bw}x10:r=30,format=rgba[fillc];color=c=black@0.0:s={bw}x10:r=30,format=rgba[empty];"
        f"[fillc][empty]hstack,crop=w={bw}:h=10:x='{bw}-{bw}*min(t/{CLIP},1)':y=0[prog];"
        f"[0:v][wave]overlay=x={wx}:y={wy}:shortest=1[v1];[v1][prog]overlay=x={L}:y={BAR_Y}:shortest=1,format=yuv420p[v]"
    )
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-loop", "1", "-framerate", "30", "-i", bg,
                    "-i", os.path.join(SRC, SONGS[n][2] + ".mp3"), "-filter_complex", fc, "-map", "[v]", "-map", "[aout]",
                    "-t", str(CLIP), "-r", "30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "44100", path], check=True)

def main():
    parts = []
    for n in range(len(SONGS)):
        p = os.path.join(OUT, f"_part{n}.mp4"); render_song(n, p); parts.append(p); print("song", n + 1, flush=True)
    lst = os.path.join(OUT, "_list.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    joined = os.path.join(OUT, "_joined.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined], check=True)

    total = CLIP * len(SONGS)
    hook = card([("10 NEW SONGS", "Hanken-700.ttf", 46, BRAND_HI, 70),
                 ("in 1 video", "Fraunces-700.ttf", 120, PAPER, 150),
                 ("Drag the bar to skip to yours", "Hanken-600.ttf", 40, GOLD, 60)], 560, 960)
    outro = outro_card()
    hp, op = os.path.join(OUT, "_hook.png"), os.path.join(OUT, "_outro.png"); hook.save(hp); outro.save(op)
    fc = (f"[1:v]format=rgba,fade=t=out:st=2.1:d=0.4:alpha=1[h];"
          f"[2:v]format=rgba,fade=t=in:st=0:d=0.4:alpha=1,setpts=PTS+{total-OUTRO_S}/TB[o];"
          f"[0:v][h]overlay=enable='lt(t,2.5)':eof_action=pass[a];[a][o]overlay=enable='gte(t,{total-OUTRO_S})':eof_action=pass,"
          f"scale=720:1280:flags=lanczos,format=yuv420p[v]")
    final = os.path.join(OUT, "MP - All Songs - TikTok Pick Your Song.mp4")
    common = ["-i", joined, "-loop", "1", "-framerate", "30", "-t", "2.5", "-i", hp, "-loop", "1", "-framerate", "30", "-t", str(OUTRO_S + 0.1), "-i", op,
              "-filter_complex", fc, "-map", "[v]", "-map", "0:a", "-r", "30", "-c:v", "libx264", "-preset", "slow",
              "-b:v", "280k", "-maxrate", "900k", "-bufsize", "1800k", "-profile:v", "high"]
    log = os.path.join(OUT, "_2pass")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *common, "-pass", "1", "-passlogfile", log, "-an", "-f", "mp4", os.devnull], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *common, "-pass", "2", "-passlogfile", log, "-c:a", "aac", "-b:a", "128k",
                    "-movflags", "+faststart", final], check=True)
    print("DONE", final, os.path.getsize(final), flush=True)

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[2] == "preview":
        frame(2).save(os.path.join(OUT, "preview-frame.png")); frame(9).save(os.path.join(OUT, "preview-last.png"))
        b = frame(9).convert("RGBA"); b.alpha_composite(outro_card()); b.convert("RGB").save(os.path.join(OUT, "preview-outro.png"))
        card([("10 NEW SONGS", "Hanken-700.ttf", 46, BRAND_HI, 70), ("in 1 video", "Fraunces-700.ttf", 120, PAPER, 150),
              ("Drag the bar to skip to yours", "Hanken-600.ttf", 40, GOLD, 60)], 560, 960).save(os.path.join(OUT, "preview-hook.png"))
    else:
        main()
