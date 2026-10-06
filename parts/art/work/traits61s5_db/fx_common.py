"""공통 개성 fx — 공명 켜짐 고리 9(태그 색 · 무기 표지) + 묶음 사슬 타일(청회 묶음 / 적갈 끌림).

공명 켜짐: 같은 태그 카드 두 장 = 태그 문양을 품은 바닥 고리 둘이 양옆에서 미끄러져 와 겹치고(겹친 렌즈에서 빛기둥),
하나로 합쳐진 겹 고리가 퍼지며 머리 위에 태그 문양이 잠깐 뜬다. 겹친 두 교차점에 무기 표지(칼 / · 대검 ▮ · 단검 X · 활 >).
"""
import math

import tk
from tk import (Frame, Rand, sheet, tline, ell, star4, sparks, chain, X0, X1, N0, N1, N2, N3, N4, N5, R0, R1, R2, R3, R4)

RES = [("res_katana_insight", "katana", "insight"), ("res_katana_breach", "katana", "breach"), ("res_katana_chain", "katana", "chain"),
       ("res_greatsword_weight", "greatsword", "weight"), ("res_greatsword_insight", "greatsword", "insight"),
       ("res_dagger_vital", "dagger", "vital"), ("res_dagger_breach", "dagger", "breach"),
       ("res_bow_weight", "bow", "weight"), ("res_bow_breach", "bow", "breach")]


def glyph(cv, cx, cy, tag, col, dark, s=1.0):
    """태그 문양(약 13도트): 간파 = 눈, 돌파 = 위로 겹친 갈매기, 급소 = X 와 마름모, 연쇄 = 엮인 고리 둘, 중량 = 모루(▼+막대), 취기 = 물방울."""
    def L(x0, y0, x1, y1, c=col, w=1.0):
        tline(cv, cx + x0 * s, cy + y0 * s, cx + x1 * s, cy + y1 * s, c, w)
    if tag == "insight":
        for sg in (-1, 1):
            for k in range(-6, 7):
                y = sg * 3.6 * (1 - (k / 6.0) ** 2)
                cv.put(cx + k * s, cy + y * s, col)
        cv.disc(cx, cy, 1.6 * s, col)
        cv.put(cx, cy, dark)
    elif tag == "breach":
        for dy in (-3, 2):
            L(-5, dy + 4, 0, dy - 2)
            L(0, dy - 2, 5, dy + 4)
            L(-5, dy + 5, 0, dy - 1, dark)
            L(0, dy - 1, 5, dy + 5, dark)
    elif tag == "vital":
        L(-5, 0, 0, -5); L(0, -5, 5, 0); L(5, 0, 0, 5); L(0, 5, -5, 0)
        L(-3, -3, 3, 3, col); L(3, -3, -3, 3, col)
    elif tag == "chain":
        ell(cv, cx - 3 * s, cy, 4 * s, 2.6 * s, col)
        ell(cv, cx + 3 * s, cy, 4 * s, 2.6 * s, col)
        ell(cv, cx + 3 * s, cy, 4 * s, 2.6 * s, dark, a0=150, a1=210)
    elif tag == "weight":
        L(-6, -4, 6, -4, col, 2.0)
        for k in range(6):
            L(-5 + k, -2 + k, 5 - k, -2 + k)
        L(-4, 5, 4, 5, col)
    elif tag == "drunk":
        for k in range(0, 11):
            t = k / 10.0
            w = 4.6 * math.sin(math.pi * min(1.0, t * 0.75 + 0.25)) if t > 0.25 else 4.6 * t / 0.25 * 0.7
            y = -6 + t * 11
            L(-w * 0.9, y, w * 0.9, y)
        cv.put(cx - 1.5 * s, cy + 1 * s, dark)
        cv.put(cx - 1.5 * s, cy + 2 * s, dark)


def weapon_mark(cv, x, y, weapon, col):
    """교차점 무기 표지(7도트)."""
    if weapon == "katana":
        tline(cv, x - 3, y + 3, x + 3, y - 3, col)
        cv.put(x + 3, y - 4, col)
    elif weapon == "greatsword":
        for dx in (-1, 0, 1):
            tline(cv, x + dx, y - 3, x + dx, y + 3, col)
        tline(cv, x - 3, y + 1, x + 3, y + 1, col)
    elif weapon == "dagger":
        tline(cv, x - 3, y - 3, x + 3, y + 3, col)
        tline(cv, x - 3, y + 3, x + 3, y - 3, col)
    elif weapon == "bow":
        for k in range(4):
            cv.put(x - 2 + k, y - 3 + k, col)
            cv.put(x - 2 + k, y + 3 - k, col)
        cv.put(x - 3, y, col)


def ring(cv, cx, cy, rx, ry, ramp, phase, dash=(26, 8), w=2, bright=False):
    """두께 3~4 고리: 어두운 테 + 몸(끊긴 마디가 돎) + 위쪽 호 하이라이트."""
    d0, d1, mid, lit, hi, top = ramp
    ell(cv, cx, cy, rx, ry, d1, w=w + 2)
    ell(cv, cx, cy, rx, ry, lit if bright else mid, w=w)
    ell(cv, cx, cy, rx, ry, hi if bright else lit, dash=dash, phase=phase)
    ell(cv, cx, cy - 1, rx, ry, top if bright else hi, a0=205, a1=335, dash=(dash[0] * 0.6, dash[1] * 2), phase=phase)


def res_on(rid, weapon, tag):
    T = tk.TAG[tag]
    ramp = T["ramp"]
    d0, d1, mid, lit, hi, top = ramp
    fr = tk.frame_sheet(192, 192, 7)
    cx, cy = 96, 156
    rx, ry = 40, 15
    for i, cv in enumerate(fr):
        off = [40, 26, 14, 0, 0, 0, 0][i]
        if i <= 2:
            for sg in (-1, 1):
                ring(cv, cx + sg * off, cy, rx, ry, ramp, phase=i * 25 * sg, bright=(i == 2))
                cv.disc(cx + sg * off, cy, 8, d0)
                glyph(cv, cx + sg * off, cy, tag, top if i == 2 else hi, d1, 1.0)
            if i == 0:
                for sg in (-1, 1):
                    star4(cv, cx + sg * off, cy - 18, 5, core=top, mid=hi, edge=lit)
            if i == 2:                                   # 겹친 렌즈: 안쪽 채움 + 교차점 무기 표지 + 빛기둥
                for y in range(cy - ry, cy + ry + 1):
                    for x in range(cx - 30, cx + 31):
                        in_l = ((x - (cx - off)) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 0.92
                        in_r = ((x - (cx + off)) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 0.92
                        if in_l and in_r and (x + y) % 2 == 0:
                            cv.put(x, y, mid)
                for sg in (-1, 1):
                    yy = cy + sg * ry * math.sqrt(max(0.0, 1 - (off / rx) ** 2))
                    weapon_mark(cv, cx, yy, weapon, X1)
                for y in range(26, cy - 4):              # 빛기둥(가운데 백열 + 양옆 hi·lit, 아래로 갈수록 넓음)
                    cv.put(cx, y, X1 if y % 3 else X0)
                    wd = 1 + int(3 * (y - 26) / float(cy - 30))
                    for d in range(1, wd + 1):
                        c = hi if d == 1 else lit
                        cv.put(cx - d, y, c)
                        cv.put(cx + d, y, c)
                sparks(cv, cx, 80, 14, 4, 50, 9, [hi, top, lit], ky=1.6, ln=2)
                star4(cv, cx, cy, 9, core=X0, mid=X1, edge=hi, diag=4)
        else:
            # 하나로 합쳐진 겹 고리가 퍼지며 식음 + 머리 위 태그 문양 + 오르는 빛 점
            r = [0, 0, 0, 44, 54, 62, 68][i]
            k = (r / rx)
            bright = i == 3
            ring(cv, cx, cy, r, ry * k * 0.95, ramp, phase=i * 30, dash=(26, 8) if i < 5 else (14, 16), bright=bright)
            if i <= 5:
                ell(cv, cx, cy, r * 0.72, ry * k * 0.7, lit if i < 5 else mid, dash=(10, 14), phase=-i * 40)
            if i <= 5:
                gy = 22 - (i - 3) * 2
                cv.disc(cx, gy, 11, d0)
                ell(cv, cx, gy, 13, 13, [lit, mid, d1][i - 3], w=2, dash=(30, 15), phase=i * 30)
                glyph(cv, cx, gy, tag, [top, hi, lit][i - 3], d1, 1.5)
            if i <= 4:                                   # 합쳐지는 순간: 바닥 방사 빛살 12
                for k in range(12):
                    a = math.radians(k * 30 + 15)
                    r0, r1 = r + 4 + (i - 3) * 8, r + 14 + (i - 3) * 12
                    tline(cv, cx + math.cos(a) * r0, cy + math.sin(a) * r0 * 0.36, cx + math.cos(a) * r1, cy + math.sin(a) * r1 * 0.36,
                          hi if i == 3 else lit)
            for sg in (-1, 1):
                weapon_mark(cv, cx + sg * r * 0.98, cy, weapon, [top, hi, lit, mid][i - 3])
            sparks(cv, cx, cy - 30 - 14 * (i - 3), 6 + i, 10, 46, 3 + i, [lit, hi, mid], ky=1.2, ln=1)
    sheet("trait_%s_on" % rid, fr, [30, 40, 50, 60, 70, 90, 110], "player_pivot", (cx, cy),
          "공명 켜짐 — %s(%s) 태그 문양을 품은 바닥 고리 둘이 양옆에서 미끄러져 와 겹침 → 겹친 렌즈가 차오르며 두 교차점에 무기 표지(%s) + 빛기둥(f2) → "
          "하나로 합쳐진 겹 고리가 퍼지고 머리 위에 태그 문양이 잠깐 뜸 → 점선으로 식음. 태그 색 = %s"
          % (T["name"], tag, {"katana": "칼 /", "greatsword": "대검 ▮", "dagger": "단검 X", "bow": "활 >"}[weapon], T["note"]),
          ["두 고리", "다가옴", "겹침(빛기둥)", "합쳐짐", "퍼짐", "식음", "사라짐"], glow=[2],
          palette="태그 색 램프(고정색, 층 교체 없음 — 60 Q19 각성 예외와 같은 방식): " + T["note"] + " + 백열 X0/X1(f2 만)",
          weapon=weapon, resonance=rid, tag=tag, tagColor="#%02x%02x%02x" % lit[:3], part="on", depth="above",
          followPlayer=True, spawn="resonance_on",
          spawnNote="공명이 켜진 뒤 전투로 돌아오면 주인공 둘레 1회(요청 노트 §1 공통). 이름 규칙: 공명 발동 fx trait_<공명 id>(무기 담당) 와 겹치지 않게 부위 _on",
          light={"color": "#eecc78", "radius": 64, "intensity": 0.8, "ms": 300})


def chain_tile():
    rows = []
    keys = [("bind", (N1, N2, N4, N5)), ("drag", (R0, R2, R3, R4))]
    for key, ramp in keys:
        row = []
        for i in range(2):
            cv = tk.Cv(64, 16)
            chain(cv, -16, 8, 80, 8, ramp, link=16, glint={1, 5, 9} if i == 1 else None)
            row.append(cv)
        rows.append(row)
    sheet("trait_common_chain", None, [120, 120], "line_start", (0, 8),
          "묶음 사슬 선 반복 타일 — 사슬 한 주기(정면 고리 + 옆면 막대 ×2, 주기 16 도트) 64 도트, 좌우 끝이 이어짐. 행 bind = 청회 묶음(끌어당김·덫·사슬 묶음), "
          "행 drag = 적갈 끌림(낙인 사슬). 열 0 = 기본, 열 1 = 팽팽(마디 반짝)",
          ["기본", "팽팽(반짝)"], rows=rows, directions=["bind", "drag"], loop=False,
          tile=True, tileAxis="x", tilePeriod=64, rowsAre="kinds",
          anchorNote="pivot = 선 시작점(왼끝 가운데 y=8). 선 방향으로 돌려(rotate) x 로 반복해 깐다(TileSprite 권장, 길이는 시스템). 두께 8 도트(화면 4px)",
          rotate=True, drawnFacing="right",
          frameNote="고정 그림 — 묶여 있는 동안 열 0, 끌어당기는 순간·조여질 때 열 1 을 잠깐(100~150ms)", depth="above",
          weapon="any", spawn="trait_tether", trait="common")


ALL = [lambda r=r: res_on(*r) for r in RES] + [chain_tile]
