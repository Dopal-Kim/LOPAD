"""단검 손에 든 무기 시트 11종 — weapons/v3/dagger_<동작> (틀·프레임·ms·피벗·앵커 그대로, 그림만 '재 발톱')."""
import d5
import blade as BL
from d5 import Cv

SHEETS = ["dagger_carry_idle", "dagger_carry_walk", "dagger_carry_run", "dagger_carry_dash", "dagger_combo1", "dagger_combo2",
          "dagger_combo3", "dagger_flurry", "dagger_special", "dagger_backstab", "dagger_fan_throw"]
DESIGN = ("61 단계 5 '재 발톱' — 손에 감기는 짧은 곡선 날(역수): 볼록한 등은 재빛 강철(외곽 G1 · 등 빛 G7~G9), 오목한 안쪽 날선 1 도트 호박(A19→A21, "
          "판정 칸 A23→A25 · 끝 A26), 끝이 날선 쪽으로 휜 발톱 끝, 붕대 손잡이(대부분 주먹 아래), 손잡이 끝 손가락 고리(무쇠 G3~G8, 판정 칸 호박 한 점). "
          "fade = 그림자에 녹는 먹빛(구멍 듬성) · embers = 날선 밝음 + 불티")


def geos(meta, fr):
    """프레임마다 Geo(축·가림). 행 안에서 날선 쪽 부호를 이어받아 휙휙 뒤집히지 않게."""
    out = {}
    for ri, d in enumerate(meta["directions"]):
        prev = None
        row = []
        for i, im in enumerate(fr[ri]):
            g = meta["gripAnchors"][d][i]
            t = meta["bladeTipAnchors"][d][i]
            geo = BL.Geo(g, t, old=im, facing=BL.FACING.get(d, (1, 0)), prev_sign=prev)
            prev = geo.sign
            row.append(geo)
        out[d] = row
    return out


def state_of(meta, i):
    st = (meta.get("frameStates") or [None] * 99)[i]
    if i in (meta.get("glowFrames") or []):
        return "glow"
    if st in ("glow", "full", "release"):
        return "glow"
    if st in ("fade", "embers"):
        return st
    return "steel"


def build_sheet(name, skin=None):
    m, fr = d5.grid("weapons/v3/" + name)
    G = geos(m, fr)
    skin = skin or BL.BaseSkin()
    rows = []
    glow_cols = set()
    for ri, d in enumerate(m["directions"]):
        row = []
        for i, old in enumerate(fr[ri]):
            st = state_of(m, i)
            if st == "glow":
                glow_cols.add(i)
            cv = Cv(*old.size)
            BL.paint(cv, G[d][i], skin, st)
            if name == "dagger_fan_throw" and (m.get("fanFrames") or [None])[i] in ("form", "held"):
                hand = m["handAnchors"][d][i].get("handL")
                BL.mini_talons(cv, G[d][i], hand, skin, "steel")
            row.append(cv.im)
        rows.append(row)
    n = d5.check(name, rows, sorted(glow_cols), d5.HERO, 16)
    meta = dict(m)
    meta.update(design=DESIGN, designPrevious=m.get("design"), source=d5.SRC, version=d5.VERSION, r61s5=d5.R61S5,
                colors=n, glowRule="판정 칸(glowFrames·frameStates glow)만 날선 A23~A25 · 끝 A26. 그 밖은 A23 이하")
    if name == "dagger_fan_throw":
        meta["fangNote"] = "gather(f0)·wind(f1) 칸은 왼손 손가락 사이에 작은 발톱 날 3(옛 송곳니 3자루 자리) — 투척 뒤 칸에는 없음"
    meta.pop("designRef", None)
    d5.write_grid("weapons", "v3", name, rows, meta)
    return rows, G


def build(only=None):
    res = {}
    for s in SHEETS:
        if only and not any(o in s for o in only):
            continue
        res[s] = build_sheet(s)
        print("weapon", s)
    return res


if __name__ == "__main__":
    import sys
    build(sys.argv[1:] or None)
