"""칼 기본 무기 시트 25 — 판정 칸 날 빛과 '칼끝 빛줄기'(tipTrail)만 서리 색으로 다시 그림.
katana61s5 의 3D 경로(ksrc + kdesign + wbuild.job)를 그대로 부르고, 이 프로세스 안에서만
  · kdesign P 의 판정 칸(g_ji·g_shin)·둘째 판정 칸 은빛(s_*) 색
  · wbuild.tip_trail 의 색
을 서리 램프로 바꿔 끼운다(katana61s5 파일은 고치지 않음). 날 본체(평소 강철 G13/G11·청강 SL)·손잡이·칼집은 그대로.
틀·피벗·프레임·ms·행·앵커(칼끝 앵커 assert 포함)는 wbuild.job 이 검사.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
K61 = os.path.normpath(os.path.join(HERE, "..", "katana61s5"))
sys.path.insert(0, HERE)
sys.path.insert(0, K61)

import aio  # noqa: E402
import ramps as R  # noqa: E402


def hx(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


F = {k: hx(v) for k, v in R.FROST.items()}
X0 = (255, 255, 255, 255)

GLOW_NOTE = ("61 단계 6 (P14 §2 칼 '서리'): 판정 칸 날 = 날선 X0 · 바탕 서리 흰빛 #e6fcff · 속 #8fe3ff · 등 청강 SL6, "
             "둘째 판정 칸부터 = 날선 #bff3ff · 바탕 #8fe3ff · 속 #5cc6ee(X0 없음). 칼끝 빛줄기 = 머리 #e6fcff(첫 판정 칸) → #8fe3ff → #5cc6ee → #3d9ccf 점선. "
             "평소 날(강철)·손잡이·칼집은 그대로")


def patch():
    import kdesign as KD
    import wbuild as W
    orig = KD.install

    def install(K, hero):
        first = KD._installed.get("K") is not K
        orig(K, hero)
        if first or not KD._installed.get("frost"):
            P = KD._installed["P"]
            P.update({"g_ji": F["white"], "g_shin": F["main"],
                      "s_edge": F["pale"], "s_tip": F["pale"], "s_ji": F["main"], "s_ji_hi": F["pale"], "s_shin": F["f5"]})
            KD._installed["frost"] = True
    KD.install = install
    W.tip_trail = tip_trail


def tip_trail(frames, tips, glow):
    """katana61s5/wbuild.tip_trail 과 같은 기하, 색만 서리."""
    import kfx as KF
    if not glow:
        return
    after = {max(glow) + 1}
    for d, lst in frames.items():
        T = tips.get(d) or []
        for i, im in enumerate(lst):
            if i not in glow and i not in after:
                continue
            if i - 1 < 0 or T[i - 1] is None or T[i] is None:
                continue
            cx, cy = 96.0, 132.0
            (x0, y0), (x1, y1) = T[i - 1], T[i]
            a0, a1 = math.atan2(y0 - cy, x0 - cx), math.atan2(y1 - cy, x1 - cx)
            da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
            r0, r1 = math.hypot(x0 - cx, y0 - cy), math.hypot(x1 - cx, y1 - cy)
            if abs(da) < 0.12 or min(r0, r1) < 20:
                continue
            curve = []
            for k in range(41):
                t = k / 40.0
                a_, r_ = a0 + da * t, r0 + (r1 - r0) * t
                curve.append((cx + math.cos(a_) * r_, cy + math.sin(a_) * r_))
            keep, acc = [curve[-1]], 0.0
            for q in reversed(curve[:-1]):
                acc += math.hypot(q[0] - keep[-1][0], q[1] - keep[-1][1])
                keep.append(q)
                if acc > 30:
                    break
            curve = list(reversed(keep))
            path = []
            for a, b in zip(curve, curve[1:]):
                for q in KF.clean_line(a, b):
                    if not path or path[-1] != q:
                        path.append(q)
            if len(path) < 6:
                continue
            px = im.load()
            W_, H_ = im.size
            m = len(path)
            hot = i in glow and (i - 1) not in glow
            soft = i in glow and not hot
            for j, (x, y) in enumerate(path):
                back = m - 1 - j
                if not (1 <= x < W_ - 1 and 1 <= y < H_ - 1) or px[x, y][3]:
                    continue
                if soft:
                    c_ = F["main"] if back < 14 else (F["f5"] if back < 24 else (F["f3"] if back % 3 else None))
                elif hot:
                    c_ = F["white"] if back < 5 else (F["main"] if back < 14 else (F["f5"] if back < 24 else (F["f3"] if back % 3 else None)))
                else:
                    c_ = (F["f5"] if back < 8 else (F["f3"] if back < 20 else None)) if (j % 4) != 1 else None
                if c_ is not None:
                    px[x, y] = c_


def has_glow(meta):
    return bool(meta.get("glowFrames")) or "glow" in (meta.get("frameStates") or [])


def build(only=None, procs=8):
    import json
    from multiprocessing import Pool
    patch()
    import wbuild as W
    import kcommon as C
    js = [j for j in W.all_jobs() if j[0] == "base" and (not only or any(o == j[1] or o in j[1] for o in only))]
    # 판정 칸이 없는 시트(휴대·발도·납도)는 칼끝 빛줄기·판정 빛이 없어 그림이 그대로 → 건드리지 않음
    js = [j for j in js if has_glow(C.old_meta("weapons/v3/" + j[1]))]
    C.snapshot_meta(sorted({"weapons/v3/" + j[1] for j in js}))
    out = []
    with Pool(procs) as p:
        for r in p.imap_unordered(W.job, js):
            rel = r[0]
            jp = os.path.join(C.SPR, rel + ".json")
            m = json.load(open(jp, encoding="utf-8"))
            m["color61s6"] = GLOW_NOTE
            m["glowRule"] = m.get("glowRule", "") if "서리" in m.get("glowRule", "") else GLOW_NOTE
            if "tipTrail" in m:
                m["tipTrail"] = m["tipTrail"].split(" — 61 단계 6")[0] + " — 61 단계 6: 서리 색(머리 #e6fcff → #8fe3ff → #5cc6ee → #3d9ccf)"
            aio.write_atlas_json(jp, m)
            print(rel, "colors", r[1], "edge", r[2], flush=True)
            out.append(rel)
    return out


if __name__ == "__main__":
    build(sys.argv[1:] or None)
