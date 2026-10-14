# MP video builder

Makes the social videos on `/videos/` from the 45-second clips in `audio/`.
Needs Python 3 with Pillow, and ffmpeg.

| Script | Makes |
|---|---|
| `make.py` | Tall 9:16 videos (TikTok, Reels, Shorts) → `out/` |
| `formats.py` | Feed 4:5 and Wide 16:9 videos → `out_formats/` |
| `cards.py` / `cards2.py` | Opening tracklist and closing cards for the all-songs videos |

Every video: song title, moving sound wave, progress bar, loudness set to -14 LUFS
(what TikTok, Instagram and YouTube expect), H.264 + AAC, 30 fps.
Cloudflare will not publish a file over 25 MB, so the 7:30 all-songs videos are
encoded at about 285 kbps to land near 23 MB.

**Next step: lyrics.** When the lyrics arrive (copy them from each song in Suno),
add them on screen, timed to the clip, in all three shapes, and rebuild `/videos/`.

Fonts: Fraunces and Hanken Grotesk, SIL Open Font License (see `fonts/`).
