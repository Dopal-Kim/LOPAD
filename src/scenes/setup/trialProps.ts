/**
 * 62 회피 시험 탄생 전장 소품 (계약 art §30 `structures/v3/birth_*`): 엄폐 3(시체 더미·시체 둔덕·창 덤불 — solid, 걷기·화살 막음)
 * + 장식 3(피 묻은 깃발·쓰러진 병사·부러진 창 — 판정 없음). 자리·크기는 `data/narrative.json ritual.trial.props`.
 * 시트는 Setup preload 에서 받는다(`trialPropRequests`). 매니페스트에 없거나 로드되지 않은 시트는 놓지 않는다(자리표시 도형 없음).
 */
import Phaser from 'phaser';
import { TILE } from '../../core/Constants';
import type { TrialPropDef } from '../../data/ritual';
import { sheetListed } from '../../systems/sprites/sheetLoader';
import { STRUCTURE_ACTION } from '../../systems/sprites/spriteActions';
import type { SheetRequest } from '../../systems/sprites/sheetPaths';
import { spriteLibrary } from '../../systems/sprites/sprites';
import { spotAt } from '../../systems/ritual/ritual';
import { StructureView } from '../../world/StructureView';

/** 받을 시트 (매니페스트에 있는 것만) */
export function trialPropRequests(props: readonly TrialPropDef[]): SheetRequest[] {
  return props
    .map((p) => ({ category: 'structures' as const, name: p.sheet, action: STRUCTURE_ACTION }))
    .filter((r) => sheetListed(r));
}

/** 소품이 차지할 칸 (왼쪽 위 칸 + 크기) */
export function propTiles(
  p: TrialPropDef,
  area: { x: number; y: number; w: number; h: number },
): { tx: number; ty: number; w: number; h: number } {
  const c = spotAt(p.at, area);
  return { tx: Math.round(c.x / TILE - p.w / 2), ty: Math.round(c.y / TILE - p.h / 2), w: p.w, h: p.h };
}

/** 놓기: 그림이 있는 소품만. 반환 = 만든 그림 · solid 칸 목록 */
export function placeTrialProps(
  scene: Phaser.Scene,
  props: readonly TrialPropDef[],
  area: { x: number; y: number; w: number; h: number },
): { views: StructureView[]; solid: { tx: number; ty: number }[] } {
  const views: StructureView[] = [];
  const solid: { tx: number; ty: number }[] = [];
  for (const p of props) {
    const tex = spriteLibrary.textureKey(p.sheet, STRUCTURE_ACTION);
    if (!tex || !scene.textures.exists(tex)) continue;
    const t = propTiles(p, area);
    const rect = new Phaser.Geom.Rectangle(t.tx * TILE, t.ty * TILE, t.w * TILE, t.h * TILE);
    views.push(
      new StructureView(scene, {
        sheet: p.sheet,
        rect,
        color: '#6a5040',
        label: '',
        floor: Boolean(p.floor),
        unlit: true,
      }),
    );
    if (p.solid)
      for (let y = t.ty; y < t.ty + t.h; y++) for (let x = t.tx; x < t.tx + t.w; x++) solid.push({ tx: x, ty: y });
  }
  return { views, solid };
}
