/**
 * 쿼터뷰 타일셋의 도트 길이 → 월드 환산 (60라운드 계약 art §11 P1: 1층 5지역 타일셋이 64도트 = 1칸·pixelScale 0.5 가 되며
 * tileLights·decals rect·props/bigProps 의 rect·pivot·occludeAbove·light radius·offset 이 모두 도트 단위로 2배 — 같은 배율
 * `TILE / tilePx`(= pixelScale / WORLD_TO_SCREEN)로 환산해 화면상 크기는 그대로). QuarterView 가 쓰고 테스트가 실제 JSON 으로 확인한다.
 * Phaser 의존 없음.
 */
import { TILE } from '../core/Constants';
import type { LightSpec } from '../systems/sprites/spriteDefs';
import { lightOffsetOf, type LightOffset } from './tileskin';

type DotLight = LightSpec & { offset?: LightOffset };

/** 바닥 타일셋 한 칸(tilePx 도트) → 월드 배율 (한 칸 = TILE) */
export function tileDotScale(tilePx: number): number {
  return TILE / Math.max(1, tilePx);
}

/**
 * 칸 하나에 붙는 광원(앞면 창·문틈 tileLights · 수로 다리 · 인덱스 소품): offset = 칸 안 도트 좌표(없으면 칸 가운데),
 * 반경 = 도트 × radiusScale. offsetScale 은 칸 도트 → 월드(TILE / tilePx)
 */
export function cellLight(
  l: DotLight,
  tx: number,
  ty: number,
  tilePx: number,
  offsetScale: number,
  radiusScale = offsetScale,
): { spec: DotLight; x: number; y: number } {
  const o = lightOffsetOf(l.offset) ?? { x: tilePx / 2, y: tilePx / 2 };
  return {
    spec: { ...l, radius: l.radius * radiusScale },
    x: tx * TILE + o.x * offsetScale,
    y: ty * TILE + o.y * offsetScale,
  };
}

/**
 * 시트 영역(rect)에 붙는 광원: offset = rect 왼쪽 위 기준 도트(없으면 피벗 위 그림 높이 절반), 피벗을 월드 (x, y) 에 둔다
 */
export function cutLight(
  l: DotLight,
  x: number,
  y: number,
  pivot: { x: number; y: number },
  k: number,
): { spec: DotLight; x: number; y: number } {
  const o = lightOffsetOf(l.offset);
  const at = o ? { x: x + (o.x - pivot.x) * k, y: y + (o.y - pivot.y) * k } : { x, y: y - pivot.y * k * 0.5 };
  return { spec: { ...l, radius: l.radius * k }, ...at };
}

/** occludeAbove(피벗 위 도트) → rect 안 자르는 높이 (그 위 = Y 정렬 그림, 아래 = 받침). 없으면 rect 전체 */
export function occludeCut(d: { rect: { h: number }; pivot: { y: number }; occludeAbove?: number }): number {
  return typeof d.occludeAbove === 'number' ? Math.max(0, Math.round(d.pivot.y - d.occludeAbove)) : d.rect.h;
}
