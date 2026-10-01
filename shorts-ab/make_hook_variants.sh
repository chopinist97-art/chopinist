#!/usr/bin/env bash
# Builds hook variants of a 1080x1920 Short: blurs the original first caption
# band (y 120-480) for the first 3.45s and draws a new hook in its place.
# Usage: ./make_hook_variants.sh base.mp4   (needs ffmpeg, python3 + Pillow)
set -euo pipefail
BASE=${1:-base.mp4}
[ -f Jua.ttf ] || curl -sSfL -o Jua.ttf https://raw.githubusercontent.com/google/fonts/main/ofl/jua/Jua-Regular.ttf
python3 - <<'PY'
from PIL import Image, ImageDraw, ImageFont
V = {"A_plane": ["백설공주는 왜 씨앗을 가지고", "비행기를 탔을까요?"],
     "B_seed": ["사과 씨앗을 심으면", "엄마 사과와 전혀 다른 사과가", "열린다는 거 아세요?"],
     "C_threebooks": ["사과 하나를 두고", "세 권의 책이 싸운다면?"]}
f = ImageFont.truetype("Jua.ttf", 74)
for k, lines in V.items():
    im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    lh = 96; top = 300 - lh * len(lines) / 2
    for i, l in enumerate(lines):
        w = d.textlength(l, font=f)
        d.text(((1080 - w) / 2, top + i * lh), l, font=f, fill=(255, 255, 255, 255),
               stroke_width=6, stroke_fill=(20, 16, 16, 255))
    im.save(f"hook_{k}.png")
m = Image.new("L", (1080, 360), 255); px = m.load()
for y in range(360):
    a = min(1, y / 50, (359 - y) / 50)
    for x in range(1080): px[x, y] = int(255 * a)
m.save("mask.png")
PY
for k in A_plane B_seed C_threebooks; do
  ffmpeg -v error -y -i "$BASE" -loop 1 -i hook_$k.png -loop 1 -i mask.png -filter_complex \
   "[0:v]split[v][c];[c]crop=1080:360:0:120,boxblur=28:3,eq=brightness=-0.10,format=rgba[b];[2:v]format=gray,scale=1080:360[m];[b][m]alphamerge[bm];[v][bm]overlay=0:120:enable='lt(t,3.45)'[v1];[v1][1:v]overlay=0:0:enable='lt(t,3.45)':shortest=1,format=yuv420p[out]" \
   -map "[out]" -map 0:a -c:v libx264 -preset veryfast -crf 18 -c:a copy -movflags +faststart \
   -t "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$BASE")" apple_shorts_$k.mp4
done
