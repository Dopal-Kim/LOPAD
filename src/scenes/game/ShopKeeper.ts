/**
 * 61라운드 단계 2 (플레이 점검 #12): 상점 노드 상인 — 상점 칸(2×2) 바로 위에 독주 행상 그림(idle, 아래를 봄)을 상인으로 세우고
 * 등불 광원을 단다. 가까이 가면 E 안내(계약 §9.1 `UiInteractable` — 종류는 NPC 상인 계열 `mapSeller`), E 로 상점을 연다.
 * 상점 칸을 밟아 여는 기존 길도 그대로. 그림이 없으면 플레이스홀더 사각형.
 */
import Phaser from 'phaser';
import { BUNDLE_FX, SHOP_KEEPER, TILE, entityDepth } from '../../core/Constants';
import { STORY } from '../../data';
import type { UiInteractable } from '../../contract/ui';
import { worldToLogicalScreen } from '../../systems/display';
import { lightRegistryOf } from '../../systems/lighting/lightRegistry';
import { spriteLibrary } from '../../systems/sprites/sprites';
import { artScale } from '../../systems/sprites/spriteDefs';
import type { Game } from '../Game';

export class ShopKeeper {
  readonly x: number;
  readonly y: number;
  private readonly view: Phaser.GameObjects.Sprite | Phaser.GameObjects.Rectangle;

  /** shop = 상점 칸 왼쪽 위 타일 */
  constructor(
    private readonly g: Game,
    shop: { x: number; y: number },
  ) {
    const K = SHOP_KEEPER;
    // 상점 칸 2×2 의 윗변 가운데, 그 위 한 칸에 선다 (발 = 칸 아랫변)
    this.x = (shop.x + 1) * TILE;
    this.y = shop.y * TILE - K.FOOT_GAP_PX;
    const anim = spriteLibrary.animKey(K.SHEET, 'idle', 'down');
    const def = spriteLibrary.sheet(K.SHEET, 'idle');
    const tex = spriteLibrary.textureKey(K.SHEET, 'idle');
    if (anim && def && tex && g.textures.exists(tex)) {
      const s = g.add
        .sprite(this.x, this.y, tex, 0)
        .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
        .setScale(artScale(def))
        .setDepth(entityDepth(this.y));
      s.play(anim);
      this.view = s;
    } else
      this.view = g.add
        .rectangle(this.x, this.y, K.PLACEHOLDER_W, K.PLACEHOLDER_H, K.PLACEHOLDER_COLOR)
        .setOrigin(0.5, 1)
        .setDepth(entityDepth(this.y));
    lightRegistryOf(g).add(K.LIGHT, { x: this.x, y: this.y, anchor: this.view, dy: K.LIGHT_LIFT_PX });
  }

  /** 상인 E 반경 안인가 */
  near(): boolean {
    const p = this.g.player;
    return Math.hypot(p.x - this.x, p.y - this.y) <= BUNDLE_FX.INTERACT_TILES * TILE;
  }

  /** 계약 §9.1 E 안내 (반경 밖이면 null) */
  interactable(roomId: string, usable: boolean): UiInteractable | null {
    if (!this.near()) return null;
    const s = worldToLogicalScreen(this.g.cameras.main, this.x, this.y - this.view.displayHeight);
    return {
      id: 'shopkeeper',
      kind: 'mapSeller',
      name: STORY.names.shop,
      roomId,
      key: 'E',
      actionKey: 'shop.open',
      action: SHOP_KEEPER.ACTION_TEXT,
      cost: null,
      hold: null,
      usable,
      reason: usable ? null : 'busy',
      reasonText: usable ? '' : BUNDLE_FX.NOT_READY_TEXT,
      screen: { x: Math.round(s.x), y: Math.round(s.y) },
    };
  }

  destroy(): void {
    this.view.destroy();
  }
}
