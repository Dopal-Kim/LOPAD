"""P21 아트 B — 주인공 몸 시트를 '쓰지 않고' 다시 렌더하는 틀(hero20 파이프라인 그대로, assets 에 쓰지 않음).

render(sheet, wound) → (frames{dir:[Image]}, rigs{dir:[Rig3|None]}, meta)
  sheet = 몸 시트 이름(player_idle …), wound = rig20.WOUND (0 = 본 시트와 같은 그림이어야 한다 — check_base 로 확인).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
H20 = os.path.join(WORK, "hero20")
sys.path.insert(0, os.path.join(WORK, "atlas57"))
sys.path.insert(0, H20)
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("hero20_build", os.path.join(H20, "build.py"))
H = importlib.util.module_from_spec(_spec)
sys.modules["hero20_build"] = H
_spec.loader.exec_module(H)  # hero20/build.py (경로 설정·shim) — atlas57/build.py 와 이름이 겹쳐 파일로 직접 읽음
import body20 as B  # noqa: E402
import rig20  # noqa: E402
import gridsheet  # noqa: E402

ROOT = os.path.normpath(os.path.join(WORK, "..", "..", ".."))
SPR = os.path.join(ROOT, "assets", "sprites")
LOCO = {"player_idle": "idle", "player_idle_free": "idle", "player_walk": "walk", "player_walk_free": "walk",
        "player_run": "run", "player_run_free": "run", "player_dash": "dash", "player_hurt": "hurt", "player_death": "death"}
_A19 = {}


def _attack19():
    """hero20.build.build_attack 의 패치를 그대로 걸되 build(쓰기)는 부르지 않는다."""
    if _A19:
        return _A19["m"]
    import attack19 as A19
    import gen20
    A19.B = H._B19Shim
    A19.draw = gen20.draw
    cur = {}
    _ra, _bt, _rend = A19.rise_adjust, A19.blade_tw, A19.render_attack

    def blade_tw(meta, i, d):
        cur["d"], cur["i"] = d, i
        return _bt(meta, i, d)

    def rise_adjust(st, elev, weapon):
        st = _ra(st, elev, weapon)
        bo = A19.belt(cur["cells"][cur["d"]][cur["i"]])
        if bo is not None:
            oc = (bo[1] - gen20.ref_belt(cur["d"])) / 1.5 + 1.0
            if oc > st["crouch"] + 1.5:
                st = dict(st, crouch=min(16.0, oc + 1.0))
        return st

    def render_attack(name):
        meta, im = H.S.src_grid("player/v3/player_" + name)
        cur["cells"] = H.S.cells(meta, im)
        return _rend(name)
    A19.blade_tw, A19.rise_adjust = blade_tw, rise_adjust
    _A19["m"], _A19["render"] = A19, render_attack
    return A19


def render(sheet, wound=0):
    rig20.WOUND = wound
    try:
        if sheet in LOCO:
            h = H.h19()
            act = LOCO[sheet]
            fr = B.render_sheet(sheet, h.L.ACTS[act], h.L.OLD_ACTS[act], free_hands=act in ("hurt", "death"))
        elif sheet[len("player_"):] in H.ATTACK19:
            _attack19()
            fr = _A19["render"](sheet[len("player_"):])[0]
        else:
            import gen20
            fr = gen20.render_generic(sheet[len("player_"):])[0]
    finally:
        rig20.WOUND = 0
    return {d: [f["img"] for f in v] for d, v in fr.items()}, {d: [f.get("rig") for f in v] for d, v in fr.items()}


def asset_frames(sheet):
    p = os.path.join(SPR, "player", "v3", sheet)
    meta = gridsheet.load_meta(p + ".json")
    im = gridsheet.open_grid(p + ".json")
    fw, fh, n = meta["frameWidth"], meta["frameHeight"], meta["frames"]
    return meta, {d: [im.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)) for c in range(n)] for r, d in enumerate(meta["directions"])}
