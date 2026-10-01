#!/usr/bin/env python3
"""LOPAD 팔레트 빌드 — 무채색 16단 + 층별 강조 램프 12칸 x 8층.

실행: python3 parts/art/work/palette/build.py
산출:
  parts/art/palette/lopad.json   (기계용 정의, 다른 빌드 스크립트가 import)
  parts/art/palette/lopad.gpl    (GIMP/Aseprite 팔레트: 무채 16 + 8층 x 12)
  parts/art/palette/preview.png  (검수용 미리보기)

규칙:
  - 무채색 16단: 순흑(#000000) ~ 순백(#ffffff), L* 등간격. 중간 톤에만 약한 한기(청색) 허용.
  - 강조 램프 12칸: 하나의 '틀'. 층마다 hue 만 바꿔 같은 인덱스(16~27)에 교체 로드한다.
    인덱스 16 = 가장 어두운 강조(거의 검정, 그림자용) … 27 = 가장 밝은 강조(거의 흰색, 섬광용).
    그림자 쪽은 hue 를 차갑게(청색 방향), 하이라이트 쪽은 따뜻하게(황색 방향) 돌린다.
"""
import colorsys
import json
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "..", "palette"))
os.makedirs(OUT, exist_ok=True)

GRAY_STEPS = 16
ACCENT_STEPS = 12


# ---------------------------------------------------------------- 색 변환
def _lab_to_srgb(L, a, b):
    """CIE L*a*b* (D65) -> sRGB 8bit."""
    fy = (L + 16.0) / 116.0
    fx = fy + a / 500.0
    fz = fy - b / 200.0

    def finv(t):
        return t ** 3 if t ** 3 > 0.008856 else (t - 16.0 / 116.0) / 7.787

    X = 0.95047 * finv(fx)
    Y = 1.00000 * finv(fy)
    Z = 1.08883 * finv(fz)
    r = X * 3.2406 + Y * -1.5372 + Z * -0.4986
    g = X * -0.9689 + Y * 1.8758 + Z * 0.0415
    bb = X * 0.0557 + Y * -0.2040 + Z * 1.0570

    def gam(c):
        c = max(0.0, min(1.0, c))
        return 1.055 * c ** (1 / 2.4) - 0.055 if c > 0.0031308 else 12.92 * c

    return tuple(int(round(gam(c) * 255)) for c in (r, g, bb))


def _hex(rgb):
    return "#%02x%02x%02x" % rgb


def grays(n=GRAY_STEPS):
    """L* 등간격 n 단. 양끝은 순흑/순백, 중간 톤은 b*=-3 (약한 청색 기운)."""
    out = []
    for i in range(n):
        t = i / (n - 1)
        L = 100.0 * t
        cool = -3.0 * (1.0 - abs(2 * t - 1)) ** 0.7  # 양끝 0, 중간 -3
        rgb = _lab_to_srgb(L, 0.0, cool)
        if i == 0:
            rgb = (0, 0, 0)
        if i == n - 1:
            rgb = (255, 255, 255)
        out.append(_hex(rgb))
    return out


BASE_T = 5 / (ACCENT_STEPS - 1)  # 인덱스 21(= 램프 6번째 칸) 이 '본색'


def accent_ramp(hue, sat, n=ACCENT_STEPS, v_dark=0.10, v_mid=0.70, v_light=0.98,
                shadow_shift=22.0, light_shift=14.0, sat_floor=0.35, sat_tail=0.25):
    """hue(0~360)·sat(0~1)의 12단 램프. 6번째 칸(인덱스 21)이 '본색'(명도 v_mid),
    어두운 쪽은 청색으로, 밝은 쪽은 황색으로 hue 가 돈다.
    sat 는 본색에서 최고, 어두운 끝은 sat_floor 배, 밝은 끝은 sat_tail 배."""
    def toward(h, target, amount):
        diff = ((target - h + 180.0) % 360.0) - 180.0
        step = max(-amount, min(amount, diff))
        return (h + step) % 360.0

    out = []
    for i in range(n):
        t = i / (n - 1)
        # 명도: 본색 칸까지 v_dark->v_mid, 그 뒤 v_mid->v_light (두 구간 모두 선형)
        if t <= BASE_T:
            v = v_dark + (v_mid - v_dark) * (t / BASE_T)
        else:
            v = v_mid + (v_light - v_mid) * ((t - BASE_T) / (1.0 - BASE_T))
        if t < BASE_T:
            k = (BASE_T - t) / BASE_T
            h = toward(hue, 240.0, k * shadow_shift)
            s = sat * (1.0 - (1.0 - sat_floor) * k ** 1.3)
            # 아주 어두운 단계에서는 채도를 더 살려 '검정이 아닌 색'으로 읽히게
            s = min(1.0, s + 0.10 * k ** 2)
        else:
            k = (t - BASE_T) / (1.0 - BASE_T)
            h = toward(hue, 60.0, k * light_shift)
            s = sat * (1.0 - (1.0 - sat_tail) * k ** 1.2)
        r, g, b = colorsys.hsv_to_rgb(h / 360.0, max(0.0, min(1.0, s)), max(0.0, min(1.0, v)))
        out.append(_hex((round(r * 255), round(g * 255), round(b * 255))))
    return out


# ---------------------------------------------------------------- 층 정의
# 28라운드 Q6: 1 잔=호박 / 2 패=도박장 녹색 / 3 붕=병원 청록 / 4 계=황토 / 5 귀=보라 / 6 연=황금 / 7 적=진홍 / 8 평상=은빛 흰색
# hue/sat 는 아트 파트 제안값 (검수 대상). 1·4·6 이 모두 난색이므로 hue 와 채도로 벌려 놓았다:
#   1 호박 = 주황 기운(hue 32), 4 황토 = 탁한 겨자(hue 44, 저채도), 6 황금 = 맑은 노랑(hue 50, 고채도)
FLOORS = [
    dict(floor=1, name="잔", romaja="zan",     label="amber",        hue=32.0,  sat=0.92, v_mid=0.84, shadow_shift=18, light_shift=16),
    dict(floor=2, name="패", romaja="pae",     label="casino green", hue=150.0, sat=0.70, v_mid=0.60, shadow_shift=20, light_shift=18),
    dict(floor=3, name="붕", romaja="bung",    label="hospital teal",hue=172.0, sat=0.62, v_mid=0.68, shadow_shift=24, light_shift=20),
    dict(floor=4, name="계", romaja="gye",     label="ochre",        hue=44.0,  sat=0.62, v_mid=0.70, shadow_shift=16, light_shift=10),
    dict(floor=5, name="귀", romaja="gwi",     label="violet",       hue=272.0, sat=0.68, v_mid=0.64, shadow_shift=12, light_shift=22),
    dict(floor=6, name="연", romaja="yeon",    label="gold",         hue=50.0,  sat=0.90, v_mid=0.88, shadow_shift=20, light_shift=8),
    dict(floor=7, name="적", romaja="jeok",    label="crimson",      hue=352.0, sat=0.90, v_mid=0.70, shadow_shift=16, light_shift=14),
    dict(floor=8, name="평상", romaja="pyeongsang", label="silver white", hue=222.0, sat=0.12, v_mid=0.74, shadow_shift=6, light_shift=6),
]

# 강조 램프 12칸의 역할 이름 (스프라이트 작업자가 어느 칸을 어디에 쓰는지 공통 어휘)
ACCENT_ROLES = [
    "ink",          # 16: 가장 어두운 강조 — 강조 재질의 윤곽/깊은 그림자
    "deep",         # 17
    "shadow2",      # 18
    "shadow1",      # 19
    "base_dark",    # 20
    "base",         # 21: 본색
    "base_light",   # 22
    "light1",       # 23
    "light2",       # 24
    "glow",         # 25: 발광·눈빛
    "flash",        # 26: 섬광
    "white",        # 27: 거의 흰색의 강조
]
GRAY_ROLES = {
    0: "pure black / selout", 1: "coat shadow", 2: "coat base", 3: "coat fold",
    4: "boot / iron dark", 5: "iron", 6: "cloth shadow", 7: "cloth base",
    8: "cloth light", 9: "pale skin", 10: "bandage shadow", 11: "bandage base",
    12: "bandage light", 13: "bone / paper", 14: "near white", 15: "pure white / glint",
}


def build():
    G = grays()
    floors = []
    for f in FLOORS:
        ramp = accent_ramp(f["hue"], f["sat"], v_mid=f["v_mid"],
                           shadow_shift=f["shadow_shift"], light_shift=f["light_shift"])
        floors.append(dict(
            floor=f["floor"], name=f["name"], romaja=f["romaja"], label=f["label"],
            hue=f["hue"], sat=f["sat"], v_mid=f["v_mid"], ramp=ramp,
        ))

    data = {
        "name": "LOPAD",
        "version": 1,
        "decision": "2026-10-01 round-28 Q2/Q5/Q6",
        "total_slots": GRAY_STEPS + ACCENT_STEPS,
        "gray": G,
        "gray_roles": {str(k): v for k, v in GRAY_ROLES.items()},
        "accent_slots": {"first_index": GRAY_STEPS, "count": ACCENT_STEPS, "roles": ACCENT_ROLES},
        "floors": floors,
        "notes": [
            "무채색 16 은 모든 층에서 고정. 강조 램프 12 는 층 진입 시 그 층의 ramp 로 교체(인덱스 16~27).",
            "피·불꽃·발광 등 모든 유채색은 현재 층의 강조 램프만 쓴다 (고정 포인트색 없음).",
            "주인공은 무채색 + 강조 램프 2칸 이내(glow, base)만 쓴다.",
        ],
    }
    with open(os.path.join(OUT, "lopad.json"), "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=1)

    # GPL (GIMP palette). Aseprite 도 읽는다. 무채 16 + 8층 x 12 = 112 색.
    lines = ["GIMP Palette", "Name: LOPAD", "Columns: 16", "#"]
    for i, h in enumerate(G):
        r, g, b = int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)
        lines.append("%3d %3d %3d\tG%02d %s" % (r, g, b, i, GRAY_ROLES[i]))
    for f in floors:
        for j, h in enumerate(f["ramp"]):
            r, g, b = int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)
            lines.append("%3d %3d %3d\tF%d_%s A%02d %s" % (r, g, b, f["floor"], f["romaja"], j, ACCENT_ROLES[j]))
    with open(os.path.join(OUT, "lopad.gpl"), "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines) + "\n")

    # ------------------------------------------------------------ preview
    cell, gap, left, top, rowh = 36, 2, 190, 40, 50
    W = left + 16 * (cell + gap) + 20
    H = top + rowh * (1 + len(floors)) + 70
    img = Image.new("RGB", (W, H), (46, 46, 50))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        fontb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)
        small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 9)
    except OSError:
        font = fontb = small = ImageFont.load_default()
    d.text((12, 10), "LOPAD palette v1 - 16 grays (fixed) + 12-slot accent ramp x 8 floors", fill=(230, 230, 230), font=fontb)

    y = top
    d.text((12, y + 10), "GRAY  G00..G15", fill=(230, 230, 230), font=fontb)
    for i, h in enumerate(G):
        x = left + i * (cell + gap)
        d.rectangle([x, y, x + cell - 1, y + cell - 1], fill=h)
        d.text((x + 2, y + cell + 1), "%02d" % i, fill=(200, 200, 200), font=small)
    y += rowh
    for f in floors:
        d.text((12, y + 4), "F%d  %s" % (f["floor"], f["romaja"].upper()), fill=(230, 230, 230), font=fontb)
        d.text((12, y + 22), f["label"], fill=(170, 170, 170), font=font)
        for j, h in enumerate(f["ramp"]):
            x = left + j * (cell + gap)
            d.rectangle([x, y, x + cell - 1, y + cell - 1], fill=h)
            d.text((x + 1, y + cell + 1), "%02d" % (16 + j), fill=(200, 200, 200), font=small)
        y += rowh
    # 설명
    y += 6
    d.text((12, y), "accent roles: " + " ".join("%d=%s" % (16 + i, r) for i, r in enumerate(ACCENT_ROLES)),
           fill=(190, 190, 190), font=small)
    d.text((12, y + 14), "sprite colour discipline: grays + at most 2 accent slots (glow 25, base 21). "
           "accent ramp swaps per floor; grays never change.", fill=(190, 190, 190), font=small)
    img.save(os.path.join(OUT, "preview.png"))

    # 1픽셀 마스터 스와치 (실제 색 추출용): 16 + 8x12 를 한 줄씩
    sw = Image.new("RGB", (16, 1 + len(floors)), (0, 0, 0))
    for i, h in enumerate(G):
        sw.putpixel((i, 0), tuple(int(h[k:k + 2], 16) for k in (1, 3, 5)))
    for r, f in enumerate(floors):
        for j, h in enumerate(f["ramp"]):
            sw.putpixel((j, r + 1), tuple(int(h[k:k + 2], 16) for k in (1, 3, 5)))
    sw.save(os.path.join(OUT, "lopad_swatch_1x.png"))

    print("grays:", " ".join(G))
    for f in floors:
        print("F%d %-4s %s" % (f["floor"], f["romaja"], " ".join(f["ramp"])))
    print("->", OUT)


if __name__ == "__main__":
    build()
