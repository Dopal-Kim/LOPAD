/**
 * P21 아트 B 시트 읽기 도우미 (art §37 · `parts/art/work/gore21/NOTES.md`) — fx v5 정지 그림 프레임 고르기·배율·피벗.
 * 프레임 번호 = row × 열 수 + column (§19 아틀라스 키). 시트가 없으면 null (호출 쪽이 임시 그림).
 */
import type Phaser from 'phaser';
import { spriteLibrary } from '../../../systems/sprites/sprites';
import { FX_ACTION, fxDrawScale, type SheetDef } from '../../../systems/sprites/spriteDefs';

/** v5 JSON 의 P21 필드 (SheetDef 에 그대로 실려 온다) */
export interface GoreSheetExtras {
  byCut?: Record<string, number[]>;
  directional?: number[];
  decalHint?: { count: number[]; distDots: [number, number]; spawnAtFrame: number };
  restFrame?: Record<string, number>;
  spawnFromEnemyPivot?: Record<string, { x: number; y: number }>;
  physicsHint?: { flightMs: [number, number]; speedDots: [number, number]; upDots: [number, number]; bounce?: number };
  floorDots?: number;
  arrowAnchors?: Record<string, (Record<string, ArrowAnchor> | null)[]>;
  timingMs?: { hitAt: number; total: number };
}

export interface ArrowAnchor {
  x: number;
  y: number;
  frame: number;
  flipX: boolean;
  depth: 'above' | 'below';
}

export type GoreSheet = SheetDef & GoreSheetExtras;

/** 로드된 fx 시트 (텍스처까지 있을 때만) */
export function fxSheet(scene: Phaser.Scene, id: string): { def: GoreSheet; key: string; scale: number } | null {
  const def = spriteLibrary.sheet(id, FX_ACTION) as GoreSheet | undefined;
  const key = spriteLibrary.textureKey(id, FX_ACTION);
  if (!def || !key || !scene.textures.exists(key)) return null;
  return { def, key, scale: fxDrawScale(def) };
}

/** 정지 그림 하나: 시트 피벗 원점·배율로 (frame = 프레임 번호) */
export function sheetImage(
  scene: Phaser.Scene,
  s: { def: GoreSheet; key: string; scale: number },
  x: number,
  y: number,
  frame: number,
): Phaser.GameObjects.Image {
  return scene.add
    .image(x, y, s.key, frame)
    .setOrigin(s.def.pivot.x / s.def.frameWidth, s.def.pivot.y / s.def.frameHeight)
    .setScale(s.scale);
}

export const pick = <T>(list: readonly T[]): T => list[Math.floor(Math.random() * list.length)];
