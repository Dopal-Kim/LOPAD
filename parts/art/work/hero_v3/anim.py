"""주인공 v3 동작 목록 + 렌더 (53라운드 Q1: 96×144).

render_body(act)          → {dir: [Frame]}   Frame = (몸 RGBA, Rig, pose)
render_carry(act, body)   → {dir: [무기 RGBA]} + 칼집 입구 기준점(도트)   — 칼집에 든 칼
render_carry_drawn(act, body) → {dir: [무기 RGBA]}                       — 뽑아 든 칼(같은 몸 시트)
render_move(kind, key)    → {dir: [ComboFrame]}  연격 1~3 · 뽑기 · 넣기 · 특수
"""
from collections import namedtuple

import hero
import katana3 as K
import motion

DIRS = hero.DIRS

# 동작 이름 → (자세 생성, 프레임 ms, loop)
BODY = {
    "idle": (hero.act_idle, hero.IDLE_MS, True),
    "walk": (hero.act_walk, hero.WALK_MS, True),
    "run": (motion.act_run, motion.RUN_MS, True),
    "dash": (motion.act_dash, motion.DASH_MS, False),
    "hurt": (motion.act_hurt, motion.HURT_MS, False),
    "death": (motion.act_death, motion.DEATH_MS, False),
}
STRIDE = {"walk": hero.STRIDE["walk"], "run": motion.STRIDE_RUN}
CARRY = ("idle", "walk", "run", "dash")        # 칼 휴대 오버레이(칼집·뽑아 든)를 만드는 몸 동작
SAYA_HOLD = ("idle", "walk", "run")            # 왼손이 칼집 입구를 쥐는 몸 동작(53라운드 '무기 든 느낌')
COMBOS = (1, 2, 3)
MOVES = ("draw", "sheathe", "special")

Frame = namedtuple("Frame", "image rig pose")
ComboFrame = namedtuple("ComboFrame", "body weapon hands state rig")


def hands_px(R):
    return {k: [round(c, 1) for c in hero.to_px(R.anchors[k])] for k in ("handR", "handL") if k in R.anchors}


def render_body(act):
    gen, ms, loop = BODY[act]
    out = {}
    for d in DIRS:
        frames = []
        for p in gen(d):
            if act in SAYA_HOLD:
                p = K.saya_hold(d, p)
            R = hero.draw_rig(d, p)
            frames.append(Frame(motion.apply_post(R.image, R, d, p), R, p))
        assert len(frames) == len(ms), (act, d)
        out[d] = frames
    return out


def render_carry(act, body):
    """body = render_body(act) 결과(같은 Rig 를 다시 쓴다)."""
    out, mouths = {}, {}
    for d in DIRS:
        out[d] = [K.carry_frame(d, f.pose, f.rig) for f in body[d]]
        mouths[d] = [[round(c, 1) for c in hero.to_px(K.mouth_point(d, f.rig)[:2])] for f in body[d]]
    return out, mouths


def render_carry_drawn(act, body):
    return {d: [K.carry_drawn_frame(d, act, i, f.pose, f.rig) for i, f in enumerate(body[d])] for d in DIRS}


def render_move(kind, key):
    defs = (K.COMBO[key] if kind == "combo" else K.MOVES[key])["frames"]
    out = {}
    for d in DIRS:
        frames = []
        for i in range(len(defs)):
            R, w, hands, state, p = K.move_frame(d, kind, key, i)
            frames.append(ComboFrame(R.image, w, hands, state, R))
        out[d] = frames
    return out


def render_combo(n):
    return render_move("combo", n)
