"""E1 미리보기 — assets 산출물을 읽어 합성(빌드 결과 그대로 확인).

  preview_<동작>_x2.png   행 = 방향, 열 = 프레임 (몸+무기+fx 합성, 노란 테 = 판정 프레임, 파란 테 = 유지/이동 프레임)
  gif/<동작>.gif          방향 격자 애니메이션(1배 = 게임 화면 도트 크기의 2배 표시 · fx 포함 · 이동/공중 오프셋 반영)
"""
import json
import math
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
SPR = os.path.join(ROOT, "assets/sprites")
GIF = os.path.join(HERE, "gif")
BG = (30, 30, 35, 255)
FLOOR = (46, 42, 40, 255)
DEG = {"right": 0.0, "down-right": 45.0, "down": 90.0, "down-left": 135.0, "left": 180.0, "up-left": -135.0, "up": -90.0, "up-right": -45.0}
GRID8 = [["up-left", "up", "up-right"], ["left", None, "right"], ["down-left", "down", "down-right"]]
GRID4 = [[None, "up", None], ["left", None, "right"], [None, "down", None]]
_cache = {}


def load(path):
    if path not in _cache:
        j = json.load(open(os.path.join(SPR, path + ".json"), encoding="utf-8"))
        im = Image.open(os.path.join(SPR, path + ".png")).convert("RGBA")
        _cache[path] = (j, im)
    return _cache[path]


def cell(path, row, i):
    j, im = load(path)
    dirs = j["directions"]
    r = dirs.index(row) if row in dirs else 0
    fw, fh = j["frameWidth"], j["frameHeight"]
    i = min(i, j["frames"] - 1)
    return im.crop((i * fw, r * fh, (i + 1) * fw, (r + 1) * fh)), (j["pivot"]["x"], j["pivot"]["y"])


def paste(canvas, im, piv, at):
    canvas.alpha_composite(im, (int(round(at[0] - piv[0])), int(round(at[1] - piv[1]))))


def frame_at(ms, t):
    acc = 0
    for i, m in enumerate(ms):
        acc += m
        if t < acc:
            return i
    return None


def starts(ms):
    s, t = [], 0
    for m in ms:
        s.append(t)
        t += m
    return s


def air(bj, i):
    a = bj.get("airOffsetPx")
    if not a:
        return 0
    return a["byFrame"][i]


def player(canvas, move, d, i, at):
    bj, _ = load("player/v3/player_" + move)
    up = air(bj, i)
    b, bp = cell("player/v3/player_" + move, d, i)
    w, wp = cell("weapons/v3/" + move, d, i)
    paste(canvas, b, bp, (at[0], at[1] - up))
    paste(canvas, w, wp, (at[0], at[1] - up))


def fx_cell(canvas, name, row, i, at):
    if not os.path.exists(os.path.join(SPR, "fx/v3/" + name + ".json")):
        return
    im, piv = cell("fx/v3/" + name, row, i)
    paste(canvas, im, piv, at)


def sheet_preview(move, fx=None, scale=2, out=None):
    bj, _ = load("player/v3/player_" + move)
    wj, _ = load("weapons/v3/" + move)
    dirs = bj["directions"]
    n = bj["frames"]
    fw, fh = wj["frameWidth"], wj["frameHeight"]
    cw, ch = fw, fh + max([0] + (bj.get("airOffsetPx") or {"byFrame": [0]})["byFrame"])
    piv = (wj["pivot"]["x"], wj["pivot"]["y"] + (ch - fh))
    W, H = 70 + cw * n, 24 + ch * len(dirs)
    c = Image.new("RGBA", (W, H), BG)
    dr = ImageDraw.Draw(c)
    st = starts(bj["frameDurationsMs"])
    act = set(bj.get("activeFrames") or [])
    hold = set(bj.get("holdFrames") or []) | set(bj.get("dashFrames") or [])
    dr.text((4, 4), "%s  %d frames  ms %s  hitAt %s  (yellow = active, blue = hold/dash)" % (
        move, n, bj["frameDurationsMs"], (bj.get("timingMs") or {}).get("hitAt")), fill=(220, 220, 220, 255))
    fstart = None
    if fx:
        fj, _ = load("fx/v3/" + fx)
        fstart = fj.get("spawnAtMs", 0)
    for r, d in enumerate(dirs):
        dr.text((4, 24 + r * ch + ch // 2), d, fill=(200, 200, 200, 255))
        for i in range(n):
            x0, y0 = 70 + i * cw, 24 + r * ch
            at = (x0 + piv[0], y0 + piv[1])
            dr.rectangle((x0, y0 + ch - (fh - wj["pivot"]["y"]) - 2, x0 + cw - 1, y0 + ch - 1), fill=FLOOR)
            player(c, move, d, i, at)
            if fx:
                fj, _ = load("fx/v3/" + fx)
                k = frame_at(fj["frameDurationsMs"], st[i] - fstart) if st[i] >= fstart else None
                if k is not None:
                    fx_cell(c, fx, d, k, at)
            col = (230, 190, 60, 255) if i in act else (90, 140, 230, 255) if i in hold else (70, 70, 80, 255)
            dr.rectangle((x0, y0, x0 + cw - 1, y0 + ch - 1), outline=col)
            dr.text((x0 + 3, y0 + 3), "%d %dms" % (i, bj["frameDurationsMs"][i]), fill=(160, 160, 170, 255))
    if scale != 1:
        c = c.resize((W * scale, H * scale), Image.NEAREST)
    c.save(out or os.path.join(HERE, "preview_%s_x%d.png" % (move, scale)))
    return c


def move_offset(bj, t, d):
    """시스템 이동 근사(그림 확인용): dashPx/stepPx 를 해당 구간 동안 선형으로."""
    a = math.radians(DEG[d])
    ux, uy = math.cos(a), math.sin(a)
    dist = 0.0
    for key in ("dashPx", "stepPx", "dragStepPx", "leapPx"):
        m = bj.get(key)
        if not m or "frames" not in m:
            continue
        st = starts(bj["frameDurationsMs"])
        f0, f1 = m["frames"][0], m["frames"][-1]
        t0, t1 = st[f0], st[f1] + bj["frameDurationsMs"][f1]
        u = max(0.0, min(1.0, (t - t0) / max(1, t1 - t0)))
        dist += m["dots"] * u * 0.5          # 도트 → 미리보기 화면(도트 0.5 = 논리 px)
    sx = sy = 0.0
    sp = bj.get("sidestepPx")
    if sp:
        st = starts(bj["frameDurationsMs"])
        f0, f1 = sp["frames"][0], sp["frames"][-1]
        t0, t1 = st[f0], st[f1] + bj["frameDurationsMs"][f1]
        u = max(0.0, min(1.0, (t - t0) / max(1, t1 - t0)))
        sx, sy = uy * sp["dots"] * u * 0.5, -ux * sp["dots"] * u * 0.5
    return ux * dist + sx, uy * dist + sy


def half(im):
    return im.resize((max(1, im.width // 2), max(1, im.height // 2)), Image.NEAREST)


def anim_gif(move, fxs=(), cw=300, ch=260, step=20, loops=1, holdloop=0, out=None, scale=2, title=""):
    """fxs = [(fx 이름, 'world'|'player', 시작 ms 키 또는 숫자)] — 게임 화면 크기(도트 0.5)로 합성 후 scale 배."""
    bj, _ = load("player/v3/player_" + move)
    dirs = bj["directions"]
    grid = GRID8 if len(dirs) == 8 else GRID4
    ms = list(bj["frameDurationsMs"])
    seq = list(range(len(ms)))
    hf = bj.get("holdFrames") or bj.get("loopFrames")
    if hf and holdloop:
        i0 = seq.index(hf[0])
        seq = seq[:i0] + hf * (holdloop + 1) + seq[hf[-1] + 1:]
    tl, t = [], 0
    for i in seq:
        tl.append((t, i))
        t += ms[i]
    total = t
    # 원래 시트 시각(fx 시작 · 이동)으로 바꾸기
    st = starts(ms)

    def sheet_t(T):
        """재생 시각 → (원래 시트 시각, 프레임). 유지 루프 반복 동안은 시트 시각이 그 프레임 안에 머문다."""
        for k in range(len(tl) - 1, -1, -1):
            if T >= tl[k][0]:
                i = tl[k][1]
                return st[i] + min(T - tl[k][0], ms[i] - 1), i
        return 0, 0
    frames = []
    for T in range(0, total + 300, step):
        c = Image.new("RGBA", (cw * 3, ch * 3 + 16), BG)
        dr = ImageDraw.Draw(c)
        dr.text((4, 2), title or move, fill=(220, 220, 220, 255))
        TT = min(T, total - 1)
        s_t, fi = sheet_t(TT)
        for gy, rowd in enumerate(grid):
            for gx, d in enumerate(rowd):
                if d is None:
                    continue
                ox, oy = gx * cw, 16 + gy * ch
                a = math.radians(DEG[d])
                base = (ox + cw / 2 - math.cos(a) * 40, oy + ch * 0.62 - math.sin(a) * 30)
                dx, dy = move_offset(bj, s_t, d)
                tmp = Image.new("RGBA", (cw * 2, ch * 2), (0, 0, 0, 0))
                at2 = (base[0] * 2 - ox * 2 + 0, base[1] * 2 - oy * 2)
                for fx in fxs:
                    name, anchor, start = fx[:3]
                    fwd = fx[3] if len(fx) > 3 else 0
                    fj, _ = load("fx/v3/" + name)
                    s0 = fj.get(start, 0) if isinstance(start, str) else start
                    k = frame_at(fj["frameDurationsMs"], s_t - s0) if s_t >= s0 else None
                    if k is None:
                        continue
                    if anchor == "world":
                        ax, ay = at2
                        if "spawnMoveOffset" in fj:
                            ddx, ddy = move_offset(bj, s0, d)
                            ax, ay = ax + ddx * 2, ay + ddy * 2
                    else:
                        ax, ay = at2[0] + dx * 2, at2[1] + dy * 2
                    if fj.get("depth") == "below_player":
                        fx_cell(tmp, name, d, k, (ax, ay))
                player(tmp, move, d, fi, (at2[0] + dx * 2, at2[1] + dy * 2))
                for fx in fxs:
                    name, anchor, start = fx[:3]
                    fwd = fx[3] if len(fx) > 3 else 0
                    fj, _ = load("fx/v3/" + name)
                    if fj.get("depth") == "below_player":
                        continue
                    s0 = fj.get(start, 0) if isinstance(start, str) else start
                    k = frame_at(fj["frameDurationsMs"], s_t - s0) if s_t >= s0 else None
                    if k is None:
                        continue
                    if anchor == "world":
                        ax, ay = at2
                    else:
                        ax, ay = at2[0] + dx * 2, at2[1] + dy * 2
                    ax, ay = ax + math.cos(a) * fwd, ay + math.sin(a) * fwd
                    fx_cell(tmp, name, d, k, (ax, ay))
                c.alpha_composite(half(tmp), (ox, oy))
                dr.text((ox + 4, oy + 4), d, fill=(120, 120, 130, 255))
        dr.text((cw * 3 - 120, 2), "t=%4d f%d" % (T, fi), fill=(160, 160, 170, 255))
        if scale != 1:
            c = c.resize((c.width * scale, c.height * scale), Image.NEAREST)
        frames.append(c.convert("P", palette=Image.ADAPTIVE, colors=255))
    os.makedirs(GIF, exist_ok=True)
    p = out or os.path.join(GIF, move + ".gif")
    frames[0].save(p, save_all=True, append_images=frames[1:], duration=step, loop=0, disposal=2)
    return p


# =============================================================================
# 전체 미리보기
# =============================================================================
SHEETS = [("katana_counter", "katana_counter"), ("katana_iai", "katana_iai"), ("greatsword_tackle", "greatsword_tackle"),
          ("greatsword_brace_upswing", "greatsword_brace_upswing"), ("greatsword_leap_slam", None), ("greatsword_guard_rush", None)]
GIFS = [
    ("katana_counter", [("katana_counter", "player", "spawnAtMs")], 0, "katana_counter 간파 반격 (패링 받은 자세 → 흘림 → 반격)"),
    ("katana_iai", [("katana_iai", "world", "spawnAtMs")], 1, "katana_iai 대치 일격 (유지 루프 2회 → 뗌 → 발도 → 납도 딸깍에 터짐)"),
    ("greatsword_tackle", [("greatsword_tackle", "player", "spawnAtMs")], 0, "greatsword_tackle 어깨 태클 (돌진 40 월드 px)"),
    ("greatsword_brace_upswing", [("greatsword_brace_upswing", "player", "spawnAtMs"), ("greatsword_brace_absorb", "player", 150)], 0,
     "greatsword_brace_upswing 버티기 올려베기 (150ms 에 피격 가정 — 재 튐)"),
    ("greatsword_leap_slam", [("greatsword_leap_slam", "world", "spawnAtMs"), ("greatsword_leap_slam_land", "player", "spawnAtMs"),
                              ("greatsword_ground_crack", "player", 410, 265)], 0, "greatsword_leap_slam 공중제비 도약 찍기 (도약 48 월드 px · 균열 m 행)"),
    ("greatsword_guard_rush", [("greatsword_guard_rush", "world", "spawnAtMs")], 0, "greatsword_guard_rush 막다가 떼면 돌진 (돌진 56 월드 px)"),
]


def main(names=None):
    for move, fx in SHEETS:
        if names and move not in names:
            continue
        sheet_preview(move, fx=fx, scale=2 if move.startswith("katana") else 1)
    for move, fxs, hl, title in GIFS:
        if names and move not in names:
            continue
        anim_gif(move, fxs, holdloop=hl, title=title)
    ember_gif()


def ember_gif(out=None):
    """울분 판 비교: 평소 / 잔불 — down-right · right."""
    return anim_gif("greatsword_brace_upswing", [("greatsword_brace_upswing_ember", "player", "spawnAtMs")],
                    out=os.path.join(GIF, "greatsword_brace_upswing_ember.gif"), title="greatsword_brace_upswing 울분 판(_ember)")
