/**
 * 62 루프 3 시스템 I (P1-N7 · art §31-9): 전투장 엄폐 담 칸을 돌기둥(`structures/v3/pillar_stone`)으로 그린다.
 * 칸은 벽 그대로(TileWorld 충돌 — 걷기·투사체 막기 유지), QuarterView 가 그 칸의 벽 타일 대신 기둥 그림 한 장을 세운다.
 * 프레임 = 지역 행 × 3 + 상태 열(온전·금·부서짐 — 칸 좌표 해시). 시트가 없으면 null → 예전 돌담 그림.
 */
import type Phaser from 'phaser';
import { STRUCTURE_ACTION } from '../systems/sprites/spriteActions';
import { spriteLibrary } from '../systems/sprites/sprites';
import { COVER_PILLAR } from '../core/Constants';
import { artScale } from '../systems/sprites/spriteDefs';
import { coverFrameIndex } from './coverFrame';

/** QuarterView 에 넘기는 기둥 그림 (칸 키 `"x,y"`) */
export interface CoverArt {
  cells: ReadonlySet<string>;
  texture: string;
  /** 칸의 프레임 이름 */
  frameOf(x: number, y: number): string | number;
  pivot: { x: number; y: number };
  frameWidth: number;
  frameHeight: number;
  /** 도트 → 월드 */
  scale: number;
}

/** 엄폐 칸 기둥 그림 (시트가 아직 없으면 null) */
export function coverArtFor(
  scene: Phaser.Scene,
  region: string | null | undefined,
  cells: readonly { x: number; y: number }[],
  seed = 0,
): CoverArt | null {
  if (cells.length === 0) return null;
  const def = spriteLibrary.sheet(COVER_PILLAR.SHEET, STRUCTURE_ACTION);
  const texture = spriteLibrary.textureKey(COVER_PILLAR.SHEET, STRUCTURE_ACTION);
  if (!def || !texture || !scene.textures.exists(texture)) return null;
  const tex = scene.textures.get(texture);
  return {
    cells: new Set(cells.map((c) => `${c.x},${c.y}`)),
    texture,
    frameOf: (x, y) => {
      const i = coverFrameIndex(region, x, y, seed);
      return tex.has(String(i)) ? String(i) : i;
    },
    pivot: { ...def.pivot },
    frameWidth: def.frameWidth,
    frameHeight: def.frameHeight,
    scale: artScale(def),
  };
}
