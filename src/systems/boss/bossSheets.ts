/**
 * 보스방 시트 로드 목록. 54라운드: 보스 정의 arena 의 촛대·기둥 시트 + 술통·이펙트 (매니페스트에 있을 때만 로드).
 * 61라운드 E (VRAM): 보스 묶음(보스 노드 preload)에 파훼 표시 작은 시트를 더하고, 큰 연출 시트는 지연 묶음으로 뺀다 —
 * 림라이트(3국면 소등 동안만) · 결정타·쓰러짐·불 끄기 fx(3국면 진입 = HP 30% 때). 등장 동작(intro)은 보스 묶음에 있고 전투 시작 때 내린다.
 * Phaser 의존 없음.
 */
import { BOSS_ART, BOSS_FX } from '../../core/Constants';
import { BOSSES } from '../../data';
import { FX_ACTION } from '../sprites/spriteActions';
import type { SheetRequest } from '../sprites/sheetPaths';

export function bossStructureSheets(): string[] {
  const A = BOSS_ART.SHEETS;
  const out = new Set<string>([BOSS_FX.SHEETS.CASK, BOSS_FX.SHEETS.CASK_BREAK, A.CASK_RIM, A.CASK_RETURNED]);
  for (const b of Object.values(BOSSES)) {
    for (const s of b.arena?.candle.sprite ?? []) out.add(s);
    for (const s of b.arena?.pillarSprite ?? []) out.add(s);
  }
  return [...out];
}

export function bossFxSheets(): string[] {
  const S = BOSS_FX.SHEETS;
  const A = BOSS_ART.SHEETS;
  return [S.TORCH, S.CUP_SHATTER, S.SPLASH, S.GLOB, S.ONFIRE, S.ONFIRE_DOWN, A.CUP_GLINT, A.BREAK_DAZE, A.CANDLE_GLINT];
}

/**
 * 보스 묶음에서 빼고 전투 시작 뒤에 올리는 몸 동작 (등장 동작과 겹치지 않게 — 국면 전환 들이켜기는 2국면 진입(HP 65%)에 처음 쓴다)
 */
export const BOSS_DEFERRED_ACTIONS: readonly string[] = ['phase_drink'];

export function bossDeferredRequests(bossIds: readonly string[]): SheetRequest[] {
  return bossIds.flatMap((name) =>
    BOSS_DEFERRED_ACTIONS.map((action): SheetRequest => ({ category: 'bosses', name, action })),
  );
}

/** 보스 지연 묶음 전부 (전투 뒤 들이켜기 · 림 · 결정타 fx) — 보스 노드를 떠날 때 내린다 */
export function bossLazyRequests(bossIds: readonly string[]): SheetRequest[] {
  return [...bossDeferredRequests(bossIds), ...bossRimRequests(bossIds), ...bossFinaleRequests()];
}

/** 림라이트 동작 이름 `<동작>_rim` */
export function rimAction(action: string): string {
  return `${action}_${BOSS_ART.RIM_SUFFIX}`;
}

/** 지연 묶음: 림라이트 오버레이 (보스 몸 동작마다 `<보스>_<동작>_rim`) */
export function bossRimRequests(bossIds: readonly string[]): SheetRequest[] {
  return bossIds.flatMap((name) =>
    BOSS_ART.RIM_ACTIONS.map((a): SheetRequest => ({ category: 'bosses', name, action: rimAction(a) })),
  );
}

/** 지연 묶음: 결정타 일섬·충격 · 쓰러짐 파편 · 불 끄기 */
export function bossFinaleRequests(): SheetRequest[] {
  const A = BOSS_ART.SHEETS;
  return [A.FINISHER_SLASH, A.FINISHER_BURST, A.DEFEAT_SHATTER, A.FLAME_SNUFF].map((name): SheetRequest => ({
    category: 'fx',
    name,
    action: FX_ACTION,
  }));
}

/** 보스 등장 동작 시트 (보스 묶음에 들어 있다 — 전투 시작 때 내리는 목록) */
export function bossIntroRequests(bossIds: readonly string[]): SheetRequest[] {
  return bossIds.map((name): SheetRequest => ({ category: 'bosses', name, action: BOSS_ART.INTRO_ACTION }));
}
