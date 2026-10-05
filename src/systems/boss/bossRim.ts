/**
 * 61라운드 E 보스 림라이트 (아트 2 `bosses/v3/<보스>_<동작>_rim` — drawRule: 보스와 같은 프레임 번호·피벗·flip, 조명 위).
 * 3국면 소등 동안만 켠다. 보스가 지금 그리는 시트에 림 시트가 올라와 있으면 그 같은 프레임을, 아니면(림 없는 동작·로드 전·
 * VRAM 예산 초과) 보스 그림 사본을 호박 채움색 ADD 로 조명 위에 겹친다 (아트 권장 대체).
 * 61 단계 4: 가벼운 림 `_rim_lite`(반 해상도·pixelScale 1.0) — 같은 프레임 번호·원점·flip, 표시 배율 = 보스 배율 × (림 도트 배율 / 보스 도트 배율 = 2).
 */
import Phaser from 'phaser';
import { BOSS_ART, DEPTH } from '../../core/Constants';
import { artScale } from '../sprites/spriteDefs';
import { spriteLibrary } from '../sprites/sprites';
import { rimAction, type RimKind } from './bossSheets';

export class BossRim {
  private readonly rim: Phaser.GameObjects.Sprite;
  private readonly fill: Phaser.GameObjects.Sprite;
  on = false;
  /** 디버그: 마지막으로 그린 방식 */
  mode: 'off' | 'sheet' | 'lite' | 'tintFill' = 'off';

  constructor(
    private readonly scene: Phaser.Scene,
    private readonly bossId: string,
    /** 올라와 있는 림 종류 (로드 전·대체만이면 null) */
    private readonly rimKind: () => RimKind | null,
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

  /** 보스 몸 동작 → 그 림 시트 텍스처 키 · 보스 배율에 곱할 배율 (림 시트가 올라와 있지 않으면 null) */
  private rimKeyFor(bodyKey: string): { key: string; scale: number } | null {
    const kind = this.rimKind();
    if (!kind) return null;
    for (const a of BOSS_ART.RIM_ACTIONS) {
      if (spriteLibrary.textureKey(this.bossId, a) !== bodyKey) continue;
      const action = rimAction(a, kind);
      const k = spriteLibrary.textureKey(this.bossId, action);
      if (!k || !this.scene.textures.exists(k)) return null;
      const body = spriteLibrary.sheet(this.bossId, a);
      const rim = spriteLibrary.sheet(this.bossId, action);
      return { key: k, scale: body && rim ? artScale(rim) / artScale(body) : 1 };
    }
    return null;
  }

  update(boss: Phaser.GameObjects.Sprite | null): void {
    if (!this.on || !boss?.active || !boss.visible) {
      if (this.mode !== 'off') this.hide();
      return;
    }
    const hit = this.rimKeyFor(boss.texture.key);
    const use = hit ? this.rim : this.fill;
    const other = hit ? this.fill : this.rim;
    other.setVisible(false);
    const k = hit?.scale ?? 1;
    use
      .setTexture(hit?.key ?? boss.texture.key, boss.frame.name)
      .setOrigin(boss.originX, boss.originY)
      .setPosition(boss.x, boss.y)
      .setScale(boss.scaleX * k, boss.scaleY * k)
      .setFlip(boss.flipX, boss.flipY)
      .setRotation(boss.rotation)
      .setDepth(DEPTH.LIGHTMAP + DEPTH.LIGHT_LAYER_STEP * 1.5)
      .setVisible(true);
    this.mode = hit ? (this.rimKind() === 'lite' ? 'lite' : 'sheet') : 'tintFill';
  }

  /** 디버그: 지금 겹친 림 (텍스처·프레임·배율·원점) */
  summary(): Record<string, unknown> {
    const r = this.mode === 'tintFill' ? this.fill : this.rim;
    return {
      on: this.on,
      mode: this.mode,
      key: r.texture.key,
      frame: r.frame.name,
      scale: Math.round(r.scaleX * 1000) / 1000,
      origin: [Math.round(r.originX * 1000) / 1000, Math.round(r.originY * 1000) / 1000],
      size: [r.frame.realWidth, r.frame.realHeight],
      flip: r.flipX,
    };
  }

  destroy(): void {
    this.rim.destroy();
    this.fill.destroy();
  }
}
