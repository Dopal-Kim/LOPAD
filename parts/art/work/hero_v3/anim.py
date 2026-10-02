"""주인공 v3 동작 목록 + 렌더 (1단계 idle·walk + 2단계 run·dash·hurt·death·칼 연격 3종 · 칼 휴대 오버레이).

render_body(act)  → {dir: [Frame]}   Frame = (몸 RGBA, Rig, pose)
render_combo(n)   → {dir: [ComboFrame]}  (몸 RGBA, 무기 RGBA, 손 기준점, 상태, Rig)
render_carry(act) → {dir: [무기 RGBA]} + 칼집 입구 기준점
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
CARRY = ("idle", "walk", "run", "dash")        # 칼 휴대 오버레이를 만드는 몸 동작
COMBOS = (1, 2, 3)

Frame = namedtuple("Frame", "image rig pose")
ComboFrame = namedtuple("ComboFrame", "body weapon hands state rig")


def _hands(R):
    return {k: [round(R.anchors[k][0], 1), round(R.anchors[k][1], 1)] for k in ("handR", "handL") if k in R.anchors}


def render_body(act):
    gen, ms, loop = BODY[act]
    out = {}
    for d in DIRS:
        frames = []
        for p in gen(d):
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
        mouths[d] = [[round(c, 1) for c in K.mouth_point(d, f.rig)[:2]] for f in body[d]]
    return out, mouths


def render_combo(n):
    out = {}
    for d in DIRS:
        frames = []
        for i in range(len(K.COMBO[n]["frames"])):
            R, w, hands, state, p = K.combo_frame(d, n, i)
            frames.append(ComboFrame(R.image, w, hands, state, R))
        out[d] = frames
    return out
