/**
 * 손에 든 무기 오버레이 (계약 art-assets.md §3.1).
 * 주인공 시트는 맨손이고, 공격 애니(`player_attack_<방향>`)가 재생되는 동안만 `weapons/<무기id>_attack` 시트의
 * **같은 프레임 번호**를 플레이어 피벗에 겹쳐 보인다. 깊이는 JSON `depth`(up 은 플레이어 아래, 나머지는 위).
 * 팔레트 스왑 변형(`@f<n>`)은 spriteLibrary 의 현재 텍스처 키를 그대로 쓴다. 시트가 없으면 아무것도 하지 않는다.
 */
import Phaser from 'phaser';
import { DEPTH } from '../core/Constants';
import { gameState } from '../core/GameState';
import { spriteLibrary } from '../systems/sprites';
import { FACINGS, WEAPON_ACTIONS, frameAt, type Facing } from '../systems/spriteDefs';

const ACTION = WEAPON_ACTIONS[0];

export class WeaponOverlay {
  private readonly sprite: Phaser.GameObjects.Sprite;
  private texture: string | null = null;
  /** 디버그: 현재 보이는 시트·프레임 */
  frame = -1;

  constructor(private readonly host: Phaser.GameObjects.Sprite) {
    this.sprite = host.scene.add.sprite(host.x, host.y, '__DEFAULT').setVisible(false);
    host.once(Phaser.GameObjects.Events.DESTROY, () => this.sprite.destroy());
  }

  get visible(): boolean {
    return this.sprite.visible;
  }

  /** 매 프레임: 호스트가 attack 애니 중이면 같은 열의 무기 프레임을 보인다 */
  update(): void {
    const anim = this.host.anims.currentAnim;
    const cur = this.host.anims.currentFrame;
    const dir = this.attackDirOf(anim?.key);
    if (!dir || !cur || !this.host.anims.isPlaying) return this.hide();
    const id = gameState.weapon.id;
    const def = spriteLibrary.sheet(id, ACTION);
    const texture = spriteLibrary.textureKey(id, ACTION);
    if (!def || !texture || !this.host.scene.textures.exists(texture)) return this.hide();
    if (this.texture !== texture) {
      this.sprite.setTexture(texture, 0);
      this.sprite.setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight);
      this.texture = texture;
    }
    // Phaser 의 currentFrame.index 는 1부터 → 열 = index - 1
    this.frame = frameAt(def, dir, cur.index - 1);
    this.sprite.setFrame(this.frame);
    const below = def.depth?.[dir] === 'below';
    this.sprite
      .setPosition(this.host.x, this.host.y)
      .setDepth(this.host.depth + (below ? -DEPTH.OVERLAY_STEP : DEPTH.OVERLAY_STEP))
      .setVisible(true);
  }

  hide(): void {
    if (this.sprite.visible) this.sprite.setVisible(false);
    this.frame = -1;
  }

  /** `<이름>_attack_<방향>[@f<n>]` 에서 방향을 꺼낸다. attack 이 아니면 null */
  private attackDirOf(key: string | undefined): Facing | null {
    if (!key) return null;
    const marker = `_${ACTION}_`;
    const i = key.indexOf(marker);
    if (i < 0) return null;
    const dir = key.slice(i + marker.length).split('@')[0] as Facing;
    return FACINGS.includes(dir) ? dir : null;
  }
}
