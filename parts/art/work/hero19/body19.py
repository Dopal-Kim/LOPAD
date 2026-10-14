"""P19 몸 렌더 — 새 자세 + 기존 손 기준점 고정(무기 오버레이 동기 '방식 b+').

원칙: 무기 오버레이(v3·v4·각성·검기·울분)는 다시 그리지 않는다. 프레임마다 정수 도트 오프셋(dx, dy)만큼 통째로 옮기고,
몸의 손은 '기존 handAnchors + 같은 오프셋' 에 IK 로 고정한다 → 손·손잡이·칼집 입구가 어긋나지 않는다.
오프셋 = 새 자세의 해부 왼허리(hipL, 칼집이 매달리는 곳) − 옛 자세의 hipL (반올림). 등 휴대(대검)는 따로(sync19).
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(HERE, "..", "hero_v3"))
sys.path.insert(0, os.path.join(HERE, "..", "atlas57"))
import gridsheet  # noqa: E402
import hero  # noqa: E402
import motion  # noqa: E402
import katana3 as K  # noqa: E402

ASSETS = os.path.join(ROOT, "assets", "sprites")
SIDE = ("left", "right")
DIRS = hero.DIRS


def load_json(rel):
    """원본(sync19.SRC_REV) 메타 — 다시 돌려도 이미 바뀐 assets 를 원본으로 읽지 않는다."""
    import sync19
    return sync19.src_meta(rel)


def load_grid(rel):
    import sync19
    return sync19.src_grid(rel)


def cell(meta, im, row, col):
    fw, fh = meta["frameWidth"], meta["frameHeight"]
    return im.crop((col * fw, row * fh, col * fw + fw, row * fh + fh))


def px_to_design(q, d):
    """몸 도트 좌표(handAnchors 값) → 설계 좌표 손 중심(앵커는 손 타원 중심 + 0.4/0.2 아래)."""
    return (32 + (q[0] - 48) / 1.5, 92 + (q[1] - 138) / 1.5 - (0.2 if d in SIDE else 0.4))


def hip_px(d, p):
    R = hero.build(d, {k: v for k, v in p.items() if k != "post"})
    return hero.to_px(R.anchors["hipL"]), R


def offsets(d, new_list, old_list, keep_y=False):
    """프레임별 정수 오프셋(도트) = 새 hipL − 옛 hipL."""
    out = []
    for pn, po in zip(new_list, old_list):
        a, _ = hip_px(d, pn)
        b, _ = hip_px(d, po)
        out.append((round(a[0] - b[0]), 0 if keep_y else round(a[1] - b[1])))
    return out


def pinned_pose(d, p, hands, off):
    """hands = {'handR': [x,y], 'handL': [x,y]} (옛 몸 도트) + off → handAt 고정."""
    q = dict(p)
    ha = {}
    for side in ("R", "L"):
        h = hands.get("hand" + side)
        if h is not None:
            ha[side] = px_to_design((h[0] + off[0], h[1] + off[1]), d)
    q["handAt"] = ha
    q["reachFrac"] = 1.06
    return q


def fold_elbows(d, p):
    """정면·뒷면: 손이 어깨 가까이 올라온 팔(앞으로 흔든 팔)은 팔꿈치를 몸 안쪽으로 접는다 — 바깥으로 뻗은 '날개 팔' 방지."""
    R0 = hero.build(d, {k: v for k, v in p.items() if k != "post"})
    el = dict(p.get("elbow") or {})
    m = -1 if d == "up" else 1
    for side, s in (("L", 1), ("R", -1)):
        h = p["handAt"].get(side)
        if h is None or side in el:
            continue
        sh = R0.anchors["shoulder" + side]
        if h[1] - sh[1] < 17.0:
            el[side] = -m * s
    q = dict(p)
    q["elbow"] = el or None
    return q


def render(d, p):
    q = {k: v for k, v in p.items() if k != "post"}
    R = hero.draw_rig(d, q)
    im = motion.apply_post(R.image, R, d, p)
    return R, im


def hand_err(R, hands, off, d):
    e = 0.0
    for side in ("R", "L"):
        h = hands.get("hand" + side)
        if h is None:
            continue
        a = hero.to_px(R.anchors["hand" + side])
        e = max(e, math.hypot(a[0] - h[0] - off[0], a[1] - h[1] - off[1]))
    return e


def render_sheet(body, new_fn, old_fn, src_cols=None, free_hands=False):
    """body = 'player_idle' 등. new_fn/old_fn = direction → [pose]. src_cols = 새 프레임 i 가 따르는 옛 프레임(기본 i).
    반환 {d: [dict(img, rig, off, hands, err)]}."""
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
            Ro = hero.build(d, {k: v for k, v in olds[i].items() if k != "post"})
            ca, cb = hero.to_px(R.anchors["chest"]), hero.to_px(Ro.anchors["chest"])
            back_off = (round(ca[0] - cb[0]), round(ca[1] - cb[1]))
            lst.append(dict(img=im, rig=R, off=off, back_off=back_off, src=cols[i], hands=new_hands, eye=eye_of(R, d, pn), chest=chest_of(R),
                            err=0.0 if free_hands else hand_err(R, hands, off, d)))
        out[d] = lst
    return out


def eye_of(R, d, p):
    """분노한 눈(해부 왼눈) 중심 도트 — 눈빛 꼬리 fx 자리. 뒷모습·눈 감은 프레임은 None. 오른쪽 보기는 먼 눈(머리 뒤로 새는 빛 자리)."""
    if d == "up" or p.get("eyeOff"):
        return None
    hx, hy = R.anchors["head"]
    if d == "down":
        q = (hx + 4.2, hy + 1.6)
    else:
        f = 1 if d == "right" else -1
        q = (hx + f * 4.6, hy + 1.4)
    return [round(c, 1) for c in hero.to_px(q)]


def chest_of(R):
    return [round(c, 1) for c in hero.to_px(R.anchors["chest"])]


def scar_of(R):
    return dict(R.scar)
