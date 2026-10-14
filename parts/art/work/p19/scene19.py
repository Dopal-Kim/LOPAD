"""P19 1-A 형태별 대표 화면(목업) — 소품·적·주인공 배치 + 조명 제안값 적용 + 휘도 측정 + lighting_proposal.json.

python3 parts/art/work/p19/scene19.py [형태 id ...] [--ambient-scan]
출력: parts/art/work/p19/shots/<형태>_z175.webp(측정은 1.75·1.6 둘 다, 그림은 1.75만), preview_shapes.webp(9장 축소 모음), luminance.json, lighting_proposal.json
"""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mock19 as M  # noqa: E402
from tk import dump  # noqa: E402

T = 64
SHOTS = os.path.join(HERE, "shots")

# ---------------------------------------------------------------- 조명 제안 (지역별 주변광 · 광원 종류)
AMBIENT = {   # RGB 배수(1.0 = 바탕색 그대로). 지금(진단) 0.34 안팎 → 0.80 안팎. 어둠은 연출 구간에만.
    "outer": [0.74, 0.72, 0.78], "gate": [0.80, 0.82, 0.88], "brewery": [0.82, 0.78, 0.76],
    "hall": [0.70, 0.66, 0.66], "waste": [0.76, 0.72, 0.70],
}
LIGHT_KINDS = {   # 도트 단위 반경(pixelScale 0.5 → 논리 = ÷2)
    "lamp_post": {"color": "#e8b858", "radius": 360, "intensity": 0.55, "flicker": {"amp": 0.06, "hz": 4}},
    "brazier": {"color": "#eebb6d", "radius": 420, "intensity": 0.6, "flicker": {"amp": 0.16, "hz": 6}},
    "fountain": {"color": "#eecc78", "radius": 480, "intensity": 0.45, "flicker": {"amp": 0.05, "hz": 2}},
    "still_fire": {"color": "#eecc78", "radius": 420, "intensity": 0.6, "flicker": {"amp": 0.18, "hz": 7}},
    "window": {"color": "#e2a33c", "radius": 200, "intensity": 0.35},
    "candelabra": {"color": "#f4de9b", "radius": 380, "intensity": 0.55, "flicker": {"amp": 0.1, "hz": 6}},
    "moon_fill": {"color": "#a8c0d6", "radius": 900, "intensity": 0.18},
    "hazard_glow": {"color": "#e2a33c", "radius": 140, "intensity": 0.4, "flicker": {"amp": 0.1, "hz": 3}},
    "player": {"color": "#e8b858", "radius": 260, "intensity": 0.35},
}


def L(kind, x, y):
    k = LIGHT_KINDS[kind]
    return (x, y, k["color"], k["radius"], k["intensity"])


# ---------------------------------------------------------------- 배치(목업 — 시스템 배치 규칙 제안의 예시)
def props_for(sid, g, info):
    """→ [(sprite rel, frame, tile x, tile y(발 칸), light kind or None)]"""
    P = []
    cx, cy = info["center"]
    stage = STAGE_PROPS.get(sid)
    if stage:
        for (rel, fr, x, y, lk) in stage(info):
            P.append((rel, fr, x, y, lk))
    return P


def _hero_enemies(info, n=8, seed=3):
    rng = np.random.default_rng(seed)
    cx, cy = info["center"]
    out = [("player/v3/player_idle", 0, cx - 3.0, cy + 3.0, "player")]
    kinds = ["enemies/v3/dummy_idle", "enemies/v3/drummer_idle", "enemies/v3/archer_idle", "enemies/v3/bomber_walk",
             "enemies/v3/dummy_walk", "enemies/v3/charger_idle", "enemies/v3/dummy_idle", "enemies/v3/peddler_idle"]
    for i in range(n):
        a = rng.uniform(0, 2 * np.pi)
        r = rng.uniform(3.5, 6.0)
        out.append((kinds[i % len(kinds)], int(rng.integers(0, 4)), cx - 3 + np.cos(a) * r, cy + 3 + np.sin(a) * r * 0.7, None))
    return out


STAGE_PROPS = {}


def stage(fn):
    STAGE_PROPS[fn.__name__.replace("st_", "")] = fn
    return fn


S3 = "structures/v3/"


@stage
def st_plaza(info):
    cx, cy = info["center"]
    out = [(S3 + "stage_fountain", 0, cx, cy + 1.6, "fountain")]
    for dx, dy in ((-9, -6), (9, -6), (-9, 7), (9, 7)):
        out.append((S3 + "set_outer_lamppost", 0, cx + dx, cy + dy, "lamp_post"))
    out += [(S3 + "hazard_pool", 0, cx - 5, cy + 4, None), (S3 + "hazard_pool", 0, cx + 6, cy - 3, None),
            (S3 + "hazard_cask_row", 0, cx + 12, cy + 2, "hazard_glow"), (S3 + "crate_f1", 0, cx - 14, cy - 1, None)]
    return out


@stage
def st_dock(info):
    out = [(S3 + "stage_dock_crane", 0, 20, 16, None), (S3 + "stage_dock_crane", 0, 38, 16, None),
           (S3 + "hazard_cask_row", 0, 14, 12, "hazard_glow"), (S3 + "hazard_cask_row", 0, 33, 13, "hazard_glow"),
           (S3 + "set_brewery_barrel_stack", 0, 47, 6, None), (S3 + "set_gate_brazier", 0, 6, 6, "brazier"),
           (S3 + "set_gate_brazier", 0, 29, 5, "brazier"), (S3 + "set_gate_brazier", 0, 50, 15, "brazier"),
           (S3 + "hazard_pool", 0, 25, 9, None)]
    return out


@stage
def st_cross(info):
    cx, cy = info["center"]
    out = [(S3 + "stage_signpost", 0, cx, cy + 0.5, "lamp_post"),
           (S3 + "set_gate_brazier", 0, 24, 5, "brazier"), (S3 + "set_gate_brazier", 0, 3, 14, "brazier"),
           (S3 + "set_gate_brazier", 0, 45, 14, "brazier"), (S3 + "set_gate_brazier", 0, 24, 29, "brazier"),
           (S3 + "set_outer_lamppost", 0, 17, 11, "lamp_post"), (S3 + "set_outer_lamppost", 0, 32, 23, "lamp_post"),
           (S3 + "setpiece_broken_cart", 0, 30, 12, None), (S3 + "hazard_cask_row", 0, 19, 22, "hazard_glow")]
    return out


@stage
def st_terrace(info):
    out = [(S3 + "stage_terrace_stair", 0, 11, 15, None), (S3 + "stage_terrace_stair", 0, 36, 15, None),
           (S3 + "set_gate_brazier", 0, 4, 6, "brazier"), (S3 + "set_gate_brazier", 0, 24, 6, "brazier"),
           (S3 + "set_gate_brazier", 0, 44, 6, "brazier"), (S3 + "set_gate_brazier", 0, 24, 25, "brazier"),
           (S3 + "hazard_cask_row", 0, 20, 12, "hazard_glow"), (S3 + "hazard_merlon", 0, 30, 13, None),
           (S3 + "set_outer_lamppost", 0, 6, 22, "lamp_post"), (S3 + "set_outer_lamppost", 0, 42, 26, "lamp_post")]
    return out


@stage
def st_cellar(info):
    out = [(S3 + "stage_cask_pile", 0, 24, 15, "hazard_glow")]
    for x in range(8, 44, 8):
        for y in (11, 22):
            out.append((S3 + "pillar_stone", 0, x + 0.5, y, None))
    for (x, y) in ((12, 6), (36, 6), (12, 26), (36, 26)):
        out.append((S3 + "hazard_cask_row", 0, x, y, "hazard_glow"))
    for (x, y) in ((4, 9), (44, 9), (24, 5), (24, 27), (4, 24), (44, 24)):
        out.append((None, 0, x, y, "brazier"))   # 매달린 등(빛만)
    return out


@stage
def st_rampart(info):
    out = [(S3 + "stage_rampart_beacon", 0, 26, 8, "brazier"), (S3 + "stage_rampart_beacon", 0, 42, 21, "brazier")]
    for x in range(4, 58, 5):
        out.append((S3 + "hazard_merlon", 0 if x % 3 else 1, x, 17, None))
    out += [(S3 + "set_gate_brazier", 0, 8, 11, "brazier"), (S3 + "set_gate_brazier", 0, 52, 11, "brazier"),
            (None, 0, 30, 14, "moon_fill")]
    return out


@stage
def st_still(info):
    cx, cy = info["center"]
    out = [(S3 + "stage_still", 0, cx, cy + 1, "still_fire"), (S3 + "hazard_cask_row", 0, 38, 24, "hazard_glow"),
           (S3 + "set_gate_brazier", 0, 6, 6, "brazier"), (S3 + "set_gate_brazier", 0, 26, 6, "brazier"),
           (S3 + "set_gate_brazier", 0, 40, 28, "brazier"), (S3 + "hazard_pool", 0, 34, 20, None),
           (S3 + "set_brewery_barrel_stack", 0, 8, 28, None)]
    return out


@stage
def st_boss(info):
    out = [(S3 + "set_hall_long_table", 0, 22, 16, None), (S3 + "set_hall_long_table", 0, 34, 21, None)]
    for (x, y) in ((17, 13), (39, 13), (17, 26), (39, 26)):
        out.append((S3 + "boss1_pillar", 0, x, y, None))
    for (x, y) in ((10, 8), (46, 8), (8, 22), (48, 22), (28, 5)):
        out.append((S3 + "boss1_candelabra", 0, x, y, "candelabra"))
    out.append((S3 + "hazard_pool", 0, 28, 25, None))
    return out


@stage
def st_waste(info):
    out = [(S3 + "set_waste_fire_ring", 0, 16, 16, "brazier"), (S3 + "hazard_cask_row", 0, 22, 9, "hazard_glow"),
           (S3 + "setpiece_broken_cart", 0, 10, 22, None), (S3 + "birth_spear_thicket", 0, 26, 21, None),
           (None, 0, 24, 14, "moon_fill"), (S3 + "set_gate_brazier", 0, 42, 24, "brazier")]
    return out


def render_shape(sid, fn, zooms=(1.75, 1.6), ambient=None, save_shots=True):
    g, info = fn()
    reg = info["region"]
    ts = M.Tileset(reg)
    canvas = M.compose(g, info, ts)
    H, W = len(g), len(g[0])
    items = []
    lights = []
    for (rel, fr, x, y, lk) in props_for(sid, g, info) + _hero_enemies(info):
        fx, fy = x * T, y * T + T // 2
        if rel:
            if not os.path.exists(os.path.join(M.SPR, rel + ".json")):
                continue
            im, pv, meta = M.sprite(rel, fr)
            items.append((fy, np.asarray(im), int(fx - pv[0]), int(fy - pv[1])))
            lt = meta.get("light")
            if lt and lk is None:
                off = lt.get("offset", {"x": pv[0], "y": pv[1] // 2})
                lights.append((fx - pv[0] + off["x"], fy - pv[1] + off["y"], lt["color"], lt["radius"], lt["intensity"] * 0.6))
        if lk:
            ly = fy - (110 if lk in ("lamp_post", "brazier", "candelabra") else 40)
            lights.append(L(lk, fx, ly))
    for (_, a, x, y) in sorted(items, key=lambda t: t[0]):
        M.blit(canvas, a, x, y)
    amb = ambient or AMBIENT[reg]
    res = {}
    cx, cy = info["center"]
    for z in zooms:
        vw, vh = int(1920 / (z * 2) / 16 * T), int(1080 / (z * 2) / 16 * T)   # 화면 칸 = 1920 / (z·2·16)
        x0 = int(min(max(0, cx * T - vw / 2), W * T - vw)) if W * T > vw else 0
        y0 = int(min(max(0, cy * T - vh / 2), H * T - vh)) if H * T > vh else 0
        box = (x0, y0, min(W * T, x0 + vw), min(H * T, y0 + vh))
        im = M.light_scene(canvas, lights, amb, box)
        mean, dark = M.measure(im)
        res["z%d" % int(z * 100)] = {"mean": round(mean, 1), "dark": round(dark * 100, 1), "viewTiles": [round(vw / T, 1), round(vh / T, 1)]}
        if save_shots and z == zooms[0]:
            os.makedirs(SHOTS, exist_ok=True)
            im.save(os.path.join(SHOTS, f"{sid}_z{int(z * 100)}.webp"), quality=88)   # 측정은 저장 전 원본으로
    al = canvas[..., :3].astype(np.float32)
    res["albedoMean"] = round(float((0.2126 * al[..., 0] + 0.7152 * al[..., 1] + 0.0722 * al[..., 2]).mean()), 1)
    res["region"] = reg
    res["name"] = info["name"]
    res["size"] = [W, H]
    res["ambient"] = amb
    res["lights"] = len(lights)
    return res, g, info


def proposal(results):
    return {
        "doc": ("P19 1-A 아트 제안 — 전투장 주변광·광원 배치 기준값(시스템 lighting.json 에 옮길 값). 목업 측정: parts/art/work/p19/scene19.py · luminance.json. "
                "모델: 빛 = ambient + Σ 광원 색·세기·(1−d²)², 결과 = 바탕 × min(빛, 1.6), 발광 색은 조명 무시(계약 §9). 반경은 도트(pixelScale 0.5 → 논리 ÷2)."),
        "target": {"meanLuminance": ">= 55", "nearBlackRatio(L<25)": "<= 15%", "source": "P19 ⑤ 3번 / F 밝기"},
        "ambient": {k: {"rgb": v, "note": "전투 기본. 지금(0.34 안팎)의 약 2~2.4배 — 바닥 바탕색(v4 albedo 80~107)과 함께 휘도 ≥ 55 를 만든다"} for k, v in AMBIENT.items()},
        "ambientDarkSections": {"boss_blackout": [0.30, 0.30, 0.36], "hidden_cellar": [0.36, 0.34, 0.34],
                                "note": "어둠은 연출 구간에만(P19 F) — 보스 소등 국면·숨은 벽 저장고"},
        "lightKinds": LIGHT_KINDS,
        "placement": {
            "rule": "빛은 길을 따라: 문 ↔ 무대 중심 경로 양옆 6~8칸 간격, 무대 중심 1개(큰 반경), 위험물(술통 줄)에 작은 호박 빛(hazard_glow) — 위험물이 어둠에서 먼저 읽히게",
            "density": "화면(34×19칸)당 광원 4~7개. 화면 가장자리 3칸 안에도 1개 이상(적이 어둠에서 걸어 나오지 않게)",
            "perShape": {
                "plaza": "분수(fountain) 1 + 둘레 등불 기둥 4(반경 9·7칸 지점) + 골목 입구 화로",
                "dock": "부두 가장자리 화로 3(수로 둑 따라) + 크레인 아래 술통 줄 hazard_glow",
                "cross": "이정표 등(lamp_post) 1 + 골목 끝 화로 4(네 갈래 끝) + 광장 모서리 등 2",
                "terrace": "위 단 화로 3(난간 따라) + 아래 단 1 + 계단 옆 등 2",
                "cellar": "매달린 등 6(기둥 줄 사이, brazier 값) + 술통 더미 hazard_glow",
                "rampart": "망루 봉화(brazier) 2 + 회랑 양끝 화로 2 + 낭떠러지 쪽 달빛 채움(moon_fill) 1",
                "still": "증류기 불(still_fire) 1 + 마당 화로 3",
                "boss": "촛대 5(기존 boss1_candelabra) — 소등 국면만 ambientDarkSections.boss_blackout",
                "waste": "모닥불 1 + 화로 1 + 달빛 채움 1",
            },
        },
        "measured": results,
    }


def board(paths, out, cols=3, w=640):
    ims = [Image.open(p).resize((w, w * 9 // 16)) for p in paths]
    rows = (len(ims) + cols - 1) // cols
    o = Image.new("RGB", (cols * (w + 8), rows * (w * 9 // 16 + 8)), (16, 16, 18))
    for i, im in enumerate(ims):
        o.paste(im, ((i % cols) * (w + 8), (i // cols) * (w * 9 // 16 + 8)))
    o.save(out, quality=88)


def main(ids=None):
    results = {}
    for sid, fn in M.SHAPES:
        if ids and sid not in ids:
            continue
        r, g, info = render_shape(sid, fn)
        results[sid] = r
        print(sid, r)
    if not ids:
        dump(results, os.path.join(HERE, "luminance.json"))
        dump(proposal(results), os.path.join(HERE, "lighting_proposal.json"))
        board([os.path.join(SHOTS, f"{s}_z175.webp") for s, _ in M.SHAPES], os.path.join(HERE, "preview_shapes.webp"))
    return results


if __name__ == "__main__":
    main([a for a in sys.argv[1:] if not a.startswith("--")] or None)
