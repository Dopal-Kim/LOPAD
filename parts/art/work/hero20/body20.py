"""P20 몸 렌더 — 새 리그(rig20) + 무기 오버레이 손 앵커 오프셋 동기(b+, P19 방식 그대로).

오프셋 = 새 몸(rig20, 새 자세)의 해부 왼허리 hipL − 옛 몸(hero_v3 리그, 옛 자세)의 hipL. 원본은 git sync19.SRC_REV(P19 직전) —
P19 와 같은 원본에서 다시 옮기므로 오프셋이 두 번 걸리지 않는다. 손은 '옛 handAnchors + 오프셋' 에 IK 고정.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(WORK, "hero_v3"))
sys.path.insert(0, os.path.join(WORK, "hero19"))
sys.path.insert(0, os.path.join(WORK, "atlas57"))
import rig20  # noqa: E402
import hero  # noqa: E402  (옛 리그 — 옛 자세의 hipL 계산에만)
import motion  # noqa: E402
import sync19 as S  # noqa: E402

S.GRID = os.path.join(HERE, "out", "grid")
SIDE = ("left", "right")
DIRS = ["down", "up", "left", "right"]


def load_json(rel):
    return S.src_meta(rel)


def px_to_design(q):
    return (32 + (q[0] - 48) / 1.5, 92 + (q[1] - 138) / 1.5)


def clean(p):
    return {k: v for k, v in p.items() if k != "post"}


def hip_new(d, p):
    R = rig20.build(d, clean(p))
    return hero.to_px(R.anchors["hipL"]), R


def hip_old(d, p):
    R = hero.build(d, clean(p))
    return hero.to_px(R.anchors["hipL"])


def offsets(d, new_list, old_list):
    out = []
    for pn, po in zip(new_list, old_list):
        a, _ = hip_new(d, pn)
        b = hip_old(d, po)
        out.append((round(a[0] - b[0]), round(a[1] - b[1])))
    return out


def pinned_pose(d, p, hands, off):
    q = dict(p)
    ha = {}
    for side in ("R", "L"):
        h = hands.get("hand" + side)
        if h is not None:
            ha[side] = px_to_design((h[0] + off[0], h[1] + off[1]))
    q["handAt"] = ha
    q["reachFrac"] = 1.06
    return q


def fold_elbows(d, p):
    """정면·뒷면: 어깨 가까이 올라온 손의 팔꿈치는 몸 안쪽으로(날개 팔 방지)."""
    R0 = rig20.build(d, clean(p))
    el = dict(p.get("elbow") or {})
    m = -1 if d == "up" else 1
    for side, s in (("L", 1), ("R", -1)):
        h = p["handAt"].get(side)
        if h is None or side in el:
            continue
        sh = R0.anchors["shoulder" + side]
        if -4.0 <= h[1] - sh[1] < 16.0:           # 앞으로 흔든 팔만 안쪽으로(머리 위로 든 팔은 rig20 이 바깥·위로 굽힘)
            el[side] = -m * s
    q = dict(p)
    q["elbow"] = el or None
    return q


def render(d, p):
    R = rig20.draw_rig(d, clean(p))
    im = motion.apply_post(R.image, R, d, p)
    return R, im


def hand_err(R, hands, off):
    e = 0.0
    for side in ("R", "L"):
        h = hands.get("hand" + side)
        if h is None:
            continue
        a = hero.to_px(R.anchors["hand" + side])
        e = max(e, math.hypot(a[0] - h[0] - off[0], a[1] - h[1] - off[1]))
    return e


def eye_of(R, d):
    e = R.anchors.get("eye")
    if d == "up" or e is None:
        return None
    return [round(c, 1) for c in hero.to_px(e)]


def chest_of(R):
    return [round(c, 1) for c in hero.to_px(R.anchors["chest"])]


def scar_of(R):
    return dict(R.scar)


def render_sheet(body, new_fn, old_fn, src_cols=None, free_hands=False):
    meta = load_json("player/v3/" + body)
    out = {}
    for d in DIRS:
        new, old = new_fn(d), old_fn(d)
        cols = src_cols or list(range(len(new)))
        olds = [old[c] for c in cols]
        offs = offsets(d, new, olds)
        lst = []
        for i, (pn, off) in enumerate(zip(new, offs)):
            hands = meta["handAnchors"][d][cols[i]]
            p = pn if free_hands else pinned_pose(d, pn, hands, off)
            if d not in SIDE and not free_hands:
                p = fold_elbows(d, p)
            R, im = render(d, p)
            new_hands = {k: [round(c, 1) for c in hero.to_px(R.anchors[k])] for k in ("handR", "handL")}
            Ro = hero.build(d, clean(olds[i]))
            ca, cb = hero.to_px(R.anchors["chest"]), hero.to_px(Ro.anchors["chest"])
            back_off = (round(ca[0] - cb[0]), round(ca[1] - cb[1]))
            lst.append(dict(img=im, rig=R, off=off, back_off=back_off, src=cols[i], hands=new_hands, eye=eye_of(R, d),
                            chest=chest_of(R), err=0.0 if free_hands else hand_err(R, hands, off)))
        out[d] = lst
    return out
