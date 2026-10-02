/**
 * 손에 든 무기 오버레이 (계약 art-assets.md §3.1, 48라운드 §6.1·6.2).
 * 주인공 시트는 맨손이고, 무기를 드는 동작(attack · <무기>_combo<n> · <무기>_special · <무기>_aim)이 보이는 동안만
 * `weapons/<무기id>_<동작>` 시트의 **같은 프레임 번호**를 플레이어 피벗에 겹쳐 보인다(무기 연격 시트가 없으면 attack 시트).
 * 깊이는 JSON `depth`(up 은 플레이어 아래, 나머지는 위). 프레임 유지(`#hold<c>`, 활 조준 진행도)도 같은 열을 보인다.
 * 팔레트 스왑 변형(`@f<n>`)은 spriteLibrary 의 현재 텍스처 키를 그대로 쓴다. 시트가 없으면 아무것도 하지 않는다.
 */
import Phaser from 'phaser';
import { DEPTH } from '../core/Constants';
import { gameState } from '../core/GameState';
import { spriteLibrary } from '../systems/sprites';
import { frameAt, overlayActionsFor, parseAnimKey, type Facing } from '../systems/spriteDefs';

export class WeaponOverlay {
  private readonly sprite: Phaser.GameObjects.Sprite;
  private texture: string | null = null;
  /** 디버그: 현재 보이는 시트·프레임 */
  frame = -1;
  /** 디버그: 현재 겹친 무기 시트 동작 */
  action: string | null = null;

  constructor(
    private readonly host: Phaser.GameObjects.Sprite,
    /** 현재 애니 키 (EntityVisual.current — 프레임 유지 `#hold<c>` 포함) */
    private readonly currentKey: () => string | null = () => null,
  ) {
    this.sprite = host.scene.add.sprite(host.x, host.y, '__DEFAULT').setVisible(false);
    host.once(Phaser.GameObjects.Events.DESTROY, () => this.sprite.destroy());
  }

  get visible(): boolean {
    return this.sprite.visible;
  }

  /** 매 프레임: 호스트가 무기를 드는 동작이면 같은 열의 무기 프레임을 보인다 */
  update(): void {
    const playing = this.host.anims.isPlaying ? this.host.anims.currentAnim?.key : undefined;
    const held = this.currentKey();
    const key = playing ?? (held && held.includes('#hold') ? held : undefined);
    const parsed = key ? parseAnimKey(key, 'player') : null;
    if (!parsed) return this.hide();
    let column: number;
    if (playing) {
      const cur = this.host.anims.currentFrame;
      if (!cur) return this.hide();
      // 파생 애니(구간 재생·반복)도 맞도록 텍스처 프레임 번호(row × frames + col)에서 열을 꺼낸다
      const body = spriteLibrary.sheet('player', parsed.action);
      const fi = Number(cur.frame.name);
      column = body && Number.isFinite(fi) ? fi % body.frames : cur.index - 1;
    } else {
      const m = /#hold(\d+)/.exec(key!);
      column = m ? Number(m[1]) : 0;
    }
    const id = gameState.weapon.id;
    let def = undefined;
    let texture: string | null = null;
    let action: string | null = null;
    for (const a of overlayActionsFor(parsed.action, id)) {
      def = spriteLibrary.sheet(id, a);
      texture = spriteLibrary.textureKey(id, a);
      if (def && texture && this.host.scene.textures.exists(texture)) {
        action = a;
        break;
      }
      def = undefined;
    }
    if (!def || !texture || !action) return this.hide();
    if (this.texture !== texture) {
      this.sprite.setTexture(texture, 0);
      this.sprite.setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight);
      this.texture = texture;
    }
    const dir: Facing = parsed.dir;
    this.frame = frameAt(def, dir, column);
    this.action = action;
    this.sprite.setFrame(this.frame);
    const below = typeof def.depth === 'object' && def.depth?.[dir] === 'below';
    this.sprite
      .setPosition(this.host.x, this.host.y)
      .setAlpha(this.host.alpha)
      .setDepth(this.host.depth + (below ? -DEPTH.OVERLAY_STEP : DEPTH.OVERLAY_STEP))
      .setVisible(this.host.visible);
  }

  hide(): void {
    if (this.sprite.visible) this.sprite.setVisible(false);
    this.frame = -1;
    this.action = null;
  }
}
