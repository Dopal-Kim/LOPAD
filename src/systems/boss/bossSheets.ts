/** 54라운드 보스방 시트 로드 목록 (Preloader): 보스 정의 arena 의 촛대·기둥 시트 + 술통·이펙트 (매니페스트에 있을 때만 로드) */
import { BOSS_FX } from '../../core/Constants';
import { BOSSES } from '../../data';

export function bossStructureSheets(): string[] {
  const out = new Set<string>([BOSS_FX.SHEETS.CASK, BOSS_FX.SHEETS.CASK_BREAK]);
  for (const b of Object.values(BOSSES)) {
    for (const s of b.arena?.candle.sprite ?? []) out.add(s);
    for (const s of b.arena?.pillarSprite ?? []) out.add(s);
  }
  return [...out];
}

export function bossFxSheets(): string[] {
  const S = BOSS_FX.SHEETS;
  return [S.TORCH, S.CUP_SHATTER, S.SPLASH, S.GLOB];
}
