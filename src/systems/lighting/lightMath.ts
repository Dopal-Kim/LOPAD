/**
 * 50라운드 동적 조명 순수 규칙 (Phaser 의존 없음): 깜빡임 · 광원 고르기(상한·화면 안) · 색.
 */
import type { LightingAmbient, LightingData } from '../../data/types';

/** '#rrggbb' → 0xrrggbb (형식이 아니면 fallback) */
export function hexColor(hex: string | undefined, fallback: number): number {
  if (!hex || !/^#[0-9a-fA-F]{6}$/.test(hex)) return fallback;
  return parseInt(hex.slice(1), 16);
}

/** 광원 감쇠 (52라운드 Q9 — 아트 목업과 같은 식): d = 중심 거리 / 반경, (1 - d²)², 반경 밖 0 */
export function lightFalloff(d: number): number {
  if (!(d < 1)) return 0;
  const t = 1 - Math.max(0, d) ** 2;
  return t * t;
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

/**
 * 지역 주변광 고르기: 지역 자기 값(regions) → 53라운드 Q38: 외벽 테두리 지역이면(borderRegions) regions 에 없을 때 default
 * (5지역 같은 방식·상향된 밝기) → `?light=1`(flag) 이면 그 밖의 전투장·시험장에도 default → 없음(끔). `?light=0` 은 늘 끔
 */
export function lightingAmbientFor(
  region: string | null | undefined,
  flag: string | null,
  arenaOrLab: boolean,
  hasBorder: (region: string | null | undefined) => boolean,
  data: Pick<LightingData, 'regions' | 'default' | 'borderRegions'>,
): LightingAmbient | null {
  if (flag === '0') return null;
  const own = region ? data.regions[region] : undefined;
  if (own) return own;
  if (data.borderRegions && hasBorder(region)) return data.default;
  return flag === '1' && arenaOrLab ? data.default : null;
}

/** 화면 w×h 를 각도 rad 만큼 돌렸을 때 원래 화면을 다 덮는 배율 (54라운드 세상이 돈다 — 라이트맵 모서리 새는 문제) */
export function rotationCover(w: number, h: number, rad: number): number {
  const c = Math.abs(Math.cos(rad));
  const s = Math.abs(Math.sin(rad));
  if (s < 1e-6) return 1;
  return Math.max((w * c + h * s) / w, (w * s + h * c) / h);
}
