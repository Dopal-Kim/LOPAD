/**
 * 57라운드 빌드 축: 지금 런의 합산 (GameState 의 패시브·무기·빌드 상태 — 캐시). 시스템 곳곳의 수치 훅이 이것만 읽는다.
 */
import { gameState } from '../../core/GameState';
import { BUILD } from '../../data/build';
import type { BuildStatKey } from '../../data/buildTypes';
import type { ComboChargeDef, ComboChargeStageDef } from '../../data/comboTypes';
import { param, ruleOf, type BuildMods } from './buildMods';

export function currentBuild(): BuildMods {
  return gameState.build.mods(gameState.passives, gameState.weapon);
}

export function buildStat(key: BuildStatKey): number {
  return currentBuild().stats[key];
}

/** 이 태그 세트가 이 단계 이상인가 */
export function setAtLeast(tag: Parameters<typeof tagStage>[0], stage: number): boolean {
  return tagStage(tag) >= stage;
}

export function tagStage(tag: keyof BuildMods['stages']): number {
  return currentBuild().stages[tag];
}

/** 무기 자원 조정 (피멍 영구 최대치 · 피멍 그로기/식힘 · 버팀 4 칼·대검 그로기 1.0초) */
export function resourceAdjust(): { maxMult: number; coolMult: number; groggyMs: number | null } {
  const m = currentBuild();
  const endure4 = BUILD.sets.endure.find((s) => s.threshold === 4)?.effect;
  const endureGroggy = m.stages.endure >= 4 && typeof endure4?.groggyMs === 'number' ? endure4.groggyMs : null;
  return {
    maxMult: 1 + gameState.build.resourceMaxBonus,
    coolMult: m.flags.coolMult,
    groggyMs: m.flags.groggyMs > 0 ? m.flags.groggyMs : endureGroggy,
  };
}

/**
 * 60라운드 (57 Q43 '거인 차지 4단'): 대검 2단 거인(rule giant) 런이면 차지 단계에 4단을 더한다 — stage4Ms(1.6초)·피해 stage4Mult(×3.8)·
 * 그림 키 stage4Art (없으면 마지막 단계 그림). 쐐기 길이·충격원은 마지막 단계와 같고, 진동 반경 5칸(ringRadiusTiles)은 중압 원형 진동이.
 * 거인이 아니면 데이터 단계 그대로
 */
export function chargeStages(def: ComboChargeDef): ComboChargeStageDef[] {
  const giant = ruleOf(currentBuild(), 'giant');
  const last = def.stages[def.stages.length - 1];
  if (!giant || !last || !(param(giant, 'stage4Ms') > last.atMs)) return def.stages;
  const art = giant.params.stage4Art;
  return [
    ...def.stages,
    {
      ...last,
      atMs: param(giant, 'stage4Ms'),
      damageMult: param(giant, 'stage4Mult', last.damageMult),
      art: typeof art === 'string' ? art : last.art,
      followUps: undefined,
    },
  ];
}
