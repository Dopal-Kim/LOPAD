/** 54라운드 Q21 굴러가는 술통 그림 → 판정·회전 수치 (Phaser 없음 — 단위 테스트) */
import { RENDER } from '../../core/Constants';
import type { SheetJson } from '../spriteDefs';

/**
 * 술통 그림 한 바퀴 굴림 둘레 (월드 px). 아트 JSON `circumferencePx` 는 **논리 px**(도트 × 0.5 — rotationNote "157 도트(78 논리 px)")
 * → 월드 = 논리 ÷ WORLD_TO_SCREEN. 없으면 null
 */
export function caskCircumferenceWorld(def: Pick<SheetJson, 'circumferencePx'> | undefined): number | null {
  const c = def?.circumferencePx;
  return typeof c === 'number' && c > 0 ? c / RENDER.WORLD_TO_SCREEN : null;
}

/**
 * 54라운드 Q21: 판정 반경 = 그림 지름 / 2 × ratio. 지름 = JSON `diameterPx`(논리 px, 아트 2차) → 없으면 굴림 둘레 / π →
 * 그림이 없으면 fallbackPx
 */
export function caskRadiusFromArt(
  def: Pick<SheetJson, 'circumferencePx' | 'diameterPx'> | undefined,
  fallbackPx: number,
  ratio: number,
): number {
  const d = def?.diameterPx;
  if (typeof d === 'number' && d > 0) return (d / RENDER.WORLD_TO_SCREEN / 2) * ratio;
  const c = caskCircumferenceWorld(def);
  return c === null ? fallbackPx : (c / (2 * Math.PI)) * ratio;
}
