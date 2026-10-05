"""60라운드 Q15~Q21 각성 실제 제작 공용 — 팔레트 허용 집합·틀 확대·시트 쓰기(격자 원본 → out/grid).

결정(decisions/2026-10-05-round-60-parallel-production.md Q15~Q21, 계약 art §21):
  칼 = 월인(K-A) · 대검 = 핏빛 거암검(G-A2) · 단검 = 귀화(D-A) · 활 = 혜성 날개(B-A).
  재·호박 제한은 기본 무기에만 → 각성 무기·각성 fx 는 LOPAD 팔레트 고유색 허용(층 램프를 고정색으로, 지역 교체 없음).
  각성 시트만 틀 확대: 칼·단검·활 +32 사방(192 → 256), 대검 가로 +40·세로 +32(240×272 → 320×336 등). 프레임 번호·시각 = 원 시트.
  각성 무기 색 상한 24 · 각성 순간 전환 8×60ms · 순환 6~12프레임 · 각성 궤적 = 기존 연격 fx 와 별개 시트.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(WORK, "../../.."))
SPR = os.path.join(ROOT, "assets/sprites")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(WORK, "build57"))

import kit60 as K6  # noqa: E402
import kit as K57  # noqa: E402  (build57 공용: grid_frames · rk · write — 읽기만)

VERSION = "v3-r60-awaken"
SRC = "parts/art/work/awaken60/prod_build.py (60라운드 Q15~Q21 최종 각성 재디자인 — 월인·핏빛 거암검·귀화·혜성 날개)"
STAGE = os.path.join(HERE, "out", "grid")
STAGE_W = os.path.join(STAGE, "weapons")
STAGE_FX = os.path.join(STAGE, "fx")
PAD = {"katana": (36, 32, 36, 40), "dagger": (32, 32, 32, 32), "bow": (32, 32, 32, 32), "greatsword": (40, 32, 40, 32)}   # 왼·위·오른·아래
CAP = 24
R60 = "60라운드 Q15~Q21 — 각성 외형 재디자인(시안 parts/art/work/awaken60/out/*_preview.png), 계약 art §21"
PALETTE_NOTE = ("60라운드 Q19: 각성 무기·각성 fx 는 재·호박 제한 없음 — LOPAD 팔레트(lopad.json) 무채 16 + 층 램프(고정색으로 사용, 지역 교체 없음) "
                "+ 주인공 흉갑 SL·붕대 PL·흙 WD + 백열 X0/X1. 각성 무기 색 상한 24")


def _allowed():
    p = json.load(open(os.path.join(ROOT, "parts/art/palette/lopad.json"), encoding="utf-8"))
    s = {c.lower() for c in p["gray"]}
    for f in p["floors"]:
        s |= {c.lower() for c in f["ramp"]}
    s |= {c.lower() for c in K6.SL + K6.PL + K6.WD + [K6.X0, K6.X1, K6.INK]}
    s |= set(K57.W.ALLOWED)
    return s


ALLOWED = _allowed()


def write_sheet(name, out_dir, rows, frames, ms, meta, loop=False, glow=None):
    """rk.write_sheet(색 상한 24 · LOPAD 허용 집합 · 반투명 0 검사) — 백열 위치 검사는 하지 않음(각성은 순환 맥동에 X1 을 씀)."""
    K57.rk.VERSION = VERSION
    K57.rk.SRC = SRC
    K57.rk.PALETTE_NOTE = PALETTE_NOTE
    m = dict(meta)
    m["palette"] = PALETTE_NOTE
    m.setdefault("r60", R60)
    if glow is not None:
        m["glowFrames"] = sorted(glow)
    sheet, j, fr = K57.rk.write_sheet(name, out_dir, rows, frames, ms, m, glow=None, cap=CAP, loop=loop, allowed=ALLOWED, edge_ok=True)
    return j


def lum(c):
    return 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]


def hx(c):
    return "#%02x%02x%02x" % tuple(c[:3])


def starts(ms):
    out, t = [], 0
    for m in ms:
        out.append(t)
        t += m
    return out
