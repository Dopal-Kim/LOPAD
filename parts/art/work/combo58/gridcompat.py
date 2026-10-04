"""57라운드 아틀라스 이후 — 옛 빌드 모듈이 assets 의 v3 시트를 '격자'로 읽을 때 쓰는 도우미(atlas57/gridsheet 감쌈)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
SPR = os.path.join(ROOT, "assets/sprites")
sys.path.insert(0, os.path.join(HERE, "..", "atlas57"))
import gridsheet  # noqa: E402


def body_meta(rel):
    """rel = 'player/v3/player_x' → 격자 메타(frames 정수)."""
    return gridsheet.load_meta(os.path.join(SPR, rel + ".json"))


def load_sheet(rel):
    """rel → (격자 메타, {dir: [RGBA 칸]})."""
    j = gridsheet.load_meta(os.path.join(SPR, rel + ".json"))
    im = gridsheet.open_grid(os.path.join(SPR, rel + ".json"))
    fw, fh, n = j["frameWidth"], j["frameHeight"], j["frames"]
    out = {}
    for r, d in enumerate(j["directions"]):
        out[d] = [im.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)) for c in range(n)]
    return j, out


def patch_rk():
    """combo56_res/rk.load_sheet 을 격자 되살리기로 바꿈(이 프로세스 안에서만)."""
    sys.path.insert(0, os.path.join(HERE, "..", "combo56_res"))
    import rk
    rk.load_sheet = load_sheet
    return rk
