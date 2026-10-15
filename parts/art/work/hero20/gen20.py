"""P20 2단계 — P19 에서 손대지 않은 몸 시트 전부(칼 iai·counter·spin·guardbreak·issen(_dash)·crescent·draw·sheathe·special·combo1~3,
대검 charge*·slam·tackle·leap_slam·brace_upswing·guard_rush·draw·sheathe·special·dashslash·combo1~3, 단검 backstab·flurry·fan_throw·special,
활 전부, attack, groggy)를 새 리그로 다시 자세 잡기.

방식(P19 attack19 와 같음 — b+): 무기 그림은 그대로. 프레임 역할(frameRoles → phases → impactFrame 순)에서 몸 자세 결(STYLE)을 고르고,
옛 몸 그림의 허리띠 높이로 웅크림을 읽어(옛 안무 유지) 새 몸을 그린 뒤, 오프셋 = 새 허리띠 − 옛 허리띠(그림에서 잰 값) 만큼 그 몸을 쓰는
오버레이 전부(v3·v4·각성·검기·울분·a1·a2·a2_glow)와 스미어를 옮기고 손을 옛 handAnchors + 오프셋에 IK 고정한다. 프레임 수·ms 그대로.
"""
import copy
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import body20 as B  # noqa: E402
import rig20  # noqa: E402
import sync19 as S  # noqa: E402
import attack19 as A19  # noqa: E402  (belt · hand_visible · fwd_vec · blade_tw · rise_adjust · STYLE · rig34.pose34)
import hero  # noqa: E402
from hero import pose  # noqa: E402

rig34 = A19.rig34
_RISE, _BLADE = A19.rise_adjust, A19.blade_tw      # build.py attack 단계가 A19 쪽을 바꿔도 gen 은 원래 함수
DIAG = A19.DIAG
SIDE = ("left", "right")
SRC = "parts/art/work/hero20/gen20.py (P20 새 몸 리그 — 역할 결 재자세 · 무기 오버레이 오프셋 동기)"

ST = copy.deepcopy(A19.STYLE)
for w in ("katana", "dagger", "greatsword"):
    base = ST[w]
    base.setdefault("hold", dict(base["windup"], crouch=7.5, tilt=14.0, far=(-12.0, 0), near=(10.0, 0), lunge=0.5))
    base["guard"] = dict(crouch=6.0, tilt=6.0, gdx=-1.0, far=(-11.0, 0), near=(8.0, 0), lunge=0.3, twist=0.6, extra=(0, 0))
    base["crouch"] = dict(crouch=11.0, tilt=22.0, gdx=-0.5, far=(-9.0, 0), near=(8.0, 0), lunge=0.2, twist=0.4, extra=(0, 0))
    base["air"] = dict(crouch=3.0, tilt=12.0, gdx=0.0, far=(-7.0, 7), near=(6.0, 9), lunge=0.2, twist=0.5, extra=(0, 0))
    base["rush"] = dict(crouch=10.0, tilt=34.0, gdx=-1.0, far=(-18.0, 2), near=(12.0, 0), lunge=1.5, twist=0.4, extra=(0, 0))
    base["dazed"] = dict(crouch=6.0, tilt=20.0, gdx=0.0, far=(-7.0, 0), near=(6.0, 0), lunge=0.0, twist=0.2, extra=(0, 0))
    base["stand"] = dict(crouch=4.5, tilt=12.0, gdx=-0.5, far=(-9.0, 0), near=(8.0, 0), lunge=0.3, twist=0.6, extra=(0, 0))
ST["bow"] = {
    "bstand": dict(crouch=3.5, tilt=5.0, gdx=-0.5, far=(-9.0, 0), near=(8.0, 0), lunge=0.4, twist=0.5, extra=(0, 0), tension=0.0),
    "bdraw": dict(crouch=4.5, tilt=3.0, gdx=-1.0, far=(-11.0, 0), near=(9.0, 0), lunge=0.6, twist=0.8, extra=(0, 0), tension=0.6),
    "bhold": dict(crouch=5.0, tilt=1.0, gdx=-1.0, far=(-12.0, 0), near=(10.0, 0), lunge=0.7, twist=1.0, extra=(0, 0), tension=1.0),
    "brelease": dict(crouch=4.5, tilt=8.0, gdx=0.0, far=(-12.0, 0), near=(10.0, 0), lunge=0.8, twist=0.6, extra=(0, 0), tension=0.3),
    "brenock": dict(crouch=4.5, tilt=6.0, gdx=-0.5, far=(-11.0, 0), near=(9.0, 0), lunge=0.6, twist=0.6, extra=(0, 0), tension=0.4),
    "breload": dict(crouch=4.0, tilt=9.0, gdx=-0.5, far=(-10.0, 0), near=(8.0, 0), lunge=0.4, twist=0.4, extra=(0, 0), tension=0.2),
    "dazed": dict(ST["katana"]["dazed"], tension=0.0),
}

KW = [  # (정규식, 역할) — frameRoles / phases 이름(괄호 앞)에서
    (r"^(windup|coil|pull|gather|wind|enter|cock|turn|grab|start|grip|depart)$", "windup"),
    (r"^(hold|brace|loop|charge|iaistance|heat\d?|ready 루프|ready루프)$", "hold"),
    (r"^(heave|launch|drop|sweep|rise|apex|shove|slip|over|lift|draw)$", "heave"),
    (r"^(strike|cut|impact|plunge|stab|drive|spin|land|arrive)$", "strike"),
    (r"^(dash|rush)$", "rush"),
    (r"^(zanshin|follow|deep|twist|rip|planted|retract|primed|riposte)$", "follow"),
    (r"^(drag)$", "drag"),
    (r"^(catch)$", "catch"),
    (r"^(guard|window)$", "guard"),
    (r"^(crouch)$", "crouch"),
    (r"^(air|flip)$", "air"),
    (r"^(recover|ready|noto|chiburi|settle|end|link|lower|drawn|seat|behind|release|stand|insert|click|sheathe|dashcatch|raise)$", "link"),
    (r"^(swayright|swayleft)$", "dazed"),
]
BOW_KW = [
    (r"^(draw|raise|raise_nock|aim)$", "bdraw"), (r"^(full|hold|strain)$", "bhold"), (r"^(release|follow)$", "brelease"),
    (r"^(renock)$", "brenock"), (r"^(reach|materialize|bring|refill|settle)$", "breload"),
    (r"^(lower|ready|stand|start|end|recover|volley)$", "bstand"), (r"^(swayright|swayleft)$", "dazed"),
]
SPECIAL_ROLES = {  # 역할 이름이 무기마다 다른 것
    ("katana", "catch"): "guard", ("katana", "release"): "heave", ("katana", "draw"): "heave",
    ("greatsword", "release"): "strike", ("greatsword", "hold"): "hold",
}
CUSTOM = {
    "attack": ["bdraw", "bdraw", "bhold", "brelease", "brelease", "bstand", "bstand"],
    "bow_aim": ["bdraw", "bdraw", "bdraw", "bhold", "bhold", "bhold", "brelease", "bstand"],
}


def weapon_of(name):
    if name in ("attack",) or name.startswith("bow_"):
        return "bow"
    if name == "groggy":
        return "katana"
    return name.split("_")[0]


def _key(s):
    s = s.split("(")[0].strip().lower()
    return s.replace(" ", "")


def map_role(w, s):
    k = _key(s)
    if (w, k) in SPECIAL_ROLES:
        return SPECIAL_ROLES[(w, k)]
    for rx, r in (BOW_KW if w == "bow" else KW):
        if re.match(rx, k):
            return r
    return "bstand" if w == "bow" else "link"


def roles_of(name, meta, w):
    n = meta["frames"]
    if name in CUSTOM:
        return list(CUSTOM[name])
    if meta.get("frameRoles"):
        return [map_role(w, x) for x in meta["frameRoles"]]
    ph = meta.get("phases") or {}
    if ph and all(isinstance(v, list) for v in ph.values()):
        out = [None] * n
        for k, v in ph.items():
            for i in v:
                if 0 <= i < n and out[i] is None:
                    out[i] = map_role(w, k)
        hits = set(meta.get("hitFrames") or [])
        for i in range(n):
            if i in hits and w != "bow":
                out[i] = "strike"
        last = "bstand" if w == "bow" else "link"
        for i in range(n):
            if out[i] is None:
                out[i] = out[i - 1] if i else last
        return out
    if meta.get("impactFrame") is not None:
        return A19.roles_of(meta, w)
    return ["link"] * n


# -----------------------------------------------------------------------------
# 자세
# -----------------------------------------------------------------------------
def make_pose(d, st, tw, i, w, glow, role):
    tw = tw * st["twist"]
    lg = st["lunge"]
    ten = st.get("tension", 0.0)
    common = dict(crouch=st["crouch"], flame=i % 6, pulse=1 if glow else 0, eyeHot=0 if role == "dazed" else 1, kneeIK=True,
                  glow=1 if glow else 0, tension=ten)
    if role == "dazed":
        common["head"] = 3
    if d in SIDE:
        far, near = st["far"], st["near"]
        p = pose(tilt=st["tilt"], gdx=st["gdx"], foot=(far, near), lean_body=0.6, hdx=1.0,
                 sway=-1.5 - 2.5 * max(0.0, lg), lean=-2.0 - 2.5 * max(0.0, lg), **common)
        if role == "dazed":
            p["tilt"] += 4.0 * math.sin(i * 1.3)
        return p
    if d in DIAG:
        sx = 1 if rig34.PSI[d] > 0 else -1
        lift = (st["far"][1], st["near"][1])
        return rig34.pose34(lean_f=0.6 + st["tilt"] / 12.0, twist_deg=-18.0 * tw, squash=0.03 * max(0.0, st["tilt"] / 10.0),
                            head=round(st["tilt"] / 10.0) + 1 + (2 if role == "dazed" else 0),
                            feet=((7.0 - 0.5 * lg, -2.5 - 4.0 * lg), (-7.0 + 0.5 * lg, 2.5 + 6.5 * lg)),
                            lift=lift, sway=-1.0 * sx + 1.5 * tw - 1.5 * lg, lean=-2.0 * tw - 1.0 * sx,
                            **{k: v for k, v in common.items() if k != "head"})
    sgn = 1 if d == "down" else -1
    fwd = st["tilt"] / 25.0
    p = pose(step=(-2.5 * lg * sgn, 5.5 * lg * sgn), footdx=(1.2 * lg, -1.2 * lg), stanceW=1.5 + 1.2 * abs(lg),
             twist=-3.4 * tw, shift=-1.2 * tw, stilt=-1.4 * tw, squash=max(-0.06, 0.12 * fwd),
             sway=2.0 * tw - 1.0 * lg, lean=-2.0 * tw, tilt=-3.0 * tw if d == "down" else 3.0 * tw,
             lift=(st["far"][1], st["near"][1]), **{k: v for k, v in common.items() if k != "head"})
    p["head"] = round(2 * fwd) + 1 + (2 if role == "dazed" else 0)
    if role == "dazed":
        p["tilt"] += 5.0 * math.sin(i * 1.3) * (1 if d == "down" else -1)
        p["shift"] += 1.5 * math.sin(i * 1.3)
    return p


_REF = {}


def ref_belt(d):
    """옛 원본 대기 0 프레임의 허리띠 y(옛 몸 기준 웅크림 1) — 옛 안무의 웅크림을 읽는 기준."""
    if d not in _REF:
        dd = d if d in ("down", "up", "left", "right") else ("down" if d.startswith("down") else "up")
        meta, im = S.src_grid("player/v3/player_idle")
        bo = A19.belt(S.cells(meta, im)[dd][0])
        _REF[d] = bo[1] if bo else 86
    return _REF[d]


def draw(d, p):
    R = rig20.draw_rig(d, B.clean(p))
    R.image.info["_rig"] = R
    return R


_belt0 = A19.belt


def belt(im):
    """허리띠 윗줄 — 새 몸은 리그가 아는 허리띠·허리천 부위만 본다(가슴 끈·화살대가 같은 가죽색이라 섞이지 않게)."""
    R = im.info.get("_rig")
    if R is None:
        return _belt0(im)
    q = hero.to_px(R.anchors["beltTop"])
    return (q[0], round(q[1]))


A19.belt = belt


def render_generic(name):
    w = weapon_of(name)
    body = "player_" + name
    meta, bim = S.src_grid("player/v3/" + body)
    try:
        wmeta = S.src_meta("weapons/v3/" + name)
        for k in ("bladeLocal", "bladeLocalByDirection"):
            if k in wmeta:
                meta[k] = wmeta[k]
    except Exception:
        pass
    roles = roles_of(name, meta, w)
    sty = ST[w]
    old = S.cells(meta, bim)
    glow = set(meta.get("glowFrames") or meta.get("hitFrames") or [])
    empty = set(meta.get("bodyInOverlayFrames") or [])
    out = {}
    for d in meta["directions"]:
        lst = []
        fv = A19.fwd_vec(d)
        for i in range(meta["frames"]):
            role = roles[i]
            st = dict(sty.get(role) or sty.get("link") or sty["bstand"])
            hands = meta["handAnchors"][d][i] if meta.get("handAnchors") else {}
            if i in empty or old[d][i].getbbox() is None:
                lst.append(dict(img=old[d][i].copy(), rig=None, off=(0, 0), back_off=(0, 0), src=i, hands=hands, err=0.0, role=role,
                                empty=True))
                continue
            tw, elev = _BLADE(meta, i, d)
            if w != "bow":
                st = _RISE(st, elev, w)
            bo = belt(old[d][i])
            if bo is not None:                     # 옛 안무의 웅크림(무릎 꿇기·착지)을 살림
                oc = (bo[1] - ref_belt(d)) / 1.5 + 1.0
                if oc > st["crouch"] + 1.5:
                    st["crouch"] = min(16.0, oc + 1.0)
            p = make_pose(d, st, tw, i, w, i in glow, role)
            R0 = draw(d, p)
            bn = belt(R0.image)
            off = (0, 0) if (bo is None or bn is None) else (bn[0] - bo[0], bn[1] - bo[1])
            assert abs(off[0]) <= 22 and abs(off[1]) <= 22, (name, d, i, "허리띠 측정 이상", bo, bn)
            ex = st["extra"]
            off = (round(off[0] + ex[0] * fv[0]), round(off[1] + ex[0] * fv[1] * 0.5 + ex[1]))
            if not hands:
                lst.append(dict(img=R0.image, rig=R0, off=off, back_off=off, src=i, hands={}, err=0.0, role=role))
                continue
            q = B.pinned_pose(d, p, hands, off)
            if d in SIDE:
                nr = "R" if d == "right" else "L"
                fr_ = "L" if nr == "R" else "R"
                q["farArmFront"] = A19.hand_visible(old[d][i], hands.get("hand" + fr_))
            else:
                q["armBack"] = tuple(s for s in ("R", "L") if not A19.hand_visible(old[d][i], hands.get("hand" + s)))
                if d not in DIAG:
                    q = B.fold_elbows(d, q)
            R = draw(d, q)
            err = B.hand_err(R, hands, off)
            for _ in range(3):
                if err <= 1.0:
                    break
                worst = max((s_ for s_ in ("R", "L") if hands.get("hand" + s_)),
                            key=lambda s_: math.dist(hero.to_px(R.anchors["hand" + s_]), (hands["hand" + s_][0] + off[0], hands["hand" + s_][1] + off[1])))
                a_ = hero.to_px(R.anchors["hand" + worst])
                off = (round(a_[0] - hands["hand" + worst][0]), round(a_[1] - hands["hand" + worst][1]))
                q = dict(q, handAt=B.pinned_pose(d, p, hands, off)["handAt"])
                R = draw(d, q)
                err = B.hand_err(R, hands, off)
            new_hands = {kk: [round(c, 1) for c in hero.to_px(R.anchors[kk])] for kk in ("handR", "handL")}
            lst.append(dict(img=R.image, rig=R, off=off, back_off=off, src=i, hands=new_hands, err=err, role=role))
        out[d] = lst
    return out, meta, roles


# -----------------------------------------------------------------------------
# 묶음(오버레이) — bodySheet 기준 + bodySheet 없는 칼 옛 오버레이(이름 규칙)
# -----------------------------------------------------------------------------
def family(body):
    rels = list(S.family(body))
    act = body[len("player_"):]
    if act.startswith("katana_") and not rels:
        a = act[len("katana_"):]
        pat = re.compile(r"^katana_(%s(_awaken|_ki\d)?|[a-z]+_a1_%s|[a-z]+_a2(_glow)?_%s)$" % (a, a, a))
        for rel, b in S._bodysheet_index().items():
            if not b and pat.match(os.path.basename(rel)):
                rels.append(rel)
    smear = "fx/v3/%s_smear" % act
    if S.exists_src(smear):
        rels.append(smear)
    return sorted(set(rels))


def build(names, log):
    for name in names:
        w = weapon_of(name)
        fr, meta, roles = render_generic(name)
        n = meta["frames"]
        body = "player_" + name
        bm = S.src_meta("player/v3/" + body)
        pl = {d: [(f["src"], f["off"][0], f["off"][1]) for f in fr[d]] for d in fr}
        m = S.remap_meta(bm, pl, n)
        if bm.get("handAnchors"):
            m["handAnchors"] = {d: [f["hands"] if not f.get("empty") else bm["handAnchors"][d][k] for k, f in enumerate(fr[d])] for d in fr}
        m["scarAnchor"] = {d: [B.scar_of(f["rig"]) if f["rig"] is not None else bm["scarAnchor"][d][k] for k, f in enumerate(fr[d])]
                           for d in fr} if bm.get("scarAnchor") else m.get("scarAnchor")
        m["weaponOffsetDots"] = {d: [list(f["off"]) for f in fr[d]] for d in fr}
        m["eyeAnchors"] = {d: [B.eye_of(f["rig"], d) if f["rig"] is not None else None for f in fr[d]] for d in fr}
        m["chestAnchors"] = {d: [B.chest_of(f["rig"]) if f["rig"] is not None else None for f in fr[d]] for d in fr}
        m["p20Roles"] = roles
        m["source"], m["previousSource"] = SRC, bm.get("source")
        S.write_grid("player/v3/" + body, {d: [f["img"] for f in fr[d]] for d in bm["directions"]}, m)
        lost, synced, outs, newpiv = 0, 0, [], {}
        for rel in family(body):
            om, oim = S.src_grid(rel)
            if om["frames"] != n or not set(om["directions"]) <= set(fr):
                print("  ! 프레임/방향 다름, 건너뜀", rel, om["frames"])
                continue
            pl2 = {d: pl[d] for d in om["directions"]}
            cells, ls = S.move_cells(om, oim, pl2, grow_tl=True)   # 계약 §7: 시스템은 JSON 틀·pivot·playerFrameOffset 을 읽는다
            nm = S.remap_meta(om, pl2, n)
            nm["p20"] = "P20 새 몸: 프레임마다 weaponOffsetDots(몸 JSON) 만큼 옮김(그림 그대로)"
            g = om.get("p19FrameGrowTL")
            if g:
                nm = S.shift_frame_coords(nm, g["addLeft"], g["addTop"])
            newpiv[rel] = nm.get("pivot")
            outs.append((rel, cells, nm))
            lost += ls
            synced += 1
        base = "weapons/v3/" + name
        for rel, cells, nm in outs:
            if "weaponSheetPivot" in nm and newpiv.get(base):
                bp = newpiv[base]
                nm["weaponSheetPivot"] = dict(bp)
                nm["pivotDelta"] = {"x": nm["pivot"]["x"] - bp["x"], "y": nm["pivot"]["y"] - bp["y"]}
            S.write_grid(rel, cells, nm)
        err = max(f["err"] for d in fr for f in fr[d])
        log[body] = dict(frames=n, handErrMax=round(err, 2), overlays=synced, lostPx=lost,
                         offRight=[list(f["off"]) for f in fr.get("right", [])])
        print(body, log[body])
