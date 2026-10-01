"""Cuts A/B hook variants of the apple book Short from two YouTube screen recordings.

Usage: python3 render_from_recordings.py REC1.mp4 REC2.mp4 OUT_DIR FONT_DIR
REC1 = the "사과가 우리를 이용했다?" / 금기·유혹·동맹 part, REC2 = the "사과는 죄가 없습니다" ending.
Needs ffmpeg and Pillow. Writes apple_short_{A,B,C}.mp4 to OUT_DIR.
"""
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
WHITE, GOLD, RED = (255, 255, 255), (255, 210, 63), (235, 72, 72)
# visible video area inside the 1404x648 recording, without the burned-in caption band
SRC_CROP = "1152:550:126:0"
VID_Y = 670  # top of the 1080x516 video panel

# (source, start, end, headline lines, [(rel_start, rel_end, caption)])
HOOKS = {
    "A": (1, 3.9, 8.5, [[("인간이 사과를", WHITE)], [("길들인 게 ", WHITE), ("아니라고?", GOLD)]],
          [(0.0, 2.6, "우리가 사과를 길러 온 게 아니라,"), (2.6, 4.6, "사과가 우리를 이용해 왔다고요.")]),
    "B": (2, 11.4, 16.4, [[("백설공주를 쓰러뜨린 건", WHITE)], [("사과가 ", GOLD), ("아니었다", WHITE)]],
          [(0.0, 3.1, "백설공주의 사과에 독을 넣은 것도"), (3.1, 5.0, "사과가 아니라 왕비의 질투였고요.")]),
    "C": (2, 0.9, 3.6, [[("사과에 씌워진", WHITE)], [("수천 년의 ", WHITE), ("누명", GOLD)]], []),
}
BODY = [
    (1, 9.5, 21.6, [[("같은 사과, ", WHITE), ("세 얼굴", GOLD)]],
     [(0.0, 1.9, "같은 사과인데, 어떤 책에서는"), (1.9, 4.3, "먹지 말아야 할 금기였고,"),
      (4.3, 8.0, "어떤 책에서는 사람을 홀리는 유혹이었고,"), (8.0, 12.1, "또 어떤 책에서는 인간과 손잡은 동맹이었습니다.")]),
    (2, 4.4, 10.4, [[("에덴의 열매는", WHITE)], [("죄가 ", GOLD), ("없다", WHITE)]],
     [(0.0, 3.6, "에덴의 열매는 그저 나무에 매달려 있었을 뿐이에요."), (3.6, 6.0, "문제는 약속을 어긴 마음이었죠.")]),
    (2, 17.4, 22.6, [[("사과는 우리와", WHITE)], [("손을 잡았다", GOLD)]],
     [(0.0, 2.2, "그리고 폴란의 사과는"), (2.2, 5.2, "달콤함을 원한 우리와 손을 잡았을 뿐입니다.")]),
    (2, 31.6, 37.7, [[("전체 이야기는", WHITE)], [("본편에서 ", GOLD), ("▶", GOLD)]],
     [(0.0, 3.2, "달라진 건 사과가 아니라,"), (3.2, 6.1, "사과를 바라보는 우리의 마음이었습니다.")]),
]


def fonts(font_dir):
    return (ImageFont.truetype(os.path.join(font_dir, "BlackHanSans.ttf"), 104),
            ImageFont.truetype(os.path.join(font_dir, "BlackHanSans.ttf"), 120),
            ImageFont.truetype(os.path.join(font_dir, "NanumGothicExtraBold.ttf"), 58),
            ImageFont.truetype(os.path.join(font_dir, "NanumGothicExtraBold.ttf"), 38))


def headline_png(lines, font, path, label=None, label_font=None):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if label:
        lw = d.textlength(label, font=label_font)
        d.text(((W - lw) / 2, 175), label, font=label_font, fill=(255, 255, 255, 200))
    # shrink the whole headline until its widest line fits inside a 960px column
    while max(sum(d.textlength(t, font=font) for t, _ in segs) for segs in lines) > 960:
        font = font.font_variant(size=font.size - 4)
    lh = font.size * 1.22
    top = 410 - lh * len(lines) / 2
    for i, segs in enumerate(lines):
        x = (W - sum(d.textlength(t, font=font) for t, _ in segs)) / 2
        for t, c in segs:
            d.text((x, top + i * lh), t, font=font, fill=c, stroke_width=7, stroke_fill=(15, 8, 8))
            x += d.textlength(t, font=font)
    im.save(path)


def wrap(d, text, font, maxw):
    lines, cur = [], ""
    for w in text.split(" "):
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + [cur]


def caption_png(text, font, path):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lines = wrap(d, text, font, 940)
    lh = 80
    for i, l in enumerate(lines):
        w = d.textlength(l, font=font)
        d.text(((W - w) / 2, 1270 + i * lh), l, font=font, fill=WHITE, stroke_width=6, stroke_fill=(10, 6, 6))
    im.save(path)


def render_segment(src, start, end, head_png, caps, out, hook):
    dur = end - start
    inputs = ["-ss", f"{start}", "-t", f"{dur}", "-i", src, "-loop", "1", "-t", f"{dur}", "-i", head_png]
    for _, _, p in caps:
        inputs += ["-loop", "1", "-t", f"{dur}", "-i", p]
    zoom = "1+0.10*max(0\\,1-t/0.5)" if hook else "1+0.04*t/%.2f" % dur
    fg_w = f"trunc(1080*({zoom})/2)*2"
    g = (f"[0:v]crop={SRC_CROP},split[a][b];"
         f"[a]scale=-2:1920,crop=1080:1920,boxblur=30:3,eq=brightness=-0.22[bg];"
         f"[b]scale=w='{fg_w}':h='ceil(ow*550/1152/2)*2':eval=frame,crop=1080:516[fg];"
         f"[bg][fg]overlay=0:{VID_Y}[v0];")
    fade = ",fade=in:st=0:d=0.15:alpha=1" if hook else ""
    g += f"[1:v]format=rgba{fade}[h];[v0][h]overlay=0:0[v1];"
    last = "v1"
    for i, (a, b, _) in enumerate(caps):
        g += f"[v{i + 1}][{i + 2}:v]overlay=0:0:enable='between(t,{a},{b})'[v{i + 2}];"
        last = f"v{i + 2}"
    g += f"[{last}]fps=30,format=yuv420p[vout];"
    g += f"[0:a]afade=t=in:d=0.05,afade=t=out:st={dur - 0.08:.2f}:d=0.08,aresample=48000[aout]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", g, "-map", "[vout]", "-map", "[aout]",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-c:a", "aac", "-b:a", "192k",
                    "-ar", "48000", "-ac", "2", "-t", f"{dur}", out], check=True)


def main():
    rec1, rec2, out_dir, font_dir = sys.argv[1:5]
    srcs = {1: rec1, 2: rec2}
    f_head, f_hook, f_cap, f_label = fonts(font_dir)
    work = os.path.join(out_dir, "work")
    os.makedirs(work, exist_ok=True)

    def build(name, seg, hook):
        src, s, e, head, caps = seg
        hp = os.path.join(work, f"{name}_head.png")
        headline_png(head, f_hook if hook else f_head, hp, None if hook else "책 속 사과의 세 얼굴", f_label)
        cps = []
        for j, (a, b, text) in enumerate(caps):
            cp = os.path.join(work, f"{name}_cap{j}.png")
            caption_png(text, f_cap, cp)
            cps.append((a, b, cp))
        out = os.path.join(work, f"{name}.mp4")
        render_segment(srcs[src], s, e, hp, cps, out, hook)
        return out

    body = [build(f"body{i}", seg, False) for i, seg in enumerate(BODY)]
    for k, seg in HOOKS.items():
        parts = [build(f"hook{k}", seg, True)] + body
        lst = os.path.join(work, f"list{k}.txt")
        with open(lst, "w") as fh:
            fh.write("".join(f"file '{p}'\n" for p in parts))
        out = os.path.join(out_dir, f"apple_short_{k}.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                        "-movflags", "+faststart", out], check=True)
        print(k, out, flush=True)


if __name__ == "__main__":
    main()
