/** 시트 분류·동작 이름 규칙 (계약 art-assets §1·§3·§6·§7, 57라운드 B7: spriteDefs 에서 분리). Phaser 의존 없음. */

/** 60라운드: items = 월드 아이템 (계약 art §22 `items/v3/consumable_f1` — 구조물 시트 형식, 경로 `sprites/items/<이름>.json`) */
export type SpriteCategory = 'player' | 'enemies' | 'bosses' | 'weapons' | 'fx' | 'structures' | 'items';

/** 계약 §1 동작 목록 (+ 52라운드 Q13 달리기 `run` — 없으면 walk) */
export const PLAYER_ACTIONS = ['idle', 'walk', 'run', 'attack', 'dash', 'hurt', 'death'] as const;

export const MOB_ACTIONS = ['idle', 'walk', 'attack', 'hurt', 'death'] as const;

/** 54라운드 계약 §15 보스 v3 추가 동작 (매니페스트에 있을 때만 로드 — 지금은 1층 '만취') */
export const BOSS_EXTRA_ACTIONS = [
  'slam',
  'drink',
  'drink_break',
  'stagger_dash',
  'fall',
  'kick',
  'throw',
  'throw_torch',
  'phase_drink',
  // 61라운드 E 아트 2: 등장(걸어 들어옴·건배·포효) — 보스 묶음, 전투 시작 때 내린다 (systems/boss/bossSheets)
  'intro',
] as const;

/** 계약 §3.1 손에 든 무기 오버레이 동작 */
export const WEAPON_ACTIONS = ['attack'] as const;

/** 48라운드 계약 art §6: 연격 수 · 탄생 동작 · 탄생 흙 이펙트 */
export const COMBO_HITS = 3;

export const BIRTH_ACTION = 'birth';

export const BIRTH_FX = 'birth_dust';

/** 주인공 몸 연격 시트 동작 `player_<무기>_combo<n>` (n 은 1부터) */
export function comboAction(weaponId: string, n: number): string {
  return `${weaponId}_combo${n}`;
}

/** 손에 든 무기 연격 시트 동작 `weapons/<무기>_combo<n>` */
export function weaponComboAction(n: number): string {
  return `combo${n}`;
}

/** 무기를 든 특수 동작 `player_<무기>_special` / 활 조준 `player_bow_aim` (§6.2) */
export function specialAction(weaponId: string): string {
  return `${weaponId}_special`;
}

export function aimAction(weaponId: string): string {
  return `${weaponId}_aim`;
}

/**
 * 49라운드 계약 art §7.1·7.2: 무기를 든 몸 동작 접미 — 뽑기 · 넣기(납도) · 대검 내리찍기 · 대검 대쉬 공격 · 활 장전.
 * 몸 `player/player_<무기>_<동작>`, 무기 `weapons/<무기>_<동작>` (같은 열·같은 시각, §6.1 겹침 규칙)
 */
export const WEAPON_MOTIONS = ['draw', 'sheathe', 'slam', 'dashslash', 'reload'] as const;

/** 56라운드 Q7 그로기 몸 `player_groggy`(칼·대검 공용 루프) · 휴대 무기 `<무기>_carry_groggy` */
export const GROGGY_ACTION = 'groggy';

export const GROGGY_CARRY = 'carry_groggy';

/**
 * 56라운드 Q9 활 당김 유지·놓기 (몸 `player_<무기>_draw_hold`·`_release`, 무기 같은 이름) · 화살비 — 61라운드 E: 좌 홀드는 서서
 * 시작하므로 아트 2 서서 시작 판 `arrow_rain_stand`(옛 당긴 채 시작 `arrow_rain` 은 로드하지 않음) — 다른 무기는 매니페스트가 거른다
 */
export const BOW_DRAW_MOTIONS = ['draw_hold', 'release', 'arrow_rain_stand'] as const;

export type WeaponMotion = (typeof WEAPON_MOTIONS)[number];

/** 몸 동작 `<무기>_<motion>` */
export function motionAction(weaponId: string, motion: WeaponMotion): string {
  return `${weaponId}_${motion}`;
}

/** 49라운드 §7.1 휴대 오버레이 동작 `weapons/<무기>_carry_<idle|walk|dash>` (+ 52라운드 Q13 `run`) */
export type CarryAction = 'idle' | 'walk' | 'run' | 'dash';

export const CARRY_ACTIONS: readonly CarryAction[] = ['idle', 'walk', 'run', 'dash'];

export function carryAction(a: CarryAction): string {
  return `carry_${a}`;
}

/** 49라운드 아트 추가(계약 외 임시): 칼·대검을 뽑아 든 채(넣기 전) `weapons/<무기>_carry_drawn_<a>` */
export function carryDrawnAction(a: CarryAction): string {
  return `carry_drawn_${a}`;
}

/**
 * 53라운드 Q19 무기별 기본 자세: 몸 이동 시트 변형 `player_<기본>_<접미>` (접미 = free(왼손이 빈 기본 자세) 또는 무기 id).
 * 고르는 규칙은 spriteMeta `bodyActionFor`
 */
/** 53라운드 Q46 확정: 대쉬는 모든 무기 공통 `player_dash` — 변형은 대기·걷기·달리기만 */
export const BODY_VARIANT_BASES: readonly CarryAction[] = ['idle', 'walk', 'run'];

export const FREE_POSE = 'free';

/** 로드할 몸 변형 동작: 기본 동작마다 `_free` + 무기 id 접미 */
export function bodyVariantActions(weaponIds: readonly string[]): string[] {
  const out: string[] = [];
  for (const base of BODY_VARIANT_BASES) for (const s of [FREE_POSE, ...weaponIds]) out.push(`${base}_${s}`);
  return out;
}

/** 몸 변형의 기본 동작 (`idle_free` → idle, `walk_bow` → walk). 변형이 아니면 그대로 */
export function bodyBaseAction(action: string): string {
  const i = action.indexOf('_');
  if (i <= 0) return action;
  const base = action.slice(0, i);
  return (BODY_VARIANT_BASES as readonly string[]).includes(base) ? base : action;
}

/** 몸 동작 → 휴대 오버레이 동작 (idle·walk·run·dash 그대로 — 무기별 자세 변형 포함, 피격·뽑기·넣기는 idle). 사망·탄생은 null(숨김) */
export function carryActionFor(bodyAction: string): CarryAction | null {
  const playerAction = bodyBaseAction(bodyAction);
  if (playerAction === 'walk' || playerAction === 'run' || playerAction === 'dash' || playerAction === 'idle')
    return playerAction;
  if (playerAction === 'death' || playerAction === BIRTH_ACTION) return null;
  return 'idle';
}

/** 무기별 48·49라운드 주인공 동작 (연격 3 · 특수 · 조준 · 뽑기·넣기·내리찍기·대쉬 공격·장전) */
export function playerWeaponActions(weaponId: string): string[] {
  const out: string[] = [];
  for (let n = 1; n <= COMBO_HITS; n++) out.push(comboAction(weaponId, n));
  out.push(specialAction(weaponId), aimAction(weaponId));
  for (const m of WEAPON_MOTIONS) out.push(motionAction(weaponId, m));
  for (const m of BOW_DRAW_MOTIONS) out.push(`${weaponId}_${m}`);
  return out;
}

/** 무기 오버레이 동작 (연격 3 · 특수 · 조준 · 49라운드 휴대 3 · 뽑기·넣기·내리찍기·대쉬 공격·장전) */
export const WEAPON_EXTRA_ACTIONS: readonly string[] = [
  ...Array.from({ length: COMBO_HITS }, (_, i) => weaponComboAction(i + 1)),
  'special',
  'aim',
  ...CARRY_ACTIONS.map(carryAction),
  ...CARRY_ACTIONS.map(carryDrawnAction),
  ...WEAPON_MOTIONS,
  ...BOW_DRAW_MOTIONS,
  // 56라운드 Q7 그로기 휴대 (`weapons/v3/<무기>_carry_groggy` — 몸 player_groggy 와 같은 열)
  GROGGY_CARRY,
];

/**
 * 주인공 애니 동작 → 겹칠 무기 시트 동작 후보 (앞이 우선, 마지막은 기존 attack 폴백).
 * attack · <무기>_combo<n> · <무기>_special · <무기>_aim 만 무기를 보인다. 그 외(idle·walk·dash·hurt·death·birth) 는 []
 * 55라운드 §17: `art` = 무기 연격 그림 이름 표 조회(`comboArt.overlayArtCandidates`) — 표의 새 동작 이름도 무기를 보인다
 */
export function overlayActionsFor(
  playerAction: string,
  weaponId: string,
  art?: (rest: string) => string[] | null,
): string[] {
  if (playerAction === 'attack') return ['attack'];
  const prefix = `${weaponId}_`;
  if (!playerAction.startsWith(prefix)) return [];
  const rest = playerAction.slice(prefix.length);
  if (/^combo\d+$/.test(rest)) return [rest, 'attack'];
  if (rest === 'special' || rest === 'aim') return [rest, 'attack'];
  // 49라운드: 내리찍기·대쉬 공격은 무기 시트가 없으면 3타·attack, 뽑기·넣기·장전은 그 시트만 (없으면 휴대 표시)
  if (rest === 'slam' || rest === 'dashslash') return [rest, weaponComboAction(COMBO_HITS), 'attack'];
  if (rest === 'draw' || rest === 'sheathe' || rest === 'reload') return [rest];
  // 56라운드 Q9 활 당김 유지·놓기 (무기 시트가 활·화살을 그림)
  if ((BOW_DRAW_MOTIONS as readonly string[]).includes(rest)) return [rest, 'aim'];
  return art?.(rest) ?? [];
}

/**
 * 이펙트 시트(`fx/<이름>.json`)는 파일 이름에 동작 접미가 없으므로 내부 동작 이름을 하나로 고정한다.
 * sheetId = `<이름>_fx`, 애니 키 = `<이름>_fx_<방향>` (directions 가 ["any"] 면 네 방향 모두 0행).
 */
export const FX_ACTION = 'fx';

/** 56라운드 고유 자원 오버레이 단계 수 (검기 3단 · 울분 3단) */
export const GAUGE_OVERLAY_LEVELS = 3;

/**
 * 61라운드 E: 고유 자원 오버레이를 붙이지 않는 무기 동작 — 칼 찌르기(검기는 좌 홀드 발도만 소모, 아트 2 '이제 안 쓰는 그림'
 * `weapons/v3/katana_thrust_ki1~3`)
 */
export const GAUGE_OVERLAY_SKIP: readonly string[] = ['thrust'];

/** 56라운드 고유 자원 오버레이 무기 동작 `<무기 동작>_<접미><단>` (`katana_rise_ki2`·`greatsword_cleave_grudge1` — 무기 시트 이름) */
export function gaugeOverlayAction(weaponAction: string, suffix: string, level: number): string {
  return `${weaponAction}_${suffix}${level}`;
}

/** 고유 자원 종류 → 오버레이 접미 (없으면 null — 낙인·숨은 무기 오버레이 없음) */
export function gaugeOverlaySuffix(kind: string | undefined): string | null {
  return kind === 'kenki' ? 'ki' : kind === 'grudge' ? 'grudge' : null;
}

/** 구조물 시트 내부 동작 이름 (파일 이름에 동작 접미가 없다 — 이펙트와 같은 방식). sheetId = `<id>_st` */
export const STRUCTURE_ACTION = 'st';
