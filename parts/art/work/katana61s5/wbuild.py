"""61 단계 5 칼 — 손에 든 무기 시트 전부(기본 25 · 검기 _ki1~3 60 · 각성 _awaken 20 · v4 a1/a2/a2_glow 180)를
같은 3D 경로(ksrc + kdesign)로 다시 그린다. 틀·피벗·프레임·ms·행·앵커(칼끝·손·칼집 입구)는 기존 JSON 그대로.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import kcommon as C  # noqa: E402

DESIGN_BASE = ("은선(銀線) 칼 (61 단계 5 P13 §2) — 얇고 긴 연마 강철 날(날선 1도트 백광 · 청강 바탕 + 물결 하몬 · 어두운 등 테, 밑동 4 → 몸 3 → 칼끝 1도트) "
               "· 요코테 반짝 · 호박 금 하바키·카시라 · 둥근 검은 쇠 코등이 · 검은 감은 끈 손잡이(마름모 눈) · 검은 옻칠 칼집(윤기 줄 · 금 입구테·끝 장식 · 짙은 호박 끈)")
GLOW_BASE = ("판정(glow) 프레임 = 날 전체 백열(날선 X0 · 바탕 X1 · 등은 청강 SL6 로 남겨 실루엣 유지) — 56 Q50: 판정 칸이 이어지면 첫 칸만 백열, "
             "둘째 칸부터 은빛(날선 G14 · 바탕 G12/G13 · 등 SL6, X0/X1 없음 — glowFrames 는 그대로). "
             "heat1~3(회전 베기·가드 불가 내려베기 모으기) = 날이 호박으로 달아오름. 평소 = 무채 G13/G11 · 청강 SL7~SL4(층 램프 교체와 무관한 고정 무채) + 호박 금 점")
COLOR_NOTE = ("61 단계 5: 칼만 무채 16 의 밝은 칸(G11·G13, 판정 X0/X1)을 쓴다 — '재 칼날' 주인공 30색 제한(53 Q32)을 칼날에 한해 풀었다(자율 모드 아트 판단, README 61 단계 5). "
              "호박(A18~A26)은 층 램프 교체 대상 그대로")
KI_DESIGN = {
    1: "1단 — 날선 바깥 3도트에 끊어진 가는 빛줄기 1줄(칼 중간~칼끝, 위상 따라 끊김이 흐름). 칼집 안: 칼집 윤기 줄이 점선으로 밝아짐",
    2: "2단 — 날선이 G14 로 밝아지고 빛줄기 2줄(3·6도트, 바깥 줄 끊김) + 칼끝에서 오르는 호박 불티 2. 칼집 안: 윤기 줄 + 칼집 입구에서 새는 빛 4가닥",
    3: "3단 — 날 전체 G12~G14, 빛줄기 3줄(3·6·8.5도트, 칼끝에서 날선으로 오므림) + 등 쪽 잔광 + 호박 불티 4. 판정 프레임만 X0/X1. 칼집 안: 밝은 윤기 줄 + 입구 빛 5가닥",
}
BR_DESIGN = {
    "senpu": dict(
        a1="선풍 1차 — 은선 날을 청록 강철로(날선 G14 · 바탕 청록 램프) + 칼등에서 뒤로 휘어 나간 가는 바람 갈퀴 2 + 청록 코등이(바람 구멍 2) · 카시라 청록 술(바람에 날림)",
        a2="선풍 2차 덧붙임 — 날을 감아 도는 1도트 나선 바람 줄(위상 따라 흐름, 칼끝 너머로 감김) + 갈퀴 셋째",
        glow="선풍 2차 빛 — 나선 바람 줄(회백, pathTint 곱)"),
    "kabuto": dict(
        a1="투구가르기 1차 — 끝까지 4도트 폭으로 곧게 선 무쇠 날 + 끌처럼 비스듬히 잘린 칼끝 + 황동 칼등 줄 · 네모 무쇠 코등이(금 모서리 못) · 황동 카시라",
        a2="투구가르기 2차 덧붙임 — 코등이 양끝에서 날 쪽으로 휘어 오른 황동 투구 뿔 2 + 가운데 쪼개는 점선 + 등 쇠 징",
        glow="투구가르기 2차 빛 — 쪼개는 점선 · 뿔 끝(회백, pathTint 곱)"),
    "mangetsu": dict(
        a1="만월 1차 — 거울 같은 은백 날(날선 G14/X1 점 · 바탕 은 램프) + 손 둘레를 감싸는 초승달 고리 코등이(위쪽이 두꺼운 호) · 은 카시라",
        a2="만월 2차 덧붙임 — 고리 바깥 점선 테 + 고리를 도는 달 구슬 3(위상 따라 공전) + 칼집 위 작은 초승달",
        glow="만월 2차 빛 — 점선 테 · 달 구슬(회백, pathTint 곱)"),
}
AWAKEN_DESIGN = "월인(月刃) 61 단계 5 갱신 — 만월 1차(katana_mangetsu_a1_*)와 같은 그림: 거울 같은 은백 날 + 초승달 고리 코등이 · 은 카시라 · 은 칼집 장식"

HOT = {(255, 255, 255), (255, 244, 220)}

OVERLAY_SHEETS = ["katana_carry_dash", "katana_carry_drawn_dash", "katana_carry_drawn_idle", "katana_carry_drawn_run", "katana_carry_drawn_walk",
                  "katana_carry_idle", "katana_carry_run", "katana_carry_walk", "katana_counter", "katana_draw", "katana_fall", "katana_guardbreak",
                  "katana_iai", "katana_issen", "katana_issen_dash", "katana_rise", "katana_sheathe", "katana_special", "katana_spin", "katana_thrust"]
BRANCHES = ("senpu", "kabuto", "mangetsu")


def _starts(ms):
    out, t = [], 0
    for m in ms:
        out.append(t)
        t += m
    return out


def jobs_for(sheet):
    out = [("base", sheet, None, 0)]
    if sheet in OVERLAY_SHEETS:
        out += [("ki", sheet, None, lv) for lv in (1, 2, 3)]
        out += [("awaken", sheet, "mangetsu", 0)]
        out += [(lay, sheet, b, 0) for b in BRANCHES for lay in ("a1", "a2", "glow")]
    return out


def rel_of(kind, sheet, branch, lv):
    act = sheet.split("_", 1)[1]
    if kind == "base":
        return "weapons/v3/" + sheet
    if kind == "ki":
        return "weapons/v3/%s_ki%d" % (sheet, lv)
    if kind == "awaken":
        return "weapons/v3/%s_awaken" % sheet
    lay = {"a1": "a1", "a2": "a2", "glow": "a2_glow"}[kind]
    return "weapons/v4/katana_%s_%s_%s" % (branch, lay, act)


def render(kind, sheet, branch, lv, ksrc, KD):
    rel = rel_of(kind, sheet, branch, lv)
    meta = C.old_meta(rel)
    base_meta = C.old_meta("weapons/v3/" + sheet)
    layer = {"base": "base", "ki": "ki", "awaken": "a1", "a1": "a1", "a2": "a2", "glow": "glow"}[kind]
    pad = (0, 0, 192, 192)
    if kind in ("awaken", "a1", "a2", "glow"):
        pd = meta.get("pivotDelta", {"x": 36, "y": 32})
        pad = (pd["x"], pd["y"], meta["frameWidth"], meta["frameHeight"])
    glow = set(base_meta.get("glowFrames") or [])
    glow |= {i for i, st in enumerate(base_meta.get("frameStates") or []) if st == "glow"}   # 옛 연격 시트는 glowFrames 키 없이 상태만
    KD.V.update(layer=layer, branch=branch, level=lv, pad=pad, starts=_starts(base_meta["frameDurationsMs"]),
                tn=meta["loopFrames"] if isinstance(meta.get("loopFrames"), int) else 8,
                loopMs=meta["loopMs"] if isinstance(meta.get("loopMs"), int) else 80, glowFrames=glow)
    fr = ksrc.frames(sheet)
    frames = {d: [f["weapon"] for f in fr[d]] for d in meta["directions"]}
    tips = None
    if kind == "base":
        tips = {d: [f["tip"] for f in fr[d]] for d in meta["directions"]}
    return rel, meta, frames, tips, glow


def tip_trail(frames, tips, glow):
    """칼끝 빛줄기: 판정 칸(과 그다음 한 칸)에 직전 칸 칼끝에서 지금 칼끝까지 어깨 중심으로 도는 짧은 호(30도트 이내) — 날끝에서 끌리는 빛(fx 호와 칼을 한 언어로 잇기).
    날 픽셀은 덮지 않는다. 판정 칸만 X1(머리 5도트)."""
    import kfx as F
    G, SL, X1 = F.G, F.SL, F.X1
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
            # 칼끝은 어깨 둘레로 돈다 → 직전 칼끝에서 지금 칼끝까지 어깨(무기 시트 (96,132) 근처) 중심 극좌표로 보간한 호
            import math
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
            # 칼끝에서 뒤로 최대 30도트만
            keep, acc = [curve[-1]], 0.0
            for q in reversed(curve[:-1]):
                acc += math.hypot(q[0] - keep[-1][0], q[1] - keep[-1][1])
                keep.append(q)
                if acc > 30:
                    break
            curve = list(reversed(keep))
            path = []
            for a, b in zip(curve, curve[1:]):
                for q in F.clean_line(a, b):
                    if not path or path[-1] != q:
                        path.append(q)
            if len(path) < 6:
                continue
            px = im.load()
            W, H = im.size
            m = len(path)
            hot = i in glow and (i - 1) not in glow          # 56 Q50: 첫 판정 칸만 X1
            soft = i in glow and not hot
            for j, (x, y) in enumerate(path):
                back = m - 1 - j                      # 칼끝에서 거리(도트)
                if not (1 <= x < W - 1 and 1 <= y < H - 1) or px[x, y][3]:
                    continue
                if soft:
                    c_ = G[13] if back < 14 else (G[11] if back < 24 else (SL[7] if back % 3 else None))
                elif hot:
                    c_ = X1 if back < 5 else (G[13] if back < 14 else (G[11] if back < 24 else (SL[7] if back % 3 else None)))
                else:
                    c_ = (G[11] if back < 8 else (G[9] if back < 20 else None)) if (j % 4) != 1 else None
                if c_ is not None:
                    px[x, y] = c_


def job(arg):
    kind, sheet, branch, lv = arg
    import ksrc
    import kdesign as KD
    KD.install(ksrc.K, ksrc.hero)
    rel, meta, frames, tips, glow = render(kind, sheet, branch, lv, ksrc, KD)
    edge = 0
    if kind == "base":
        for lst in frames.values():
            for im in lst:
                edge += C.clear_border(im)
        tip_trail(frames, tips, glow)
        old = meta.get("bladeTipAnchors")
        if isinstance(old, dict):
            for d, lst in tips.items():
                for i, t in enumerate(lst):
                    o = old[d][i]
                    assert (t is None) == (o is None), (rel, d, i, t, o)
                    if t is not None:
                        assert abs(t[0] - o[0]) < 0.11 and abs(t[1] - o[1]) < 0.11, (rel, d, i, t, o)
    first = {i for i in glow if (i - 1) not in glow}          # 56 Q50: 이어진 판정 칸은 첫 칸만 백열
    if kind in ("base", "ki"):                 # 각성 층은 60 Q19 예외(순환에도 X1) — 반투명만 검사
        C.check(rel, frames, first if (kind == "base" or lv == 3) else set(), HOT)
    else:
        C.check(rel, frames)
    cols = C.colors(frames)
    m = dict(meta)
    m["colors"] = len(cols)
    m["source"] = C.SRC
    m["r61s5"] = "61 단계 5 P13 §2 칼 재디자인(무기+이펙트 함께) — 틀·피벗·프레임·ms·행·앵커 그대로, 그림만 교체"
    if kind == "base":
        m["version"] = C.VERSION
        m["design"] = DESIGN_BASE
        m["designRef"] = "parts/art/README.md 「61 단계 5」 절 (Gemini 미사용, 도트 직접)"
        m["glowRule"] = GLOW_BASE
        m["colorNote"] = COLOR_NOTE
        m["colorBudget"] = str(len(cols))
        m["previousDesign"] = "53 Q26 B '재 칼날'(검은 재 칼날 + 호박 균열) — git 2aa9fe6 이전"
        if isinstance(meta.get("bladeTipAnchors"), dict):
            m["tipTrail"] = ("판정 칸(glowFrames)과 그다음 한 칸에 직전 칸 칼끝 → 지금 칼끝(bladeTipAnchors)을 어깨 중심 호로 잇는 30도트 이내 가는 빛줄기를 무기 시트에 그려 둠 — "
                             "칼끝 → 휘두름 fx 호를 한 언어로 잇는다. 판정 칸만 X1")
    elif kind == "ki":
        m["version"] = C.VERSION
        m["design"] = KI_DESIGN[lv]
        m.pop("keyArt", None)
        m["sheathNote"] = "칼끝 null(칼집 안) 프레임: 칼집 윤기 줄을 단계 밝기로 + 2·3단은 칼집 입구에서 새는 빛"
    elif kind == "awaken":
        m["version"] = C.VERSION
        m["design"] = AWAKEN_DESIGN
        m["sameAs"] = "weapons/v4/katana_mangetsu_a1_" + sheet.split("_", 1)[1]
    else:
        m["version"] = C.VERSION_V4
        m["design"] = BR_DESIGN[branch][{"a1": "a1", "a2": "a2", "glow": "glow"}[kind]]
        m.pop("reusedFrom", None)
    info = C.write_grid(rel, frames, m)
    return rel, len(cols), edge, info


def all_jobs(only=None):
    import ksrc
    out = []
    for s in ksrc.BASE_SHEETS:
        for j in jobs_for(s):
            if only and not any(o in rel_of(*j) for o in only):
                continue
            out.append(j)
    return out


def build(only=None, procs=8):
    from multiprocessing import Pool
    js = all_jobs(only)
    C.snapshot_meta(sorted({rel_of(*j) for j in all_jobs()} | {"weapons/v3/" + j[1] for j in all_jobs()}))
    res = []
    with Pool(procs) as p:
        for r in p.imap_unordered(job, js):
            print(r[0], "colors", r[1], "edge", r[2], flush=True)
            res.append(r)
    return res


if __name__ == "__main__":
    build(sys.argv[1:] or None)
