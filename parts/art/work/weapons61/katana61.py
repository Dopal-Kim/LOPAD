"""61라운드 칼 발도 검기 단수별 fx(선택 요청) — fx/v3/katana_iai_ki1~3.

56라운드 katana_iai(발도 일격 붓획 + 잔심 + 납도 딸깍 터짐)를 바탕으로, 검기 단수가 높을수록:
1단 = 붓획 둘레 얇은 호박 기운 + 불씨 / 2단 = 기운이 넓어지고 붓획과 나란한 그림자 획 1줄 / 3단 = 넓은 기운 + 양옆 그림자 획 2줄 + 획을 따라 튀는 불꽃.
프레임·ms·피벗·행·판정 프레임·anchor·spawn 은 katana_iai 와 같음 — 발도 순간의 검기 단수로 시트만 고른다.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from wk61 import (Cv, Rand, A17, A18, A19, A21, A23, A25, A26, X1, old_meta, old_grid, GLOW)  # noqa: E402
from pk import BAYER  # noqa: E402

SRC = "parts/art/work/weapons61/build.py katana (61라운드 발도 검기 단수별 fx)"
STROKE = {c[:3] for c in (A19, A21, A23, A25, A26, X1)} | {(255, 255, 255)}


def _axis(im):
    p = im.load()
    pts = [(x, y) for y in range(im.height) for x in range(im.width) if p[x, y][3] == 255 and p[x, y][:3] in STROKE]
    if len(pts) < 10:
        return None
    mx = sum(x for x, y in pts) / len(pts)
    my = sum(y for x, y in pts) / len(pts)
    sxx = sum((x - mx) ** 2 for x, y in pts)
    syy = sum((y - my) ** 2 for x, y in pts)
    sxy = sum((x - mx) * (y - my) for x, y in pts)
    a = 0.5 * math.atan2(2 * sxy, sxx - syy)
    return math.cos(a), math.sin(a)


def kiframes(level):
    m = old_meta("fx", "katana_iai")
    g = old_grid("fx", "katana_iai")
    fw, fh, n = m["frameWidth"], m["frameHeight"], m["frames"]
    glow = set(m.get("glowFrames", []))
    halo = {1: 3, 2: 6, 3: 9}[level]
    echoes = {1: [], 2: [10], 3: [11, -11]}[level]
    rows = []
    for j, d in enumerate(m["directions"]):
        ax = _axis(g.crop((2 * fw, j * fh, 3 * fw, (j + 1) * fh)))
        nx, ny = (-ax[1], ax[0]) if ax else (0.0, 1.0)
        row = []
        for i in range(n):
            im = g.crop((i * fw, j * fh, (i + 1) * fw, (j + 1) * fh))
            p = im.load()
            src = [(x, y, p[x, y]) for y in range(fh) for x in range(fw) if p[x, y][3] == 255 and p[x, y][:3] in STROKE]
            out = Cv(fw, fh)
            fade = 1.0 if i <= 2 else (0.7 if i <= 6 else (1.0 if i == 7 else 0.4))
            # 그림자 획(나란히 비켜 선 어두운 획)
            for e in echoes:
                for (x, y, c) in src:
                    if (x + y) % 3 == 0 and i > 2:
                        continue
                    xx, yy = x + nx * e, y + ny * e
                    out.put(xx, yy, A21 if c[:3] in GLOW or c[:3] == A25[:3] else A19)
            # 기운(붓획 둘레 디더 띠)
            if fade > 0:
                rr = int(round(halo * fade))
                for (x, y, c) in src:
                    for s in range(1, rr + 1):
                        t = s / float(rr + 1)
                        dens = (1 - t) * (0.8 if i <= 2 or i == 7 else 0.5)
                        for sg in (1, -1):
                            xx, yy = int(round(x + nx * s * sg)), int(round(y + ny * s * sg))
                            if not (1 <= xx < fw - 1 and 1 <= yy < fh - 1) or out.get(xx, yy)[3]:
                                continue
                            if (BAYER[yy % 4][xx % 4] + 0.5) / 16.0 < dens:
                                out.put(xx, yy, A23 if t < 0.3 and level == 3 else (A21 if t < 0.6 else A19))
            out.im.alpha_composite(im)
            # 불꽃·불씨
            r = Rand(7700 + level * 100 + j * 13 + i)
            nsp = {1: 4, 2: 8, 3: 16}[level] if (1 <= i <= 2 or i == 7) else {1: 1, 2: 3, 3: 6}[level]
            for k in range(nsp if src else 0):
                x, y, c = src[r.i(0, len(src) - 1)]
                off = (r.f() * 2 - 1) * (halo + 8)
                xx, yy = x + nx * off, y + ny * off - r.i(0, 4)
                col = A25 if (i not in glow and level >= 2) else (A23 if level == 1 else A26 if i in glow else A25)
                out.put(xx, yy, col)
                if level == 3 and k % 2 == 0:
                    out.put(xx + nx, yy + ny, A23)
            op = out.im.load()
            for x in range(fw):
                for y in (0, 1, fh - 2, fh - 1):
                    if op[x, y][:3] != p[x, y][:3] or op[x, y][3] != p[x, y][3]:
                        op[x, y] = p[x, y]
            for y in range(fh):
                for x in (0, 1, fw - 2, fw - 1):
                    if op[x, y] != p[x, y]:
                        op[x, y] = p[x, y]
            row.append(out.im)
        rows.append(row)
    meta = {k: v for k, v in m.items() if k not in ("colors", "source", "effectRule")}
    meta.update(version="v3-r61", source=SRC + " · 원 붓획 = katana_iai(56라운드 E1)",
                kiLevel=level, kiOf="katana_iai",
                kiVariants={"0": "katana_iai", "1": "katana_iai_ki1", "2": "katana_iai_ki2", "3": "katana_iai_ki3"},
                kiRule=("발도(좌 홀드 떼기 일격) 순간의 검기 단수로 시트를 고른다 — 0단 = katana_iai, 1~3단 = katana_iai_ki<n>. "
                        "같은 프레임 번호·ms·피벗·행·판정 프레임(그림만 다름). 무기 시트의 검기 오버레이(_ki1~3, §18.10)와 함께 쓴다"),
                design={1: "1단: 붓획 둘레 얇은 호박 기운(3 도트) + 불씨",
                        2: "2단: 넓은 기운(6 도트) + 붓획과 나란한 그림자 획 1줄 + 불씨",
                        3: "3단: 넓은 기운(9 도트, 안쪽 밝게) + 양옆 그림자 획 2줄 + 획을 따라 튀는 불꽃 16"}[level],
                r61="61라운드 시스템 보고 — 칼 발도 검기 단수별 fx(선택)")
    return "katana_iai_ki%d" % level, rows, fw, fh, meta, m["frameDurationsMs"], m.get("loop", False)
