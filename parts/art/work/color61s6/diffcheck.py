"""작업 트리 vs git rev(기본 HEAD) — 시트별 바뀐 프레임 수·알파 변화(있으면 오류: 색만 바꿨으면 알파는 같아야 함)."""
import os
import sys

from PIL import ImageChops

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import view as V  # noqa: E402


def diff(rel, rev="HEAD"):
    m0, a = V.load(rel, rev)
    m1, b = V.load(rel)
    assert a.size == b.size, (rel, a.size, b.size)
    rgb = ImageChops.difference(a, b).getbbox(alpha_only=False)
    al = ImageChops.difference(a.getchannel("A"), b.getchannel("A")).getbbox()
    fw = m1.get("frameWidth") or m1["atlas"]["grid"]["frameWidth"]
    fh = m1.get("frameHeight") or m1["atlas"]["grid"]["frameHeight"]
    n = 0
    if rgb:
        for y in range(0, a.height, fh):
            for x in range(0, a.width, fw):
                if ImageChops.difference(a.crop((x, y, x + fw, y + fh)), b.crop((x, y, x + fw, y + fh))).getbbox(alpha_only=False):
                    n += 1
    return n, al


if __name__ == "__main__":
    for r in sys.argv[1:]:
        print(r, *diff(r))
