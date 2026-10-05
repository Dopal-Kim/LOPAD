/** 로드 대상 목록·시트 경로·텍스처/애니 키 규칙 (계약 art-assets §1, 57라운드 B7: spriteDefs 에서 분리). Phaser 의존 없음. */
import { ASSETS, TEXTURES } from '../../core/Constants';
import {
  BIRTH_ACTION,
  bodyVariantActions,
  BOSS_EXTRA_ACTIONS,
  FX_ACTION,
  GAUGE_OVERLAY_LEVELS,
  GAUGE_OVERLAY_SKIP,
  gaugeOverlayAction,
  GROGGY_ACTION,
  MOB_ACTIONS,
  PLAYER_ACTIONS,
  playerWeaponActions,
  type SpriteCategory,
  STRUCTURE_ACTION,
  WEAPON_ACTIONS,
  WEAPON_EXTRA_ACTIONS,
} from './spriteActions';
import { type Dir8, DIRS8 } from './spriteDirs';

/** 애니 키 `<이름>_<동작>_<방향>[@f<n>][#…]` 에서 동작·방향을 꺼낸다. 형식이 아니면 null */
export function parseAnimKey(key: string, name: string): { action: string; dir: Dir8 } | null {
  if (!key.startsWith(`${name}_`)) return null;
  const body = key
    .slice(name.length + 1)
    .split('#')[0]
    .split('@')[0];
  const i = body.lastIndexOf('_');
  if (i <= 0) return null;
  const dir = body.slice(i + 1) as Dir8;
  if (!DIRS8.includes(dir)) return null;
  return { action: body.slice(0, i), dir };
}

/** 파생 애니 키: 특정 열만 반복 (`<애니>#p1-2`) */
export function phaseAnimKey(base: string, columns: readonly number[]): string {
  return `${base}#p${columns.join('-')}`;
}

export interface SheetRequest {
  category: SpriteCategory;
  name: string;
  action: string;
}

/** 로드 대상: 주인공 6동작, 이름 목록(적·보스 id)별 5동작, 무기 id 별 attack 오버레이, 이펙트 id 목록, 구조물 시트 id 목록 */
export function wantedSheets(
  enemyIds: readonly string[],
  bossIds: readonly string[],
  weaponIds: readonly string[] = [],
  fxIds: readonly string[] = [],
  structureIds: readonly string[] = [],
  /** 55라운드 §17: 무기별 연격 그림 이름 표의 몸·무기 동작 이름 (`comboArt.comboArtNames(...).body`) */
  comboArt: Readonly<Record<string, readonly string[]>> = {},
  /** 56라운드: 무기별 고유 자원 오버레이 접미 (칼 `ki` · 대검 `grudge` — 무기 동작마다 `<동작>_<접미><1~3>`) */
  gaugeOverlay: Readonly<Record<string, string>> = {},
): SheetRequest[] {
  const out: SheetRequest[] = [];
  for (const action of PLAYER_ACTIONS) out.push({ category: 'player', name: 'player', action });
  // 48라운드 §6: 탄생 · 무기별 연격·특수·조준 (매니페스트에 없으면 로더가 건너뛴다)
  out.push({ category: 'player', name: 'player', action: BIRTH_ACTION });
  out.push({ category: 'player', name: 'player', action: GROGGY_ACTION });
  for (const id of weaponIds) {
    const known = new Set(playerWeaponActions(id));
    for (const action of known) out.push({ category: 'player', name: 'player', action });
    for (const n of comboArt[id] ?? [])
      if (!known.has(`${id}_${n}`)) out.push({ category: 'player', name: 'player', action: `${id}_${n}` });
  }
  // 53라운드 Q19: 무기별 기본 자세 (`player_idle_free`·`player_walk_bow` 등, 없으면 기본 몸)
  for (const action of bodyVariantActions(weaponIds)) out.push({ category: 'player', name: 'player', action });
  for (const name of enemyIds) for (const action of MOB_ACTIONS) out.push({ category: 'enemies', name, action });
  for (const name of bossIds)
    for (const action of [...MOB_ACTIONS, ...BOSS_EXTRA_ACTIONS]) out.push({ category: 'bosses', name, action });
  for (const name of weaponIds) for (const action of WEAPON_ACTIONS) out.push({ category: 'weapons', name, action });
  for (const name of weaponIds) {
    const acts = [...WEAPON_EXTRA_ACTIONS];
    for (const n of comboArt[name] ?? []) if (!acts.includes(n)) acts.push(n);
    for (const action of acts) out.push({ category: 'weapons', name, action });
    const suffix = gaugeOverlay[name];
    if (suffix)
      for (const action of acts.filter((a) => !GAUGE_OVERLAY_SKIP.includes(a)))
        for (let lv = 1; lv <= GAUGE_OVERLAY_LEVELS; lv++)
          out.push({ category: 'weapons', name, action: gaugeOverlayAction(action, suffix, lv) });
  }
  for (const name of fxIds) out.push({ category: 'fx', name, action: FX_ACTION });
  for (const name of structureIds) out.push({ category: 'structures', name, action: STRUCTURE_ACTION });
  return out;
}

/** `sprites/<분류>/<이름>_<동작>.json` (매니페스트·URL 공통 상대 경로). 이펙트는 `sprites/fx/<이름>.json` */
export function sheetJsonPath(r: SheetRequest): string {
  if (r.category === 'fx' || r.category === 'structures' || r.category === 'items')
    return `${ASSETS.SPRITES_DIR}/${r.category}/${r.name}.json`;
  return `${ASSETS.SPRITES_DIR}/${r.category}/${r.name}_${r.action}.json`;
}

export function sheetId(name: string, action: string): string {
  return `${name}_${action}`;
}

export function sheetTextureKey(name: string, action: string, suffix = ''): string {
  return `${TEXTURES.SHEET_PREFIX}${sheetId(name, action)}${suffix}`;
}

/** 계약 §1 애니메이션 키 `<이름>_<동작>_<방향>` (+ 층 변형 접미) */
export function animKey(name: string, action: string, dir: string, suffix = ''): string {
  return `${sheetId(name, action)}_${dir}${suffix}`;
}
