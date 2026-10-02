/**
 * 50라운드 동적 조명 순수 규칙 (Phaser 의존 없음): 깜빡임 · 광원 고르기(상한·화면 안) · 색.
 */

/** '#rrggbb' → 0xrrggbb (형식이 아니면 fallback) */
export function hexColor(hex: string | undefined, fallback: number): number {
  if (!hex || !/^#[0-9a-fA-F]{6}$/.test(hex)) return fallback;
  return parseInt(hex.slice(1), 16);
}

/** 0..1 의 결정적 의사 난수 (광원마다 깜빡임 위상·주파수를 다르게) */
export function hash01(seed: number): number {
  const x = Math.sin(seed * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
}

/**
 * 깜빡임 배율 (1 - amount × 잡음). 잡음 = 서로 다른 주파수 사인 두 개의 합(0..1) — 불꽃처럼 고르지 않게.
 * amount 0 이면 1. hz = [최소, 최대] 주파수, seed 로 광원마다 주파수·위상이 다르다
 */
export function flickerFactor(timeMs: number, seed: number, amount: number, hz: readonly [number, number]): number {
  if (!(amount > 0)) return 1;
  const t = timeMs / 1000;
  const f1 = hz[0] + (hz[1] - hz[0]) * hash01(seed);
  const f2 = f1 * 2.37;
  const p1 = hash01(seed + 1) * Math.PI * 2;
  const p2 = hash01(seed + 2) * Math.PI * 2;
  const n = 0.5 + 0.5 * (0.6 * Math.sin(Math.PI * 2 * f1 * t + p1) + 0.4 * Math.sin(Math.PI * 2 * f2 * t + p2));
  return 1 - Math.min(1, amount) * n;
}

export interface LightPick {
  x: number;
  y: number;
  radius: number;
  /** 늘 포함 (주인공 빛) */
  pinned?: boolean;
}

/**
 * 그릴 광원 고르기: 보이는 영역(중심 cx,cy · 반폭 hw·반높이 hh)에 반경이 걸치는 것만, 고정(pinned) 먼저, 그다음 화면 중심에
 * 가까운 순으로 max 개. 반환 = 원래 배열의 인덱스
 */
export function pickLights(
  lights: readonly LightPick[],
  cx: number,
  cy: number,
  hw: number,
  hh: number,
  max: number,
): number[] {
  const visible: { i: number; d: number; pinned: boolean }[] = [];
  lights.forEach((l, i) => {
    const dx = Math.max(0, Math.abs(l.x - cx) - hw);
    const dy = Math.max(0, Math.abs(l.y - cy) - hh);
    if (dx * dx + dy * dy > l.radius * l.radius && !l.pinned) return;
    visible.push({ i, d: (l.x - cx) ** 2 + (l.y - cy) ** 2, pinned: Boolean(l.pinned) });
  });
  visible.sort((a, b) => Number(b.pinned) - Number(a.pinned) || a.d - b.d);
  return visible.slice(0, Math.max(0, max)).map((v) => v.i);
}
