"""공격 시제품: python3 proto3.py katana_rise right,down → proto/atk_<name>.png (위 = 옛, 아래 = 새 + 오프셋 무기)"""
import sys
import attack19 as A, body19 as B, preview19 as V, sync19 as S
name = sys.argv[1]; dirs = sys.argv[2].split(",")
fr, meta, plan, roles = A.render_attack(name)
om, oim = S.src_grid("player/v3/player_" + name); oc = S.cells(om, oim)
wrel = "weapons/v3/" + name
rows = []
for d in dirs:
    old = [V.label(V.compose(oc[d][i], [V.overlay_cell_c(wrel, d, i)], pad=64), "%d %s" % (i, roles[i])) for i in range(om["frames"])]
    new = [V.label(V.compose(f["img"], [V.overlay_cell_c(wrel, d, f["src"], f["off"])], pad=64), "%d<%d %dms e%.1f" % (k, f["src"], f["ms"], f["err"])) for k, f in enumerate(fr[d])]
    rows += [V.strip(old, 1), V.strip(new, 1)]
V.stack(rows).save("proto/atk_%s.png" % name)
print(name, [(d, k, round(f["err"], 1)) for d in fr for k, f in enumerate(fr[d]) if f["err"] > 1.0][:20])
