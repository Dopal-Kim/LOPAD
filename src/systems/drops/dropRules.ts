/**
 * 61 단계 5 (P13 §4) 바닥 줍기 물건의 순수 규칙 (Phaser 의존 없음 — 단위 테스트): 전표 무더기 크기 · 시트 행·프레임 ·
 * 자석 흡수 한 걸음 · 늘어남 배율.
 */

export type VoucherSize = 'small' | 'mid' | 'large';
export const VOUCHER_SIZES: readonly VoucherSize[] = ['small', 'mid', 'large'];

/** 전표 값 → 무더기 크기 (경계 = economy.json pickup.voucherSize) */
export function voucherSize(value: number, T: { mid: number; large: number }): VoucherSize {
  if (value >= T.large) return 'large';
  if (value >= T.mid) return 'mid';
  return 'small';
}

/** 시트 메타 중 줍기 그림이 쓰는 부분 (계약 art §27 — 행 = kinds, states = 그 행 안의 열 번호) */
export interface DropSheetMeta {
  frames: number;
  kinds?: string[];
  states?: Record<string, number[]>;
  shadow?: boolean;
}

/**
 * 상태 프레임 (아틀라스 프레임 번호 = 행 × 행당 프레임 + 열). 행 = kinds 에서 row 이름의 자리 (없으면 0).
 * 상태가 없으면 [] (idle 이 없으면 0 열 하나)
 */
export function dropFrames(def: DropSheetMeta, state: string, row: string | null): number[] {
  const r = row && def.kinds ? Math.max(0, def.kinds.indexOf(row)) : 0;
  const cols = def.states?.[state];
  if (Array.isArray(cols) && cols.length > 0)
    return cols.filter((c) => c >= 0 && c < def.frames).map((c) => r * def.frames + c);
  return state === 'idle' ? [r * def.frames] : [];
}

/**
 * 자석 흡수 한 걸음: 속도(px/s)를 accel 만큼 올리고(최고 max) 대상 쪽으로. 도착(이번 걸음 안)이면 arrived.
 * 반환 = 새 위치·속도 (위치는 대상을 넘지 않는다)
 */
export function magnetStep(
  pos: { x: number; y: number },
  target: { x: number; y: number },
  speed: number,
  dtMs: number,
  o: { accel: number; max: number },
): { x: number; y: number; speed: number; vx: number; vy: number; arrived: boolean } {
  const dt = Math.max(0, dtMs) / 1000;
  const v = Math.min(o.max, speed + o.accel * dt);
  const dx = target.x - pos.x;
  const dy = target.y - pos.y;
  const d = Math.hypot(dx, dy);
  const step = v * dt;
  if (d <= step || d === 0) return { x: target.x, y: target.y, speed: v, vx: 0, vy: 0, arrived: true };
  const ux = dx / d;
  const uy = dy / d;
  return { x: pos.x + ux * step, y: pos.y + uy * step, speed: v, vx: ux * v, vy: uy * v, arrived: false };
}

/**
 * 흡수 중 늘어남: 움직이는 축으로 1 + s, 다른 축으로 1 − s/2 (s = 최대 비율 × 속도/최고 속도). 정지면 [1, 1]
 */
export function stretchScale(vx: number, vy: number, max: number, stretch: number): [number, number] {
  const sp = Math.hypot(vx, vy);
  if (sp <= 0 || max <= 0) return [1, 1];
  const s = stretch * Math.min(1, sp / max);
  return Math.abs(vx) >= Math.abs(vy) ? [1 + s, 1 - s / 2] : [1 - s / 2, 1 + s];
}
