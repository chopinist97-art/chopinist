"""Writes subtitles.srt from the narration script, spread over each scene window by character count.
Timings are estimates: re-time against the recorded voice before publishing."""
import re
import sys

# (start_s, end_s, text) windows follow the SCENES table in build_video.py
SEGMENTS = [
    (0, 12, "“공부 잘하는 약은 없습니다”… 정부, ADHD치료제 오남용 주의"),
    (12, 40, "약 한 알로 머리가 좋아진다면, 여러분은 드시겠어요? 60여 년 전, 이 질문에 답한 소설이 있습니다. 그리고 그 답을 영화 세 편이 나눠서 이어 말합니다."),
    (40, 110, "서른두 살 찰리는 빵집에서 일합니다. 지능지수는 68. 그는 실험용 쥐 앨저넌과 함께 지능을 높이는 수술을 받습니다. 소설은 찰리가 직접 쓴 경과보고서로 이어지는데요, 처음엔 맞춤법이 엉망이던 보고서가 점점 정확해지고, 어느새 교수들보다 어려운 문장을 씁니다."),
    (110, 120, "그런데 이 곡선은 끝까지 올라가지 않습니다. 오늘은 그 곡선의 세 구간을, 영화 세 편으로 하나씩 들여다보겠습니다."),
    (120, 200, "애런 크로스는 비밀 요원입니다. 그런데 그의 능력은 약에서 나와요. 몸을 강하게 하는 초록 알약, 그리고 머리를 좋게 하는 파란 알약. 원래 그는 군대 지능 기준에도 못 미치던 사람이었습니다."),
    (200, 220, "약이 떨어져 가자 애런은 총보다 이것을 더 두려워합니다. 예전으로 돌아가는 것. 찰리도 같았습니다. 똑똑해진 찰리가 가장 무서워한 건 실패가 아니라, 원래의 자신이었어요."),
    (220, 280, "트루먼은 평범한 보험회사 직원입니다. 단 하나, 그의 인생 전체가 생중계되는 방송이라는 걸 본인만 모르죠. 가장 친한 친구조차 대본을 읽는 배우였습니다."),
    (280, 340, "찰리가 똑똑해져서 처음 알게 된 것도 이거였어요. 빵집 동료들이 자기를 좋아해서 웃은 게 아니라, 자기를 보고 웃었다는 것. 둘 다 관찰당하는 사람이었고, 진실을 안 순간 편안했던 세계가 무너집니다."),
    (340, 370, "이 영화는 실화입니다. 신경학자 올리버 색스가 기록한 환자들이죠. 수십 년 동안 몸이 굳은 채 지내던 사람들이 새 약을 맞고 깨어납니다. 레너드는 다시 걷고, 사랑에 빠집니다."),
    (370, 425, "하지만 약효는 오래가지 않았습니다. 몸이 다시 굳어 가는 걸 느낀 레너드는 의사에게 부탁해요. 나를 찍어 달라고, 기록해 두라고."),
    (425, 460, "찰리도 똑같았습니다. 자기가 퇴행할 거라는 걸 스스로 밝혀내고, 그 과정을 끝까지 보고서로 남깁니다."),
    (480, 500, "의존 대 각성. 약으로 얻은 눈으로 본 진실도 진실일까?"),
    (500, 520, "각성 대 상실. 알게 된 것을 잃는 것과, 처음부터 모르는 것 중 무엇이 더 아플까?"),
    (520, 540, "상실 대 의존. 언젠가 잃을 줄 알았다면, 그래도 그 약을 먹었을까?"),
    (540, 580, "지능을 모두 잃은 찰리는 이전보다 오히려 따뜻한 사람으로 돌아옵니다. 그리고 마지막에 이런 부탁을 남기죠. 뒷마당 앨저넌의 무덤에 꽃을 놓아 달라고. 세 영화 속 누구도, 찰리도, 지능을 지키지 못했습니다. 하지만 마음은 끝까지 남았습니다."),
    (588, 600, "여러분이라면 그 약, 드시겠어요? 댓글로 들려주세요."),
]


def chunks(text, limit=40):
    out = []
    for s in re.split(r"(?<=[.?!])\s+", text.strip()):
        if len(s) <= limit:
            out.append(s)
            continue
        cur = ""
        for part in re.split(r"(?<=[,])\s+|\s+", s):
            if cur and len(cur) + len(part) + 1 > limit:
                out.append(cur)
                cur = part
            else:
                cur = f"{cur} {part}".strip()
        if cur:
            out.append(cur)
    merged = []
    for c in out:  # no cue of a stray word or two: glue it onto the previous line
        if merged and len(c) < 8 and len(merged[-1]) + len(c) < limit + 12:
            merged[-1] += " " + c
        else:
            merged.append(c)
    return merged


def ts(t):
    ms = round(t * 1000)
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def main(path):
    n, lines = 0, []
    for a, b, text in SEGMENTS:
        cs = chunks(text)
        total = sum(len(c) for c in cs)
        t = a
        for c in cs:
            d = (b - a - 0.4) * len(c) / total
            n += 1
            lines.append(f"{n}\n{ts(t)} --> {ts(t + d)}\n{c}\n")
            t += d + 0.4 / len(cs)
    open(path, "w", encoding="utf-8").write("\n".join(lines))
    print(n, "cues ->", path)


if __name__ == "__main__":
    main(sys.argv[1])
