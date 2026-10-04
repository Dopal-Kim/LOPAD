/**
 * 이펙트 시트 id 목록 (계약 art §3·§3.1·§3.2·§6·§7.2) — 무기 데이터에서 유도하는 연격·가열·내리찍기·베기·화살 id 와
 * 피격·적 양상·보조·구조물 이펙트 고정 목록. Phaser 의존 없음 (53라운드 6-1 정리: spriteDefs 에서 분리, 동작 그대로).
 * 갈래 시트 id 는 `branchFx`(활)·`fxVariants`(근접).
 */
import type { ComboDef, WeaponMovesDef } from '../data/types';
import { moveFxNames } from '../data/moveTypes';
import { comboArtNames } from './comboArt';
import { BIRTH_FX, COMBO_HITS } from './spriteDefs';

/** 연격 베기 이펙트 `fx/<무기>_combo<n>` */
export function comboFxId(weaponId: string, n: number): string {
  return `${weaponId}_combo${n}`;
}

/** 이펙트 id 를 정하는 데 필요한 무기 데이터 최소 형태 (data/weapons.json). 2차 노드는 1차의 `next` */
export interface FxWeaponShape {
  kind: 'melee' | 'ranged';
  personality: { branches: { id: string; next?: { id: string }[] }[] };
  /** 49라운드: 과열 무기면 가열 단계별 연격 이펙트, 내리찍기가 있으면 내리찍기 이펙트 */
  resource?: { kind: string };
  slam?: unknown;
  /** 55라운드 §17: 연격 그림 이름 표 (휘두름·바닥 충격 이펙트 `fx/<무기>_<이름>`) */
  combo?: Pick<ComboDef, 'art'>;
  /** 56라운드: 일섬 선·분신 · 꽂아내리기 충격파 · 활 약한 화살 */
  issen?: { lineSheets: string[]; soloSuffix: string; shadow: { sheet: string } };
  plunge?: { wave: { sheet: string } };
  draw?: { weakArrowSheet: string };
  /** 56라운드 2단계 새 기본기 보조 fx (`<무기>_<이름>`) */
  moves?: WeaponMovesDef;
}

/** 56라운드 Q9 완벽 놓기 섬광 `fx/<무기>_perfect_release` */
export function perfectReleaseFxId(weaponId: string): string {
  return `${weaponId}_perfect_release`;
}

/** 56라운드 이펙트: 일섬 선 t1~t4(+분신 없는 _solo)·그림자 분신 · 꽂아내리기 충격파 · 활 약한 화살·완벽 놓기 섬광 · 2단계 새 기본기 보조 fx */
export function weapon56FxIds(id: string, w: FxWeaponShape): string[] {
  const out: string[] = [];
  if (w.issen) {
    for (const s of w.issen.lineSheets) out.push(s, `${s}${w.issen.soloSuffix}`);
    out.push(w.issen.shadow.sheet);
  }
  if (w.plunge) out.push(w.plunge.wave.sheet);
  if (w.draw) out.push(w.draw.weakArrowSheet, perfectReleaseFxId(id));
  for (const n of moveFxNames(w.moves)) out.push(`${id}_${n}`);
  return out;
}

/** 49라운드 §7.2 과열 단계 수 (fx/<무기>_combo<n>_heat<k>, k = 1..3) */
export const HEAT_STAGES = 3;

/** 과열 단계별 연격 이펙트 `fx/<무기>_combo<n>_heat<k>` */
export function heatComboFxId(weaponId: string, n: number, k: number): string {
  return `${comboFxId(weaponId, n)}_heat${k}`;
}

/** 대검 내리찍기 이펙트 `fx/<무기>_slam` */
export function slamFxId(weaponId: string): string {
  return `${weaponId}_slam`;
}

/** 베기 이펙트 이름 `<무기id>_slash` */
export function slashFxId(weaponId: string): string {
  return `${weaponId}_slash`;
}

/** 55라운드 계약 §16 무기별 적중 스파크 `hit_<무기>` · 막타 `hit_<무기>_heavy` */
export function weaponHitFxIds(weaponId: string): string[] {
  return [`hit_${weaponId}`, `hit_${weaponId}_heavy`];
}

/** 화살 텍스처 이름 `<무기id>_arrow` / `<무기id>_arrow_aimed` */
export function arrowFxId(weaponId: string, aimed: boolean): string {
  return aimed ? `${weaponId}_arrow_aimed` : `${weaponId}_arrow`;
}

/**
 * 계약 §3·§3.1 이펙트 목록: 근접 무기는 `<id>_slash`, 원거리는 `<id>_arrow`·`<id>_arrow_aimed`,
 * 그리고 1차·2차 진화 노드 id 전부(35라운드 3단계: 2차 전용 시트). 데이터에서 유도하므로 무기·트리가 바뀌면 자동 반영.
 */
export function fxSheetIds(weapons: Record<string, FxWeaponShape>): string[] {
  const out = new Set<string>();
  for (const [id, w] of Object.entries(weapons)) {
    if (w.kind === 'melee') {
      out.add(slashFxId(id));
      // 48라운드 §6.1 연격 베기 이펙트
      for (let n = 1; n <= COMBO_HITS; n++) out.add(comboFxId(id, n));
      // 49라운드 §7.2: 단검 가열 단계 · 대검 내리찍기
      if (w.resource?.kind === 'heat')
        for (let n = 1; n <= COMBO_HITS; n++) for (let k = 1; k <= HEAT_STAGES; k++) out.add(heatComboFxId(id, n, k));
      if (w.slam) out.add(slamFxId(id));
      for (const n of comboArtNames(w.combo).fx) out.add(`${id}_${n}`);
    } else {
      for (const f of weapon56FxIds(id, w)) out.add(f);
      out.add(arrowFxId(id, false));
      out.add(arrowFxId(id, true));
    }
    if (w.kind === 'melee') for (const f of weapon56FxIds(id, w)) out.add(f);
    for (const b of w.personality.branches) {
      out.add(b.id);
      for (const n of b.next ?? []) out.add(n.id);
    }
  }
  return [...out];
}

/** 피격 이펙트 시트 (35라운드 1단계, 계약 §3 anchor hitbox_center): 타격 섬광(43라운드 hit_burst 대체 가능)·피 튀김·치명타 버스트·넉백 먼지·플레이어 피격 */
export const HIT_FX_IDS: readonly string[] = [
  'hit_spark',
  'hit_burst',
  'blood',
  'crit_burst',
  'knock_dust',
  'player_hit',
  // 55라운드 계약 §16: 재 파편 입자 · 칼끝 잔상 리본
  'particles_ash',
  'ribbon_ash',
  'ribbon_ash_thin',
];
/** 적·보스 양상 시트 (35라운드 2단계): 예고 마커 3종(+43라운드 수렴 오라), 46라운드 보스 내리찍기 충격파, 적 탄, 보스 부채꼴 탄, 총구 화염 */
export const ENEMY_FX_IDS: readonly string[] = [
  'telegraph_line',
  'telegraph_circle',
  'telegraph_cone',
  'telegraph_aura',
  'boss_slam',
  'enemy_bullet',
  'boss_fan_shot',
  'muzzle_flash',
];
/** 보조 동작·대쉬 연출 시트 (35라운드 3단계, 계약 §3.2) + 2차 진화 부속(중시 적중) */
export const SECONDARY_FX_IDS: readonly string[] = [
  'parry_flash',
  'guard_wave',
  'shadowstep_ghost',
  'aim_charge',
  'aim_line',
  'dash_dust',
  'dash_trail',
  'heavyarrow_hit',
  // 56라운드 (계약 §18): 퍼펙트 가드·패링 · 그로기 소용돌이 · 단검 낙인 표식·폭발 · 과열 폭발·식음
  'guard_perfect_fx',
  'player_groggy_swirl',
  'dagger_brand_mark',
  'dagger_brand_burst',
  'dagger_overheat_burst',
  'dagger_overheat_cool',
];

/** 47라운드 구조물 이펙트 (계약 art-assets §5): 1-1 불붙은 독주 웅덩이 루프. 48라운드 §6.3 탄생 흙 */
export const STRUCTURE_FX_IDS: readonly string[] = ['fire_pool', BIRTH_FX, 'soul_wisp'];

/** 무기 유도 이펙트 + 무기별 적중 스파크(55라운드) + 피격 이펙트 + 적 양상 이펙트 + 보조 연출 + 구조물 이펙트 (중복 제거) */
export function allFxSheetIds(weapons: Record<string, FxWeaponShape>): string[] {
  return [
    ...new Set([
      ...fxSheetIds(weapons),
      ...Object.keys(weapons).flatMap(weaponHitFxIds),
      ...HIT_FX_IDS,
      ...ENEMY_FX_IDS,
      ...SECONDARY_FX_IDS,
      ...STRUCTURE_FX_IDS,
    ]),
  ];
}
