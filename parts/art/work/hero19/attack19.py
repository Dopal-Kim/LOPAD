"""P19 공격 몸 재작업 — 칼 3연격·대검 관성 순환 3타(무게 프레임 추가)·단검 3연격.

방식 b+(loco 와 같음): 무기 그림은 그대로, 몸만 새 자세. 프레임마다 정수 오프셋 = 새 몸 허리띠 − 옛 몸 허리띠(그림에서 잰 값) + 역할별
추가(대검 버팀 = 칼을 더 들어 올림 · 끌림 = 앞으로 쏠림). 손은 옛 handAnchors + 오프셋에 IK 고정. 같은 프레임 번호의 무기 오버레이
(v3·v4·각성·검기·울분)와 스미어 fx(fx/v3/<동작>_smear)를 같은 오프셋으로 옮긴다.

자세 규칙(키아트 OVERHEAD SLASH): 예비동작에서 크게 감고(허리 비틀기·뒷발 디딤) → 휘두름에서 깊이 내딛고 상체가 칼 쪽으로 쏠림 →
여운(잔심)에서 낮게 뻗은 채 버팀 → 풀림. 대검은 무게: 들어 올릴 때 몸이 뒤로 젖혀지며 앞발 뒤꿈치가 들리고, 정점에서 떨며 버팀,
내려칠 때 어깨·허리가 칼에 끌려 앞으로 쏠렸다가(끌림) 다시 끌어올림(버팀·잇기).

대검 '느린 구간' 채우기(도영 님 추가 지시): 75ms 이상인 예비·버팀·끌림·버팀 프레임을 둘로 나눈다(ms 반씩 — 구 프레임 시작 ms·hitAt·
cancelAt 불변). 나눈 뒤 칸은 몸이 계속 움직이고(감기 → 떨며 버팀 / 쏠림 → 끌어올림) 무기는 같은 그림을 다른 오프셋으로 둔다.
JSON p19FrameMap = 옛 프레임 → 새 프레임들, 프레임 번호 필드는 새 번호(시작 필드 = 첫 칸, 목록 = 전부).
"""
import copy
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import body19 as B  # noqa: E402
import sync19 as S  # noqa: E402
import hero  # noqa: E402
from hero import pose, WD, PL  # noqa: E402

sys.path.insert(0, os.path.join(S.WORK, "combo58"))
import rig34  # noqa: E402

rig34.install()
DIAG = list(rig34.PSI)
SIDE = ("left", "right")
SRC = "parts/art/work/hero19/attack19.py (P19 공격 몸 재자세 · 무기 오버레이 오프셋 동기 · 대검 무게 프레임 추가)"

# 역할별 자세(측면 오른쪽 기준). crouch·tilt(앞 +)·gdx(몸 앞 이동)·far/near 발(x, 들림)·lunge(0~1.5, 정면 발 내딛기)·extra(무기 추가 오프셋 도트 (앞, 위))
STYLE = {
    "katana": {
        "windup": dict(crouch=5.0, tilt=6.0, gdx=-1.5, far=(-10.0, 0), near=(7.0, 0), lunge=0.2, twist=1.0, extra=(0, 0)),
        "heave": dict(crouch=6.0, tilt=12.0, gdx=-0.5, far=(-12.0, 0), near=(10.0, 1), lunge=0.6, twist=1.2, extra=(0, 0)),
        "strike": dict(crouch=8.0, tilt=24.0, gdx=2.0, far=(-16.0, 0), near=(15.0, 0), lunge=1.3, twist=0.7, extra=(2, 0)),
        "follow": dict(crouch=8.5, tilt=27.0, gdx=2.5, far=(-17.0, 1), near=(15.0, 0), lunge=1.4, twist=0.5, extra=(2, 0)),
        "link": dict(crouch=5.5, tilt=15.0, gdx=0.5, far=(-11.0, 0), near=(9.0, 0), lunge=0.6, twist=0.6, extra=(0, 0)),
    },
    "dagger": {
        "windup": dict(crouch=6.5, tilt=14.0, gdx=-1.0, far=(-10.0, 0), near=(8.0, 0), lunge=0.4, twist=1.0, extra=(0, 0)),
        "heave": dict(crouch=7.5, tilt=18.0, gdx=0.0, far=(-12.0, 0), near=(11.0, 1), lunge=0.8, twist=1.0, extra=(0, 0)),
        "strike": dict(crouch=8.5, tilt=28.0, gdx=2.5, far=(-15.0, 2), near=(15.0, 0), lunge=1.4, twist=0.6, extra=(2, 0)),
        "follow": dict(crouch=8.0, tilt=24.0, gdx=2.0, far=(-14.0, 1), near=(13.0, 0), lunge=1.2, twist=0.5, extra=(1, 0)),
        "link": dict(crouch=6.5, tilt=16.0, gdx=0.5, far=(-11.0, 0), near=(9.0, 0), lunge=0.6, twist=0.6, extra=(0, 0)),
    },
    "greatsword": {
        "windup": dict(crouch=4.0, tilt=-5.0, gdx=-2.0, far=(-12.0, 0), near=(7.0, 0), lunge=0.0, twist=1.3, extra=(0, 0)),
        "hold": dict(crouch=6.0, tilt=-10.0, gdx=-3.0, far=(-13.0, 0), near=(6.0, 2), lunge=-0.2, twist=1.6, extra=(0, -2)),
        "heave": dict(crouch=7.0, tilt=6.0, gdx=-0.5, far=(-13.0, 0), near=(14.0, 0), lunge=0.9, twist=1.0, extra=(0, 0)),
        "strike": dict(crouch=9.0, tilt=21.0, gdx=2.0, far=(-17.0, 0), near=(16.0, 0), lunge=1.4, twist=0.4, extra=(2, 0)),
        "drag": dict(crouch=10.0, tilt=27.0, gdx=3.5, far=(-15.0, 3), near=(16.0, 0), lunge=1.5, twist=-0.2, extra=(4, 2)),
        "catch": dict(crouch=8.0, tilt=14.0, gdx=2.5, far=(-12.0, 0), near=(14.0, 0), lunge=1.1, twist=0.0, extra=(2, 0)),
        "link": dict(crouch=5.0, tilt=6.0, gdx=1.0, far=(-10.0, 0), near=(9.0, 0), lunge=0.6, twist=0.3, extra=(0, 0)),
    },
}
ROLE_MAP = {"pull": "windup", "coil": "windup", "hold": "hold", "launch": "heave", "extend": "strike", "zanshin": "follow",
            "settle": "follow", "withdraw": "link", "recover": "link", "windup": "windup", "heave": "heave", "strike": "strike",
            "drag": "drag", "catch": "catch", "link": "link", "planted": "strike"}

SHEETS = {
    "katana_rise": "katana", "katana_fall": "katana", "katana_thrust": "katana",
    "greatsword_sweep_cw": "greatsword", "greatsword_cleave": "greatsword", "greatsword_sweep_ccw": "greatsword",
    "dagger_combo1": "dagger", "dagger_combo2": "dagger", "dagger_combo3": "dagger",
}
SMEARS = {"katana_fall": ["fx/v3/katana_fall_smear", "fx/v3/katana_fall_wide_smear"]}
SPLIT_MIN_MS = 75
SPLIT_ROLES = ("windup", "hold", "drag", "catch")


def roles_of(meta, weapon):
    n = meta["frames"]
    if meta.get("frameRoles"):
        r = [ROLE_MAP.get(x, "link") for x in meta["frameRoles"]]
    else:
        imp, hits = meta["impactFrame"], meta.get("hitFrames") or [meta["impactFrame"]]
        ph = meta.get("phases") or {}
        r = []
        for i in range(n):
            if i < imp:
                r.append("heave" if i == imp - 1 else "windup")
            elif i in hits or i in ph.get("cut", [])[:1]:
                r.append("strike")
            elif i == n - 1:
                r.append("link")
            else:
                r.append("follow")
    if weapon != "greatsword":
        r = ["windup" if x == "hold" else ("follow" if x in ("drag", "catch") else x) for x in r]
    return r


def lerp_style(a, b, t):
    out = {}
    for k in a:
        if isinstance(a[k], tuple):
            out[k] = tuple(a[k][j] + (b[k][j] - a[k][j]) * t for j in range(len(a[k])))
        else:
            out[k] = a[k] + (b[k] - a[k]) * t
    return out


def blade_tw(meta, i, d):
    """(비틀림 −1~1, 날 높이 elev 도) — 무기 방향(bladeLocal)에서."""
    bl = meta.get("bladeLocalByDirection", {}).get(d) if meta.get("bladeLocalByDirection") else None
    v = (bl or meta.get("bladeLocal") or [None] * meta["frames"])[i]
    if not v or v.get("thetaDeg") is None:
        return 0.0, 0.0
    return max(-1.0, min(1.0, math.sin(math.radians(v["thetaDeg"])))), (v.get("elevDeg") or 0.0)


def rise_adjust(st, elev, weapon):
    """올려 든 칼(높은 elev): 몸이 칼을 따라 펴진다 — 숙임·웅크림을 덜어 '얼굴을 땅에 박은' 자세를 막음. 대검 버팀은 제외(뒤로 젖힘 유지)."""
    if elev <= 12.0 or st["tilt"] < 0:
        return st
    k = min(1.0, (elev - 12.0) / 30.0)
    st = dict(st)
    st["tilt"] = st["tilt"] * (1.0 - 0.75 * k)
    st["crouch"] = st["crouch"] - 2.5 * k
    st["gdx"] = st["gdx"] * (1.0 - 0.5 * k)
    return st


# -----------------------------------------------------------------------------
# 자세 만들기
# -----------------------------------------------------------------------------
def make_pose(d, st, tw, i, weapon, glow):
    tw = tw * st["twist"]
    lg = st["lunge"]
    common = dict(crouch=st["crouch"], flame=i % 6, pulse=1 if glow else 0, eyeHot=1, kneeIK=True, glow=1 if glow else 0)
    if d in SIDE:
        return pose(tilt=st["tilt"], gdx=st["gdx"], foot=(st["far"], st["near"]), lean_body=0.6, hdx=1.0,
                    sway=-1.5 - 2.5 * max(0.0, lg), lean=-2.0 - 2.5 * max(0.0, lg), **common)
    if d in DIAG:
        sx = 1 if rig34.PSI[d] > 0 else -1
        return rig34.pose34(lean_f=0.6 + st["tilt"] / 12.0, twist_deg=-18.0 * tw, squash=0.03 * max(0.0, st["tilt"] / 10.0),
                            head=round(st["tilt"] / 10.0) + 1,
                            feet=((7.0 - 0.5 * lg, -2.5 - 4.0 * lg), (-7.0 + 0.5 * lg, 2.5 + 6.5 * lg)),
                            lift=(0, st["near"][1]), sway=-1.0 * sx + 1.5 * tw - 1.5 * lg, lean=-2.0 * tw - 1.0 * sx, **common)
    sgn = 1 if d == "down" else -1
    fwd = st["tilt"] / 25.0
    return pose(step=(-2.5 * lg * sgn, 5.5 * lg * sgn), footdx=(1.2 * lg, -1.2 * lg), stanceW=1.5 + 1.2 * abs(lg),
                twist=-3.4 * tw, shift=-1.2 * tw, stilt=-1.4 * tw, squash=max(-0.06, 0.12 * fwd), head=round(2 * fwd) + 1,
                sway=2.0 * tw - 1.0 * lg, lean=-2.0 * tw, tilt=-3.0 * tw if d == "down" else 3.0 * tw, **common)


def draw(d, p):
    q = {k: v for k, v in p.items() if k != "post"}
    if d in DIAG:
        return rig34.draw_rig8(d, q)
    return hero.draw_rig(d, q)


CLOTH_RGB = None


def belt(im):
    """허리천(가장 큰 가죽색 덩어리)의 윗줄: (x 평균, y) — 옛·새 몸 그림에서 같은 방법으로 재 오프셋을 정한다.
    가죽색(WD)은 가슴 끈·화살대·완갑 끈에도 있지만 허리천+허리띠가 압도적으로 큰 덩어리다."""
    global CLOTH_RGB
    if CLOTH_RGB is None:
        CLOTH_RGB = {tuple(c[:3]) for c in (WD[0], WD[1], WD[2], WD[3], WD[4])}
    px = im.load()
    W, H = im.size
    cells = {(x, y) for y in range(H) for x in range(W) if px[x, y][3] and px[x, y][:3] in CLOTH_RGB}
    best = []
    seen = set()
    for c in cells:
        if c in seen:
            continue
        comp, st = [], [c]
        seen.add(c)
        while st:
            x, y = st.pop()
            comp.append((x, y))
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    n = (x + dx, y + dy)
                    if n in cells and n not in seen:
                        seen.add(n)
                        st.append(n)
        if len(comp) > len(best):
            best = comp
    if len(best) < 20:
        return None
    rows = {}
    for x, y in best:
        rows.setdefault(y, []).append(x)
    mw = max(len(v) for v in rows.values())
    y0 = min(y for y, v in rows.items() if len(v) >= 0.6 * mw)      # 끈(가는 사선)이 붙어도 넓은 허리띠 줄부터
    top = [x for y in range(y0, y0 + 3) for x in rows.get(y, [])]
    return (sum(top) / len(top), y0)


def hand_visible(im, h):
    if h is None:
        return False
    px = im.load()
    band = {tuple(c[:3]) for c in (PL[0], PL[1], PL[2])}
    x, y = int(round(h[0])), int(round(h[1]))
    hits = 0
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if 0 <= x + dx < 96 and 0 <= y + dy < 144 and px[x + dx, y + dy][3] and px[x + dx, y + dy][:3] in band:
                hits += 1
    return hits >= 2


def fwd_vec(d):
    return {"right": (1, 0), "left": (-1, 0), "down": (0, 1), "up": (0, -1), "down-right": (1, 1), "down-left": (-1, 1),
            "up-right": (1, -1), "up-left": (-1, -1)}[d]


# -----------------------------------------------------------------------------
# 프레임 계획(대검 나누기)
# -----------------------------------------------------------------------------
def frame_plan(meta, roles, weapon):
    """→ [(옛 프레임, 몫 0/1, 칸 수, ms)]"""
    plan = []
    for i, ms in enumerate(meta["frameDurationsMs"]):
        if weapon == "greatsword" and roles[i] in SPLIT_ROLES and ms >= SPLIT_MIN_MS and i not in (meta.get("hitFrames") or []):
            a = ms // 2
            plan += [(i, 0, 2, a), (i, 1, 2, ms - a)]
        else:
            plan.append((i, 0, 1, ms))
    return plan


SUB = {  # 나눈 칸의 두 번째 몫: 다음 역할 쪽으로 이만큼 진행 + 떨림
    "windup": 0.5, "hold": 0.35, "drag": 0.5, "catch": 0.5,
}


def style_at(weapon, roles, i, part, parts):
    sty = STYLE[weapon]
    r = roles[i]
    st = dict(sty[r])
    if parts == 2:
        nxt = sty[roles[i + 1]] if i + 1 < len(roles) else sty["link"]
        t = SUB[r] * (0.5 if part == 0 else 1.0)
        st = lerp_style(sty[r], nxt, t)
        if r == "hold":                       # 정점에서 떨며 버팀: 몫마다 몸이 반대로 미세하게 · 칼은 더 들림
            st["gdx"] += -0.6 if part == 0 else 0.4
            st["extra"] = (0, -1 if part == 0 else -3)
        if r == "drag" and part == 1:          # 끌림 뒤 몫: 칼이 박히고 몸이 앞으로 가장 쏠림
            st["tilt"] += 3.0
            st["extra"] = (st["extra"][0] + 1, st["extra"][1] + 1)
        if r == "catch" and part == 1:         # 다시 끌어올림
            st["extra"] = (st["extra"][0], st["extra"][1] - 1)
    return st


def render_attack(name):
    weapon = SHEETS[name]
    body = "player_" + name
    meta, bim = S.src_grid("player/v3/" + body)
    wmeta = S.src_meta("weapons/v3/" + name)
    for k in ("bladeLocal", "bladeLocalByDirection"):
        if k in wmeta:
            meta[k] = wmeta[k]
    roles = roles_of(meta, weapon)
    plan = frame_plan(meta, roles, weapon)
    old = S.cells(meta, bim)
    glow = set(meta.get("glowFrames") or meta.get("hitFrames") or [])
    out = {}
    for d in meta["directions"]:
        lst = []
        fv = fwd_vec(d)
        for k, (i, part, parts, ms) in enumerate(plan):
            st = style_at(weapon, roles, i, part, parts)
            tw, elev = blade_tw(meta, i, d)
            st = rise_adjust(st, elev, weapon)
            p = make_pose(d, st, tw, k, weapon, i in glow)
            R0 = draw(d, p)
            bo, bn = belt(old[d][i]), belt(R0.image)
            off = (0, 0) if (bo is None or bn is None) else (bn[0] - bo[0], bn[1] - bo[1])
            assert abs(off[0]) <= 18 and abs(off[1]) <= 18, (name, d, i, "허리띠 측정 이상", bo, bn)
            ex = st["extra"]
            off = (round(off[0] + ex[0] * fv[0]), round(off[1] + ex[0] * fv[1] * 0.5 + ex[1]))
            hands = meta["handAnchors"][d][i]
            q = B.pinned_pose(d if d not in DIAG else "down", p, hands, off)
            if d in SIDE:
                near = "R" if d == "right" else "L"
                far = "L" if near == "R" else "R"
                q["farArmFront"] = hand_visible(old[d][i], hands.get("hand" + far))
            else:
                q["armBack"] = tuple(s for s in ("R", "L") if not hand_visible(old[d][i], hands.get("hand" + s)))
                if d not in DIAG:
                    q = B.fold_elbows(d, q)
            R = draw(d, q)
            err = B.hand_err(R, hands, off, d)
            for _ in range(3):                     # 팔이 닿지 않으면 무기를 손이 닿는 쪽으로 옮김(오프셋 보정)
                if err <= 1.0:
                    break
                worst = max((s_ for s_ in ("R", "L") if hands.get("hand" + s_)),
                            key=lambda s_: math.dist(hero.to_px(R.anchors["hand" + s_]), (hands["hand" + s_][0] + off[0], hands["hand" + s_][1] + off[1])))
                a_ = hero.to_px(R.anchors["hand" + worst])
                off = (round(a_[0] - hands["hand" + worst][0]), round(a_[1] - hands["hand" + worst][1]))
                q = dict(q, handAt=B.pinned_pose(d if d not in DIAG else "down", p, hands, off)["handAt"])
                R = draw(d, q)
                err = B.hand_err(R, hands, off, d)
            new_hands = {kk: [round(c, 1) for c in hero.to_px(R.anchors[kk])] for kk in ("handR", "handL")}
            lst.append(dict(img=R.image, rig=R, off=off, back_off=off, src=i, part=part, ms=ms, hands=new_hands, err=err,
                            role=roles[i]))
        out[d] = lst
    return out, meta, plan, roles


# -----------------------------------------------------------------------------
# 프레임 번호 다시 매기기
# -----------------------------------------------------------------------------
START_KEYS = ("impactFrame", "cancelFromFrame", "holdFrame", "releaseFrame", "teleportAfterFrame")
LIST_KEYS = ("hitFrames", "activeFrames", "glowFrames", "anticipationFrames", "recoverFrames", "holdFrames", "dragFrames",
             "smearFrames", "sweepFrames", "decayFrames", "releaseFrames")


def reindex(m, fmap):
    """fmap = 옛 프레임 → [새 프레임들]."""
    def L(lst):
        return sorted({j for i in lst for j in fmap.get(i, [])})
    for k in START_KEYS:
        if isinstance(m.get(k), int):
            m[k] = fmap[m[k]][0]
    for k in LIST_KEYS:
        if isinstance(m.get(k), list) and all(isinstance(x, int) for x in m[k]):
            m[k] = L(m[k])
    if isinstance(m.get("phases"), dict):
        m["phases"] = {k: L(v) for k, v in m["phases"].items()}
    for k in ("stepPx", "dragStepPx"):
        if isinstance(m.get(k), dict) and isinstance(m[k].get("frames"), list):
            m[k] = dict(m[k], frames=L(m[k]["frames"]))
    return m


def remap_sheet(meta, fr, plan, fmap, n_old, extra_note):
    """오버레이·스미어·몸 공용: 프레임별 목록 재배열 + 앵커 이동 + 번호 다시 + ms."""
    pl = {d: [(f["src"], f["off"][0], f["off"][1]) for f in fr[d]] for d in fr if d in meta["directions"]}
    m = S.remap_meta(meta, pl, n_old)
    # 방향별 프레임 목록(bladeLocalByDirection 등) — remap_meta 가 다루지 않는 것
    for k, v in list(m.items()):
        if isinstance(v, dict) and k in ("bladeLocalByDirection",):
            m[k] = {d: ([lst[c] for c, _, _ in pl[d]] if d in pl and isinstance(lst, list) and len(lst) == n_old else lst) for d, lst in v.items()}
        if k in ("frameRoles",) and isinstance(v, list) and len(v) == n_old:
            m[k] = [v[i] for (i, _, _, _) in plan]
    m["frameDurationsMs"] = [ms for (_, _, _, ms) in plan]
    m["fps"] = round(1000.0 * len(plan) / sum(m["frameDurationsMs"]), 2)
    if len(plan) != n_old:
        m = reindex(m, fmap)
        m["p19FrameMap"] = {str(k): v for k, v in fmap.items()}
        m["p19FrameMapNote"] = "P19 대검 무게: 옛 프레임 → 새 프레임들(75ms 이상 예비·버팀·끌림·버팀 칸을 반씩 둘로). 구 프레임 시작 ms·timingMs 불변"
    m["p19"] = extra_note
    return m, pl


def build(names=None):
    names = names or list(SHEETS)
    for name in names:
        weapon = SHEETS[name]
        fr, meta, plan, roles = render_attack(name)
        n_old = meta["frames"]
        fmap = {}
        for k, (i, _, _, _) in enumerate(plan):
            fmap.setdefault(i, []).append(k)
        err = max(f["err"] for d in fr for f in fr[d])
        body = "player_" + name
        bm = S.src_meta("player/v3/" + body)
        m, pl = remap_sheet(bm, fr, plan, fmap, n_old, "P19 공격 몸 재자세(키아트 OVERHEAD SLASH): 큰 예비동작 → 깊은 내딛기 → 낮은 잔심. 무기 오버레이는 weaponOffsetDots 만큼 옮김")
        m["handAnchors"] = {d: [f["hands"] for f in fr[d]] for d in fr}
        m["scarAnchor"] = {d: [B.scar_of(f["rig"]) for f in fr[d]] for d in fr}
        m["weaponOffsetDots"] = {d: [list(f["off"]) for f in fr[d]] for d in fr}
        m["p19Roles"] = [fr[meta["directions"][0]][k]["role"] for k in range(len(plan))]
        m["source"], m["previousSource"] = SRC, bm.get("source")
        S.write_grid("player/v3/" + body, {d: [f["img"] for f in fr[d]] for d in bm["directions"]}, m)
        rels = S.family(body) + [r for r in ["fx/v3/%s_smear" % name] + SMEARS.get(name, []) if S.exists_src(r)]
        rels = list(dict.fromkeys(rels))
        lost = 0
        newpiv, outs = {}, []
        for rel in rels:
            om, oim = S.src_grid(rel)
            if om["frames"] != n_old:
                print("  ! 프레임 수 다름, 건너뜀", rel, om["frames"])
                continue
            pl2 = {d: [(f["src"], f["off"][0], f["off"][1]) for f in fr[d]] for d in fr if d in om["directions"]}
            cells, ls = S.move_cells(om, oim, pl2, grow_tl=(weapon == "greatsword"))   # 대검 틀은 JSON 크기·피벗을 읽는 규약(§17) → 왼쪽·위로도 키움
            nm, _ = remap_sheet(om, fr, plan, fmap, n_old, "P19: 몸 새 자세에 맞춰 프레임마다 weaponOffsetDots 만큼 옮김(그림 그대로)" +
                                (" · 대검 무게 프레임 나눔(p19FrameMap)" if len(plan) != n_old else ""))
            g = om.get("p19FrameGrowTL")
            if g:
                nm = S.shift_frame_coords(nm, g["addLeft"], g["addTop"])
            newpiv[rel] = nm.get("pivot")
            outs.append((rel, cells, nm))
            lost += ls
        base = "weapons/v3/" + name
        for rel, cells, nm in outs:                   # 각성·v4 의 weaponSheetPivot·pivotDelta 를 원 무기 시트의 새 피벗에 맞춤
            if "weaponSheetPivot" in nm and newpiv.get(base):
                bp = newpiv[base]
                nm["weaponSheetPivot"] = dict(bp)
                nm["pivotDelta"] = {"x": nm["pivot"]["x"] - bp["x"], "y": nm["pivot"]["y"] - bp["y"]}
            S.write_grid(rel, cells, nm)
        print(name, dict(frames="%d→%d" % (n_old, len(plan)), handErr=round(err, 2), synced=len(rels), lostPx=lost,
                         off_right=[tuple(f["off"]) for f in fr["right"]]))
