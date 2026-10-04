#!/usr/bin/env python3
"""56라운드 — 무기별 공격 수단 키아트 후처리 (Pillow 만).

1) 생성 원본 raw_<weapon>_<tag>.jpg 마다 패널을 검은 홈(gutter)으로 나누고 한국어 수단 이름 라벨을 얹은
   labeled_<weapon>_<tag>.jpg 를 만든다(Gemini 글자 생성은 신뢰가 낮아 라벨은 전부 후처리).
2) 수단마다 가장 잘 읽히는 패널을 골라(SEL) 무기별 시트 sheet_<weapon>.png 로 모은다:
   제목 띠 + 번호 라벨 패널 + 아래 '수단 목록'(번호·이름·설명·근거·참조 게임).
3) 같은 목록을 list_<weapon>.md 로 쓴다.
원본 픽셀은 다시 칠하지 않는다(색조 보정 없음 — 참고 그림).
실행: python3 build.py
"""
import os
from PIL import Image, ImageDraw, ImageFont
from moves import WEAPONS

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
AMBER = (232, 184, 88)
AMBER_D = (214, 122, 17)
PAPER = (236, 228, 210)
GRAYT = (150, 146, 140)
BG = (22, 21, 24)

# 생성 회차 — gen_log.jsonl 순서와 같다. (tag, 시트 번호)
RAWS = {
    "katana": [("A", 0), ("B", 1), ("A2", 0), ("B2", 1)],
    "greatsword": [("A", 0), ("B", 1)],
    "dagger": [("A", 0), ("B", 1), ("A2", 0)],
    "bow": [("A", 0), ("B", 1), ("B2", 1)],
}
# 채택 패널: 수단 순서대로 (원본 tag, 그 원본 안 패널 번호). 자기 비평(see→critique→fix) 결과:
#  칼   1회차 A: 일섬 선이 적을 지나지 않음 → A2 의 일섬·분신 채택(적이 선을 따라 갈라짐). 검기 3단·기본 연격은 A 가 더 깨끗.
#       1회차 B: 대치가 '칼 거두기'로 안 읽힘 → B2 대치(납도 + 뒤 적 사선) 채택. B2 회전은 닫힌 원(Q11 위반)이라 B,
#       가드 불가는 B2(방패가 세로로 갈라짐)가 더 분명. B2 는 배경이 평평한 청회색 — 6·8번만 땅이 약함.
#  대검 A·B 1회로 8수단 모두 읽힘 → 재생성 없음.
#  단검 1회차 A: 낙인이 '불붙은 적'으로 보임, 등 뒤 찌르기가 정면 → A2 의 낙인(셀 수 있는 발톱 자국)·등 뒤 찌르기 채택.
#       A2 의 1·2번은 적 소매가 파란색(팔레트 위반)이라 A 유지.
#  활   1회차 B: 숨이 감속으로 약하게 읽힘 → B2 숨(회색으로 멈춘 세계·떠 있는 탄환) 채택, 재장전은 B 가 덜 어수선.
SEL = {
    "katana": [("A", 0), ("A2", 1), ("A2", 2), ("A", 3), ("B", 0), ("B2", 1), ("B", 2), ("B2", 3)],
    "greatsword": [("A", 0), ("A", 1), ("A", 2), ("A", 3), ("B", 0), ("B", 1), ("B", 2), ("B", 3)],
    "dagger": [("A", 0), ("A", 1), ("A2", 2), ("A2", 3), ("B", 0), ("B", 1), ("B", 2), ("B", 3)],
    "bow": [("A", 0), ("A", 1), ("A", 2), ("A", 3), ("B2", 0), ("B", 1)],
}


def font(sz):
    return ImageFont.truetype(FONT, sz)


def _gutter(lum, lo, hi, thr=24):
    """lum: 1차원 평균 밝기 목록. [lo,hi) 구간에서 가장 어두운 연속 구간(홈)의 (시작, 끝)."""
    best = min(range(lo, hi), key=lambda i: lum[i])
    if lum[best] > thr:
        return best, best + 1
    a = b = best
    while a > lo and lum[a - 1] <= thr:
        a -= 1
    while b < hi - 1 and lum[b + 1] <= thr:
        b += 1
    return a, b + 1


def split(im, grid):
    """2×2 또는 2×1 패널 상자 목록(왼→오, 위→아래)."""
    g = im.convert("L")
    w, h = g.size
    px = g.load()
    step = 4
    col = [sum(px[x, y] for y in range(0, h, step)) / len(range(0, h, step)) for x in range(w)]
    xa, xb = _gutter(col, int(w * 0.4), int(w * 0.6))
    xs = [(0, xa), (xb, w)]
    if grid[1] == 1:
        ys = [(0, h)]
    else:
        row = [sum(px[x, y] for x in range(0, w, step)) / len(range(0, w, step)) for y in range(h)]
        ya, yb = _gutter(row, int(h * 0.4), int(h * 0.6))
        ys = [(0, ya), (yb, h)]
    boxes = []
    for (y0, y1) in ys:
        for (x0, x1) in xs:
            boxes.append((x0, y0, x1, y1))
    return boxes


def label(im, num, text, sz=24):
    """패널 왼쪽 위에 반투명 검은 띠 + 호박 번호 + 한국어 이름."""
    im = im.convert("RGBA")
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    fN, fT = font(sz + 4), font(sz)
    ns = str(num)
    nw = d.textlength(ns, font=fN)
    tw = d.textlength(text, font=fT)
    pad = 9
    bw, bh = int(pad * 3 + nw + tw), int(sz + 4 + pad * 2)
    d.rectangle((8, 8, 8 + bw, 8 + bh), fill=(8, 7, 9, 200))
    d.rectangle((8, 8, 11, 8 + bh), fill=AMBER_D + (255,))
    d.text((8 + pad + 2, 8 + pad - 3), ns, font=fN, fill=AMBER + (255,))
    d.text((8 + pad * 2 + nw + 2, 8 + pad), text, font=fT, fill=PAPER + (255,))
    return Image.alpha_composite(im, ov).convert("RGB")


def wrap(d, text, f, width):
    lines, cur = [], ""
    for ch in text:
        if d.textlength(cur + ch, font=f) > width and cur:
            # 단어 중간을 피하려고 마지막 공백에서 끊는다
            sp = cur.rfind(" ")
            if sp > len(cur) * 0.6:
                lines.append(cur[:sp])
                cur = cur[sp + 1:] + ch
            else:
                lines.append(cur)
                cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def panels_of(weapon):
    """{tag: [(box, crop)]} 와 수단 번호 붙은 평평한 목록."""
    out = {}
    for tag, si in RAWS[weapon]:
        im = Image.open(os.path.join(HERE, f"raw_{weapon}_{tag}.jpg")).convert("RGB")
        grid = tuple(WEAPONS[weapon]["sheets"][si]["grid"])
        out[tag] = (si, im, split(im, grid))
    return out


def labeled_raws(weapon, P):
    w = WEAPONS[weapon]
    start = [0]
    for sh in w["sheets"]:
        start.append(start[-1] + len(sh["panels"]))
    for tag, (si, im, boxes) in P.items():
        res = im.copy()
        for i, b in enumerate(boxes):
            m = w["sheets"][si]["panels"][i]
            res.paste(label(im.crop(b), start[si] + i + 1, m["ko"], sz=22), b[:2])
        res.save(os.path.join(HERE, f"labeled_{weapon}_{tag}.jpg"), quality=92)


def sheet(weapon, P):
    w = WEAPONS[weapon]
    moves = [m for sh in w["sheets"] for m in sh["panels"]]
    crops = []
    for (tag, i) in SEL[weapon]:
        si, im, boxes = P[tag]
        crops.append(im.crop(boxes[i]))
    PW = 680
    crops = [c.resize((PW, round(c.size[1] * PW / c.size[0])), Image.LANCZOS) for c in crops]
    G, M = 8, 24
    W = M * 2 + PW * 2 + G
    # 행 높이 = 그 행 두 패널 중 큰 쪽
    rows = [crops[k:k + 2] for k in range(0, len(crops), 2)]
    rh = [max(c.size[1] for c in r) for r in rows]
    # 목록 높이 계산
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    fH, fName, fBody, fSmall = font(40), font(26), font(20), font(18)
    colw = W - M * 2 - 70
    legend = []
    for n, m in enumerate(moves, 1):
        body = wrap(tmp, m["desc"], fBody, colw)
        refl = wrap(tmp, "근거 " + m["src"] + "   ·   참조 " + m["ref"], fSmall, colw)
        legend.append((n, m, body, refl))
    lh = sum(36 + 27 * len(b) + 24 * len(r) + 16 for _, _, b, r in legend)
    TH = 92
    H = TH + sum(rh) + G * (len(rows) - 1) + 40 + 50 + lh + M
    out = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(out)
    d.text((M, 22), f"{w['ko']} — 공격 수단 키아트", font=fH, fill=PAPER)
    sub = "56라운드 원문 8번 · Q13~Q24 · Gemini 참고 그림(게임 도트 아님) · 입력·조건은 검수 후 인터뷰"
    d.text((M + d.textlength(f"{w['ko']} — 공격 수단 키아트", font=fH) + 24, 40), sub, font=fSmall, fill=GRAYT)
    d.rectangle((M, TH - 10, W - M, TH - 8), fill=AMBER_D)
    y = TH
    k = 0
    for r, h in zip(rows, rh):
        x = M
        for c in r:
            k += 1
            out.paste(label(c, k, moves[k - 1]["ko"]), (x, y + (h - c.size[1]) // 2))
            x += PW + G
        y += h + G
    y += 40 - G
    d.text((M, y), "수단 목록", font=font(30), fill=AMBER)
    y += 50
    for n, m, body, refl in legend:
        d.text((M, y), str(n), font=fName, fill=AMBER)
        d.text((M + 40, y), m["ko"], font=fName, fill=PAPER)
        y += 36
        for ln in body:
            d.text((M + 40, y), ln, font=fBody, fill=(206, 200, 188))
            y += 27
        for ln in refl:
            d.text((M + 40, y), ln, font=fSmall, fill=GRAYT)
            y += 24
        y += 16
    fn = os.path.join(HERE, f"sheet_{weapon}.png")
    out.save(fn)
    return fn, out.size


def md(weapon):
    w = WEAPONS[weapon]
    moves = [m for sh in w["sheets"] for m in sh["panels"]]
    L = [f"# {w['ko']} — 공격 수단 목록 (56라운드 키아트)", "",
         f"그림: `sheet_{weapon}.png`(채택 패널 + 라벨 + 목록) · 원본 `raw_{weapon}_*.jpg` · 라벨 합성본 `labeled_{weapon}_*.jpg`.",
         "참고 그림이다(게임 도트 아님). 입력·조건(기본기/갈래/자원 소모)은 검수 후 인터뷰(56라운드 Q21~Q24 비고).", "",
         "| 패널 | 이름 | 간단 설명 | 근거 | 참조 게임(메커니즘) | 채택 원본 |", "|---|---|---|---|---|---|"]
    for n, (m, (tag, i)) in enumerate(zip(moves, SEL[weapon]), 1):
        L.append(f"| {n} | {m['ko']} | {m['desc']} | {m['src']} | {m['ref']} | raw_{weapon}_{tag} 패널 {i + 1} |")
    open(os.path.join(HERE, f"list_{weapon}.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")


if __name__ == "__main__":
    for wk in WEAPONS:
        P = panels_of(wk)
        for tag, (si, im, boxes) in P.items():
            print(wk, tag, boxes)
        labeled_raws(wk, P)
        print(sheet(wk, P))
        md(wk)
