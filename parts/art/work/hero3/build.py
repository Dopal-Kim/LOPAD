#!/usr/bin/env python3
"""주인공 hero3 도트 초안 — 혼불이 새는 재 껍데기 망령 (52라운드 Q6, 임시 · 검수 전)

근거: 52라운드 Q4(외양 재정의)·Q6(C 형체 유지, 사슬 없음, 얼굴은 어둡게 + 분노한 눈빛만, 일기장 허리, 어깨 혼불 작게 상시 깜빡임).
개념 참고: parts/art/work/gemini/concept_char/hero3_b.jpg (게임 도트에 생성 이미지 픽셀은 쓰지 않음 — 전부 여기서 찍음).

규격: v2 주인공과 같음 — 32×48, 피벗 (16,46) = 발, 팔레트 = lopad 무채 16 + 1층 램프(16~27) + v2 재질 블록(SL/WD/PL),
      kit.Rig 부위 셰이딩(빛 좌상단) + 안쪽 셀아웃(SL0). 범위: 정면 대기 1 + 정면 걷기 4 (초안).
출력(미리보기만, assets/** 는 건드리지 않음):
  preview_hero3_x4.png      — 대기 1 + 걷기 4, 4배 확대 (+ 혼불 깜빡임 확인용 확대 띠)
  preview_hero3_dark_x1.png — 외곽 거리 v2 목업 바닥(albedo) 위 1배, 조명 합성 (+ 같은 그림 3배)
사용: python3 parts/art/work/hero3/build.py
"""
import os, sys

OUTDIR = os.path.dirname(os.path.abspath(__file__))   # kit 의 HERE 와 겹치지 않게 다른 이름
sys.path.insert(0, os.path.join(OUTDIR, "..", "v2_outer"))
from kit import *  # noqa: E402,F401  (G, A, SL, WD, PL, Rig, Part, Canvas, upscale, light_scene, CLEAR, colors_of, isolated)
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

FW, FH = 32, 48
PIV = (16, 46)

# 재질 램프 (0 가장 어둠 → 4 밝음) — Part.base 가 본색 인덱스
ASH = [SL[0], G[2], G[4], G[5], G[7]]        # 재·탄 흙 몸 (바닥 청회 SL3~4 와 색상으로 분리되는 무채)
FACE = [SL[0], G[1], G[2], G[3], G[5]]        # 민머리 재 껍데기 — 얼굴은 그늘(G01~G02), 정수리만 빛
IRON = [SL[0], SL[2], SL[4], SL[6], SL[7]]    # 갑옷 파편(차가운 쇠)
LEATHER = [WD[0], WD[1], WD[2], WD[3], WD[4]]  # 허리 가죽 조각·끈
BAND = [PL[0], PL[1], PL[2], PL[3], PL[4]]    # 때 묻은 붕대 (v2 보다 한 단 어둡게 — 얼굴이 아닌 손·정강이라)
DIARY = [A[17], A[19], A[21], A[22], A[23]]   # 일기장 (바이블 4절: 층 램프 21 본색)

# 혼불(자체 발광 — kit.EMISSIVE 의 23~27 은 조명 뒤 원색 복원)
F_DEEP, F_BASE, F_LIGHT, F_GLOW, F_HOT = A[19], A[21], A[23], A[25], A[26]
EYE, EYE_HI = A[23], A[25]


def P(name, ramp, base, **kw):
    return Part(name, ramp, base, **kw)


def pose(**kw):
    p = dict(bob=0, fl=(0, 0), fr=(0, 0), hl=(0, 0), hr=(0, 0), flame=0, eye=1)
    p.update(kw)
    return p


# 어깨 혼불 3모양 (매 프레임 교체) — 왼어깨(화면 오른쪽) 균열 위 2~3px
FLAMES = [
    [(22, 15, F_BASE), (23, 15, F_GLOW), (23, 14, F_LIGHT), (23, 13, F_BASE)],
    [(22, 15, F_LIGHT), (23, 15, F_GLOW), (22, 14, F_BASE)],
    [(22, 15, F_BASE), (23, 15, F_GLOW), (24, 14, F_LIGHT), (24, 13, F_DEEP)],
]


def draw_down(p):
    R = Rig(FW, FH)
    b = p["bob"]
    # ---- 다리 (마른 다리, 맨발) — 화면 왼쪽 = 오른다리(정강이받이), 화면 오른쪽 = 왼다리(붕대)
    for side, (dx, lift) in (("r", p["fl"]), ("l", p["fr"])):
        x0 = (12 if side == "r" else 17) + dx
        fy = 46 - lift
        R.rect(P("leg" + side, ASH, 2, group="leg" + side, edge=True), x0, 35 + b // 2, x0 + 2, fy - 1)
        R.rect(P("foot" + side, ASH, 1, group="foot" + side), x0 - 1, fy - 1, x0 + 3, fy)
        if side == "r":
            R.rect(P("greave", IRON, 2, group="greave"), x0, 38 - lift // 2, x0 + 2, 42 - lift)
        else:
            R.rect(P("shinband", BAND, 2, group="shinband"), x0, 39 - lift // 2, x0 + 2, 42 - lift)
    # ---- 허리 가죽 조각 (들쭉날쭉한 단)
    R.poly(P("loin", LEATHER, 1, group="loin", sh=1),
           [(12, 28 + b), (20, 28 + b), (20, 32 + b), (18, 34 + b), (17, 32 + b), (15, 35 + b), (14, 32 + b), (12, 33 + b)])
    # ---- 몸통 (어깨 16폭 → 허리 10폭), 등이 굽어 어깨가 높고 머리가 앞으로
    R.poly(P("torso", ASH, 2, group="body", sh=2), [(8, 17 + b), (24, 17 + b), (22, 24 + b), (21, 29 + b), (11, 29 + b), (10, 24 + b)])
    # 흉갑 조각 (화면 오른쪽 가슴)
    R.poly(P("plate", IRON, 2, group="plate", edge=True), [(17, 19 + b), (22, 18 + b), (22, 22 + b), (20, 25 + b), (17, 24 + b)])
    # 왼어깨(화면 오른쪽) 견갑 조각
    R.poly(P("pauldron", IRON, 3, group="pauldron", edge=True), [(20, 16 + b), (24, 16 + b), (26, 18 + b), (25, 20 + b), (21, 19 + b)])
    # 끈 (혼불이 붙든 갑옷을 묶은 끊어진 가죽끈) — 오른어깨 → 흉갑
    R.limb(P("strap", LEATHER, 2, group="strap"), [(10, 18 + b), (17, 22 + b)], 1)
    # ---- 팔 (가는 팔, 늘어뜨림), 손 붕대, 왼팔뚝 완갑
    hand_r = (8 + p["hl"][0], 33 + b + p["hl"][1])     # 화면 왼쪽 = 오른손
    hand_l = (24 + p["hr"][0], 33 + b + p["hr"][1])    # 화면 오른쪽 = 왼손
    R.limb(P("armr", ASH, 2, group="armr", edge=True), [(9, 19 + b), (hand_r[0], hand_r[1] - 2)], 3)
    R.limb(P("arml", ASH, 2, group="arml", edge=True), [(23, 19 + b), (hand_l[0], hand_l[1] - 2)], 3)
    R.rect(P("vamb", IRON, 2, group="vamb"), hand_l[0] - 1, hand_l[1] - 6, hand_l[0] + 1, hand_l[1] - 3)
    R.rect(P("handr", BAND, 2, group="handr"), hand_r[0] - 1, hand_r[1] - 1, hand_r[0] + 1, hand_r[1] + 1)
    R.rect(P("handl", BAND, 2, group="handl"), hand_l[0] - 1, hand_l[1] - 1, hand_l[0] + 1, hand_l[1] + 1)
    # ---- 일기장: 오른 허리(화면 왼쪽)에 끈으로
    R.rect(P("diary", DIARY, 1, group="diary"), 10, 30 + b, 12, 32 + b)
    # ---- 목 · 머리 (민머리, 앞으로 숙임 → 머리가 어깨선에 걸침)
    R.rect(P("neck", ASH, 1, group="neck"), 14, 15 + b, 18, 17 + b)
    R.ellipse(P("head", FACE, 3, group="head", sh=1), 12, 5 + b, 20, 15 + b)
    R.rect(P("jaw", FACE, 2, group="head", sh=1), 14, 13 + b, 18, 16 + b)      # 좁은 턱(두개골 꼴)
    for x, y in ((12, 13), (12, 14), (20, 13), (20, 14), (13, 15), (19, 15)):
        R.erase.add((x, y + b))
    # ---- 화살 (오른어깨 뒤에서 위·왼쪽으로 솟음) — 실루엣 돌기
    shaft = [(9, 16 + b), (8, 15 + b), (7, 14 + b), (6, 13 + b), (5, 12 + b)]
    R.pixels(P("arrow", LEATHER, 3, group="arrow", flat=True), shaft)
    # ---- 덧칠 ----
    # 머리 윗면 재빛 하이라이트(빛 좌상단) — 얼굴은 그늘로 남김
    for x, y in ((14, 5), (15, 5), (13, 6), (14, 6), (12, 7), (13, 7), (12, 8)):
        R.dot(x, y + b, G[5])
    for x, y in ((16, 5), (15, 6), (16, 6), (14, 7), (11, 9)):
        R.dot(x, y + b, G[4])
    # 얼굴 = 그늘 한 덩어리(G02, 이목구비 없음). 눈 줄은 더 어둡게(G01) — 눈빛만 떠 보이게
    for x in range(13, 20):
        for y in (11, 12, 13):
            R.dot(x, y + b, G[1] if y == 11 else G[2])
    for x in range(14, 19):
        R.dot(x, 14 + b, G[2])
    # 정수리 균열(혼불 2px) — 두건이 아니라 금 간 머리임을 보이는 표식
    R.dot(18, 6 + b, F_DEEP); R.dot(19, 7 + b, F_BASE)
    # 이마 그늘(찌푸린 이마 덩어리): 눈 위 한 줄 가장 어둡게
    for x in range(16, 20):
        R.dot(x, 10 + b, SL[0])
    R.dot(16, 11 + b, SL[0])                                          # 미간 쪽으로 처진 이마(분노)
    # 눈: 왼눈(화면 오른쪽) 분노 — 안쪽 낮고 바깥 높은 사선 3px. 오른눈(화면 왼쪽) 꺼짐
    if p["eye"]:
        R.dot(17, 11 + b, EYE)
        R.dot(18, 11 + b, EYE_HI if p["eye"] == 2 else EYE)
        R.dot(19, 10 + b, EYE)
    R.dot(14, 11 + b, G[0])
    # 가슴 균열 혼불 (화면 왼쪽~가운데) — 번개꼴 5×6
    for x, y, c in ((13, 19, F_BASE), (14, 20, F_LIGHT), (15, 20, F_BASE), (14, 21, F_GLOW), (15, 21, F_HOT),
                    (13, 22, F_LIGHT), (14, 22, F_GLOW), (15, 23, F_LIGHT), (16, 24, F_BASE), (12, 23, F_DEEP)):
        R.dot(x, y + b, c)
    # 갈비 그늘 (마른 몸) — 균열 아래 몸통 왼쪽
    for x, y in ((11, 25), (12, 25), (11, 27), (12, 27), (13, 27)):
        R.dot(x, y + b, G[2])
    # 배 아래 잔금 1줄
    R.dot(18, 26 + b, F_DEEP); R.dot(19, 27 + b, F_BASE)
    # 화살 깃 · 촉 쪽 못
    R.dot(4, 11 + b, G[8]); R.dot(5, 11 + b, G[6]); R.dot(4, 12 + b, G[6])
    R.dot(25, 23 + b, IRON[3]); R.dot(26, 23 + b, IRON[1])            # 왼팔뚝 위 못머리
    # 일기장 끈 + 걸쇠
    R.dot(11, 29 + b, LEATHER[3]); R.dot(12, 31 + b, G[9])
    # 허리끈 매듭
    for x in range(11, 22):
        R.dot(x, 28 + b, LEATHER[3] if x % 3 else LEATHER[1])
    # 어깨 혼불
    for x, y, c in FLAMES[p["flame"] % len(FLAMES)]:
        R.dot(x, y + b, c)
    R.dot(22, 16 + b, F_DEEP); R.dot(23, 16 + b, F_BASE)              # 견갑 틈(발원점)
    return R.render()


def idle():
    return [draw_down(pose(flame=0))]


def walk():
    out = []
    lifts = [(0, 0), (2, 0), (0, 0), (0, 2)]
    bobs = [0, -1, 0, -1]
    sw = [0, -1, 0, 1]
    for i in range(4):
        fl, fr = lifts[i]
        out.append(draw_down(pose(bob=bobs[i], fl=(0, fl), fr=(0, fr), hl=(0, sw[i]), hr=(0, -sw[i]), flame=(i + 1) % 3)))
    return out


# ---------------------------------------------------------------------------
# 미리보기
# ---------------------------------------------------------------------------
FONT = None
for f in ["/usr/share/fonts/truetype/unifont/unifont.ttf", "/usr/share/fonts/opentype/unifont/unifont.otf"]:
    if os.path.exists(f):
        FONT = ImageFont.truetype(f, 16)
        break
FONT = FONT or ImageFont.load_default()


def label(d, x, y, t, fill=(235, 236, 237)):
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        d.text((x + dx, y + dy), t, font=FONT, fill=(0, 0, 0))
    d.text((x, y), t, font=FONT, fill=fill)


def preview_x4(frames):
    k, pad = 4, 16
    W = pad + len(frames) * (FW * k + pad)
    H = 28 + FH * k + pad + 28 + 18 * 8 + pad
    sheet = Image.new("RGBA", (W, H), (46, 48, 56, 255))
    d = ImageDraw.Draw(sheet)
    names = ["idle f0"] + ["walk f%d" % i for i in range(4)]
    for i, im in enumerate(frames):
        x = pad + i * (FW * k + pad)
        label(d, x, 6, names[i])
        sheet.alpha_composite(upscale(im, k), (x, 28))
        # 피벗 표시
        px, py = x + PIV[0] * k, 28 + PIV[1] * k
        d.line((px - 4, py + 2, px + 4, py + 2), fill=(200, 80, 80, 255))
    # 어깨 혼불 깜빡임 확대(8배): 각 프레임의 x 19..27, y 10..18
    y2 = 28 + FH * k + pad
    label(d, pad, y2, "어깨 혼불 깜빡임 (8배, 프레임마다 모양 교체)")
    for i, im in enumerate(frames):
        crop = im.crop((19, 9, 28, 18))
        sheet.alpha_composite(upscale(crop, 16), (pad + i * (9 * 16 + pad), y2 + 24))
    return sheet


def preview_dark(frames):
    """외곽 거리 v2 목업 albedo 의 바닥 일부(240×135) 위에 1배로 놓고 조명 합성."""
    alb_path = os.path.join(OUTDIR, "..", "v2_outer", "preview_mock_albedo.png")
    base = Image.open(alb_path).convert("RGBA").crop((40, 290, 280, 425))
    W, H = base.size
    old = Image.open(os.path.join(ROOT, "assets/sprites/player/v2/player_idle.png")).crop((0, 0, 32, 48))
    charger = Image.open(os.path.join(ROOT, "assets/sprites/enemies/v2/charger_idle.png")).crop((0, 0, 32, 48))
    spots = []
    xs = [40, 72, 104, 136, 168]
    for i, im in enumerate(frames):
        spots.append((xs[i], 60, im))
    lights = []
    canvas = base.copy()
    dr = ImageDraw.Draw(canvas)
    for x, y, im in spots + [(206, 82, charger)]:
        dr.ellipse((x + 3, y + 43, x + 29, y + 49), fill=(10, 11, 14, 255))   # 발밑 그림자(목업)
    for x, y, im in spots:
        canvas.alpha_composite(im, (x, y))
        lights.append({"x": x + 15, "y": y + 22, "color": "#b0611a", "radius": 34, "intensity": 0.45})  # 몸 혼불 빛(임시)
    canvas.alpha_composite(charger, (206, 82))
    # 위쪽 줄: 비교용 기존 v2(반려) 1개를 왼쪽 위 작은 자리에
    canvas.alpha_composite(old, (6, 60))
    lit = light_scene(canvas, lights, scale=2)
    k = 3
    out = Image.new("RGB", (W + 16 + W * k, max(H, H * k) + 30), (18, 19, 22))
    d = ImageDraw.Draw(out)
    out.paste(lit, (0, 30))
    out.paste(lit.resize((W * k, H * k), Image.NEAREST), (W + 16, 30))
    label(d, 4, 6, "1배 (왼쪽) / 같은 그림 3배 (오른쪽) — 맨 왼쪽 = 반려된 기존 v2(비교), 맨 오른쪽 = 결사병 v2")
    return out, lit


def main():
    frames = idle() + walk()
    preview_x4(frames).save(os.path.join(OUTDIR, "preview_hero3_x4.png"))
    out, lit = preview_dark(frames)
    out.save(os.path.join(OUTDIR, "preview_hero3_dark_x1.png"))
    for i, im in enumerate(frames):
        cs = colors_of(im)
        print("frame", i, "colors", len(cs), "isolated", isolated(im))


if __name__ == "__main__":
    main()
