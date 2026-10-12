"""P1-2 칼·대검 연격 1~3타 스미어 프레임 (62 루프 2).

원칙
- 스미어는 **무기 오버레이와 같은 틀·피벗·프레임 번호**(weapons/v3/<동작>)로 그린다 → 몸·무기와 같은 프레임을 같은 시각에 겹치면
  궤적이 칼날에 붙는다(원점 어긋남이 구조적으로 생길 수 없음).
- 모양: 칼끝 궤적(bladeTipAnchors 를 Catmull-Rom 으로 이은 곡선)이 바깥 테, 칼끝에서 손잡이 쪽으로 폭 w(s)만큼 메운 띠.
  s = 0(가장 오래된 꼬리) → 1(지금 칼날). 폭은 머리(지금 칼날)에서 가장 굵고 꼬리로 갈수록 가늘어지며 끝은 디더로 부서진다.
- 색: 무기 정체성(계약 §28) — 칼 '서리' 램프 · 대검 '용암' 램프. 가장 밝은 칸(흰 끝)은 판정 칸(glowFrames)에만.
- 찌르기(katana_thrust)는 휘두름이 아니라 칼끝 뒤로 꼬리를 끄는 '찌름 줄기'.
"""
import math

from PIL import Image

from common import (FROST, LAVA, X0, b2, bayer, ramp_pick, load_grid, cell, SRC, hexc)

# 동작별: 무기 색 · 휘두름 칸 · 사라짐 칸 · 최대 폭(칼날 길이 비율)
MOVES = {
    "katana_rise": dict(weapon="katana", ramp=FROST, sweep=[2, 3, 4], decay=[5, 6], width=0.46, hit=1),
    "katana_fall": dict(weapon="katana", ramp=FROST, sweep=[1, 2, 3], decay=[4, 5], width=0.46, hit=2),
    "katana_thrust": dict(weapon="katana", ramp=FROST, thrust=[3, 4, 5], decay=[6], width=0.0, hit=3),
    "greatsword_sweep_cw": dict(weapon="greatsword", ramp=LAVA, sweep=[5, 6, 7], decay=[8, 9], width=0.62, hit=1),
    "greatsword_cleave": dict(weapon="greatsword", ramp=LAVA, sweep=[4, 5, 6], decay=[7, 8], width=0.62, hit=2),
    "greatsword_sweep_ccw": dict(weapon="greatsword", ramp=LAVA, sweep=[5, 6, 7], decay=[8, 9], width=0.62, hit=3),
}
MIN_MOVE = 14   # 이 도트보다 덜 움직인 칸 사이는 휘두름이 아님(그리지 않음)


def catmull(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return tuple(0.5 * ((2 * p1[i]) + (-p0[i] + p2[i]) * t + (2 * p0[i] - 5 * p1[i] + 4 * p2[i] - p3[i]) * t2
                        + (-p0[i] + 3 * p1[i] - 3 * p2[i] + p3[i]) * t3) for i in range(2))


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


class Buf:
    """칸마다 가장 새로운 s(머리 쪽)와 그때의 가장자리 값 e(0 안쪽 → 1 칼끝 테)를 기록."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.s = [[-1.0] * w for _ in range(h)]
        self.e = [[0.0] * w for _ in range(h)]

    def put(self, x, y, s, e):
        xi, yi = int(round(x)), int(round(y))
        if 0 <= xi < self.w and 0 <= yi < self.h and s >= self.s[yi][xi]:
            self.s[yi][xi] = s
            self.e[yi][xi] = max(e, self.e[yi][xi]) if s == self.s[yi][xi] else e


def sweep_samples(tips, grips, k, steps):
    """칸 k-1 → k 구간의 (칼끝, 손잡이) 표본 steps+1 개."""
    n = len(tips)
    p0 = tips[max(0, k - 2)] or tips[k - 1]
    p3 = tips[min(n - 1, k + 1)] or tips[k]
    out = []
    for i in range(steps + 1):
        t = i / steps
        out.append((catmull(p0, tips[k - 1], tips[k], p3, t), lerp(grips[k - 1], grips[k], t)))
    return out


def paint_band(buf, samples, s0, s1, lmax, width, taper=1.2):
    """samples(오래된 → 새것) 를 s0..s1 로 매겨 칼끝에서 손잡이 쪽으로 폭 w(s) 의 띠를 칠한다."""
    m = len(samples)
    for i, (tip, grip) in enumerate(samples):
        s = s0 + (s1 - s0) * (i / max(1, m - 1))
        w = lmax * width * (0.10 + 0.90 * (s ** taper))
        dx, dy = grip[0] - tip[0], grip[1] - tip[1]
        L = math.hypot(dx, dy) or 1.0
        reach = min(L * 0.92, w)
        ux, uy = dx / L, dy / L
        k = max(2, int(reach * 2))
        for j in range(k + 1):
            r = (j / k) * reach                       # 칼끝에서 안쪽으로
            e = 1.0 - (r / reach if reach > 0 else 0)
            x, y = tip[0] + ux * r, tip[1] + uy * r
            buf.put(x, y, s, e)
            buf.put(x + 0.5, y, s, e)
            buf.put(x, y + 0.5, s, e)


def paint_thrust(buf, tip, grip, lmax, length, head_w, fwd=0.0):
    """찌름 줄기: 칼끝(머리)에서 칼 반대쪽으로 length 만큼 꼬리(폭 head_w → 1) + 칼끝 앞 fwd 만큼 뾰족한 찌름 끝."""
    dx, dy = tip[0] - grip[0], tip[1] - grip[1]
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    k = int((length + fwd) * 2)
    for j in range(k + 1):
        d = j / k * (length + fwd) - fwd           # d < 0 = 칼끝 앞
        if d < 0:
            s = 1.0
            hw = head_w * max(0.0, 1.0 - (-d / fwd)) ** 0.7 if fwd else 0
        else:
            s = max(0.0, 1.0 - d / length)         # 머리 1 → 꼬리 0
            hw = max(0.6, head_w * (s ** 1.3))
        cx, cy = tip[0] - ux * d, tip[1] - uy * d
        m = int(hw * 2) + 1
        for q in range(-m, m + 1):
            o = q / 2.0
            if abs(o) > hw:
                continue
            e = 1.0 - abs(o) / (hw + 0.01)
            buf.put(cx + nx * o, cy + ny * o, s, e)


def render(buf, ramp, glow, fade=1.0, dissolve=0.0, seed=0):
    """버퍼 → RGBA. glow 칸이면 흰 끝(램프 마지막 칸)과 X0 날선 허용."""
    im = Image.new("RGBA", (buf.w, buf.h), (0, 0, 0, 0))
    px = im.load()
    top = len(ramp) - (1 if glow else 2)              # glow 밖은 흰 끝 칸 금지
    sub = ramp[:top + 1]
    for y in range(buf.h):
        for x in range(buf.w):
            s = buf.s[y][x]
            if s < 0:
                continue
            e = buf.e[y][x]
            b = bayer(x + seed, y)
            # 꼬리 부서짐: s 가 작을수록 듬성(꼬리 25% 구간)
            if s < 0.28 and b > (s / 0.28) ** 0.8:
                continue
            # 안쪽 가장자리 부서짐
            if e < 0.18 and b > e / 0.18 + 0.15:
                continue
            if dissolve:
                # 2×2 덩어리 잡음으로 부서짐(망점 대신 조각)
                hsh = ((x >> 1) * 73856093 ^ (y >> 1) * 19349663 ^ seed * 83492791) & 1023
                if hsh / 1023.0 < dissolve * (1.2 - 0.5 * s):
                    continue
            v = (0.14 + 0.46 * (s ** 0.9) + 0.40 * (e ** 2.2)) * fade
            if fade < 1.0:
                v = max(v, 0.42)
            if e > 0.9 and s > 0.45:
                v += 0.12
            c = ramp_pick(sub, v, x, y)
            if glow and s > 0.9 and e > 0.93:
                c = X0
            px[x, y] = c + (255,)
    # 먹빛 안쪽 테 1도트(밝은 바닥 위 가독성): 칠한 칸 바로 안쪽(손잡이 쪽)의 빈 칸이 아니라, 칠한 칸 중 e 가 가장 낮은 경계
    dark = ramp[1]
    for y in range(buf.h):
        for x in range(buf.w):
            if px[x, y][3] and buf.e[y][x] < 0.1 and buf.s[y][x] > 0.3:
                px[x, y] = dark + (255,)
    return im


def build_move(name, cfg, preview=False):
    wm, wg = load_grid("weapons/v3/" + name)
    fw, fh = wm["frameWidth"], wm["frameHeight"]
    n = wm["frames"]
    dirs = wm["directions"]
    glow_frames = set(wm.get("glowFrames", []))
    frames, head, tail = [], {}, {}
    drawn = set()
    for d in dirs:
        tips = wm["bladeTipAnchors"][d]
        grips = wm["gripAnchors"][d]
        lmax = max(math.dist(t, g) for t, g in zip(tips, grips) if t)
        head[d], tail[d] = [None] * n, [None] * n
        row = []
        for f in range(n):
            buf = Buf(fw, fh)
            fade, dissolve, active = 1.0, 0.0, False
            if "thrust" in cfg and f in cfg["thrust"] + cfg["decay"]:
                i = (cfg["thrust"] + cfg["decay"]).index(f)
                length = [0.8, 1.35, 1.15, 0.85][i] * lmax
                hw = [4.5, 7.5, 6.0, 4.0][i]
                fwd = [0.12, 0.38, 0.22, 0.0][i] * lmax
                if f in cfg["decay"]:
                    fade, dissolve = 0.6, 0.45
                paint_thrust(buf, tips[f], grips[f], lmax, length, hw, fwd)
                active = True
                head[d][f] = list(tips[f])
                ux = tips[f][0] - grips[f][0]; uy = tips[f][1] - grips[f][1]; L = math.hypot(ux, uy) or 1
                tail[d][f] = [round(tips[f][0] - ux / L * length, 1), round(tips[f][1] - uy / L * length, 1)]
            elif "sweep" in cfg:
                sw = [k for k in cfg["sweep"] if tips[k] and tips[k - 1] and math.dist(tips[k], tips[k - 1]) >= MIN_MOVE]
                if f in cfg["sweep"] and f in sw:
                    prev = f - 1 in sw
                    if prev:
                        paint_band(buf, sweep_samples(tips, grips, f - 1, 40), 0.0, 0.38, lmax, cfg["width"])
                        paint_band(buf, sweep_samples(tips, grips, f, 60), 0.38, 1.0, lmax, cfg["width"])
                    else:
                        paint_band(buf, sweep_samples(tips, grips, f, 70), 0.0, 1.0, lmax, cfg["width"])
                    active = True
                    head[d][f] = list(tips[f])
                    tail[d][f] = list(tips[f - 2] if prev else tips[f - 1])
                elif f in cfg["decay"] and sw:
                    i = cfg["decay"].index(f)
                    last = sw[-1]
                    prev = last - 1 in sw
                    # 사라지는 칸: 마지막 휘두름 자리에 남아 가늘어지며 식는다(칼날에서 떨어져 나감 — 머리 쪽 s 를 깎음)
                    cut = [0.82, 0.62][min(i, 1)]
                    if prev:
                        paint_band(buf, sweep_samples(tips, grips, last - 1, 40), 0.0, 0.38 * cut, lmax, cfg["width"] * 0.8)
                    paint_band(buf, sweep_samples(tips, grips, last, 60)[:int(60 * cut)], 0.38 * cut if prev else 0.0, cut,
                               lmax, cfg["width"] * 0.8)
                    fade, dissolve = [0.72, 0.5][min(i, 1)], [0.3, 0.6][min(i, 1)]
                    active = True
                    pts = sweep_samples(tips, grips, last, 60)
                    head[d][f] = [round(v, 1) for v in pts[int(59 * cut)][0]]
                    tail[d][f] = list(tips[last - 2] if prev else tips[last - 1])
            if active:
                im = render(buf, cfg["ramp"], f in glow_frames, fade, dissolve, seed=f)
                drawn.add(f)
            else:
                im = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
            row.append(im)
        frames.extend(row)
    smear_frames = sorted(drawn)
    meta = {
        "directions": dirs,
        "layout": wm.get("layout", "rows = directions, columns = frames"),
        "pivot": wm["pivot"],
        "playerFrameOffset": wm.get("playerFrameOffset"),
        "anchor": "player_pivot",
        "overlayOf": "weapons/v3/" + name,
        "sameFrameAs": "weapons/v3/" + name,
        "overlay": f"player_{name} · weapons/v3/{name} 와 **같은 프레임 번호를 같은 시각에** 겹친다(같은 틀 {fw}×{fh}·피벗·"
                   "playerFrameOffset·방향 행). 휘두름 궤적의 원점이 칼날에 붙어 있도록 칼끝 좌표에서 그렸다.",
        "depth": wm.get("depth"),
        "depthRule": "무기 오버레이 바로 아래(같은 depth 규칙의 무기 직전). 무기가 몸 뒤로 가는 방향 행이면 스미어도 몸 뒤.",
        "blendMode": "NORMAL",
        "drawOver": "lightmap",
        "dirTransform": wm.get("dirTransform", "drawn4"),
        "smearFrames": smear_frames,
        "sweepFrames": cfg.get("sweep") or cfg.get("thrust"),
        "decayFrames": cfg["decay"],
        "glowFrames": sorted(glow_frames & set(smear_frames)),
        "impactFrame": wm.get("impactFrame"),
        "hitFrames": wm.get("hitFrames"),
        "timingMs": wm.get("timingMs"),
        "bladeTipAnchors": wm["bladeTipAnchors"],
        "gripAnchors": wm["gripAnchors"],
        "smearHeadAnchors": head,
        "smearTailAnchors": tail,
        "anchorNote": "좌표는 모두 이 시트(= 무기 시트) 원 프레임 도트. 주인공 피벗 기준 = (x − pivot.x, y − pivot.y) × pixelScale 0.5 → 논리 px. "
                      "bladeTipAnchors = 칼끝(무기 시트 값 그대로). smearHeadAnchors = 그 칸 스미어 머리(휘두름 칸 = 칼끝, 사라짐 칸 = 칼에서 떨어진 머리), "
                      "smearTailAnchors = 그 칸 스미어 꼬리 끝(가장 오래된 칼끝). null = 그 칸에 스미어 없음.",
        "systemHint": "P1-2 시스템: 칼끝 리본(feel.ribbon)·궤적 원점을 bladeTipAnchors 로 옮기고, 기존 떨어진 호 fx(" + name +
                      ") 는 끄거나 알파 0.35 이하로 낮춰 스미어와 겹침을 줄이길 권장(판정·히트 불티는 그대로).",
        "weapon": cfg["weapon"],
        "comboHit": cfg["hit"],
        "weaponColor": {"katana": "서리 #8fe3ff(흰 끝 #e6fcff 는 판정 칸만)", "greatsword": "용암 #ff5a2a(흰 끝 #ffd496 는 판정 칸만)"}[cfg["weapon"]],
        "palette": "무기 색 램프(계약 §28, color61s6 ramps) + 판정 칸 X0 날선 — 새 색 없음. paletteSwap none",
        "paletteSwap": "none",
        "version": "v3-r62b",
        "source": SRC + " · smear.py",
        "design": "칼끝에서 시작하는 굵은 스미어 — 머리(지금 칼날)가 가장 굵고 밝으며 꼬리로 갈수록 가늘고 식어 부서진다. "
                  + ("찌르기는 칼끝 뒤로 끄는 찌름 줄기." if "thrust" in cfg else "사라짐 칸은 칼에서 떨어져 제자리에서 식는다."),
    }
    b2.write_sheet("fx", name + "_smear", frames, fw, fh, meta, rows=len(dirs),
                   durations=list(wm["frameDurationsMs"]), loop=False)
    return frames, wm, smear_frames


def build_all():
    out = {}
    for name, cfg in MOVES.items():
        out[name] = build_move(name, cfg)
    return out


def preview(out, path):
    from PIL import Image as I
    from common import board
    items = []
    for name, (frames, wm, sf) in out.items():
        bm, bg = load_grid("player/v3/player_" + name)
        wmeta, wg = load_grid("weapons/v3/" + name)
        fw, fh = wmeta["frameWidth"], wmeta["frameHeight"]
        n = wmeta["frames"]
        dirs = wmeta["directions"]
        for r, d in enumerate(dirs[:4]):
            cols = list(range(max(0, sf[0] - 1), min(n, sf[-1] + 2)))
            strip = I.new("RGBA", (len(cols) * fw, fh), (52, 46, 40, 255))
            for i, c in enumerate(cols):
                ox = i * fw
                body = cell(bm, bg, r, c)
                strip.alpha_composite(body, (ox + wmeta["pivot"]["x"] - bm["pivot"]["x"], wmeta["pivot"]["y"] - bm["pivot"]["y"]))
                strip.alpha_composite(frames[r * n + c], (ox, 0))
                strip.alpha_composite(cell(wmeta, wg, r, c), (ox, 0))
            items.append(strip)
    board(items, k=1, max_w=2600).save(path)
