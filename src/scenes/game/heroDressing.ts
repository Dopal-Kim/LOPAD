/**
 * 62 루프 2 시스템 D (P2-10 · art §31.9) 세트피스·그을음 그림 (자리는 world/heroSetpiece — 칸 막힘은 TileWorld 고정 큰 소품).
 * 세트피스 = 발자국 아래 가운데에 피벗(Y 정렬, occludeAbove 는 StructureView), 그을음 = 바닥 깊이 데칼(변주 v0~v5 · 좌우 뒤집기).
 * 시트가 없으면 그리지 않는다(칸만 막힌다 — 플레이스홀더 사각형 금지).
 */
import Phaser from 'phaser';
import { BUNDLE_FX, DEPTH, HERO_SETPIECE, TILE } from '../../core/Constants';
import { STRUCTURE_ACTION } from '../../systems/sprites/spriteActions';
import { spriteLibrary } from '../../systems/sprites/sprites';
import type { HeroSetpiece, SootDecal } from '../../world/heroSetpiece';
import { StructureView } from '../../world/StructureView';

const loaded = (scene: Phaser.Scene, sheet: string): boolean => {
  const tex = spriteLibrary.textureKey(sheet, STRUCTURE_ACTION);
  return Boolean(tex && scene.textures.exists(tex));
};

export function drawHeroDressing(scene: Phaser.Scene, hero: HeroSetpiece | null, soot: readonly SootDecal[]): void {
  if (hero && loaded(scene, hero.sheet)) {
    const v = new StructureView(scene, {
      sheet: hero.sheet,
      rect: new Phaser.Geom.Rectangle(hero.tx * TILE, hero.ty * TILE, hero.w * TILE, hero.h * TILE),
      color: BUNDLE_FX.PROP_COLOR,
      label: '',
      floor: false,
    });
    v.sprite?.setFlipX(hero.flipX);
  }
  if (!loaded(scene, HERO_SETPIECE.SOOT_SHEET)) return;
  for (const d of soot) {
    const v = new StructureView(scene, {
      sheet: HERO_SETPIECE.SOOT_SHEET,
      rect: new Phaser.Geom.Rectangle(d.x * TILE, d.y * TILE, TILE, TILE),
      color: BUNDLE_FX.PROP_COLOR,
      label: '',
      floor: true,
      unlit: true,
    });
    if (v.hasState(`v${d.variant}`)) v.setState(`v${d.variant}`);
    v.sprite?.setFlipX(d.flipX).setDepth(DEPTH.FX_GROUND - 1);
  }
}
