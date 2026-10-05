/**
 * 61라운드 E 보스 림라이트 (아트 2 `bosses/v3/<보스>_<동작>_rim` — drawRule: 보스와 같은 프레임 번호·피벗·flip, 조명 위).
 * 3국면 소등 동안만 켠다. 보스가 지금 그리는 시트에 림 시트가 올라와 있으면 그 같은 프레임을, 아니면(림 없는 동작·로드 전·
 * VRAM 예산 초과) 보스 그림 사본을 호박 채움색 ADD 로 조명 위에 겹친다 (아트 권장 대체).
 */
import Phaser from 'phaser';
import { BOSS_ART, DEPTH } from '../../core/Constants';
import { spriteLibrary } from '../sprites/sprites';
import { rimAction } from './bossSheets';

export class BossRim {
  private readonly rim: Phaser.GameObjects.Sprite;
  private readonly fill: Phaser.GameObjects.Sprite;
  on = false;
  /** 디버그: 마지막으로 그린 방식 */
  mode: 'off' | 'sheet' | 'tintFill' = 'off';

  constructor(
    private readonly scene: Phaser.Scene,
    private readonly bossId: string,
    private readonly rimReady: () => boolean,
  ) {
    this.rim = scene.add.sprite(0, 0, '__DEFAULT').setVisible(false);
    const F = BOSS_ART.RIM_FALLBACK;
    this.fill = scene.add
      .sprite(0, 0, '__DEFAULT')
      .setVisible(false)
      .setTintFill(F.COLOR)
      .setAlpha(F.ALPHA)
      .setBlendMode(Phaser.BlendModes.ADD);
  }

  /** 림을 그리는 스프라이트 (VRAM 해제 확인용) */
  get sprites(): Phaser.GameObjects.Sprite[] {
    return [this.rim, this.fill];
  }

  setOn(on: boolean): void {
    this.on = on;
    if (!on) this.hide();
  }

  private hide(): void {
    this.rim.setVisible(false).setTexture('__DEFAULT');
    this.fill.setVisible(false).setTexture('__DEFAULT');
    this.mode = 'off';
  }

  /** 보스 몸 동작 → 그 림 시트 텍스처 키 (림 시트가 올라와 있지 않으면 null) */
  private rimKeyFor(bodyKey: string): string | null {
    if (!this.rimReady()) return null;
    for (const a of BOSS_ART.RIM_ACTIONS) {
      if (spriteLibrary.textureKey(this.bossId, a) !== bodyKey) continue;
      const k = spriteLibrary.textureKey(this.bossId, rimAction(a));
      return k && this.scene.textures.exists(k) ? k : null;
    }
    return null;
  }

  update(boss: Phaser.GameObjects.Sprite | null): void {
    if (!this.on || !boss?.active || !boss.visible) {
      if (this.mode !== 'off') this.hide();
      return;
    }
    const key = this.rimKeyFor(boss.texture.key);
    const use = key ? this.rim : this.fill;
    const other = key ? this.fill : this.rim;
    other.setVisible(false);
    use
      .setTexture(key ?? boss.texture.key, boss.frame.name)
      .setOrigin(boss.originX, boss.originY)
      .setPosition(boss.x, boss.y)
      .setScale(boss.scaleX, boss.scaleY)
      .setFlip(boss.flipX, boss.flipY)
      .setRotation(boss.rotation)
      .setDepth(DEPTH.LIGHTMAP + DEPTH.LIGHT_LAYER_STEP * 1.5)
      .setVisible(true);
    this.mode = key ? 'sheet' : 'tintFill';
  }

  destroy(): void {
    this.rim.destroy();
    this.fill.destroy();
  }
}
