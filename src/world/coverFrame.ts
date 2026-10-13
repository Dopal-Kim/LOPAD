/** 62 I (P1-N7): 엄폐 칸 돌기둥 프레임 고르기 (Phaser 없음 — 그림은 coverPillars) */
import { COVER_PILLAR } from '../core/Constants';

/** 지역 → 시트 행 (없으면 0행) */
export function coverRow(region: string | null | undefined): number {
  const P = COVER_PILLAR;
  const r = region ? (P.REGION_ROWS.includes(region) ? region : (P.REGION_ALIAS[region] ?? null)) : null;
  return Math.max(0, r ? P.REGION_ROWS.indexOf(r) : 0);
}

/** 칸 → 상태 열 (좌표 해시 · STATE_WEIGHTS 비율, 결정적) */
export function coverColumn(x: number, y: number, seed = 0): number {
  const W = COVER_PILLAR.STATE_WEIGHTS;
  const total = W.reduce((a, b) => a + b, 0);
  let h =
    (Math.imul(x + 0x9e37, 0x85ebca6b) ^ Math.imul(y + 0x7f4a, 0xc2b2ae35) ^ Math.imul(seed | 0, 0x27d4eb2f)) >>> 0;
  h = Math.imul(h ^ (h >>> 15), 0x2c1b3c6d) >>> 0;
  let r = (h ^ (h >>> 13)) % total;
  for (let i = 0; i < W.length; i++) {
    if (r < W[i]) return i;
    r -= W[i];
  }
  return 0;
}

/** 프레임 번호 = 행 × 열 수 + 열 */
export function coverFrameIndex(region: string | null | undefined, x: number, y: number, seed = 0): number {
  return coverRow(region) * COVER_PILLAR.STATE_WEIGHTS.length + coverColumn(x, y, seed);
}
