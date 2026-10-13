"""미리보기 판 모음 → parts/art/work/r62c/preview_*.png"""
import os

import preview as P
from c62 import HERE


def build():
    out = []
    import doors
    names = doors.all_doors()
    used = ["door_waste_battle", "door_gate_rest", "door_outer_battle", "door_outer_event", "door_outer_elite", "door_outer_curse",
            "door_brewery_battle", "door_brewery_elite", "door_brewery_curse", "door_brewery_shop", "door_brewery_rest", "door_hall_boss"]
    out.append(P.doors(used, os.path.join(HERE, "preview_doors_floor1.png")))
    rest = [n for n in names if n not in used]
    out.append(P.doors(rest, os.path.join(HERE, "preview_doors_spare.png")))
    try:
        import memory
        out.append(memory.preview())
    except (ImportError, AttributeError):
        pass
    return out
