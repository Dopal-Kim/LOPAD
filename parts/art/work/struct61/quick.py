"""반복 검수용: 지정 구조물 함수만 그려 미리보기(assets 를 건드리지 않음).
python3 quick.py crate_f1 chest ... [--k 3] [--bg dark|light] [--out name]"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import s61  # noqa: E402,F401
import b2  # noqa: E402
import structs61  # noqa: E402
import sets61  # noqa: E402

V1 = os.path.join(s61.SPR, "structures")


def v1json(id_):
    p = os.path.join(V1, id_ + ".json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {"footprint": [1, 1], "solid": True, "states": {"idle": [0]}}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    k = 3
    if "--k" in sys.argv:
        k = int(sys.argv[sys.argv.index("--k") + 1]); args = [a for a in args if a != str(k)]
    items = []
    for name in args:
        fn = getattr(structs61, name, None) or getattr(sets61, name)
        fr, W, H, piv, m = fn(v1json(name))
        for im in fr:
            items.append((im, piv))
    out = os.path.join(HERE, "out", "quick.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    print(b2.preview(out, items, k=k, max_w=1400))


if __name__ == "__main__":
    main()
