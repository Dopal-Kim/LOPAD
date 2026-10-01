import Phaser from 'phaser';
import { UI_EVENTS, uiBus, uiCommands, type UiSnapshot, type UiStoryLine } from '../contract/ui';
import { UI_SCENE_KEYS } from './keys';
import { THEME } from './theme';
import { fill, uiText } from './text';
import { Bar, drawPanel, label, panel } from './widgets';
import { Minimap } from './Minimap';

/**
 * 무기 이름 → 아이콘 id. 스냅샷에 `weapon.id` 가 없어 이름으로 매핑한다 (29라운드 자율 결정, 계약에 id 추가 요청).
 * 아이콘 파일은 `assets/ui/weapons/<id>_icon.png` (아트 산출물 사본, README 참조).
 */
const WEAPON_ICON_IDS: Record<string, string> = {
  '사무라이 칼': 'katana',
  대검: 'greatsword',
  단검: 'dagger',
  활: 'bow',
};
const WEAPON_ICON_KEY = (id: string): string => `ui-weapon-${id}`;
const WEAPON_PANEL_H = 34;
/** 무기 패널 최소 폭. 텍스트가 더 길면 패널을 텍스트에 맞춰 넓힌다 */
const WEAPON_PANEL_MIN_W = 190;

/** 게임 위에 병렬로 떠 있는 HUD. 매 프레임 STATE 스냅샷으로 갱신. */
export class HudScene extends Phaser.Scene {
  private hpBar: Bar;
  private hpText: Phaser.GameObjects.Text;
  private goldText: Phaser.GameObjects.Text;
  private potionText: Phaser.GameObjects.Text;
  private stageText: Phaser.GameObjects.Text;
  private weaponText: Phaser.GameObjects.Text;
  private weaponIcon: Phaser.GameObjects.Image;
  private weaponTextX = 0;
  private weaponPanel: Phaser.GameObjects.Graphics;
  private weaponPanelTop = 0;
  private weaponPanelW = 0;
  private personalityBar: Bar;
  private bossPanel: Phaser.GameObjects.Graphics;
  private bossBar: Bar;
  private bossText: Phaser.GameObjects.Text;
  private minimap: Minimap;
  private banner?: Phaser.GameObjects.Text;
  private caption?: Phaser.GameObjects.Text;
  private captionTimer?: Phaser.Time.TimerEvent;
  private handlers: [string, (p: never) => void][] = [];
  private escKey?: Phaser.Input.Keyboard.Key;

  constructor() {
    super(UI_SCENE_KEYS.HUD);
  }

  /** 무기 아이콘. 파일이 없으면 로드 실패만 나고 (아이콘 없이 이름만 표시) 게임에는 영향 없다 */
  preload(): void {
    for (const id of Object.values(WEAPON_ICON_IDS)) {
      const key = WEAPON_ICON_KEY(id);
      if (!this.textures.exists(key)) this.load.image(key, `assets-game/ui/weapons/${id}_icon.png`);
    }
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

    // 좌하단: 무기 아이콘(16×16)·무기·개성 게이지
    const H = this.scale.height;
    const wpTop = H - P - WEAPON_PANEL_H;
    this.weaponPanelTop = wpTop;
    this.weaponPanelW = WEAPON_PANEL_MIN_W;
    this.weaponPanel = panel(this, P, wpTop, WEAPON_PANEL_MIN_W, WEAPON_PANEL_H);
    this.weaponIcon = this.add
      .image(P + 6, wpTop + 3, '__DEFAULT')
      .setOrigin(0, 0)
      .setVisible(false);
    this.weaponTextX = P + 8;
    this.weaponText = label(this, this.weaponTextX, wpTop + 6, '');
    this.personalityBar = new Bar(this, P + 8, H - P - 12, 174, 6, THEME.personality, THEME.hpBack);

    // 보스 바 (중앙 하단, 보스전만)
    const bossY = wpTop - 32; // 무기 패널 위
    this.bossPanel = panel(this, W / 2 - 150, bossY, 300, 26).setVisible(false);
    this.bossBar = new Bar(this, W / 2 - 144, bossY + 18, 288, 6, THEME.boss, THEME.bossBack);
    this.bossText = label(this, W / 2, bossY + 3, '', THEME.font, '#ffb0c8')
      .setOrigin(0.5, 0)
      .setVisible(false);
    this.bossBar.set(0).setVisible(false);

    // 우상단: 미니맵, 그 아래 음소거 힌트 (토글은 시스템이 M 키로 처리, UI 는 힌트만)
    this.minimap = new Minimap(this, W - P - 110, P, 110, 90);
    label(this, W - P, P + 94, 'M 음소거', THEME.fontSmall, THEME.textDim).setOrigin(1, 0);

    this.on(UI_EVENTS.STATE, (s: UiSnapshot) => this.render(s));
    this.on(UI_EVENTS.WEAPON_EVOLVED, (p: { name: string }) =>
      this.showBanner(fill(uiText('hud', 'evolvedBanner', '개성 변화: {name}'), { name: p.name })),
    );
    this.on(UI_EVENTS.STAGE_STARTED, (p: { stageName: string }) => this.showBanner(p.stageName));
    this.on(UI_EVENTS.STORY, (l: UiStoryLine) => this.showCaption(l));
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
    this.goldText.setText(`◆ ${s.gold} ${s.names.gold}`);
    this.potionText.setText(`${s.names.potion} ${s.potions}/${s.potionMax} [Q]`);
    const boss = s.bossUnlocked ? `  ${uiText('hud', 'bossUnlocked', '보스 문 열림')}` : '';
    const exit = s.exitOpen ? `  ${uiText('hud', 'exitOpen', '출구 열림')}` : '';
    this.stageText.setText(`${s.floorTitle || s.stageName}   시련 ${s.trialsCleared}/${s.trialsTotal}${boss}${exit}`);
    const evo = s.weapon.evolutionName ? ` · ${s.weapon.evolutionName}` : '';
    this.renderWeaponIcon(s.weapon.name);
    this.weaponText.setText(
      `${s.weapon.name}${evo}   개성 ${s.weapon.personality}/${s.weapon.threshold}   우클릭: ${s.weapon.secondaryName}`,
    );
    this.fitWeaponPanel();
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

  /** 무기 아이콘: 이름 매핑 + 텍스처가 있을 때만 보이고, 이름은 아이콘 오른쪽으로 비킨다 */
  private renderWeaponIcon(weaponName: string): void {
    const id = WEAPON_ICON_IDS[weaponName];
    const key = id ? WEAPON_ICON_KEY(id) : '';
    const has = Boolean(key) && this.textures.exists(key);
    if (has && this.weaponIcon.texture.key !== key) this.weaponIcon.setTexture(key);
    this.weaponIcon.setVisible(has);
    const x = this.weaponTextX + (has ? 20 : 0);
    if (this.weaponText.x !== x) this.weaponText.setX(x);
  }

  /** 무기 패널 폭을 이름·개성·보조 동작 텍스트에 맞춘다 (최소 190, 텍스트가 길면 넓힘) */
  private fitWeaponPanel(): void {
    const P = THEME.pad;
    const w = Math.max(WEAPON_PANEL_MIN_W, Math.ceil(this.weaponText.x + this.weaponText.width + 8 - P));
    if (w === this.weaponPanelW) return;
    this.weaponPanelW = w;
    drawPanel(this.weaponPanel, P, this.weaponPanelTop, w, WEAPON_PANEL_H);
  }

  /** 스토리 자막: 화면 하단 중앙(보스 체력바 위), 종류별로 유지 시간이 다르다 */
  private showCaption(l: UiStoryLine): void {
    this.caption?.destroy();
    this.captionTimer?.remove();
    const hold = l.kind === 'notice' ? 1800 : 3600;
    this.caption = this.add
      .text(this.scale.width / 2, this.scale.height - 88, l.text, {
        font: THEME.font,
        color: l.kind === 'boss' ? '#ffb0c8' : l.kind === 'notice' ? THEME.textDim : THEME.text,
        backgroundColor: '#000000a0',
        padding: { x: 8, y: 4 },
        align: 'center',
        wordWrap: { width: this.scale.width - 240 },
      })
      .setOrigin(0.5, 1)
      .setDepth(50);
    this.captionTimer = this.time.delayedCall(hold, () => {
      this.tweens.add({ targets: this.caption, alpha: 0, duration: 300, onComplete: () => this.caption?.destroy() });
    });
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
