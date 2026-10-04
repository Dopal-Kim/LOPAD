"""58라운드 미리보기 — parts/art/work/combo58/preview/ 에 PNG·GIF.

  thrust_ki_<dir>.gif / thrust_ki.png      칼 3타 찌르기 검기 0~3단(몸+무기+검기 오버레이+fx) 나란히
  issen_dash.gif                           대쉬 일섬(시작 f0~f2 대쉬 연결) — 4방향
  charge_swing_8dir.gif / .png             대검 차지 휘둘러 내리찍기 8방향(몸+무기+붓획+땅 충격+균열 선, 3단 = 5칸)
  charge_swing_stages.png                  균열 선 t1~t5 · 차지 단계 3/4/5칸
  diag_<sheet>.png                         대검 대각 4행 56 → 58 전후 비교(10시트 + charge_swing 은 58만)
  diag_cmp_<sheet>.gif                     대각 전후 비교 움직임(왼쪽 56 · 오른쪽 58)
"""
import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import peek  # noqa: E402
from peek import BG  # noqa: E402

OUT = os.path.join(HERE, "preview")
ANG = {"right": 0, "down-right": 45, "down": 90, "down-left": 135, "left": 180, "up-left": -135, "up": -90, "up-right": -45}


def label(im, text, xy=(4, 4)):
    ImageDraw.Draw(im).text(xy, text, fill=(255, 214, 140, 255))
    return im


def rot_fx(cell, pivot, deg):
    """회전 fx 칸 → (회전된 RGBA, 회전 뒤 pivot 위치)."""
    w, h = cell.size
    big = Image.new("RGBA", (w * 3, h * 3), (0, 0, 0, 0))
    big.paste(cell, (w, h))
    c = (w + pivot[0], h + pivot[1])
    r = big.rotate(-deg, resample=Image.NEAREST, center=c)
    bb = r.getbbox()
    if not bb:
        return r.crop((0, 0, 1, 1)), (0, 0)
    return r.crop(bb), (c[0] - bb[0], c[1] - bb[1])


# =============================================================================
def thrust(dirs=("right", "down", "left", "up")):
    names = ["katana_thrust", "katana_thrust_ki1", "katana_thrust_ki2", "katana_thrust_ki3"]
    bm, _ = peek.load("player/v3/player_katana_thrust")
    times = list(range(160, 640, 20))
    pngrows = []
    for d in dirs:
        cw, ch = (440, 170) if d in ("left", "right") else (200, 400)
        piv = {"right": (70, 150), "left": (370, 150), "down": (100, 110), "up": (100, 380)}[d]
        cols = []
        for lv, n in enumerate(names):
            fm, _ = peek.load("fx/v3/" + n)
            ov = None if lv == 0 else "weapons/v3/katana_thrust_ki%d" % lv
            fr = peek.timeline("player/v3/player_katana_thrust", "weapons/v3/katana_thrust", [("fx/v3/" + n, fm["spawnAtMs"], None, (0, 0))],
                               d=d, times=times, canvas=(cw, ch), piv=piv, overlay=ov)
            cols.append([label(f, "ki%d" % lv) for f in fr])
        frames = []
        for k in range(len(times)):
            if d in ("left", "right"):
                g = Image.new("RGBA", (cw, ch * 4), BG)
                for lv in range(4):
                    g.paste(cols[lv][k], (0, lv * ch))
            else:
                g = Image.new("RGBA", (cw * 4, ch), BG)
                for lv in range(4):
                    g.paste(cols[lv][k], (lv * cw, 0))
            frames.append(g)
        peek.save_gif(frames, os.path.join(OUT, "thrust_ki_%s.gif" % d), 40, 2)
        # 판정 순간(260ms) 정지 그림
        pngrows.append(frames[times.index(260)])
    w = sum(r.width for r in pngrows)
    h = max(r.height for r in pngrows)
    s = Image.new("RGBA", (w, h), BG)
    x = 0
    for r in pngrows:
        s.paste(r, (x, 0))
        x += r.width
    s.resize((s.width * 2, s.height * 2), Image.NEAREST).save(os.path.join(OUT, "thrust_ki.png"))
    return ["thrust_ki.png"] + ["thrust_ki_%s.gif" % d for d in dirs]


def issen_dash():
    bm, _ = peek.load("player/v3/player_katana_issen_dash")
    ms = bm["frameDurationsMs"]
    times = list(range(0, sum(ms), 20))
    frames = []
    dash = bm["dash"]
    for t in times:
        row = []
        for d in ("down", "up", "left", "right"):
            # 몸 이동(돌진) 반영: 출발 피벗에서 진행
            dx = {"right": 1, "left": -1, "down": 0, "up": 0}[d]
            dy = {"down": 1, "up": -1, "right": 0, "left": 0}[d]
            u = max(0.0, min(1.0, (t - dash["startMs"]) / (dash["endMs"] - dash["startMs"])))
            dist = 64 * u                             # 월드 64 px = 화면 2배 기준 표시 64 px(미리보기 축소)
            cw, ch = 260, 260
            base = (130 - dx * 32, 170 - dy * 40)
            line_spawn = dash["startMs"]
            f = peek.timeline("player/v3/player_katana_issen_dash", "weapons/v3/katana_issen_dash",
                              [("fx/v3/katana_issen_line_t1_solo", line_spawn, d, (-dx * dist, -dy * dist))], d=d, times=[t],
                              canvas=(cw, ch), piv=(int(base[0] + dx * dist), int(base[1] + dy * dist)))[0]
            row.append(label(f, "%s %dms" % (d, t)))
        g = Image.new("RGBA", (260 * 4, 260), BG)
        for i, f in enumerate(row):
            g.paste(f, (i * 260, 0))
        frames.append(g)
    peek.save_gif(frames, os.path.join(OUT, "issen_dash.gif"), 40, 1)
    # 시작 f0~f3 정지 비교(일섬 · 대쉬 일섬)
    rows = []
    for n in ("katana_issen", "katana_issen_dash"):
        rows.append(label(peek.compose("player/v3/player_" + n, "weapons/v3/" + n, scale=1, label=False).crop((0, 0, 192 * 5, 192 * 4)), n))
    peek.grid(rows, 2).save(os.path.join(OUT, "issen_dash_start.png"))
    return ["issen_dash.gif", "issen_dash_start.png"]


# =============================================================================
def swing_frames(d, stage=3, times=None, cw=520, ch=520):
    bm, _ = peek.load("player/v3/player_greatsword_charge_swing")
    ms = bm["frameDurationsMs"]
    hit = bm["timingMs"]["hitAt"]
    imp = bm["impactFrame"]
    times = times or list(range(0, sum(ms) + 200, 10))
    tiles = bm["crackLine"]["maxTilesByStage"][stage - 1]
    cm, ci = peek.load("fx/v3/greatsword_charge_crack_line_t%d" % tiles)
    cc = peek.cells(cm, ci)["any"]
    gm, gi = peek.load("fx/v3/greatsword_ground_crack")
    gc = peek.cells(gm, gi)
    grow = {1: "m", 2: "m", 3: "l"}[stage]
    slam = bm["slamAnchors"][d][imp]
    sm, _ = peek.load("fx/v3/greatsword_charge_swing")
    piv = (cw // 2, ch // 2 + 40)
    ang = ANG[d]

    def extra(im, t):
        ft = t - hit
        if ft < 0:
            return
        k = peek.frame_at(cm["frameDurationsMs"], ft)
        k2 = peek.frame_at(gm["frameDurationsMs"], ft)
        sx = piv[0] - bm["pivot"]["x"] + slam[0]
        sy = piv[1] - bm["pivot"]["y"] + slam[1]
        layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
        if k2 is not None:
            g = gc[grow][k2]
            layer.alpha_composite(g, (int(sx - gm["pivot"]["x"]), int(sy - gm["pivot"]["y"])))
        if k is None:
            k = len(cc) - 1
        r, p = rot_fx(cc[k], (cm["pivot"]["x"], cm["pivot"]["y"]), ang)
        layer.alpha_composite(r, (int(sx - p[0]), int(sy - p[1])))
        # 바닥 fx 는 몸 아래처럼 보이게 — 이미 몸이 그려진 위라 간단히 위에(미리보기)
        im.alpha_composite(layer)

    fr = peek.timeline("player/v3/player_greatsword_charge_swing", "weapons/v3/greatsword_charge_swing",
                       [("fx/v3/greatsword_charge_swing", sm["spawnAtMs"], None, (0, 0))], d=d, times=times, canvas=(cw, ch), piv=piv,
                       overlay=None, extra=extra)
    return fr, times


def swing8():
    order = [["up-left", "up", "up-right"], ["left", None, "right"], ["down-left", "down", "down-right"]]
    cw = ch = 520
    per = {}
    times = None
    for row in order:
        for d in row:
            if d:
                per[d], times = swing_frames(d, 3, times, cw, ch)
    frames = []
    for k in range(len(times)):
        g = Image.new("RGBA", (cw * 3, ch * 3), BG)
        for r, row in enumerate(order):
            for c, d in enumerate(row):
                if d:
                    g.paste(label(per[d][k].copy(), "%s %dms" % (d, times[k])), (c * cw, r * ch))
                else:
                    label(g, "greatsword_charge_swing\n3단(균열 5칸)", (c * cw + 160, r * ch + 250))
        frames.append(g)
    peek.save_gif(frames[::2], os.path.join(OUT, "charge_swing_8dir.gif"), 40, 1)
    bm, _ = peek.load("player/v3/player_greatsword_charge_swing")
    hit = bm["timingMs"]["hitAt"]
    pick = [times.index(t) for t in (40, 160, 260, hit, hit + 100, hit + 220)]
    rows = []
    for d in ("down", "down-right", "right", "up-right", "up", "up-left", "left", "down-left"):
        rows.append(peek.strip([label(per[d][i].crop((60, 40, 460, 440)).copy(), "%s %dms" % (d, times[i])) for i in pick]))
    peek.grid(rows, 1).save(os.path.join(OUT, "charge_swing_8dir.png"))
    return ["charge_swing_8dir.gif", "charge_swing_8dir.png"]


def swing_stages():
    bm, _ = peek.load("player/v3/player_greatsword_charge_swing")
    hit = bm["timingMs"]["hitAt"]
    rows = []
    for st in (1, 2, 3):
        fr, _ = swing_frames("right", st, [hit + 60, hit + 140, hit + 220, hit + 420], 640, 300)
        rows.append(peek.strip([label(f, "stage %d (%d tiles) +%dms" % (st, bm["crackLine"]["maxTilesByStage"][st - 1], t - hit))
                                for f, t in zip(fr, [hit + 60, hit + 140, hit + 220, hit + 420])]))
    # t1~t5 시트 자체(가장 긴 칸)
    for n in (1, 2, 3, 4, 5):
        cm, ci = peek.load("fx/v3/greatsword_charge_crack_line_t%d" % n)
        cc = peek.cells(cm, ci)["any"]
        rows.append(peek.strip([label(Image.alpha_composite(Image.new("RGBA", c.size, BG), c), "") for c in cc]))
    peek.grid(rows, 2).save(os.path.join(OUT, "charge_swing_stages.png"))
    return ["charge_swing_stages.png"]


# =============================================================================
GS_SHEETS = ["greatsword_sweep_cw", "greatsword_cleave", "greatsword_sweep_ccw", "greatsword_charge", "greatsword_charge_slam",
             "greatsword_charge_plunge", "greatsword_tackle", "greatsword_brace_upswing", "greatsword_leap_slam", "greatsword_guard_rush"]


def diag(old_root):
    import cmp_diag
    out = []
    for n in GS_SHEETS:
        p = os.path.join(OUT, "diag_%s.png" % n)
        cmp_diag.make(old_root, n, p)
        out.append(os.path.basename(p))
    # 움직임 비교 GIF(연격 3종 · 차지 내려찍기 · 태클): 왼쪽 56 · 오른쪽 58, 대각 4행
    for n in ("greatsword_sweep_cw", "greatsword_cleave", "greatsword_charge_slam", "greatsword_brace_upswing"):
        a = cmp_diag.comp_rows(old_root, n, ["down-right", "down-left", "up-right", "up-left"])
        b = cmp_diag.comp_rows(os.path.join(peek.ROOT, "assets/sprites"), n, ["down-right", "down-left", "up-right", "up-left"])
        bm, _ = peek.load("player/v3/player_" + n)
        F = bm["frames"]
        cw = a.width // F
        frames, durs = [], []
        for i in range(F):
            g = Image.new("RGBA", (cw * 2 + 8, a.height), BG)
            g.paste(a.crop((i * cw, 0, (i + 1) * cw, a.height)), (0, 0))
            g.paste(b.crop((i * cw, 0, (i + 1) * cw, b.height)), (cw + 8, 0))
            label(g, "56", (4, 4)); label(g, "58 3/4", (cw + 12, 4))
            frames.append(g)
            durs.append(bm["frameDurationsMs"][i])
        fr = [f.convert("RGB") for f in frames]
        fr[0].save(os.path.join(OUT, "diag_cmp_%s.gif" % n), save_all=True, append_images=fr[1:], duration=durs, loop=0)
        out.append("diag_cmp_%s.gif" % n)
    return out


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    args = sys.argv[1:]
    res = []
    if not args or "thrust" in args:
        res += thrust()
    if not args or "issen" in args:
        res += issen_dash()
    if not args or "swing" in args:
        res += swing8() + swing_stages()
    if "diag" in args:
        res += diag(args[args.index("diag") + 1])
    print("\n".join(res))
