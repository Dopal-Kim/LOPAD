"""61 단계 5 칼 fx 빌드 — kfxsheets(은선 베기, 다시 그림) + recolor(갈래 2단·준비 표시 등 보조 fx 는 모양 유지·은선 램프로 색만 이음)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kcommon as C  # noqa: E402

PRIMARY = ["katana_rise", "katana_fall", "katana_counter", "katana_fall_wide", "katana_spin", "katana_thrust", "katana_thrust_ki1",
           "katana_thrust_ki2", "katana_thrust_ki3", "katana_iai", "katana_iai_ki1", "katana_iai_ki2", "katana_iai_ki3", "katana_guardbreak",
           "hit_katana", "hit_katana_heavy"] + ["katana_issen_line_t%d%s" % (t, s) for t in (1, 2, 3, 4) for s in ("", "_solo")] + \
          ["%s_awaken" % b for b in ("katana_rise", "katana_fall", "katana_fall_wide", "katana_spin", "katana_thrust", "katana_issen_line_t1",
                                    "katana_issen_line_t2", "katana_issen_line_t3", "katana_issen_line_t4")]
# 보조: 모양(붓획)은 그대로 두고 호박 잉크 램프만 은선 램프로(같은 디자인 언어의 색) — 갈래 2단(시험장)·준비 표시·각성 시그니처
RECOLOR = ["katana_iai_ready", "katana_spin_ready", "katana_whirl_loop", "katana_whirl_reflect", "katana_moon_trail", "katana_cleave_crack",
           "katana_execute", "katana_mirror_ki", "katana_mirror_parry"]

PAL_NOTE = ("61 단계 5: 칼 fx 는 무채 16(G4~G14)·청강 SL·백열 X0/X1(glowFrames 만) + 호박 불티 A19~A25 — 53 Q61 '재·호박 잉크만'을 칼에 한해 은선 램프로 바꿈"
            "(대검·단검·활은 그대로). paletteSwap none")


def _hex(c):
    return "#%02x%02x%02x" % tuple(c[:3])


def job(name):
    import kfx as F
    import kfxsheets as S
    rel = "fx/v3/" + name
    meta = C.old_meta(rel)
    _, old = F.head_grid(rel)
    if name in RECOLOR:
        frames = recolor_frames(old)
        design = (meta.get("design") or "") + " · 61 단계 5: 호박 잉크 → 은선 램프로 색만 바꿈(모양·타이밍 그대로)"
    else:
        frames = S.render(name, meta, old)
        design = S.design_of(name)
    glow = set(meta.get("glowFrames") or [])
    C.check(rel, frames, glow, F.HOT)
    cols = C.colors(frames)
    m = dict(meta)
    m.update(version=C.VERSION, source=C.SRC, design=design, colors=len(cols), palette=PAL_NOTE,
             r61s5="61 단계 5 P13 §2 칼 재디자인(무기+이펙트 함께) — 틀·피벗·프레임·ms·행·판정 앵커(hitOriginInFrame·impactFrame 등)·glowFrames 그대로, 그림만 교체")
    if "brushStroke" in m:                      # 키 값은 그대로(시스템이 frameRoles·hold 규칙에 쓸 수 있음), 그림 말투만 표시
        m["strokeStyle"] = "silver_slit"
        m["strokeNote"] = "56 Q11 붓획 → 61 단계 5 은선 베기(가는 빛 틈 + 잔상 실선 + 베인 자국 소멸). drawnArc·frameRoles 의 기하·역할은 그대로"
    info = C.write_grid(rel, frames, m)
    return rel, len(cols), info


def recolor_frames(old):
    """호박·재 잉크 → 은선(밝기 순서 유지). 백열 X0/X1·A26 은 그대로(glowFrames 규칙 유지)."""
    import kfx as F
    G, SL = F.G, F.SL
    MAP = {
        (0x3f, 0x27, 0x1d): SL[2], (0x65, 0x3b, 0x24): SL[4], (0x8b, 0x4d, 0x22): SL[6], (0xd6, 0x7a, 0x11): G[9],
        (0xe2, 0xa3, 0x3c): G[11], (0xee, 0xcc, 0x78): G[13], (0xf4, 0xde, 0x9b): F.A26,
        (0x2a, 0x1e, 0x17): SL[1], (0x3b, 0x2a, 0x1f): SL[2], (0x4f, 0x38, 0x28): SL[3], (0x66, 0x4a, 0x33): SL[5],
        (0x45, 0x40, 0x3b): SL[3], (0x5c, 0x55, 0x4e): SL[5], (0x75, 0x6c, 0x62): SL[6], (0x90, 0x85, 0x7a): SL[7],
    }
    out = {}
    for d, lst in old.items():
        o = []
        for im in lst:
            im = im.copy()
            p = im.load()
            W, H = im.size
            bb = im.getbbox()
            if bb:
                for y in range(bb[1], bb[3]):
                    for x in range(bb[0], bb[2]):
                        c = p[x, y]
                        if c[3] and c[:3] in MAP:
                            p[x, y] = MAP[c[:3]][:3] + (c[3],)
            o.append(im)
        out[d] = o
    return out


def build(only=None, procs=8):
    from multiprocessing import Pool
    names = [n for n in PRIMARY + RECOLOR if not only or any(o in n for o in only)]
    C.snapshot_meta(["fx/v3/" + n for n in PRIMARY + RECOLOR])
    res = []
    with Pool(procs) as p:
        for r in p.imap_unordered(job, names):
            print(r[0], "colors", r[1], flush=True)
            res.append(r)
    return res


if __name__ == "__main__":
    build(sys.argv[1:] or None)
