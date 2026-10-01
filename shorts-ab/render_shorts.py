"""Renders three A/B hook variants of the apple book-review Short.

Inputs in the working directory: book.png (thumbnail, 1920x1080), s1.png..s6.png
(slides, 1920x1080), BlackHanSans.ttf, NanumGothicExtraBold.ttf.
Needs ffmpeg, Pillow and edge-tts. Outputs apple_short_{A,B,C}.mp4.
"""
import os
import re
import subprocess

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
BG = (239, 228, 208)
INK = (52, 36, 28)
RED = (176, 32, 36)
WHITE = (255, 255, 255)
GOLD = (255, 210, 63)
VOICE, RATE = "ko-KR-SunHiNeural", "+12%"

HOOKS = {
    "A": dict(vo="사과는 수천 년 동안, 누명을 쓰고 살았습니다.",
              crop=(581, 0, 1189, 1080),
              lines=[[("사과는", WHITE)], [("수천 년 동안", WHITE)], [("누명", GOLD), ("을 썼다", WHITE)]]),
    "B": dict(vo="백설공주는 두 번이나 속고도, 왜 또 사과를 먹었을까요?",
              crop=(992, 0, 1600, 1080),
              lines=[[("두 번 속고도", WHITE)], [("왜 또", WHITE)], [("사과", GOLD), ("를 먹었을까?", WHITE)]]),
    "C": dict(vo="인간이 사과를 키운 게 아니라, 사과가 인간을 이용했다면요?",
              crop=(1312, 0, 1920, 1080),
              lines=[[("사과가", WHITE)], [("인간을", WHITE)], [("이용", GOLD), ("했다?", WHITE)]]),
}

BODY = [
    dict(img="s3.png", crop=(0, 180, 1920, 1080),
         head=[[("두 번 실패,", INK)], [("세 번째는 ", INK), ("사과", RED)]],
         vo="왕비는 조인 끈으로, 독 빗으로 두 번 실패했어요. 세 번째에 꺼낸 게 바로 사과였죠."),
    dict(img="book.png", crop=(90, 520, 700, 1060),
         head=[[("성경엔 ", INK), ("'사과'", RED), ("가 없다", INK)]],
         vo="그런데 성경엔 사과라는 단어조차 없어요. 그냥 열매였죠. 그 열매를 사과로 만든 건, 수백 년 동안 그려진 그림들이었습니다."),
    dict(img="s4.png", crop=(0, 180, 1920, 1080),
         head=[[("누가 누구를", INK)], [("길들였나", RED)]],
         vo="욕망하는 식물은 한 번 더 뒤집어요. 우리가 사과를 길들인 게 아니라, 사과가 달콤함으로 우리를 이용했다고요."),
    dict(img="s5.png", crop=(0, 230, 1920, 1080),
         head=[[("씨앗은 ", INK), ("엄마", RED), ("를", INK)], [("닮지 않는다", INK)]],
         vo="사과 씨앗을 심으면, 엄마와 전혀 다른 사과가 열려요. 그 맛은 사람 손으로만 이어집니다."),
    dict(img="s1.png", crop=(0, 250, 1920, 1080),
         head=[[("금기 · ", INK), ("유혹", RED), (" · 동맹", INK)]],
         vo="금기, 유혹, 동맹. 사과 한 알을 두고 세 권의 책이 싸웁니다. 전체 이야기는 본편에서 만나요."),
]

F_HEAD = ImageFont.truetype("BlackHanSans.ttf", 96)
F_HOOK = ImageFont.truetype("BlackHanSans.ttf", 132)
F_SUB = ImageFont.truetype("NanumGothicExtraBold.ttf", 54)
F_LABEL = ImageFont.truetype("NanumGothicExtraBold.ttf", 40)


def tts(text, out):
    subprocess.run(["edge-tts", "--voice", VOICE, f"--rate={RATE}", "--text", text,
                    "--write-media", out], check=True, capture_output=True)
    d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", out], check=True, capture_output=True, text=True)
    return float(d.stdout.strip())


def rich_lines(draw, lines, font, cy, lh, stroke=0, stroke_fill=None):
    top = cy - lh * len(lines) / 2
    for i, segs in enumerate(lines):
        total = sum(draw.textlength(t, font=font) for t, _ in segs)
        x = (W - total) / 2
        for t, c in segs:
            draw.text((x, top + i * lh), t, font=font, fill=c,
                      stroke_width=stroke, stroke_fill=stroke_fill)
            x += draw.textlength(t, font=font)


def wrap(text, font, maxw):
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    words, lines, cur = text.split(" "), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def subtitle_layer(text):
    lines = wrap(text, F_SUB, 900)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    lh = 74
    h = lh * len(lines) + 40
    y0 = 1560
    widest = max(d.textlength(l, font=F_SUB) for l in lines)
    d.rounded_rectangle(((W - widest) / 2 - 34, y0, (W + widest) / 2 + 34, y0 + h),
                        radius=22, fill=(40, 26, 20, 225))
    for i, l in enumerate(lines):
        w = d.textlength(l, font=F_SUB)
        d.text(((W - w) / 2, y0 + 16 + i * lh), l, font=F_SUB, fill=WHITE)
    return lay


def chunks(vo, dur):
    parts = [p.strip() for p in re.split(r"(?<=[,.?])\s+", vo) if p.strip()]
    weights = [len(p.replace(" ", "")) for p in parts]
    total, t, out = sum(weights), 0.0, []
    for p, w in zip(parts, weights):
        span = dur * w / total
        out.append((t, t + span, subtitle_layer(p.rstrip(".,"))))
        t += span
    return out


class Encoder:
    def __init__(self, path):
        self.p = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset",
             "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)

    def write(self, im):
        self.p.stdin.write(im.convert("RGB").tobytes())

    def close(self):
        self.p.stdin.close()
        self.p.wait()


def render_hook(key, dur, path):
    h = HOOKS[key]
    src = Image.open("book.png").convert("RGB").crop(h["crop"]).resize((W, H), Image.LANCZOS)
    # blur and darken the upper part so the hook text reads cleanly
    top = src.crop((0, 0, W, 1000)).filter(ImageFilter.GaussianBlur(16))
    src.paste(top, (0, 0))
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    for y in range(H):
        a = 170 if y < 900 else max(0, int(170 * (1 - (y - 900) / 300)))
        sd.line([(0, y), (W, y)], fill=(12, 6, 6, a))
    base = Image.alpha_composite(src.convert("RGBA"), shade)
    text = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rich_lines(ImageDraw.Draw(text), h["lines"], F_HOOK, 560, 168, stroke=8, stroke_fill=(10, 6, 6))
    subs = chunks(h["vo"], dur)
    n = round(dur * FPS)
    enc = Encoder(path)
    for f in range(n):
        t = f / FPS
        z = 1.12 - 0.12 * min(1, t / dur)  # punch-out zoom
        cw, ch = W / z, H / z
        frame = base.crop(((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2)).resize((W, H), Image.BILINEAR)
        s = 1.25 - 0.25 * min(1, f / 6)  # text pop-in
        if s > 1.001:
            # scale around the text centre (540, 560)
            left, top_ = int(540 * s - 540), int(560 * s - 560)
            tl = text.resize((int(W * s), int(H * s)), Image.BILINEAR).crop((left, top_, left + W, top_ + H))
        else:
            tl = text
        frame = Image.alpha_composite(frame, tl)
        for a, b, lay in subs:
            if a <= t < b:
                frame = Image.alpha_composite(frame, lay)
        enc.write(frame)
    enc.close()
    return n / FPS


def render_body(durs, path):
    enc = Encoder(path)
    lengths = []
    for sc, dur in zip(BODY, durs):
        img = Image.open(sc["img"]).convert("RGB").crop(sc["crop"])
        cw, ch = img.size
        tw, th = W, round(W * ch / cw)
        if th > 900:
            th, tw = 900, round(900 * cw / ch)
        base = Image.new("RGBA", (W, H), BG + (255,))
        d = ImageDraw.Draw(base)
        lw = d.textlength("책 속 사과의 세 얼굴", font=F_LABEL)
        d.text(((W - lw) / 2, 150), "책 속 사과의 세 얼굴", font=F_LABEL, fill=RED)
        rich_lines(d, sc["head"], F_HEAD, 400, 120)
        subs = chunks(sc["vo"], dur)
        n = round(dur * FPS)
        for f in range(n):
            t = f / FPS
            z = 1.0 + 0.06 * (t / dur)  # slow Ken Burns push-in
            zw, zh = cw / z, ch / z
            pic = img.crop(((cw - zw) / 2, (ch - zh) / 2, (cw + zw) / 2, (ch + zh) / 2)).resize((tw, th), Image.BILINEAR)
            frame = base.copy()
            frame.paste(pic, ((W - tw) // 2, 1040 - th // 2))
            for a, b, lay in subs:
                if a <= t < b:
                    frame = Image.alpha_composite(frame, lay)
            enc.write(frame)
        lengths.append(n / FPS)
    enc.close()
    return lengths


def pad_audio(src, length, out):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", "apad", "-t", f"{length:.4f}",
                    "-ar", "44100", "-ac", "2", out], check=True)


def main():
    body_mp3 = []
    for i, sc in enumerate(BODY):
        d = tts(sc["vo"], f"body{i}.mp3")
        body_mp3.append((f"body{i}.mp3", d + 0.35))
    body_len = render_body([d for _, d in body_mp3], "body.mp4")
    for i, ((mp3, _), L) in enumerate(zip(body_mp3, body_len)):
        pad_audio(mp3, L, f"body{i}.wav")
    for k, h in HOOKS.items():
        d = tts(h["vo"], f"hook{k}.mp3") + 0.25
        L = render_hook(k, d, f"hook{k}.mp4")
        pad_audio(f"hook{k}.mp3", L, f"hook{k}.wav")
        with open(f"v{k}.txt", "w") as fh:
            fh.write(f"file 'hook{k}.mp4'\nfile 'body.mp4'\n")
        with open(f"a{k}.txt", "w") as fh:
            fh.write(f"file 'hook{k}.wav'\n" + "".join(f"file 'body{i}.wav'\n" for i in range(len(BODY))))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"v{k}.txt",
                        "-f", "concat", "-safe", "0", "-i", f"a{k}.txt", "-map", "0:v", "-map", "1:a",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
                        f"apple_short_{k}.mp4"], check=True)
        print(k, "done", os.path.getsize(f"apple_short_{k}.mp4"), flush=True)


if __name__ == "__main__":
    main()
