"""Builds the 16:9 main video "똑똑해지는 약의 세 얼굴" (10:00) from the Drive images.

Usage: python3 build_video.py ASSET_DIR WORK_DIR OUT.mp4
Needs ffmpeg, Pillow and fonts-nanum. The video is silent: the narration is recorded
separately and laid over the timeline (see cue_sheet.md for what is said when).

ASSET_DIR file names (missing ones are drawn as labelled placeholders):
  sit_record, sit_three, sit_dep_awake, sit_awake_loss, sit_loss_dep, sit_left   diagrams
  lastdance (blue pill), tm_morning, tm_fakefriend, tm_skywall, love_lastdance, love_record
  newspaper, hospital                                                         photos
"""
import math
import os
import random
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 30
BG = (243, 235, 221)
INK = (52, 36, 28)
BLUE, PURPLE, ORANGE = (58, 104, 168), (122, 74, 140), (200, 118, 40)
CARD = (252, 247, 238)
FD = "/usr/share/fonts/truetype/nanum/"


def font(size, bold=True):
    return ImageFont.truetype(FD + ("NanumGothicBold.ttf" if bold else "NanumGothic.ttf"), size)


def serif(size):
    return ImageFont.truetype(FD + "NanumMyeongjoBold.ttf", size)


def center(d, xy, text, f, fill=INK, spacing=10):
    d.multiline_text(xy, text, font=f, fill=fill, anchor="mm", align="center", spacing=spacing)


def pill(d, cx, cy, text, f=None, w=None):
    f = f or font(40)
    tw = w or d.textlength(text, font=f) + 120
    d.rounded_rectangle((cx - tw / 2, cy - 48, cx + tw / 2, cy + 48), 26, fill=INK)
    d.text((cx, cy), text, font=f, fill="white", anchor="mm")


def canvas():
    im = Image.new("RGB", (W, H), BG)
    return im, ImageDraw.Draw(im)


def title(d, text):
    d.text((W / 2, 80), text, font=font(58), fill=INK, anchor="mm")


def rot_paste(im, layer, center_xy, angle):
    r = layer.rotate(angle, expand=True, resample=Image.BICUBIC)
    im.paste(r, (int(center_xy[0] - r.width / 2), int(center_xy[1] - r.height / 2)), r)


def wobble_text(d, x, y, text, f, rnd):
    for ch in text:
        d.text((x, y + rnd.randint(-7, 7)), ch, font=f, fill=(70, 60, 55))
        x += d.textlength(ch, font=f) + rnd.randint(0, 3)


# ---------------------------------------------------------------- drawn scenes
def draw_mouse(d, cx, cy, s=1.0):
    k = lambda v: v * s
    d.ellipse((cx - k(110), cy - k(60), cx + k(80), cy + k(60)), fill=(250, 250, 250), outline=(120, 110, 105), width=4)
    d.ellipse((cx + k(40), cy - k(50), cx + k(130), cy + k(30)), fill=(250, 250, 250), outline=(120, 110, 105), width=4)
    d.ellipse((cx + k(55), cy - k(72), cx + k(95), cy - k(32)), fill=(240, 170, 175), outline=(120, 110, 105), width=3)
    d.ellipse((cx + k(108), cy - k(18), cx + k(128), cy + k(2)), fill=(230, 120, 130))
    d.ellipse((cx + k(95), cy - k(25), cx + k(105), cy - k(15)), fill=INK)
    pts = [(cx - k(105), cy + k(15)), (cx - k(170), cy + k(40)), (cx - k(210), cy), (cx - k(250), cy + k(30))]
    d.line(pts, fill=(235, 150, 160), width=int(k(7)), joint="curve")
    for dx in (-60, 20):
        d.ellipse((cx + k(dx), cy + k(45), cx + k(dx + 40), cy + k(70)), fill=(240, 170, 175))


def scene_maze():
    im, d = canvas()
    title(d, "미로 속 흰 쥐 앨저넌")
    x0, y0, x1, y1 = 560, 190, 1360, 900
    d.rectangle((x0, y0, x1, y1), outline=INK, width=8)
    step, gaps = 70, 0
    for i in range(1, 6):
        a, b, c, e = x0 + i * step, y0 + i * step, x1 - i * step, y1 - i * step
        d.line([(a, e), (a, b), (c, b), (c, e)], fill=INK, width=8)
        d.line([(a, e), (c - 150, e)], fill=INK, width=8)
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    d.ellipse((cx - 40, cy - 40, cx + 40, cy + 40), fill=(244, 214, 120), outline=INK, width=4)
    d.text((cx, cy), "치즈", font=font(24), fill=INK, anchor="mm")
    draw_mouse(d, 930, 845, 0.55)
    # Charlie watching from the side
    px, py = 1560, 560
    d.ellipse((px - 55, py - 220, px + 55, py - 110), fill=(236, 200, 170), outline=INK, width=5)
    d.rounded_rectangle((px - 75, py - 105, px + 75, py + 120), 40, fill=(88, 120, 160), outline=INK, width=5)
    d.line([(px - 40, py + 120), (px - 40, py + 270)], fill=INK, width=14)
    d.line([(px + 40, py + 120), (px + 40, py + 270)], fill=INK, width=14)
    d.line([(px - 75, py - 60), (px - 160, py + 20)], fill=INK, width=14)
    d.text((px, py + 330), "찰리", font=font(44), fill=BLUE, anchor="mm")
    d.text((620, 960), "앨저넌", font=font(44), fill=ORANGE, anchor="mm")
    return im


def paper(w, h, lines, f, header, hf, wobbly, rnd):
    p = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(p)
    d.rectangle((0, 0, w - 1, h - 1), fill=(255, 253, 248), outline=(150, 140, 130), width=4)
    d.text((40, 36), header, font=hf, fill=(150, 90, 40))
    y = 130
    for ln in lines:
        if wobbly:
            wobble_text(d, 40, y, ln, f, rnd)
        else:
            d.text((40, y), ln, font=f, fill=(40, 35, 32))
        y += f.size + 26
    return p


def scene_report():
    rnd = random.Random(3)
    im, d = canvas()
    title(d, "찰리의 경과보고서")
    left = paper(620, 560, ["나는 차리 곤.", "오느른 병원에서", "시험을 바닷다.", "대단이 조은 날."],
                 font(40, False), "경과 보고 1", font(34), True, rnd)
    right = paper(700, 600, ["지능의 급격한 상승은", "정서적 성숙의 속도를", "결코 따라오지 못한다.", "이 곡선은 나 자신의", "퇴행으로 이어질 것이다."],
                  serif(36), "경과 보고 15 — 가설과 검증", font(30), False, rnd)
    rot_paste(im, left, (450, 560), -5)
    rot_paste(im, right, (1430, 560), 2)
    d.polygon([(800, 520), (940, 520), (940, 480), (1030, 560), (940, 640), (940, 600), (800, 600)], fill=INK)
    d.text((450, 940), "삐뚤빼뚤, 틀린 글씨", font=font(40), fill=BLUE, anchor="mm")
    d.text((1430, 940), "반듯한 논문 한 장", font=font(40), fill=ORANGE, anchor="mm")
    return im


def capsule(im, cx, cy, c1, c2, angle=35):
    L = Image.new("RGBA", (460, 220), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    d.rounded_rectangle((10, 10, 450, 210), 100, fill=c1, outline=INK, width=6)
    d.rounded_rectangle((230, 10, 450, 210), 100, fill=c2, outline=INK, width=6)
    d.rectangle((230, 10, 340, 210), fill=c2)
    d.line([(230, 14), (230, 206)], fill=INK, width=6)
    rot_paste(im, L, (cx, cy), angle)


def scene_pills():
    im, d = canvas()
    title(d, "두 개의 알약")
    capsule(im, 560, 400, (88, 170, 100), (140, 205, 140))
    capsule(im, 1360, 400, (50, 100, 200), (110, 160, 235))
    d.text((560, 640), "초록 · 몸", font=font(56), fill=(60, 130, 70), anchor="mm")
    d.text((1360, 640), "파랑 · 머리", font=font(56), fill=BLUE, anchor="mm")
    d.polygon([(1330, 720), (1390, 720), (1390, 790), (1430, 790), (1360, 860), (1290, 790), (1330, 790)], fill=INK)
    pill(d, 1360, 940, "끊으면?", font(60), 420)
    return im


def scene_pairs():
    im, d = canvas()
    title(d, "둘 다 관찰당하던 사람")
    for x, col, head, sub, body in [(80, BLUE, "트루먼의 친구", "『트루먼 쇼』", "= 배우"),
                                    (1020, ORANGE, "찰리의 동료", "『앨저넌에게 꽃을』", "= 사실은\n놀리고 있었다")]:
        d.rounded_rectangle((x, 190, x + 820, 700), 22, fill=CARD, outline=col, width=6)
        d.text((x + 410, 280), head, font=font(62), fill=col, anchor="mm")
        d.text((x + 410, 350), sub, font=font(34, False), fill=(130, 120, 110), anchor="mm")
        center(d, (x + 410, 540), body, font(66))
    d.text((W / 2, 445), "↔", font=font(120), fill=INK, anchor="mm")
    pill(d, W / 2, 880, "진실을 안 순간, 편안했던 세계가 무너진다", font(46))
    return im


def scene_grave():
    im, d = canvas()
    d.text((W / 2, 130), "앨저넌의 무덤에 꽃을", font=font(64), fill=INK, anchor="mm")
    d.rectangle((0, 760, W, H), fill=(150, 170, 110))
    d.ellipse((560, 700, 1360, 900), fill=(125, 100, 75))
    d.rounded_rectangle((880, 560, 1040, 770), 70, fill=(200, 196, 188), outline=INK, width=5)
    d.rectangle((880, 700, 1040, 770), fill=(200, 196, 188), outline=INK, width=5)
    d.text((960, 650), "앨저넌", font=font(30), fill=INK, anchor="mm")
    d.line([(1180, 790), (1190, 560)], fill=(60, 130, 70), width=10)
    d.ellipse((1120, 640, 1190, 690), fill=(60, 130, 70))
    for a in range(0, 360, 60):
        x, y = 1190 + 55 * math.cos(math.radians(a)), 520 + 55 * math.sin(math.radians(a))
        d.ellipse((x - 38, y - 38, x + 38, y + 38), fill=(235, 110, 140), outline=INK, width=3)
    d.ellipse((1160, 490, 1220, 550), fill=(250, 214, 90), outline=INK, width=3)
    return im


def scene_end():
    im, d = canvas()
    center(d, (W / 2, 330), "여러분이라면\n그 약, 드시겠어요?", font(110), INK, 24)
    pill(d, W / 2, 700, "댓글로 들려주세요", font(56), 700)
    return im


def placeholder(label):
    im, d = canvas()
    d.rounded_rectangle((120, 120, W - 120, H - 120), 30, outline=(150, 140, 130), width=6)
    center(d, (W / 2, H / 2), f"{label}\n(이미지 교체 예정)", font(70), (150, 140, 130))
    return im


# ---------------------------------------------------------------- scene table
# (start, end, source, zoom) ; source = file in ASSET_DIR, or a drawn scene "draw:<name>"
SCENES = [
    (0, 22, "newspaper", "in"), (22, 40, "sit_three", "in"),
    (40, 75, "draw:maze", "in"), (75, 110, "draw:report", "in"), (110, 120, "sit_three", "out"),
    (120, 150, "lastdance", "in"), (150, 200, "draw:pills", "in"), (200, 220, "lastdance", "out"),
    (220, 250, "tm_morning", "in"), (250, 280, "tm_fakefriend", "in"), (280, 325, "draw:pairs", "in"),
    (325, 340, "tm_skywall", "in"),
    (340, 370, "hospital", "in"), (370, 400, "love_lastdance", "in"), (400, 425, "love_record", "in"),
    (425, 460, "sit_record", "in"),
    (460, 480, "sit_three", "in"), (480, 500, "sit_dep_awake", "in"), (500, 520, "sit_awake_loss", "in"),
    (520, 540, "sit_loss_dep", "in"),
    (540, 565, "draw:grave", "in"), (565, 580, "sit_left", "in"), (580, 588, "newspaper", "out"),
    (588, 600, "draw:end", "out"),
]
DRAWN = {"maze": scene_maze, "report": scene_report, "pills": scene_pills, "pairs": scene_pairs,
         "grave": scene_grave, "end": scene_end}
CONTAIN = {"newspaper"}
CROPS = {"tm_morning": (0, 0, 1.0, 0.94)}  # fractions x0, y0, x1, y1: trims the generator watermark

CHAPTERS = [(0, "약 한 알로 똑똑해질 수 있다면"), (40, "앨저넌에게 꽃을, 찰리의 곡선"),
            (120, "첫 번째 얼굴 · 의존"), (220, "두 번째 얼굴 · 각성"), (340, "세 번째 얼굴 · 상실"),
            (460, "세 영화, 한자리에"), (540, "앨저넌의 무덤에 꽃을")]
SUBS = {120: "『본 레거시』", 220: "『트루먼 쇼』", 340: "『사랑의 기적』"}
KEYWORDS = [(208, 218, "의존", "빌린 지능은 언제든 돌려줘야 할 수 있다"),
            (328, 338, "각성", "아는 것은 행복일까, 대가일까"),
            (448, 458, "상실", "잃어 가면서도 기록하는 것, 그게 사람이다")]


def load_scene(asset_dir, name):
    if name.startswith("draw:"):
        return DRAWN[name[5:]]()
    path = os.path.join(asset_dir, name + ".png")
    if not os.path.exists(path):
        path = os.path.join(asset_dir, name + ".jpg")
    if not os.path.exists(path):
        print("missing asset, drawing placeholder:", name)
        return placeholder(name)
    im = Image.open(path).convert("RGB")
    if name in CONTAIN:  # wide screenshot: keep it whole on the paper-coloured background
        s = min((W - 240) / im.width, (H - 240) / im.height)
        im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        out, d = canvas()
        x, y = (W - im.width) // 2, (H - im.height) // 2
        d.rectangle((x + 10, y + 12, x + im.width + 10, y + im.height + 12), fill=(215, 205, 190))
        out.paste(im, (x, y))
        d.rectangle((x, y, x + im.width, y + im.height), outline=(190, 180, 165), width=2)
        return out
    if name in CROPS:
        x0, y0, x1, y1 = CROPS[name]
        im = im.crop((int(im.width * x0), int(im.height * y0), int(im.width * x1), int(im.height * y1)))
    # cover-fit to 16:9
    r = max(W / im.width, H / im.height)
    im = im.resize((math.ceil(im.width * r), math.ceil(im.height * r)), Image.LANCZOS)
    l, t = (im.width - W) // 2, (im.height - H) // 2
    return im.crop((l, t, l + W, t + H))


def overlay_png(kind, a, b, path):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if kind == "chapter":
        main, sub = a
        d.rounded_rectangle((70, 60, 70 + max(d.textlength(main, font=font(54)), d.textlength(sub, font=font(34, False))) + 90,
                             60 + (150 if sub else 110)), 20, fill=(30, 22, 18, 215))
        d.text((115, 115), main, font=font(54), fill="white", anchor="lm")
        if sub:
            d.text((115, 172), sub, font=font(34, False), fill=(235, 215, 170), anchor="lm")
    else:
        word, line = a, b
        d.rounded_rectangle((260, 900, W - 260, 1020), 30, fill=(30, 22, 18, 225))
        d.text((330, 960), f"키워드 · {word}", font=font(44), fill=(255, 210, 120), anchor="lm")
        d.text((620, 960), line, font=font(44, False), fill="white", anchor="lm")
    im.save(path)


def run(cmd):
    subprocess.run(cmd, check=True, capture_output=True)


def main(asset_dir, work, out):
    os.makedirs(work, exist_ok=True)
    clips = []
    for i, (s, e, src, zoom) in enumerate(SCENES):
        dur = e - s
        png, mp4 = os.path.join(work, f"s{i:02d}.png"), os.path.join(work, f"s{i:02d}.mp4")
        load_scene(asset_dir, src).save(png)
        z = f"1+0.05*t/{dur}" if zoom == "in" else f"1.05-0.05*t/{dur}"
        vf = (f"scale=w='trunc(({W}*({z}))/2)*2':h=-2:eval=frame,crop={W}:{H},"
              f"fade=in:st=0:d=0.4,fade=out:st={dur - 0.4}:d=0.4,format=yuv420p")
        run(["ffmpeg", "-y", "-loop", "1", "-framerate", str(FPS), "-t", str(dur), "-i", png,
             "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-r", str(FPS), mp4])
        clips.append(mp4)
        print("scene", i, src, f"{s}-{e}s")
    lst = os.path.join(work, "list.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{os.path.abspath(c)}'\n" for c in clips)
    base = os.path.join(work, "base.mp4")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", base])

    overlays = []  # (png, start, end)
    for i, (t, name) in enumerate(CHAPTERS):
        p = os.path.join(work, f"ov_c{i}.png")
        overlay_png("chapter", (name, SUBS.get(t, "")), None, p)
        overlays.append((p, t + 1.0, t + 6.0))
    for i, (a, b, word, line) in enumerate(KEYWORDS):
        p = os.path.join(work, f"ov_k{i}.png")
        overlay_png("keyword", word, line, p)
        overlays.append((p, a, b))
    cmd = ["ffmpeg", "-y", "-i", base]
    for p, _, _ in overlays:
        cmd += ["-loop", "1", "-framerate", str(FPS), "-i", p]
    chain, last = [], "[0:v]"
    for k, (_, a, b) in enumerate(overlays, start=1):
        chain.append(f"[{k}:v]format=rgba,fade=in:st={a}:d=0.4:alpha=1,fade=out:st={b - 0.4}:d=0.4:alpha=1[o{k}]")
        chain.append(f"{last}[o{k}]overlay=enable='between(t,{a},{b})':shortest=0[v{k}]")
        last = f"[v{k}]"
    cmd += ["-filter_complex", ";".join(chain), "-map", last, "-t", "600", "-c:v", "libx264",
            "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
    run(cmd)
    print("wrote", out)


if __name__ == "__main__":
    main(*sys.argv[1:4])
