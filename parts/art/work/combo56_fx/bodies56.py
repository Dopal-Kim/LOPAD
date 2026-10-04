"""56라운드 칼 몸·무기 — combo55 렌더·내보내기 경로를 그대로 쓰고 k56 정의를 끼워 넣는다.

산출: assets/sprites/player/v3/player_katana_{rise,fall,issen}.png/.json · assets/sprites/weapons/v3/katana_{rise,fall,issen}.png/.json
(대검·단검·활 몸/무기 시트는 건드리지 않는다 — 작업 B 소유)
"""
import json
import os

import k56

M = k56.install()
import bodies as B  # noqa: E402  (combo55/bodies.py — 같은 moves 모듈 객체를 본다)
import wv3  # noqa: E402
from wv3 import DIRS, EX, colors_of, has_alpha_partial, hero  # noqa: E402

SRC = "parts/art/work/combo56_fx/build.py (56라운드 Q1 칼 템포 · Q2 일섬 — combo55 렌더 경로)"
B.SRC = SRC


def _check(name, fr, pal):
    wc, bc, partial, edge = set(), set(), False, 0
    for d in DIRS:
        for f in fr[d]:
            wc |= colors_of(f["weapon"])
            bc |= colors_of(f["body"])
            partial |= has_alpha_partial(f["weapon"]) or has_alpha_partial(f["body"])
            edge += EX.edge_pixels(f["weapon"])
    assert not (wc - pal) and not (bc - pal), (name, "색이 주인공 팔레트 밖")
    assert len(wc) <= 16 and not partial and edge == 0, (name, len(wc), partial, edge)
    return dict(weaponColors=len(wc), bodyColors=len(bc), edgePixels=edge)


def _patch_json(path, upd, drop=()):
    j = json.load(open(path, encoding="utf-8"))
    for k in drop:
        j.pop(k, None)
    j.update(upd)
    j["version"] = "v3-r56"
    j["source"] = SRC
    with open(path, "w", encoding="utf-8") as f:
        json.dump(j, f, ensure_ascii=False, indent=1)


def issen_hit_shape():
    L = k56.ISSEN_DOTS
    return dict(type="rect", fromPx=-24.0, lengthPx=float(L + 24 + 40), widthPx=72.0, angleDeg=0,
                note="돌진 경로를 쓸고 지나가는 직사각형 — 출발 피벗 뒤 24 도트부터 도착 피벗 앞 40 도트(칼 끝 여유 · 일섬 선 끝과 같음)까지, 폭 72 도트(18 월드 px). "
                     "벽에 막혀 짧게 멈추면 lengthPx 도 실제 이동 거리 + 64 로 줄인다",
                travelPx={"world": k56.ISSEN_WORLD, "dots": L}, R={"world": k56.R_KATANA_56, "dots": M.dots(k56.R_KATANA_56)},
                units="…Px = 도트(pixelScale 0.5, 월드 px = 도트 / 4). 원점 = 돌진 출발 시점의 판정 원점(피벗 위 40 도트), 0° = 돌진 방향",
                reference="참고값 — 시스템 데이터가 기준")


def build():
    pal = wv3.hero_palette()
    stats = {}
    out = {}
    for name in k56.ORDER:
        fr = B.render_katana(name)
        data = B.export_move(name, fr, "katana", frame=wv3.STD_FRAME)
        stats[name] = _check(name, fr, pal)
        out[name] = fr
        m = M.KATANA[name]
        upd = dict(tempoNote=m.get("tempoNote"), r56="56라운드 Q1(템포·사거리 ×1.15)" + (" · Q2 일섬 · Q3 그림자 분신" if name == "katana_issen" else ""))
        if name == "katana_issen":
            st = M.starts(m["ms"])
            d0, d1 = m["dashFrames"][0], m["dashFrames"][-1]
            upd.update(hitShape=issen_hit_shape(), dashFrames=m["dashFrames"], invulnFrames=m["invulnFrames"],
                       dash=dict(startMs=st[d0], endMs=st[d1] + m["ms"][d1], distancePx={"world": k56.ISSEN_WORLD, "dots": k56.ISSEN_DOTS},
                                 easing="linear", stopsAtWall=True, invulnerable=True, passesThroughEnemies=True,
                                 note="dashFrames 동안 조준 방향(4방향 행)으로 이동 — 그림은 제자리(피벗 고정), 이동은 시스템. 벽에 막히면 그 자리에서 멈추고 나머지 프레임은 그대로 재생"),
                       shadow=dict(sheet="fx/v3/katana_issen_shadow", startAtMs=st[d0] + k56.SHADOW_DELAY_MS, damageScale=0.5,
                                   note="돌진 시작 + 200ms 에 출발 피벗에서 출발 → 같은 시간(150ms)에 도착 피벗까지 달려 베고 사라짐(fx JSON travel)"),
                       lineSheets={"t%d" % k: "fx/v3/katana_issen_line_t%d" % k for k in (1, 2, 3, 4)},
                       lineNote="돌진 시작에 출발 피벗에 일섬 선 시트를 띄운다(실제 이동 칸 수에 맞는 t1~t4, 4칸 = t4)",
                       stepPx=dict(world=k56.ISSEN_WORLD, dots=k56.ISSEN_DOTS, frames=m["dashFrames"],
                                   note="일섬 돌진 거리(방향키와 무관 — 항상 조준 방향으로)"),
                       stepStartMs=st[d0])
            _patch_json(os.path.join(EX.OUT_P, "player_katana_issen.json"), upd, drop=("arcFromDeg", "arcToDeg", "arcDeg", "arcNote"))
            _patch_json(os.path.join(EX.OUT_W, "katana_issen.json"),
                        dict(upd, bodySheet="player_katana_issen"), drop=("arcFromDeg", "arcToDeg", "arcDeg", "arcNote"))
        else:
            _patch_json(os.path.join(EX.OUT_P, "player_%s.json" % name), upd)
            _patch_json(os.path.join(EX.OUT_W, "%s.json" % name), upd)
        print(name, "ok", data["timingMs"], stats[name])
    return out, stats


def _wdir():
    root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../.."))
    return os.path.join(root, "assets/sprites/weapons/v3")
