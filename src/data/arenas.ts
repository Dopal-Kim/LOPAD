/** P19 S2 전투장 형태 틀 (`data/arenas/*.json`, 계약 free-combat §3) — 파일 하나 = 형태 하나 */
import { validateShape, type ArenaShapeDef } from '../systems/mapgen/shape';

const files = import.meta.glob('../../data/arenas/*.json', { eager: true, import: 'default' }) as Record<
  string,
  ArenaShapeDef
>;

/** id → 형태 (id 순) */
export const ARENA_SHAPES: ReadonlyMap<string, ArenaShapeDef> = new Map(
  Object.values(files)
    .map((d) => validateShape(d))
    .sort((a, b) => a.id.localeCompare(b.id))
    .map((d) => [d.id, d]),
);
