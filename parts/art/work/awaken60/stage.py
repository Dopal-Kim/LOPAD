"""시안 미리보기 조립 — 주인공 몸(에셋 읽기만) 위에 각성 무기를 그려 '대기 · 휘두르기 2 · 색 전환 띠' 키아트급 미리보기 + GIF.

원래 무기 시트에서 날 부분만 지우고(주먹·칼집 유지) 그 자리에 시안 무기를 다시 그린다. 에셋은 바꾸지 않는다.
"""
import math
import os

from PIL import Image

import kit60 as K
from kit60 import Cv, F, BG

M = 72          # 맥락 칸 여백(각성 무기가 원래 무기 틀 192/240×272 밖으로 나감 — 틀 확대 여부는 인터뷰)


def comps(im):
    px = im.load()
    W, H = im.size
    seen = set()
    out = []
    for y in range(H):
        for x in range(W):
            if px[x, y][3] and (x, y) not in seen:
                st = [(x, y)]
                seen.add((x, y))
                c = []
                while st:
                    p = st.pop()
                    c.append(p)
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            q = (p[0] + dx, p[1] + dy)
                            if 0 <= q[0] < W and 0 <= q[1] < H and q not in seen and px[q][3]:
                                seen.add(q)
                                st.append(q)
                out.append(c)
    return out


def axis(pose):
    jw, wf = K.sheet_frame("weapons/v3/" + pose["ws"], pose["wi"])
    g = pose.get("grip") or jw["gripAnchors"]["right"][pose["wi"]]
    if pose.get("tip"):
        t = pose["tip"]
    elif pose.get("ang") is not None:
        a = math.radians(pose["ang"])
        t = (g[0] + 50 * math.cos(a), g[1] + 50 * math.sin(a))
    else:
        cs = comps(wf)
        c = min(cs, key=lambda cc: min((x - g[0]) ** 2 + (y - g[1]) ** 2 for x, y in cc) - len(cc) * 0.01)
        t = max(c, key=lambda p: (p[0] - g[0]) ** 2 + (p[1] - g[1]) ** 2)
        t = (t[0] + 0.5, t[1] + 0.5)
    return jw, wf, tuple(g), tuple(t)


def context(concept, pose, f, trail_frac=1.0):
    jw, wf, g, t = axis(pose)
    jb, bf = K.sheet_frame("player/v3/" + pose["bs"], pose["bi"])
    off = jw["playerFrameOffset"]
    W, H = wf.width + 2 * M, wf.height + 2 * M
    ang = math.atan2(t[1] - g[1], t[0] - g[0])
    if pose.get("erase") == "all":
        rest = Image.new("RGBA", wf.size, (0, 0, 0, 0))
    else:
        ln = math.hypot(t[0] - g[0], t[1] - g[1]) or 1
        a0 = (g[0] + (t[0] - g[0]) * 2.5 / ln, g[1] + (t[1] - g[1]) * 2.5 / ln)
        rest = K.erase_seg(wf, a0, t, pose.get("erase", 4), umin=0.0, umax=1.15, extra=pose.get("erase_extra"))
    G0 = (g[0] + M, g[1] + M)
    mid = K.L2W(G0, ang, concept.reach * 0.5, 0)
    img = K.glow_bg(W, H, mid[0], mid[1], concept.bg, r=concept.reach * 0.75 + 30)
    img.alpha_composite(bf, (off["x"] + M, off["y"] + M))
    cv = Cv(W, H)
    tr = pose.get("trail")
    if tr and f.p > 0:
        S = (tr["S"][0] + M, tr["S"][1] + M)
        tipW = K.L2W(G0, ang, concept.reach, 0)
        r1 = math.hypot(G0[0] - S[0], G0[1] - S[1]) + concept.trail_in
        r2 = math.hypot(tipW[0] - S[0], tipW[1] - S[1])
        a1 = math.atan2(tipW[1] - S[1], tipW[0] - S[0])
        sweep = math.radians(tr["sweep"]) * trail_frac
        a0 = a1 - sweep * tr.get("dir", 1)
        concept.trail(cv, S, r1, r2, a0, a1, f, G0, ang)
    if pose.get("arrow_fly") and f.p > 0 and hasattr(concept, "arrow_fly"):
        concept.arrow_fly(cv, G0, ang, f, pose["arrow_fly"])
    f.handR = None
    if "handR_from" in pose:
        hr = jw["handAnchors"]["right"][pose["wi"]]["handR"]
        f.handR = (hr[0] + M, hr[1] + M)
    concept.draw(cv, G0, ang, f)
    img.alpha_composite(cv.image())
    img.alpha_composite(rest, (M, M))
    return img


def isolated(concept, f, ang=-0.6, size=420):
    cv = Cv(size, size)
    G0 = (size // 2 - int(concept.reach * 0.45 * math.cos(ang)), size // 2 - int(concept.reach * 0.45 * math.sin(ang)))
    f.handR = None
    concept.draw(cv, G0, ang, f)
    return cv


def crop_union(cvs, m=6):
    boxes = [c.image().getbbox() for c in cvs]
    boxes = [b for b in boxes if b]
    x0 = min(b[0] for b in boxes) - m
    y0 = min(b[1] for b in boxes) - m
    x1 = max(b[2] for b in boxes) + m
    y1 = max(b[3] for b in boxes) + m
    return [c.image().crop((x0, y0, x1, y1)) for c in cvs]


def label(im, s, sz=15):
    out = Image.new("RGBA", (im.width, im.height + 22), K.hexrgb(BG) + (255,))
    K.text(out, (4, 2), s, sz, fill=(190, 190, 184))
    out.alpha_composite(im, (0, 22))
    return out


def preview(concept, poses, outdir):
    """키아트급 미리보기 PNG + GIF. 반환 = (미리보기 이미지, 요약 칸 이미지들)."""
    os.makedirs(outdir, exist_ok=True)
    tag = concept.key
    # A. 원래 → 각성 (같은 각도·같은 배율)
    hero_ang = concept.hero_ang
    base_cv = isolated(concept, F(p=0.0, t=0, tn=concept.tn), ang=hero_ang)
    full_f = F(p=1.0, t=concept.hero_t, tn=concept.tn, glow=True, draw=concept.hero_draw)
    aw_cv = isolated(concept, full_f, ang=hero_ang)
    b_im, a_im = crop_union([base_cv, aw_cv], m=8)
    ks = max(3, min(10, int(900 / max(a_im.width, a_im.height))))
    b_big = K.up(K.on_bg(b_im), ks)
    a_big = K.up(K.glow_bg(a_im.width, a_im.height, a_im.width / 2, a_im.height / 2, concept.bg, r=max(a_im.size) * 0.55), ks)
    a_big.alpha_composite(K.up(a_im, ks))
    rowA = K.stack_h([label(b_big, "원래 무기 (각성 전)", 20), label(a_big, f"각성 {concept.name} — 순환 {concept.hero_t}프레임째 · 판정 밝기", 20)], gap=24)

    # B. 맥락 3칸
    ctx = []
    for pose in poses:
        f = F(p=1.0, t=pose.get("t", 2), tn=concept.tn, glow=pose.get("glow", False), draw=pose.get("draw", 0.0),
              release=pose.get("release", False), flip=pose.get("flip", 1))
        ctx.append(label(K.up(context(concept, pose, f), 3), pose["name"], 20))
    rowB = K.stack_h(ctx, gap=16)

    # C. 색 전환 띠 (가로, 판정 밝기 아님)
    strip_ang = concept.strip_ang
    tr_cvs = [isolated(concept, F(p=i / (concept.trans_n - 1), t=0, tn=concept.tn, draw=concept.strip_draw), ang=strip_ang)
              for i in range(concept.trans_n)]
    lp_cvs = [isolated(concept, F(p=1.0, t=i, tn=concept.tn, draw=concept.strip_draw), ang=strip_ang) for i in range(concept.tn)]
    ims = crop_union(tr_cvs + lp_cvs, m=4)
    k3 = max(2, min(4, int(3000 / (concept.trans_n * ims[0].width))))
    tr_ims = [label(K.up(K.on_bg(im), k3), f"전환 {i} · {i * concept.trans_ms}ms") for i, im in enumerate(ims[:concept.trans_n])]
    lp_ims = [label(K.up(K.on_bg(im), k3), f"순환 {i} · {i * concept.loop_ms}ms") for i, im in enumerate(ims[concept.trans_n:])]
    rowC1 = K.stack_h(tr_ims, gap=6)
    rowC2 = K.stack_h(lp_ims, gap=6)

    # D. 칩 + 설명
    ch = K.up(K.chips([("전 " + n, r) for n, r in concept.ramps_before] + [("후 " + n, r) for n, r in concept.ramps_after]), 2)
    W = max(rowA.width, rowB.width, rowC1.width, rowC2.width)
    head = K.text_block(W, [(f"[{concept.key}] {concept.weapon_ko} 각성 '{concept.name}' 시안 — {concept.title}", 30, None),
                            ("형태: " + concept.form, 19, None), ("색 전환: " + concept.color, 19, None), ("이펙트: " + concept.fx, 19, None),
                            (f"색 수(각성 무기 단독, 테 포함): {len(aw_cv.colors())} · 전환 {concept.trans_n}프레임×{concept.trans_ms}ms · "
                             f"순환 {concept.tn}프레임×{concept.loop_ms}ms · 맥락 칸은 원래 무기 틀 + 사방 {M}도트 여백", 16, (170, 170, 164))])
    sec = lambda im, s: K.caption(im, s, 20, 32)  # noqa: E731
    out = K.stack_v([head, sec(rowA, "A. 실루엣 변화 — 원래 무기 ↔ 각성 무기 (같은 각도·같은 배율)"),
                     sec(rowB, "B. 맥락 — 대기 · 휘두르기 1 · 휘두르기 2 (주인공 몸 = 현재 에셋, 배경 조명은 연출)"),
                     sec(rowC1, "C-1. 각성 순간 색 전환 (픽셀 단위 문턱, 반투명 없음)"),
                     sec(rowC2, "C-2. 각성 상태 주기 순환"),
                     sec(ch, "D. 램프 (LOPAD 팔레트)")], gap=14)
    out = K.pad(out, 12)
    if max(out.size) > 8000:
        k = 8000 / max(out.size)
        out = out.resize((int(out.width * k), int(out.height * k)), Image.NEAREST)
    out.save(os.path.join(outdir, f"{tag}_preview.png"))

    # GIF: 대기(전환 → 순환) → 휘두르기 1 → 휘두르기 2(궤적 자람) → 대기 순환
    frames, ms = [], []
    idle, sA, sB = poses
    for i in range(concept.trans_n):
        frames.append(context(concept, idle, F(p=i / (concept.trans_n - 1), t=0, tn=concept.tn, flip=idle.get("flip", 1))))
        ms.append(concept.trans_ms if i else 300)
    for i in range(concept.tn):
        frames.append(context(concept, idle, F(p=1.0, t=i, tn=concept.tn, flip=idle.get("flip", 1))))
        ms.append(concept.loop_ms)
    for i in range(3):
        frames.append(context(concept, sA, F(p=1.0, t=i, tn=concept.tn, draw=sA.get("draw", 0.0), flip=sA.get("flip", 1))))
        ms.append(90)
    for i, fr in enumerate((0.35, 0.7, 1.0, 1.0)):
        frames.append(context(concept, sB, F(p=1.0, t=i, tn=concept.tn, glow=i < 3, draw=sB.get("draw", 0.0), release=sB.get("release", False),
                                             flip=sB.get("flip", 1)), trail_frac=fr))
        ms.append(50 if i < 3 else 160)
    for i in range(concept.tn):
        frames.append(context(concept, idle, F(p=1.0, t=i, tn=concept.tn, flip=idle.get("flip", 1))))
        ms.append(concept.loop_ms)
    K.save_gif(frames, os.path.join(outdir, f"{tag}.gif"), ms, k=3)
    a1x = K.glow_bg(a_im.width, a_im.height, a_im.width / 2, a_im.height / 2, concept.bg, r=max(a_im.size) * 0.55)
    a1x.alpha_composite(a_im)
    summary = {"hero": a_big, "base": b_big, "hero_1x": a1x, "base_1x": K.on_bg(b_im), "ctx": ctx[2], "strip": rowC1, "loop": rowC2}
    return out, summary
