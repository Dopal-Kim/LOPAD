"""62 루프 3 (P17 묶음 D · 점검 P1-14) 보스 1층 '만취' 시트 재도트 — 월드 64도트 결로.

문제(점검 E_fight_start): 1.5배 네이티브 시트가 넓은 평면 색 + 아주 부드러운 명암이라, 같은 밀도(pixelScale 0.5)의 월드 타일·
소품·적(바깥 먹 테 · 3면 명암 · 경계 디더)보다 '매끈한 그림'으로 보인다.

방법(틀·피벗·프레임 수·ms·이름·앵커·실루엣 알파 전부 그대로 — 코드 무변경, 림·불타는 오버레이도 그대로 맞음):
 1. 재질 램프: 시트에 이미 있는 색(LOPAD 무채·1층 램프·v2 재질 — 새 색 없음)을 색상 방향으로 묶어 재질별 램프(어두움→밝음)를 만든다.
 2. 높이장 = 실루엣 알파(큰 흐림 — 덩어리 부피) + 명도(작은 흐림 — 옷 주름·수염·끈 같은 안쪽 형태)를 섞은 것.
    법선 · 좌상단 빛(바이블 L) 으로 램프 위치를 옮긴다(밝은 쪽 +, 그늘 쪽 −) + 가장자리 어둡힘(AO).
 3. 램프 칸 사이는 4×4 바이어 디더(경계 폭만) — 넓은 평면에 도트 결이 생긴다(프레임마다 몸 모양에서 계산 → 움직여도 '헤엄' 없음).
 4. 재질 경계 먹 선: 다른 재질과 맞닿은 칸 중 그늘 쪽(아래·오른쪽)은 두 칸 어둡게, 실루엣 안쪽 테두리는 아래·오른쪽 = 재질 가장 어두운 칸,
    위·왼쪽 = 한 칸 어둡게(월드 소품 outline 규칙과 같음). 실루엣 밖은 건드리지 않는다.
 5. 떨어진 점·1도트 가는 선(3×3 안 칠한 칸 4 이하 — 먼지·불티)과 자체 발광 색(emissiveColors — 눈빛·술 반짝임·횃불)과 호박 술은 그대로 둔다.
"""
import math
import os
import sys

from PIL import Image, ImageFilter

from c62 import ROOT, SRC, WORK, hx, load_json, save_json

sys.path.insert(0, os.path.join(WORK, "atlas57"))
import gridsheet  # noqa: E402

BOSS = os.path.join(ROOT, "assets", "sprites", "bosses", "v3")
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
_L = (-0.5, -0.6, 0.62)
_n = math.sqrt(sum(v * v for v in _L))
L = tuple(v / _n for v in _L)

# 기본 세기(미리보기로 맞춤)
P = dict(big_blur=9, huge_blur=26, small_blur=1.6, w_big=0.8, w_huge=1.4, w_small=0.6, med_blur=7, w_med=0.6, reg_blur=9, w_reg=2.2, gain=3.4, ao=1.2, sharp=4.0, edge_br=3, edge_tl=2,
         mat_line=1)


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def chroma_dir(c):
    m = sum(c) / 3
    v = (c[0] - m, c[1] - m, c[2] - m)
    n = math.sqrt(sum(x * x for x in v))
    return v, n


RAMPS_HEX = {
    "brown": ["#1b1411", "#2a1e17", "#3b2a1f", "#4f3828", "#664a33", "#82623f"],          # 망토·가죽·살·수염·통 나무 (v2 SL·WD)
    "amber": ["#1a110f", "#3f271d", "#653b24", "#8b4d22", "#b0611a", "#d67a11", "#dc8e23"],  # 1층 램프(볼·코·술 그늘)
    "shirt": ["#2a1e17", "#45403b", "#5c554e", "#756c62", "#90857a", "#ada08f"],          # 바랜 셔츠(PL)
    "cold": ["#14161c", "#1d2028", "#272b35", "#323743", "#3f4552", "#4e5563", "#626a78", "#7e8693"],  # 바지·쇠(차가운 SL)
    "gray": ["#141516", "#212224", "#2f3033", "#3e3f42", "#4d4f52", "#5c5e62", "#6c6f73", "#7d8084", "#8e9195",
             "#a0a2a6", "#c5c6c9", "#d8d9db", "#ebeced"],                                         # 털 깃·왕관·쇠(G)
}


def fixed_ramps(emissive):
    ramps, index = [], {}
    for name, hs in RAMPS_HEX.items():
        r = [hx(h) for h in hs]
        ramps.append(r)
        for i, c in enumerate(r):
            if c not in index and c not in emissive:
                index[c] = (len(ramps) - 1, i)
    return ramps, index


def build_ramps(colors, emissive):
    """색 목록 → 재질 램프 목록 [(ramp[list], set)] · 색 → (램프 번호, 칸)."""
    groups = []   # (대표 방향, [색])
    for c in sorted(colors, key=lum):
        if c in emissive:
            continue
        v, n = chroma_dir(c)
        sat = n / (lum(c) + 20)
        best, bd = None, 1e9
        for gi, (dv, dn, cs, kind) in enumerate(groups):
            if (sat < 0.10) != (kind == "gray"):
                continue
            if kind == "gray":
                d = 0
            else:
                d = 1 - (v[0] * dv[0] + v[1] * dv[1] + v[2] * dv[2]) / (n * dn + 1e-6)
            if d < bd:
                best, bd = gi, d
        if best is not None and (groups[best][3] == "gray" or bd < 0.06):
            groups[best][2].append(c)
        else:
            groups.append((v, n, [c], "gray" if sat < 0.10 else "chroma"))
    ramps = []
    index = {}
    for gi, (_, _, cs, kind) in enumerate(groups):
        r = sorted(cs, key=lum)
        ramps.append(r)
        for i, c in enumerate(r):
            index[c] = (gi, i)
    return ramps, index


def redot_frame(fr, ramps, index, emissive, p=P):
    """fr: RGBA 288×360. 알파 그대로, 색만 다시."""
    w, h = fr.size
    px = fr.load()
    a = fr.getchannel("A")
    solid = a.point(lambda v: 255 if v >= 128 else 0)
    if not solid.getbbox():
        return fr.copy()
    L8 = Image.new("L", fr.size, 0)
    lp = L8.load()
    for y in range(h):
        for x in range(w):
            c = px[x, y]
            if c[3] >= 128:
                lp[x, y] = int(lum(c))
    big = solid.filter(ImageFilter.GaussianBlur(p["big_blur"])).load()
    huge = solid.filter(ImageFilter.GaussianBlur(p["huge_blur"])).load()
    small = L8.filter(ImageFilter.GaussianBlur(p["small_blur"])).load()
    med = L8.filter(ImageFilter.GaussianBlur(p["med_blur"])).load()
    sp = solid.load()
    out = fr.copy()
    po = out.load()
    mat = {}
    regs = [Image.new("L", fr.size, 0) for _ in ramps]
    rps = [r.load() for r in regs]
    for y in range(h):
        for x in range(w):
            c = px[x, y]
            if c[3] < 128:
                continue
            k = index.get(c[:3])
            mat[(x, y)] = k[0] if k else -1
            if k and k[1] >= max(1, len(ramps[k[0]]) // 4):
                rps[k[0]][x, y] = 255                      # 재질 덩어리(선 색 제외) — 덩어리마다 둥근 부피
    regb = [r.filter(ImageFilter.GaussianBlur(p["reg_blur"])).load() for r in regs]
    for (x, y), m in mat.items():
        c = px[x, y]
        if m < 0:
            continue                                   # 발광·미분류 색은 그대로
        ramp = ramps[m]
        n = len(ramp)
        if n < 2:
            continue
        nb = sum(1 for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                 if 0 <= x + dx < w and 0 <= y + dy < h and sp[x + dx, y + dy])
        if nb <= 4:
            continue                                   # 떨어진 점·1도트 선(먼지·불티·가는 줄) — 원래 색 그대로
        i0 = index[c[:3]][1]
        x0, x1 = max(0, x - 1), min(w - 1, x + 1)
        y0, y1 = max(0, y - 1), min(h - 1, y + 1)
        rb = regb[m]
        gx = p["w_reg"] * (rb[x1, y] - rb[x0, y]) / 255
        gy = p["w_reg"] * (rb[x, y1] - rb[x, y0]) / 255
        gx += (p["w_big"] * (big[x1, y] - big[x0, y]) + p["w_huge"] * (huge[x1, y] - huge[x0, y])
              + p["w_small"] * (small[x1, y] - small[x0, y]) + p["w_med"] * (med[x1, y] - med[x0, y])) / 255
        gy += (p["w_big"] * (big[x, y1] - big[x, y0]) + p["w_huge"] * (huge[x, y1] - huge[x, y0])
              + p["w_small"] * (small[x, y1] - small[x, y0]) + p["w_med"] * (med[x, y1] - med[x, y0])) / 255
        nx, ny, nz = -gx * 2.2, -gy * 2.2, 1.0
        nl = math.sqrt(nx * nx + ny * ny + nz * nz)
        lam = (nx * L[0] + ny * L[1] + nz * L[2]) / nl - L[2]
        s = i0 + p["gain"] * lam * (n - 1) / 3
        s -= p["ao"] * (1 - big[x, y] / 255) * (n - 1) / 2
        # 경계 먹 선
        right = x + 1 >= w or sp[x + 1, y] == 0
        down = y + 1 >= h or sp[x, y + 1] == 0
        left = x == 0 or sp[x - 1, y] == 0
        up = y == 0 or sp[x, y - 1] == 0
        if right or down:
            s = min(s, 0) - p["edge_br"]
        elif left or up:
            s = min(s, i0) - p["edge_tl"]
        else:
            mr = mat.get((x + 1, y), m)
            md = mat.get((x, y + 1), m)
            if (mr != m and mr >= 0) or (md != m and md >= 0):
                # 맞닿은 이웃이 더 밝으면 나는 그늘 경계
                nb = px[x + 1, y] if mr != m else px[x, y + 1]
                if lum(nb) >= lum(c) - 4:
                    s = min(s, i0) - p["mat_line"]
        s = max(0.0, min(n - 1.0, s))
        i = int(s)
        f = s - i
        f = max(0.0, min(1.0, (f - 0.5) * p["sharp"] + 0.5))
        th = (BAYER[y % 4][x % 4] + 0.5) / 16
        j = i + 1 if (f > th and i + 1 < n) else i
        po[x, y] = ramp[j] + (c[3],)
    return out


def sheet_colors(names):
    cols = set()
    for nm in names:
        g = gridsheet.open_grid(os.path.join(BOSS, nm + ".json"))
        for n, c in g.convert("RGBA").getcolors(1 << 22) or []:
            if c[3] >= 128:
                cols.add(c[:3])
    return cols
