"""P19 미리보기 — 전/후 비교 GIF·띠 + 움직임 목업(눈빛 꼬리·대쉬 잔상·미끄럼 먼지).

출력(parts/art/work/hero19/):
  preview_<동작>_before_after.gif  위 = 이전(SRC_REV) · 아래 = 새 그림, 방향 right · down (몸 + 무기 오버레이)
  preview_sheets.png               새 시트 정지 띠(동작별 right 행)
  preview_mock_motion.gif          1배 목업: 달리기 → 대쉬(잔상·눈빛 꼬리) → 미끄럼 방향 전환(먼지) → 반대로 달리기 → 대기(불씨 숨결)
"""
import json
import os

from PIL import Image, ImageDraw

import body19 as B
import preview19 as V
import sync19 as S

HERE = B.HERE
BG = (34, 36, 42, 255)


def new_grid(rel):
    jp = os.path.join(S.GRID, rel + ".json")
    m = json.load(open(jp, encoding="utf-8"))
    return m, Image.open(jp[:-5] + ".png").convert("RGBA")


def cellof(m, im, d, c):
    r = m["directions"].index(d)
    return B.cell(m, im, r, c)


def comp(body_m, body_im, d, c, wrel_m=None, wrel_im=None, wcol=None):
    ov = []
    if wrel_m is not None:
        w = cellof(wrel_m, wrel_im, d, c if wcol is None else wcol)
        ov = [(w, (48 - wrel_m["pivot"]["x"], 138 - wrel_m["pivot"]["y"]))]
    return V.compose(cellof(body_m, body_im, d, c), ov, pad=64)


PAIRS = [  # (이름, 몸, 무기 오버레이)
    ("idle", "player_idle", "weapons/v3/katana_carry_idle"),
    ("walk", "player_walk", "weapons/v3/katana_carry_walk"),
    ("run", "player_run", "weapons/v3/katana_carry_run"),
    ("run_free_greatsword", "player_run_free", "weapons/v3/greatsword_carry_run"),
    ("dash", "player_dash", "weapons/v3/katana_carry_dash"),
    ("hurt", "player_hurt", None),
    ("death", "player_death", None),
    ("katana_rise", "player_katana_rise", "weapons/v3/katana_rise"),
    ("katana_fall", "player_katana_fall", "weapons/v3/katana_fall"),
    ("katana_thrust", "player_katana_thrust", "weapons/v3/katana_thrust"),
    ("greatsword_sweep_cw", "player_greatsword_sweep_cw", "weapons/v3/greatsword_sweep_cw"),
    ("greatsword_cleave", "player_greatsword_cleave", "weapons/v3/greatsword_cleave"),
    ("greatsword_sweep_ccw", "player_greatsword_sweep_ccw", "weapons/v3/greatsword_sweep_ccw"),
    ("dagger_combo1", "player_dagger_combo1", "weapons/v3/dagger_combo1"),
    ("dagger_combo2", "player_dagger_combo2", "weapons/v3/dagger_combo2"),
    ("dagger_combo3", "player_dagger_combo3", "weapons/v3/dagger_combo3"),
]


def before_after(name, body, wrel, dirs=("right", "down")):
    om, oim = S.src_grid("player/v3/" + body)
    nm, nim = new_grid("player/v3/" + body)
    wom = woim = wnm = wnim = None
    if wrel:
        wom, woim = S.src_grid(wrel)
        wnm, wnim = new_grid(wrel)
    # 시간축: 두 시트를 ms 로 맞춰 20ms 칸으로 표본(새 시트는 프레임 수가 다를 수 있음)
    def timeline(ms):
        t, out = 0, []
        for i, m in enumerate(ms):
            out.append((t, i))
            t += m
        return out, t
    to, To = timeline(om["frameDurationsMs"])
    tn, Tn = timeline(nm["frameDurationsMs"])
    T = max(To, Tn)
    frames, durs = [], []
    step = 20 if T < 1200 else 40
    for t in range(0, T, step):
        io = max([i for s, i in to if s <= t % To] or [0])
        inn = max([i for s, i in tn if s <= t % Tn] or [0])
        row_o = [comp(om, oim, d, io, wom, woim) for d in dirs]
        row_n = [comp(nm, nim, d, inn, wnm, wnim) for d in dirs]
        top = V.strip(row_o, 1)
        bot = V.strip(row_n, 1)
        img = V.stack([V.label(top, "before"), V.label(bot, "after (P19)")])
        frames.append(img)
        durs.append(step)
    V.gif(frames, durs, os.path.join(HERE, "preview_%s_before_after.gif" % name), scale=2)


# -----------------------------------------------------------------------------
# 움직임 목업(1배 화면 감각 — 도트 2배 표시)
# -----------------------------------------------------------------------------
def mock_motion():
    W, H = 720, 260
    ground = 200
    bodies = {n: new_grid("player/v3/" + n) for n in ("player_run", "player_dash", "player_turn_skid", "player_idle")}
    ovs = {n: new_grid("weapons/v3/katana_carry_" + n) for n in ("run", "dash", "turn_skid", "idle")}
    fx = {n: new_grid("fx/v3/" + n) for n in ("hero_eye_trail", "hero_dash_afterimage", "hero_skid_dust", "hero_ember_breath")}
    seq = []          # (몸, 동작, 방향, 프레임, ms, 이동 도트/프레임)
    for k in range(16):
        seq.append(("player_run", "run", "right", k % 8, 65, 25))
    for k in range(5):
        seq.append(("player_dash", "dash", "right", k, [30, 40, 60, 60, 50][k], [10, 30, 40, 40, 14][k]))
    for k in range(4):
        seq.append(("player_turn_skid", "turn_skid", "left", k, [40, 50, 50, 40][k], [8, 4, -4, -10][k]))
    for k in range(10):
        seq.append(("player_run", "run", "left", k % 8, 65, -25))
    for k in range(12):
        seq.append(("player_idle", "idle", "left", k % 6, [200, 200, 180, 220, 200, 220][k % 6], 0))
    x = 60.0
    live = []         # (fx 이름, 행, 시작 칸, 칸 범위, 위치 x, y, 남은 ms 목록 idx)
    frames, durs = [], []
    clock = 0
    for (body, act, d, c, ms, mv) in seq:
        x += mv
        bm, bim = bodies[body]
        om, oim = ovs[act]
        can = Image.new("RGBA", (W, H), BG)
        dr = ImageDraw.Draw(can)
        dr.rectangle((0, ground + 2, W, H), fill=(44, 46, 52, 255))
        # 새 fx 생성
        ey = bm.get("eyeAnchors", {}).get(d, [None] * 99)[c]
        if act in ("run", "dash") and ey:
            live.append(["hero_eye_trail", "any", 0, (0, 5), x - 48 + ey[0], ground - 138 + ey[1], 0, d == "left"])
        if act == "dash" and c in (1, 2, 3):
            live.append(["hero_dash_afterimage", d, 4 * (c - 1), (4 * (c - 1), 4 * (c - 1) + 3), x, ground, 0])
        if act == "turn_skid" and c == 0:
            live.append(["hero_skid_dust", d, 0, (0, 5), x, ground, 0])
        if act == "dash" and c == 4:
            live.append(["hero_skid_dust", d, 0, (0, 5), x, ground, 0])
        # 아래층 fx
        for L in live:
            m_, im_ = fx[L[0]]
            if m_.get("depth") != "below":
                continue
            cell = cellof(m_, im_, L[1], L[2])
            V._paste(can, cell, int(L[4] - m_["pivot"]["x"]), int(L[5] - m_["pivot"]["y"]))
        # 몸 + 무기
        V._paste(can, cellof(bm, bim, d, c), int(x - 48), ground - 138)
        V._paste(can, cellof(om, oim, d, c), int(x - om["pivot"]["x"]), ground - om["pivot"]["y"])
        if act == "idle":
            m_, im_ = fx["hero_ember_breath"]
            ch = bm["chestAnchors"][d][c]
            V._paste(can, cellof(m_, im_, "any", (clock // 80) % 12), int(x - 48 + ch[0] - m_["pivot"]["x"]), int(ground - 138 + ch[1] - m_["pivot"]["y"]))
        for L in live:
            m_, im_ = fx[L[0]]
            if m_.get("depth") == "below":
                continue
            cell = cellof(m_, im_, L[1], L[2])
            px_ = m_["pivot"]["x"]
            if len(L) > 7 and L[7]:                    # 왼쪽으로 움직임 → 꼬리를 오른쪽으로(회전 180°)
                cell = cell.transpose(Image.FLIP_LEFT_RIGHT)
                px_ = cell.width - 1 - px_
            V._paste(can, cell, int(L[4] - px_), int(L[5] - m_["pivot"]["y"]))
        frames.append(can)
        durs.append(ms)
        clock += ms
        # fx 진행(한 칸 = 이 프레임 ms 와 무관하게 1칸 — 목업 단순화)
        nl = []
        for L in live:
            L[2] += 1
            if L[2] <= L[3][1]:
                nl.append(L)
        live = nl
    V.gif(frames, durs, os.path.join(HERE, "preview_mock_motion.gif"), scale=2)


def sheets_png():
    rows = []
    for name, body, wrel in PAIRS + [("turn_skid", "player_turn_skid", "weapons/v3/katana_carry_turn_skid")]:
        nm, nim = new_grid("player/v3/" + body)
        wm = wim = None
        if wrel:
            wm, wim = new_grid(wrel)
        cs = [V.label(comp(nm, nim, "right", c, wm, wim), "%s %d" % (name, c) if c == 0 else str(c)) for c in range(nm["frames"])]
        rows.append(V.strip(cs, 1))
    W = max(r.width for r in rows)
    out = Image.new("RGBA", (W, sum(r.height for r in rows)), BG)
    y = 0
    for r in rows:
        out.paste(r, (0, y))
        y += r.height
    out.save(os.path.join(HERE, "preview_sheets.png"))


def build():
    for name, body, wrel in PAIRS:
        try:
            before_after(name, body, wrel)
            print("gif", name)
        except FileNotFoundError as e:
            print("  (건너뜀 — 새 격자 없음)", name, e)
    mock_motion()
    sheets_png()
    print("preview ok")
