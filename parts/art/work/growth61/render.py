"""프레임 하나 → (a1, a2, glow) 세 장. 시트(원 무기 프레임)와 미리보기 정지 그림(합성 무기 프레임)이 같은 경로를 쓴다."""
import math

import g61 as Z
import br61 as BR
from g61 import F, PO, OV

SHEATHED = OV.SHEATHED_STATES


def _recolor(ctx, geo, br, f, weapon):
    px = ctx.px
    for p in geo.pts:
        c = Z.hx(px[p])
        if weapon == "katana" and (c in PO.SLSET or c in PO.PLSET):
            continue
        if weapon == "dagger" and c in PO.PLSET:
            continue
        if weapon == "katana":
            cls = "edge" if c in PO.EDGE_HEX else "steel"
        else:
            cls = "amber" if c in PO.AMBER else "steel"
        ud, vd = geo.loc(*p)
        col = br.recolor(cls, BR.lum(px[p]), ud, vd, f)
        if col:
            ctx.put_orig(p, col)


def render(weapon, bid, im, tip=None, grip=None, hand_r=None, state=None, glow=False, ms0=0, sheathed=False, refine=False, skip=False):
    """→ (a1 RGBA, a2 RGBA, glow RGBA) — 크기 = 원 프레임 + PAD(기존 _awaken 틀)."""
    br = BR.REG[bid]
    c1, c2, c3 = PO.Ctx(im, weapon), PO.Ctx(im, weapon), PO.Ctx(im, weapon)
    if skip:
        return c1.finish(), c2.finish(), c3.finish()
    t_aw = int(ms0 / PO.LOOP[weapon][1]) % PO.LOOP[weapon][0]      # 60라운드 그림 재사용분의 순환 위상
    t = int(ms0 / br.loop_ms) % br.tn
    if weapon == "katana":
        geo = Z.katana_geo(im, tip, grip, sheathed, refine)
    elif weapon == "greatsword":
        geo = Z.gs_geo(im, grip, tip)
    elif weapon == "dagger":
        geo = Z.dagger_geo(im, grip, tip)
    else:
        geo = Z.bow_geo(im, grip, tip, hand_r, state)
    f = F(p=1.0, t=t, tn=br.tn, glow=glow, flip=geo.flip)
    # ---- a1
    if br.reuse:
        if weapon == "katana":
            PO.katana_frame(c1, tip, grip, glow, sheathed, refine, t_aw)
        elif weapon == "greatsword":
            PO.gs_frame(c1, grip, tip, glow, t_aw)
        elif weapon == "dagger":
            PO.dagger_frame(c1, grip, tip, glow, t_aw)
        else:
            PO.bow_frame(c1, grip, tip, hand_r, state, glow, t_aw)
        if geo.kind == "blade" and hasattr(br, "a1_extra"):
            br.a1_extra(c1, geo, f)
    elif geo.kind == "sheathed":
        br.s1(c1, geo, f)
    elif geo.kind in ("blade", "short"):
        _recolor(c1, geo, br, f, weapon)
        if geo.kind == "blade":
            br.a1(c1, geo, f)
    elif geo.kind == "bow":
        br.a1(c1, geo, f)
    # ---- a2 · glow
    if geo.kind == "sheathed":
        br.s2(c2, geo, f)
        br.sg(c3, geo, f)
    elif geo.kind in ("blade", "bow"):
        br.a2(c2, geo, f)
        br.gl(c3, geo, f)
    return c1.finish(), c2.finish(), c3.cv.image()


# =============================================================================
# 합성 무기 프레임(미리보기 정지 그림용) — awaken60 base.py 설계 도트(weapons_v3 규격 근사)를 실제 크기로 그린다
# =============================================================================
STILL = {
    # 틀, 쥔 곳(코등이) 위치, 각도(도), 설계 상자, 끝까지 길이
    "katana": dict(size=(192, 192), g=(78, 118), deg=-42, box=(-18, 60, -6, 6), L=58),
    "greatsword": dict(size=(240, 272), g=(92, 168), deg=-42, box=(-26, 94, -11, 11), L=93),
    "dagger": dict(size=(192, 192), g=(88, 104), deg=-42, box=(-10, 27, -5, 5), L=26),
    "bow": dict(size=(192, 192), g=(92, 98), deg=-42, box=(-24, 6, -32, 32), L=20),
}


def still_frame(weapon, deg=None):
    """→ (원 무기 그림 RGBA, tip, grip). 활은 (줌통, 쏘는 방향 앞 20)."""
    s = STILL[weapon]
    W, H = s["size"]
    cv = Z.Cv(W, H)
    ang = math.radians(s["deg"] if deg is None else deg)
    g = s["g"]
    import base as B
    if weapon == "katana":
        fn = lambda u, v, x, y: B.katana(u, v)              # noqa: E731
    elif weapon == "greatsword":
        fn = lambda u, v, x, y: B.greatsword(u, v)          # noqa: E731
    elif weapon == "dagger":
        fn = lambda u, v, x, y: B.dagger(u, v)              # noqa: E731
    else:
        def fn(u, v, x, y):
            c = B.bow_limb(u, v, 0.0)
            if c:
                return c
            if abs(u + 5.0) < 0.5 and abs(v) < 29.5:
                return (Z.PL[3], True)
            return None
    cv.shape(g, ang, s["box"], fn)
    cv.outline(Z.INK)
    im = cv.image()
    tip = Z.K6.L2W(g, ang, s["L"], 0)
    return im, (tip[0], tip[1]), (g[0], g[1])
