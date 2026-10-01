import Phaser from 'phaser';
import { UI_EVENTS, uiBus, uiCommands, type UiSnapshot } from '../contract/ui';
import { UI_SCENE_KEYS } from './keys';
import { THEME } from './theme';
import { Bar, label, panel } from './widgets';
import { Minimap } from './Minimap';

/** 게임 위에 병렬로 떠 있는 HUD. 매 프레임 STATE 스냅샷으로 갱신. */
export class HudScene extends Phaser.Scene {
  private hpBar: Bar;
  private hpText: Phaser.GameObjects.Text;
  private goldText: Phaser.GameObjects.Text;
  private potionText: Phaser.GameObjects.Text;
  private stageText: Phaser.GameObjects.Text;
  private weaponText: Phaser.GameObjects.Text;
  private personalityBar: Bar;
  private bossPanel: Phaser.GameObjects.Graphics;
  private bossBar: Bar;
  private bossText: Phaser.GameObjects.Text;
  private minimap: Minimap;
  private banner?: Phaser.GameObjects.Text;
  private handlers: [string, (p: never) => void][] = [];
  private escKey?: Phaser.Input.Keyboard.Key;

  constructor() {
    super(UI_SCENE_KEYS.HUD);
  }

  create(): void {
    uiCommands.registerRenderer();
    const W = this.scale.width;
    const P = THEME.pad;

    // 좌상단: 체력·골드·물약
    panel(this, P, P, 170, 46);
    this.hpBar = new Bar(this, P + 6, P + 6, 158, 10, THEME.hp, THEME.hpBack);
    this.hpText = label(this, P + 8, P + 17, '');
    this.goldText = label(this, P + 8, P + 30, '', THEME.font, '#f0c830');
    this.potionText = label(this, P + 90, P + 30, '', THEME.font, '#60e080');

    // 중앙 상단: 층·시련
    this.stageText = label(this, W / 2, P + 4, '', THEME.font, THEME.textDim).setOrigin(0.5, 0);

    // 좌하단: 무기·개성 게이지
    const H = this.scale.height;
    panel(this, P, H - P - 30, 190, 30);
    this.weaponText = label(this, P + 8, H - P - 26, '');
    this.personalityBar = new Bar(this, P + 8, H - P - 12, 174, 6, THEME.personality, THEME.hpBack);

    // 보스 바 (중앙 하단, 보스전만)
    const bossY = H - P - 30 - 32; // 무기 패널 위
    this.bossPanel = panel(this, W / 2 - 150, bossY, 300, 26).setVisible(false);
    this.bossBar = new Bar(this, W / 2 - 144, bossY + 18, 288, 6, THEME.boss, THEME.bossBack);
    this.bossText = label(this, W / 2, bossY + 3, '', THEME.font, '#ffb0c8')
      .setOrigin(0.5, 0)
      .setVisible(false);
    this.bossBar.set(0).setVisible(false);

    // 우상단: 미니맵
    this.minimap = new Minimap(this, W - P - 110, P, 110, 90);

    this.on(UI_EVENTS.STATE, (s: UiSnapshot) => this.render(s));
    this.on(UI_EVENTS.WEAPON_EVOLVED, (p: { name: string }) => this.showBanner(`개성 변화: ${p.name}`));
    this.on(UI_EVENTS.STAGE_STARTED, (p: { stageName: string }) => this.showBanner(p.stageName));
    this.on(UI_EVENTS.PAUSED, () => {
      if (!this.scene.isActive(UI_SCENE_KEYS.PAUSE)) this.scene.launch(UI_SCENE_KEYS.PAUSE);
    });

    this.escKey = this.input.keyboard?.addKey('ESC');
    this.render(uiCommands.getUiSnapshot());
    this.events.once('shutdown', () => {
      for (const [e, h] of this.handlers) uiBus.off(e, h);
      this.handlers = [];
    });
  }

  update(): void {
    if (this.escKey && Phaser.Input.Keyboard.JustDown(this.escKey)) {
      if (!this.scene.isActive(UI_SCENE_KEYS.MENU) && !this.scene.isActive(UI_SCENE_KEYS.PAUSE)) uiCommands.pause();
    }
  }

  private on<T>(event: string, handler: (p: T) => void): void {
    uiBus.on(event, handler);
    this.handlers.push([event, handler as (p: never) => void]);
  }

  private render(s: UiSnapshot): void {
    const ratio = s.maxHp > 0 ? s.hp / s.maxHp : 0;
    this.hpBar.set(ratio, ratio <= 0.3 ? THEME.hpLow : THEME.hp);
    this.hpText.setText(`HP ${s.hp} / ${s.maxHp}`);
    this.goldText.setText(`◆ ${s.gold} G`);
    this.potionText.setText(`물약 ${s.potions}/${s.potionMax}  [Q]`);
    const boss = s.bossUnlocked ? '  보스 문 열림' : '';
    const exit = s.exitOpen ? '  출구 열림' : '';
    this.stageText.setText(`${s.stageName}   시련 ${s.trialsCleared}/${s.trialsTotal}${boss}${exit}`);
    const evo = s.weapon.evolutionName ? ` · ${s.weapon.evolutionName}` : '';
    this.weaponText.setText(
      `${s.weapon.name}${evo}   개성 ${s.weapon.personality}/${s.weapon.threshold}   우클릭: ${s.weapon.secondaryName}`,
    );
    this.personalityBar.set(s.weapon.threshold > 0 ? s.weapon.personality / s.weapon.threshold : 0);
    if (s.boss) {
      this.bossPanel.setVisible(true);
      this.bossText.setVisible(true).setText(`${s.boss.name}  ${s.boss.hp}/${s.boss.maxHp}  페이즈 ${s.boss.phase}`);
      this.bossBar.setVisible(true).set(s.boss.maxHp > 0 ? s.boss.hp / s.boss.maxHp : 0);
    } else {
      this.bossPanel.setVisible(false);
      this.bossText.setVisible(false);
      this.bossBar.setVisible(false);
    }
    this.minimap.render(s.map);
  }

  private showBanner(text: string): void {
    this.banner?.destroy();
    this.banner = label(this, this.scale.width / 2, this.scale.height / 2 - 50, text, THEME.fontHeading)
      .setOrigin(0.5)
      .setAlpha(0);
    this.tweens.add({
      targets: this.banner,
      alpha: 1,
      duration: 200,
      yoyo: true,
      hold: 1200,
      onComplete: () => this.banner?.destroy(),
    });
  }
}
