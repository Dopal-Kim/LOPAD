"""61 단계 5 칼 재디자인 — 기존 칼 3D 렌더 경로(hero_v3/katana3 · combo55/bodies · k56 · k58 · bk · kg_katana · groggy)를
그대로 불러 무기 프레임만 다시 얻는다(몸 시트는 쓰지 않음, 읽기 전용 import).

frames(sheet) → {dir: [dict(weapon=RGBA, tip=(x,y)|None, state=str)]}  (무기 시트 좌표 192×192)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(WORK, "../../.."))
for p in ("combo56_res", "combo56_moves_kg", "branch57", "combo58", "combo56_fx", "combo55", "weapons_v3", "hero_v3", "atlas57"):
    sys.path.insert(0, os.path.join(WORK, p))

import k56  # noqa: E402
M = k56.install()
k56.install = lambda: M        # bk·k58·kg_katana 가 import 때 다시 부르면 rise·fall 이 두 번 바뀜 → 한 번만
import bodies as B  # noqa: E402  combo55/bodies.py
import wv3  # noqa: E402
from wv3 import K, hero, DIRS  # noqa: E402
import bk  # noqa: E402  (K.draw_katana 를 heat 래퍼로 바꿈)
import k58  # noqa: E402
import kg_katana  # noqa: E402
import anim  # noqa: E402  hero_v3/anim.py

ORIG = dict(draw_katana=bk._orig_draw, heat_draw=bk.draw_katana, draw_saya=K.draw_saya, draw_hilt=K.draw_hilt, draw_tsuba=K.draw_tsuba)

for _name, _fn in list(k58.MOVES.items()):
    M.KATANA[_name] = _fn()
for _name, _fn in list(bk.MOVES.items()):
    M.KATANA[_name] = _fn()
for _name, _fn in list(kg_katana.MOVES.items()):
    M.KATANA[_name] = _fn()

OFF = K.OFF
COMBO55 = ("katana_rise", "katana_fall", "katana_issen", "katana_crescent", "katana_counter", "katana_iai", "katana_issen_dash")
HERO = {"katana_combo1": ("combo", 1), "katana_combo2": ("combo", 2), "katana_combo3": ("combo", 3),
        "katana_draw": ("move", "draw"), "katana_sheathe": ("move", "sheathe"), "katana_special": ("move", "special")}
CARRY = [("katana_carry_" + a, a, False) for a in anim.CARRY] + [("katana_carry_drawn_" + a, a, True) for a in anim.CARRY]
BASE_SHEETS = (list(COMBO55) + ["katana_thrust", "katana_spin", "katana_guardbreak"] + list(HERO) + [c[0] for c in CARRY]
               + ["katana_carry_groggy"])


import kdesign as KD  # noqa: E402

_orig_katana_frame = B.katana_frame


def _set_i(i):
    KD.V["i"] = i
    st = KD.V.get("starts")
    if st:
        KD.V["phase"] = int(st[min(i, len(st) - 1)] / KD.V.get("loopMs", 80)) % KD.V["tn"]
    gf = KD.V.get("glowFrames")
    KD.V["glowframe"] = bool(gf and i in gf and (i - 1) not in gf)     # 56 Q50: 이어진 판정 칸은 첫 칸만 백열


def _katana_frame(d, fr, i, seed):
    _set_i(i)
    return _orig_katana_frame(d, fr, i, seed)


B.katana_frame = _katana_frame


def _wrap(lst):
    return [dict(weapon=f["weapon"], tip=None if f.get("tip") is None else (f["tip"][0] + OFF, f["tip"][1] + OFF), state=f.get("state")) for f in lst]


_body_cache = {}


def _body(act):
    if act not in _body_cache:
        _body_cache[act] = anim.render_body(act)
    return _body_cache[act]


_grog = {}


def frames(sheet, dirs=DIRS):
    if sheet in ("katana_spin", "katana_guardbreak"):
        fr = bk.render(sheet, row_dirs=list(dirs))
        return {d: _wrap(fr[d]) for d in dirs}
    if sheet == "katana_thrust":
        fr = k58.render_thrust(sheet)
        return {d: _wrap(fr[d]) for d in dirs}
    if sheet in COMBO55:
        m = M.KATANA[sheet]
        out = {}
        for d in dirs:
            lst = []
            for i, fr in enumerate(m["frames"]):
                R, im, tip, st = B.katana_frame(d, fr, i, K.ember_seed("k55", sheet))
                lst.append(dict(weapon=im, tip=tip, state=st))
            out[d] = _wrap(lst)
        return out
    if sheet in HERO:
        kind, key = HERO[sheet]
        out = {}
        for d in dirs:
            lst = []
            for i in range(len((K.COMBO[key] if kind == "combo" else K.MOVES[key])["frames"])):
                _set_i(i)
                R, im, anc, st, p = K.move_frame(d, kind, key, i)
                lst.append(dict(weapon=im, tip=None, state=st))
            out[d] = lst
        return out
    for name, act, drawn in CARRY:
        if name == sheet:
            fr = _body(act)
            out = {}
            for d in dirs:
                lst = []
                for i, f in enumerate(fr[d]):
                    _set_i(i)
                    im = K.carry_drawn_frame(d, act, i, f.pose, f.rig) if drawn else K.carry_frame(d, f.pose, f.rig)
                    lst.append(dict(weapon=im, tip=None, state=None))
                out[d] = lst
            return out
    if sheet == "katana_carry_groggy":
        import groggy
        if "fr" not in _grog:
            _grog["fr"] = groggy.render()
        fr = _grog["fr"]
        out = {}
        for d in dirs:
            lst = []
            for i, f in enumerate(fr[d]):
                _set_i(i)
                lst.append(dict(weapon=K.carry_frame(d, f.pose, f.rig), tip=None, state=None))
            out[d] = lst
        return out
    raise KeyError(sheet)
