/**
 * 57라운드 빌드 축: 지금 런의 합산 (GameState 의 패시브·무기·빌드 상태 — 캐시). 시스템 곳곳의 수치 훅이 이것만 읽는다.
 */
import { gameState } from '../../core/GameState';
import { BUILD } from '../../data/build';
import type { BuildStatKey } from '../../data/buildTypes';
import type { BuildMods } from './buildMods';

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
