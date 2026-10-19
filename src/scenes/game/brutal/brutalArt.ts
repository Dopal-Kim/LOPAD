/**
 * P21 아트 시트 이름 (계약 dark-brutal §8) — 매니페스트에 있는 것만 로드한다 (없으면 건너뜀 → GoreFx·HeroWounds 의 임시 그림).
 * - fx v5: `sprites/fx/v5/<id>.json` → fx id 그대로 (FxPool·텍스처 `sheet_<id>_fx`)
 * - 적 사망 변형: `sprites/enemies/v4/<적>_death_<변형>.json` → 적 시트 동작 `death_<변형>`
 * - 주인공 상흔: `sprites/player/[v4|v3/]hero_wound<n>_player_<동작>.json` → 이름 `hero_wound<n>`·동작 `<동작>` (본 시트와 같은 프레임)
 * - 처형: `sprites/player/v3/hero_execute_<무기>.json` → 주인공 동작 `<무기>_execute` + 무기 `sprites/weapons/v3/hero_execute_<무기>.json` → 무기 동작 `execute`
 */
import { ENEMIES } from '../../../data';
import type { DeathVariant, GoreCut, GoreWeapon } from '../../../core/eventsP21';
import { FX_ACTION } from '../../../systems/sprites/spriteDefs';
import type { SheetRequest } from '../../../systems/sprites/sheetPaths';
import { isGoreWeapon } from '../../../systems/gore/rules';

export const GORE_FX = {
  spray: (cut: GoreCut) => `blood_spray_${cut}`,
  DRIP: 'blood_drip',
  POOL: 'blood_pool',
  DECAL_FLOOR: 'blood_decal_floor',
  DECAL_WALL: 'blood_decal_wall',
  TAR_EMBER: 'tar_ember_hit',
  ASH_CHIPS: 'ash_chips',
  WOUND_CUT: 'wound_cut',
  STUCK_ARROW: 'stuck_arrow',
  parts: (enemy: string) => `gore_parts_${enemy}`,
  INK_ASH: 'ink_ash_burst',
} as const;

const CUTS: readonly GoreCut[] = ['slash', 'stab', 'crush', 'pierce'];
export const DEATH_VARIANTS: readonly DeathVariant[] = ['collapse', 'behead', 'bisect', 'pinned', 'burn', 'drown'];
export const HERO_WOUND_STAGES = [1, 2, 3] as const;

/** 상흔 오버레이 이름 (단계 1~3) */
export const heroWoundName = (stage: number) => `hero_wound${stage}`;
/** 처형 동작 (주인공 시트 동작 이름 — `<무기>_execute` 라 무기 오버레이 `weapons/<무기>_execute` 가 같은 프레임으로 겹친다) */
export const executeAction = (weapon: GoreWeapon) => `${weapon}_execute`;
/** 적 사망 변형 동작 */
export const deathAction = (v: DeathVariant) => `death_${v}`;

function fxReq(id: string): SheetRequest {
  return { category: 'fx', name: id, action: FX_ACTION, file: `v5/${id}` };
}

/** 이 런 무기로 시도할 P21 시트 요청 전부 (매니페스트 밖은 로더가 건너뛴다) */
export function brutalSheetRequests(weaponId: string, bodyActions: readonly string[]): SheetRequest[] {
  const out: SheetRequest[] = [];
  for (const c of CUTS) out.push(fxReq(GORE_FX.spray(c)));
  for (const id of [
    GORE_FX.DRIP,
    GORE_FX.POOL,
    GORE_FX.DECAL_FLOOR,
    GORE_FX.DECAL_WALL,
    GORE_FX.TAR_EMBER,
    GORE_FX.ASH_CHIPS,
    GORE_FX.WOUND_CUT,
    GORE_FX.STUCK_ARROW,
    GORE_FX.INK_ASH,
  ])
    out.push(fxReq(id));
  for (const enemy of Object.keys(ENEMIES)) {
    out.push(fxReq(GORE_FX.parts(enemy)));
    for (const v of DEATH_VARIANTS) out.push({ category: 'enemies', name: enemy, action: deathAction(v) });
  }
  // 상흔 오버레이: 지금 등록된 주인공 몸 시트마다 (art §37 — 20 몸 시트만 있고 나머지는 매니페스트에 없어 건너뜀)
  for (const n of HERO_WOUND_STAGES)
    for (const a of bodyActions)
      out.push({ category: 'player', name: heroWoundName(n), action: a, file: `${heroWoundName(n)}_player_${a}` });
  if (isGoreWeapon(weaponId)) {
    const file = `hero_execute_${weaponId}`;
    out.push({ category: 'player', name: 'player', action: executeAction(weaponId), file });
    out.push({ category: 'weapons', name: weaponId, action: 'execute', file });
  }
  return out;
}
