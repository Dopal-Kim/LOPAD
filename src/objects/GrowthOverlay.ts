/**
 * 61라운드 단계 4 P12 무기 각성 외형 오버레이 (계약 art §26 — WeaponOverlay 에서 분리): 무기 위에 같은 프레임 번호·피벗으로
 * 무기 → 1차 모양 `<갈래>_a1_<동작>` → 2차 덧붙임 `<갈래>_a2_<동작>` → 길 강조색 마스크 `<갈래>_a2_glow_<동작>`(setTint(JSON
 * pathTint[길]), NORMAL) → (WeaponOverlay 의 검기·울분). 옛 `_awaken` 대신 (art §26 완료 — 틀·프레임은 `sameFrameAs`).
 * 그 동작의 a1 시트가 없을 때만 옛 `<동작>_awaken` 으로 폴백하고, 2차 덧붙임이 없으면 1차(또는 폴백) 오버레이를 길 색으로 물들인다.
 * 각성 순간(시트 로드·메뉴 닫힘 전)에는 잠시 숨긴다(`held`) — 각성 연출 fx 와 같은 순간에 켠다.
 */
import Phaser from 'phaser';
import { DEPTH } from '../core/Constants';
import { spriteLibrary } from '../systems/sprites/sprites';
import { overlayPivot } from '../systems/sprites/spriteMeta';
import { artScale, frameAt, type Dir8, type SheetDef } from '../systems/sprites/spriteDefs';
import { AWAKEN_OVERLAY_SUFFIX, growthOverlayAction } from '../systems/sprites/sheetSets';

export interface GrowthLook {
  branch: string;
  stage: 1 | 2;
  /** 2차 길 id (glow 색 = 시트 JSON pathTint[길]) */
  path: string | null;
  /** 2차 길 강조색 폴백 (0xRRGGBB — 시트 JSON 에 pathTint 가 없을 때, 없으면 null) */
  tint: number | null;
  /** 셋째 갈래 = 옛 최종 각성 모양을 1차 모양으로 (a1 이 없으면 `_awaken`) */
  legacy: boolean;
}

type SheetOf = (id: string, action: string) => SheetDef | undefined;

export class GrowthOverlay {
  look: GrowthLook | null = null;
  held = false;
  /** 디버그: 지금 겹친 1차·2차 시트 동작 */
  shown: { a1: string | null; a2: string | null; glow: string | null } = { a1: null, a2: null, glow: null };
  private readonly sprites: Phaser.GameObjects.Sprite[] = [];

  constructor(
    private readonly scene: Phaser.Scene,
    private readonly sheetOf: SheetOf,
  ) {}

  private sprite(i: number): Phaser.GameObjects.Sprite {
    let s = this.sprites[i];
    if (!s) {
      s = this.scene.add.sprite(0, 0, '__DEFAULT').setVisible(false);
      this.sprites[i] = s;
    }
    return s;
  }

  /** 무기 시트(base)와 같은 프레임으로 겹친다 */
  show(
    weaponId: string,
    action: string,
    dir: Dir8,
    column: number,
    base: Phaser.GameObjects.Sprite,
    body: SheetDef | undefined,
    drawScale: number,
  ): void {
    const L = this.look;
    if (!L || this.held) {
      this.hide();
      return;
    }
    const a1Name = growthOverlayAction(L.branch, 1, action);
    const fallback = `${action}_${AWAKEN_OVERLAY_SUFFIX}`;
    const a1 = this.sheetOf(weaponId, a1Name) ? a1Name : this.sheetOf(weaponId, fallback) ? fallback : null;
    const a2Name = L.stage >= 2 ? growthOverlayAction(L.branch, 2, action) : null;
    const a2 = a2Name && this.sheetOf(weaponId, a2Name) ? a2Name : null;
    const glowName = L.stage >= 2 ? growthOverlayAction(L.branch, 2, action, true) : null;
    const glow = glowName && this.sheetOf(weaponId, glowName) ? glowName : null;
    // 2차인데 덧붙임이 없으면 1차 오버레이를 길 색으로 (glow 마스크가 있으면 그것만 물들인다)
    const tintA1 = L.stage >= 2 && !a2 && !glow ? L.tint : null;
    this.place(0, weaponId, a1, dir, column, base, body, drawScale, 0.125, tintA1);
    this.place(1, weaponId, a2, dir, column, base, body, drawScale, 0.15, null);
    this.place(2, weaponId, glow, dir, column, base, body, drawScale, 0.175, this.glowTint(weaponId, glow, L));
    this.shown = { a1, a2, glow };
  }

  /** 길 강조색: glow 시트 JSON pathTint[길] (없으면 데이터 폴백) */
  private glowTint(weaponId: string, glow: string | null, L: GrowthLook): number | null {
    const def = glow
      ? (this.sheetOf(weaponId, glow) as (SheetDef & { pathTint?: Record<string, number[]> }) | undefined)
      : undefined;
    const c = L.path ? def?.pathTint?.[L.path] : undefined;
    return c && c.length >= 3 ? (c[0] << 16) | (c[1] << 8) | c[2] : L.tint;
  }

  private place(
    i: number,
    weaponId: string,
    name: string | null,
    dir: Dir8,
    column: number,
    base: Phaser.GameObjects.Sprite,
    body: SheetDef | undefined,
    drawScale: number,
    depthStep: number,
    tint: number | null,
  ): void {
    const def = name ? this.sheetOf(weaponId, name) : undefined;
    if (!name || !def) {
      if (this.sprites[i]?.visible) this.sprites[i].setVisible(false);
      return;
    }
    const o = this.sprite(i);
    const tex = spriteLibrary.textureKey(weaponId, name)!;
    if (o.texture.key !== tex) o.setTexture(tex, 0);
    const pv = overlayPivot(def, body);
    o.setOrigin(pv.x / def.frameWidth, pv.y / def.frameHeight)
      .setFrame(frameAt(def, dir, Math.min(column, def.frames - 1)))
      .setScale(artScale(def) * drawScale)
      .setPosition(base.x, base.y)
      .setAlpha(base.alpha)
      .setDepth(base.depth + DEPTH.OVERLAY_STEP * depthStep)
      .setVisible(base.visible);
    if (tint !== null) o.setTint(tint);
    else o.clearTint();
  }

  hide(): void {
    for (const s of this.sprites) if (s?.visible) s.setVisible(false);
    this.shown = { a1: null, a2: null, glow: null };
  }

  destroy(): void {
    for (const s of this.sprites) s?.destroy();
    this.sprites.length = 0;
  }
}
