#!/usr/bin/env python3
"""LOPAD 49라운드 — 무기 휴대 오버레이 + 뽑기·넣기 (칼·대검) — 단일 소스.

실행: python3 parts/art/work/carry/build.py   (combos/build.py 와 독립. 공용 기하 = combos/gear.py)
근거: decisions/2026-10-02-round-49-playtest2.md 4절(무기 휴대) · 5절, contracts/art-assets.md §7.1 (+ §3.1·§6.1 겹침 규약).
입력 (읽기만): parts/art/work/player/build.py (몸 리그 — player_idle/walk/dash 와 픽셀 단위로 같음을 확인), parts/art/work/weapons/build.py,
      parts/art/work/combos/{build.py, gear.py}, assets/tiles/stage1.png (목업 바닥), assets/sprites/enemies/dummy_idle.png (미사용)
산출:
  assets/sprites/weapons/<w>_carry_<a>.png/.json        w = katana·greatsword·dagger·bow, a = idle·walk·dash (몸 player_<a> 과 같은 프레임 수·ms)
  assets/sprites/weapons/<w>_carry_drawn_<a>.png/.json  (임시 추가) 칼·대검을 뽑아 든 채 이동할 때 — 납도 대기 상태
  assets/sprites/player/player_{katana,greatsword}_{draw,sheathe}.png/.json + weapons/<w>_{draw,sheathe}.png/.json
  parts/art/work/carry/preview_carry_{sword,hand,drawn}.png, preview_drawsheathe.png, preview_mock_1x.png, preview_mock_2x.png,
  gif/carry_walk_<dir>.gif, gif/<w>_draw_sheathe_right.gif
"""
import importlib.util
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
COMBOS = os.path.join(ROOT, "parts", "art", "work", "combos")
sys.path.insert(0, COMBOS)
import gear  # noqa: E402

spec = importlib.util.spec_from_file_location("lopad_combos", os.path.join(COMBOS, "build.py"))
CB = importlib.util.module_from_spec(spec)
sys.modules["lopad_combos"] = CB
spec.loader.exec_module(CB)

P = gear.P
G, C = gear.G, gear.C
DIRS = gear.DIRS
SPR = os.path.join(ROOT, "assets", "sprites")
OUT_P = os.path.join(SPR, "player")
OUT_W = os.path.join(SPR, "weapons")
os.makedirs(os.path.join(HERE, "gif"), exist_ok=True)
SRC = "parts/art/work/carry/build.py (49라운드 4절 · art §7.1)"
CB.SRC = SRC

SPEC = CB.SPEC
GS_SPEC = SPEC["greatsword"]
KT_SPEC = SPEC["katana"]

ACTION_POSES = {
    "idle": lambda d: P.poses_idle(),
    "walk": lambda d: P.poses_walk(d in ("left", "right")),
    "dash": lambda d: P.poses_dash(d in ("left", "right")),
}
ACTION_LOOP = {"idle": True, "walk": True, "dash": False}
CARRY_WHERE = {"katana": "waist sheath (허리 칼집)", "greatsword": "back (등)", "dagger": "hand, reverse grip (손 · 역수)",
               "bow": "hand (손)"}


def canvas_of(w):
    S = 64 if w == "greatsword" else 48
    off = (S - 16) // 2
    return S, (off, off), (off + 8, off + 23)


# ============================================================ 1. 휴대 그림 (몸 프레임 하나에 대해)
def draw_carry(ly, w, d, p, drawn=False):
    if w == "katana":
        g = gear.sheath_geo(d, p)
        gear.draw_scabbard(ly, g, empty=drawn)
        if not drawn:
            gear.draw_katana_hilt(ly, g)
        else:
            hand = gear.weapon_hand_rest(d, p)
            phi = {"right": 35, "left": 145, "down": 70, "up": 110}[d]
            gear.blade(ly, hand, phi, KT_SPEC, gear.blade_layer(d, phi) if d != "up" else "front")
    elif w == "greatsword":
        if not drawn:
            gear.draw_back_sword(ly, d, p, GS_SPEC)
        else:
            hand = gear.weapon_hand_rest(d, p)
            phi = {"right": 160, "left": 20, "down": 58, "up": 122}[d]
            gear.blade(ly, hand, phi, GS_SPEC, "front")
    elif w == "dagger":
        gear.draw_dagger_reverse(ly, d, gear.weapon_hand_rest(d, p))
    elif w == "bow":
        gear.draw_bow_hand(ly, d, gear.weapon_hand_rest(d, p))


def build_carry(w, action, drawn=False):
    S, poff, wpivot = canvas_of(w)
    bodies, weapons, depth, depth_by = {}, {}, {}, {}
    durs = None
    for d in DIRS:
        ps, durs = ACTION_POSES[action](d)
        bl, ll = [], []
        for p in ps:
            bl.append(P.render(d, p))
            ly = gear.Layers(S, poff)
            draw_carry(ly, w, d, p, drawn)
            ll.append(ly)
        weapons[d], depth[d] = gear.bake_dir(ll, bl)
        depth_by[d] = [depth[d]] * len(ps)
        bodies[d] = bl
    name = "%s_carry_%s%s" % (w, "drawn_" if drawn else "", action)
    memo = {
        "weapon": w, "carry": CARRY_WHERE[w] if not drawn else "drawn, in hand (뽑아 든 상태)",
        "bodySheet": "player_%s" % action,
        "framesBasis": "player_%s 와 같은 프레임 수·같은 frameDurationsMs·같은 방향 행. 몸 프레임 번호와 1:1" % action,
        "anchor": "player_pivot", "playerFrameOffset": {"x": poff[0], "y": poff[1]},
        "depth": depth, "depthByFrame": depth_by,
        "occlusionBaked": True,
        "depthNote": "몸 뒤로 가는 부분(먼 허리 칼집·등의 대검 날 등)은 그 프레임 몸 실루엣으로 이미 지워 두었다. "
                     "above = 몸 위에 그대로 겹침, below = 몸 아래(앞 층이 없는 방향). 방향 안에서 프레임마다 같다.",
        "overlay": "player_%s 와 같은 프레임 번호(row*frames+col)를 같은 시각에 겹친다. 피벗 (%d,%d) = 주인공 피벗 (8,23)." % (action, wpivot[0], wpivot[1]),
    }
    if drawn:
        memo["state"] = "drawn"
        memo["stateNote"] = "임시(49라운드 아트): 공격 뒤 납도 전(비전투 타이머 동안) 이동·대기 때 carry 대신 사용. 칼집은 빈 칼집."
    CB.save_png_json(OUT_W, name, weapons, S, S, durs, ACTION_LOOP[action], wpivot, CB.PAL_WEAPON, memo, "carry_" + action)
    CB.check("weapons/" + name, "weapon", weapons)
    return dict(bodies=bodies, weapons=weapons, ms=durs, S=S, poff=poff, wpivot=wpivot, depth=depth)


# ============================================================ 2. 뽑기·넣기 (몸 + 무기)
def katana_drawsheathe(kind):
    """kind = draw | sheathe. 칼: 무기 손이 왼쪽 허리 칼집의 손잡이를 잡는다(발도 호 시작 쪽)."""
    S, poff, wpivot = canvas_of("katana")
    if kind == "draw":
        ms = [70, 70, 90]
        nf = 3
    else:
        ms = [90, 90, 90, 120]
        nf = 4
    bodies, weapons, depth, depth_by = {}, {}, {}, {}
    for d in DIRS:
        bl, ll = [], []
        for f in range(nf):
            ly = gear.Layers(S, poff)
            if kind == "draw":
                if f < 2:
                    slide = 0 if f == 0 else 4
                    p = P.Pose(crouch=0, body_dy=1 if f == 0 else 0)
                    if d in ("left", "right"):
                        p.lean = 1
                    grip = gear.katana_hilt_grip(d, p, slide)
                    g = gear.sheath_geo(d, p)
                    gear.draw_scabbard(ly, g, empty=False)
                    gear.draw_katana_hilt(ly, g, slide=slide, blade_out=slide, layer="front" if f == 1 and d != "up" else None)
                    if d == "up":
                        p.l_arm = "pos"
                    else:
                        p.r_arm = "pos"
                    p.hand_pos = gear.clamp_hand(*grip)
                else:
                    p = P.Pose()
                    draw_carry(ly, "katana", d, p, drawn=True)
                    hand = gear.weapon_hand_rest(d, p)
                    phi = {"right": 35, "left": 145, "down": 70, "up": 110}[d]
                    dx, dy = gear.qdir(phi)
                    gear.P2(ly, hand[0] + dx * 12, hand[1] + dy * 12, C(27), "front")   # 뽑은 칼빛
                    gear.P2(ly, hand[0] + dx * 13, hand[1] + dy * 13, C(25), "front")
            else:
                if f == 0:   # 피 털기(치부리): 칼을 앞-아래로 털어 낸다
                    p = P.Pose()
                    phi = {"right": 55, "left": 125, "down": 80, "up": 100}[d]
                    sx, sy = gear.main_shoulder(d, p)
                    ux, uy = gear.unit(phi)
                    hand = gear.clamp_hand(sx + 5 * ux, sy + 5 * uy)
                    if d == "up":
                        p.l_arm = "pos"
                    else:
                        p.r_arm = "pos"
                    p.hand_pos = hand
                    g = gear.sheath_geo(d, p)
                    gear.draw_scabbard(ly, g, empty=True)
                    gear.blade(ly, hand, phi, KT_SPEC, "front")
                    dx, dy = gear.qdir(phi)
                    gear.P2(ly, hand[0] + dx * 12, hand[1] + dy * 12, C(27), "front")
                else:
                    slide = {1: 6, 2: 3, 3: 0}[f]
                    p = P.Pose(body_dy=1 if f == 3 else 0)
                    g = gear.sheath_geo(d, p)
                    gear.draw_scabbard(ly, g, empty=False)
                    gear.draw_katana_hilt(ly, g, slide=slide, blade_out=slide, glint=(f == 3),
                                          layer="front" if (slide and d != "up") else None)
                    grip = gear.katana_hilt_grip(d, p, slide)
                    if d == "up":
                        p.l_arm = "pos"
                    else:
                        p.r_arm = "pos"
                    p.hand_pos = gear.clamp_hand(*grip)
            bl.append(gear.render_body(d, p))
            ll.append(ly)
        weapons[d], depth[d] = gear.bake_dir(ll, bl)
        depth_by[d] = [depth[d]] * nf
        bodies[d] = bl
    name = "katana_" + kind
    if kind == "draw":
        memo = {"phases": {"grip": [0], "pull": [1], "drawn": [2]},
                "note": "발도: 무기 손이 허리 칼집 손잡이를 잡고(f0) 뽑아(f1) 앞-아래로 든다(f2 = katana_carry_drawn_idle f0 과 같은 자세).",
                "usage": "공격이 아닌 동작(보조 동작 등)으로 전투에 들어갈 때. 연격 1타(katana_combo1)는 자체가 발도 베기라 draw 없이 바로 재생."}
    else:
        memo = {"phases": {"chiburi": [0], "insert": [1, 2], "click": [3]},
                "note": "납도: 피 털기(f0) → 칼끝을 칼집 입구에 대고(f1) 밀어 넣고(f2) 딸깍(f3, 날밑 글린트). 끝나면 katana_carry_idle 로.",
                "usage": "공격 뒤 비전투·무공격 시간이 지나면 재생(시간은 시스템)."}
    memo.update({"weapon": "katana", "framesBasis": "player_%s 프레임 번호 (몸·무기 공통)" % name})
    CB.save_png_json(OUT_P, "player_" + name, bodies, 16, 24, ms, False, (8, 23), CB.PAL_PLAYER, memo, name)
    CB.save_png_json(OUT_W, name, weapons, S, S, ms, False, wpivot, CB.PAL_WEAPON,
                     dict(memo, anchor="player_pivot", depth=depth, depthByFrame=depth_by, occlusionBaked=True,
                          playerFrameOffset={"x": poff[0], "y": poff[1]}), kind)
    CB.check("player_" + name, "player", bodies)
    CB.check("weapons/" + name, "weapon", weapons)
    return dict(bodies=bodies, weapons=weapons, ms=ms, S=S, poff=poff, wpivot=wpivot, depth=depth)


def greatsword_drawsheathe(kind):
    """대검: 두 손으로 무기 손 쪽 어깨 위 손잡이를 잡아 머리 위로 끌어내 앞으로 넘긴다 / 반대로 등에 멘다."""
    S, poff, wpivot = canvas_of("greatsword")
    if kind == "draw":
        ms = [90, 110, 90, 110]
        seq = ["grab", ("up", -112, 6, -1, -1, 0, {"down": -95, "up": -85}), ("over", -35, 5, 1, 0, 0, {}), "drag"]
    else:
        ms = [100, 110, 110, 120]
        seq = [("up", -105, 5, 0, -1, 0, {"down": -95, "up": -85}), ("behind", -165, 3, -1, 0, 0, {}), "grab", "rest"]
    bodies, weapons, depth, depth_by = {}, {}, {}, {}
    for d in DIRS:
        bl, ll = [], []
        for st in seq:
            ly = gear.Layers(S, poff)
            if st == "grab":       # 두 손이 어깨 위 손잡이에, 칼은 아직 등
                p = P.Pose(crouch=1)
                gear.draw_back_sword(ly, d, p, GS_SPEC)
                grip = gear.clamp_hand(*gear.back_hilt_grip(d, p, GS_SPEC))
                p.hand_pos = grip
                under = []
                if d in ("left", "right"):
                    p.r_arm = "pos"
                    ox, oy = gear.off_shoulder(d, p)
                    under.append((ox, oy, grip[0], grip[1] + 1))
                else:
                    p.l_arm = p.r_arm = "pos"
                body = gear.render_body(d, p, under_arms=under)
            elif st == "rest":     # 손 내림 = carry idle f0
                p = P.Pose()
                gear.draw_back_sword(ly, d, p, GS_SPEC)
                body = P.render(d, p)
            elif st == "drag":     # 한 손으로 끌어 든 자세 = greatsword_carry_drawn_idle f0
                p = P.Pose()
                draw_carry(ly, "greatsword", d, p, drawn=True)
                body = P.render(d, p)
            else:
                _, th, L, fwd, dip, crouch, phis = st
                p, under, over, hand, phi = gear.twohand_pose(d, th, L, fwd, dip, crouch, pull=0.0, phi=phis.get(d))
                gear.blade(ly, hand, phi, GS_SPEC, gear.blade_layer(d, phi))
                body = gear.render_body(d, p, under, over)
            bl.append(body)
            ll.append(ly)
        weapons[d], depth[d] = gear.bake_dir(ll, bl)
        depth_by[d] = [depth[d]] * len(seq)
        bodies[d] = bl
    name = "greatsword_" + kind
    if kind == "draw":
        memo = {"phases": {"grab": [0], "lift": [1], "over": [2], "drawn": [3]},
                "note": "두 손으로 어깨 위 손잡이를 잡고(f0) 머리 위로 끌어올려(f1) 앞으로 넘긴 뒤(f2) 한 손으로 끌어 든다(f3 = greatsword_carry_drawn_idle f0).",
                "usage": "공격이 아닌 동작(가드 등)으로 전투에 들어갈 때. 연격 1타(greatsword_combo1)는 f0~f1 이 '어깨 위에서 끌어내 머리 위로'라 draw 없이 바로 재생."}
    else:
        memo = {"phases": {"lift": [0], "behind": [1], "seat": [2], "release": [3]},
                "note": "두 손으로 머리 위로 들어(f0) 어깨 뒤로 넘기고(f1) 등에 걸친 뒤(f2) 손을 내린다(f3 = greatsword_carry_idle f0).",
                "usage": "공격 뒤 비전투·무공격 시간이 지나면 재생(시간은 시스템)."}
    memo.update({"weapon": "greatsword", "framesBasis": "player_%s 프레임 번호 (몸·무기 공통)" % name})
    CB.save_png_json(OUT_P, "player_" + name, bodies, 16, 24, ms, False, (8, 23), CB.PAL_PLAYER, memo, name)
    CB.save_png_json(OUT_W, name, weapons, S, S, ms, False, wpivot, CB.PAL_WEAPON,
                     dict(memo, anchor="player_pivot", depth=depth, depthByFrame=depth_by, occlusionBaked=True,
                          playerFrameOffset={"x": poff[0], "y": poff[1]}), kind)
    CB.check("player_" + name, "player", bodies)
    CB.check("weapons/" + name, "weapon", weapons)
    return dict(bodies=bodies, weapons=weapons, ms=ms, S=S, poff=poff, wpivot=wpivot, depth=depth)


# ============================================================ 3. 미리보기
FLOOR = CB.FLOOR


def cell_img(r, d, f, k, bgS=64, bg=FLOOR):
    cell = Image.new("RGBA", (bgS, bgS), bg)
    o = (bgS - r["S"]) // 2
    tmp = Image.new("RGBA", (r["S"], r["S"]), (0, 0, 0, 0))
    wim = r["weapons"][d][f].im
    if r["depth"][d] == "below":
        tmp.alpha_composite(wim)
        tmp.alpha_composite(r["bodies"][d][f], r["poff"])
    else:
        tmp.alpha_composite(r["bodies"][d][f], r["poff"])
        tmp.alpha_composite(wim)
    cell.alpha_composite(tmp, (o, o))
    return CB.scaled(cell, k)


def preview_grid(blocks, path, k=4, bgS=48):
    """blocks: [(title, res)] → 각 블록 4행(방향) × 프레임."""
    rows = []
    for title, r in blocks:
        nf = len(r["ms"])
        cw = bgS * k
        blk = Image.new("RGB", (60 + nf * (cw + 3), 18 + 4 * (cw + 3)), (34, 34, 38))
        dr = ImageDraw.Draw(blk)
        dr.text((4, 2), "%s  %s ms  depth %s" % (title, r["ms"], r["depth"]), fill=(235, 235, 235), font=CB.FONT)
        for ri, d in enumerate(DIRS):
            y = 18 + ri * (cw + 3)
            dr.text((4, y + cw // 2 - 6), d, fill=(220, 220, 220), font=CB.FONT)
            for f in range(nf):
                blk.paste(cell_img(r, d, f, k, bgS).convert("RGB"), (60 + f * (cw + 3), y))
        rows.append(blk)
    Wd = max(b.width for b in rows) + 16
    Hd = sum(b.height + 6 for b in rows) + 10
    img = Image.new("RGB", (Wd, Hd), (22, 22, 26))
    y = 6
    for b in rows:
        img.paste(b, (8, y))
        y += b.height + 6
    img.save(path)


def preview_mock(res):
    """월드 480×270 (카메라 2배 → 960×540). 4무기 × (idle/walk/dash) 4방향을 실제 크기로 늘어놓은 장면."""
    tiles = CB.floor_tile()
    world = CB.scene(480, 270, tiles, seed=11)
    for wi, w in enumerate(("katana", "greatsword", "dagger", "bow")):
        for ai, a in enumerate(("idle", "walk", "dash")):
            r = res[(w, a)]
            for di, d in enumerate(DIRS):
                f = {"idle": 0, "walk": 2, "dash": 1}[a]
                x = 20 + ai * 155 + di * 36
                y = 40 + wi * 62
                wim = r["weapons"][d][f].im
                if r["depth"][d] == "below":
                    CB.put(world, wim, x - r["wpivot"][0], y - r["wpivot"][1])
                CB.put(world, r["bodies"][d][f], x - 8, y - 23)
                if r["depth"][d] == "above":
                    CB.put(world, wim, x - r["wpivot"][0], y - r["wpivot"][1])
    world.save(os.path.join(HERE, "preview_mock_1x.png"))
    big = CB.scaled(world, 2)
    dr = ImageDraw.Draw(big)
    for wi, w in enumerate(("katana", "greatsword", "dagger", "bow")):
        dr.text((4, 2 + wi * 124), w, fill=(235, 235, 235), font=CB.FONT)
    for ai, a in enumerate(("idle f0", "walk f2", "dash f1")):
        dr.text((40 + ai * 310, 520), a, fill=(235, 235, 235), font=CB.FONT)
    big.save(os.path.join(HERE, "preview_mock_2x.png"))


def walk_gif(res, d="right", k=3):
    """4무기 휴대 걷기를 나란히 (시간축, 110ms)."""
    tiles = CB.floor_tile()
    frames, durs = [], []
    for f in range(8):
        img = CB.scene(4 * 48, 56, tiles, seed=5)
        for wi, w in enumerate(("katana", "greatsword", "dagger", "bow")):
            r = res[(w, "walk")]
            x, y = 24 + wi * 48, 44
            wim = r["weapons"][d][f].im
            if r["depth"][d] == "below":
                CB.put(img, wim, x - r["wpivot"][0], y - r["wpivot"][1])
            CB.put(img, r["bodies"][d][f], x - 8, y - 23)
            if r["depth"][d] == "above":
                CB.put(img, wim, x - r["wpivot"][0], y - r["wpivot"][1])
        frames.append(CB.scaled(img, k).convert("RGB").convert("P", palette=Image.ADAPTIVE))
        durs.append(110)
    frames[0].save(os.path.join(HERE, "gif", "carry_walk_%s.gif" % d), save_all=True, append_images=frames[1:],
                   duration=durs, loop=0, disposal=2)


def seq_gif(name, seq, d="right", k=3):
    """[(res, frame_indices or None)] 을 이어 붙인 시간축 GIF."""
    tiles = CB.floor_tile()
    frames, durs = [], []
    for r, idxs in seq:
        for f in (idxs if idxs is not None else range(len(r["ms"]))):
            img = CB.scene(96, 64, tiles, seed=7)
            x, y = 48, 46
            wim = r["weapons"][d][f].im
            if r["depth"][d] == "below":
                CB.put(img, wim, x - r["wpivot"][0], y - r["wpivot"][1])
            CB.put(img, r["bodies"][d][f], x - 8, y - 23)
            if r["depth"][d] == "above":
                CB.put(img, wim, x - r["wpivot"][0], y - r["wpivot"][1])
            frames.append(CB.scaled(img, k).convert("RGB").convert("P", palette=Image.ADAPTIVE))
            durs.append(r["ms"][f])
    frames[0].save(os.path.join(HERE, "gif", "%s_%s.gif" % (name, d)), save_all=True, append_images=frames[1:],
                   duration=durs, loop=0, disposal=2)


def main():
    res = {}
    for w in ("katana", "greatsword", "dagger", "bow"):
        for a in ("idle", "walk", "dash"):
            res[(w, a)] = build_carry(w, a)
    for w in ("katana", "greatsword"):
        for a in ("idle", "walk", "dash"):
            res[(w, "drawn_" + a)] = build_carry(w, a, drawn=True)
    ds = {}
    for kind in ("draw", "sheathe"):
        ds[("katana", kind)] = katana_drawsheathe(kind)
        ds[("greatsword", kind)] = greatsword_drawsheathe(kind)
    preview_grid([("%s_carry_%s" % (w, a), res[(w, a)]) for w in ("katana", "greatsword") for a in ("idle", "walk", "dash")],
                 os.path.join(HERE, "preview_carry_sword.png"), bgS=48)
    preview_grid([("%s_carry_%s" % (w, a), res[(w, a)]) for w in ("dagger", "bow") for a in ("idle", "walk", "dash")],
                 os.path.join(HERE, "preview_carry_hand.png"), bgS=48)
    preview_grid([("%s_carry_drawn_%s" % (w, a), res[(w, "drawn_" + a)]) for w in ("katana", "greatsword") for a in ("idle", "walk", "dash")],
                 os.path.join(HERE, "preview_carry_drawn.png"), bgS=48)
    preview_grid([("%s_%s" % (w, k), ds[(w, k)]) for w in ("katana", "greatsword") for k in ("draw", "sheathe")],
                 os.path.join(HERE, "preview_drawsheathe.png"), bgS=56)
    preview_mock(res)
    for d in ("right", "down", "up", "left"):
        walk_gif(res, d)
    for w in ("katana", "greatsword"):
        seq_gif("%s_draw_sheathe" % w, [(res[(w, "idle")], [0, 1]), (ds[(w, "draw")], None), (res[(w, "drawn_walk")], None),
                                        (ds[(w, "sheathe")], None), (res[(w, "idle")], [0, 1, 2])])
    bad = [r for r in CB.REPORT if not r[1]]
    print("\n%d sheets checked, %d CHECK" % (len(CB.REPORT), len(bad)))


if __name__ == "__main__":
    main()
