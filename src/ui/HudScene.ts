import Phaser from 'phaser';
import { UI_EVENTS, uiBus, uiCommands, type UiSnapshot, type UiStoryLine } from '../contract/ui';
import { GlowText } from './glow';
import {
  Gauge,
  ICON,
  NinePanel,
  WEAPON_ICON_IDS,
  fontsReady,
  icon,
  inkPanel,
  preloadKit,
  setupKit,
  weaponIconKey,
} from './kit';
import { UI_SCENE_KEYS } from './keys';
import { Minimap } from './Minimap';
import { fill, uiText } from './text';
import { LAYOUT } from './theme';

/** 하단 중앙 묶음 (33라운드 Q3) */
const HUD_W = 480;
const HUD_H = 64;
const BOSS_W = 360;
const HP_GAUGE_W = 170;
const PERSONALITY_W = 100;
const CAPTION_DEPTH = 50;

/**
 * 게임 위에 병렬로 떠 있는 HUD (41라운드 키트 적용). 매 프레임 STATE 스냅샷으로 갱신.
 * 하단 중앙 panel_ink 480×64: 1행 체력 게이지·수치·전표·독주, 2행 무기·개성 게이지·우클릭.
 * 보스 게이지는 묶음 위 8px, 자막은 그 위. 상단 좌 층 제목·시련, 상단 우 미니맵 + M 음소거. 우하단 공지.
 */
export class HudScene extends Phaser.Scene {
  private built = false;
  private alive = false;
  private stageIndex = -1;
  private glows: GlowText[] = [];
  private handlers: [string, (p: never) => void][] = [];
  private pending?: UiSnapshot;

  // 하단 묶음
  private panelX = 0;
  private panelY = 0;
  private hpGauge!: Gauge;
  private hpText!: GlowText;
  private goldIcon!: Phaser.GameObjects.Image;
  private goldText!: GlowText;
  private potionIcon!: Phaser.GameObjects.Image;
  private potionText!: GlowText;
  private potionKey!: GlowText;
  private weaponIcon!: Phaser.GameObjects.Image;
  private weaponText!: GlowText;
  private senseIcon!: Phaser.GameObjects.Image;
  private personalityGauge!: Gauge;
  private personalityText!: GlowText;
  private secondaryText!: GlowText;
  // 보스
  private bossGauge!: Gauge;
  private bossIcon!: Phaser.GameObjects.Image;
  private bossName!: GlowText;
  // 상단
  private floorText!: GlowText;
  private minimap!: Minimap;
  // 공지
  private noticePanel!: NinePanel;
  private noticeIcon!: Phaser.GameObjects.Image;
  private noticeText!: GlowText;
  private noticeKind = '';
  // 자막·배너
  private banner?: GlowText;
  private caption?: GlowText;
  private captionTimer?: Phaser.Time.TimerEvent;

  constructor() {
    super(UI_SCENE_KEYS.HUD);
  }

  preload(): void {
    preloadKit(this);
  }

  create(): void {
    uiCommands.registerRenderer();
    setupKit(this);
    this.alive = true;
    this.built = false;
    this.glows = [];
    this.on(UI_EVENTS.STATE, (s: UiSnapshot) => this.render(s));
    this.on(UI_EVENTS.WEAPON_EVOLVED, (p: { name: string }) =>
      this.showBanner(fill(uiText('hud', 'evolvedBanner', '{name}'), { name: p.name })),
    );
    this.on(UI_EVENTS.STAGE_STARTED, (p: { stageName: string }) => this.showBanner(p.stageName));
    this.on(UI_EVENTS.STORY, (l: UiStoryLine) => this.showCaption(l));
    this.on(UI_EVENTS.PAUSED, () => {
      if (!this.scene.isActive(UI_SCENE_KEYS.PAUSE)) this.scene.launch(UI_SCENE_KEYS.PAUSE);
    });
    // Esc 는 Key 폴링(JustDown) 대신 keydown 이벤트로 받는다 — 씬이 바뀌는 프레임에 Key 상태가 눌린 채 남아
    // 다음 Esc 가 '반복 입력' 으로 취급돼 무시되는 문제가 있었다 (41라운드 헤드리스 검증)
    this.input.keyboard?.on('keydown-ESC', this.onEsc);
    this.events.once('shutdown', () => {
      this.input.keyboard?.off('keydown-ESC', this.onEsc);
      this.alive = false;
      this.built = false;
      for (const [e, h] of this.handlers) uiBus.off(e, h);
      this.handlers = [];
      this.captionTimer?.remove();
    });
    fontsReady().then(() => {
      if (!this.alive) return;
      this.build();
      this.render(this.pending ?? uiCommands.getUiSnapshot());
    });
  }

  private onEsc = (): void => {
    if (!this.scene.isActive(UI_SCENE_KEYS.MENU) && !this.scene.isActive(UI_SCENE_KEYS.PAUSE)) uiCommands.pause();
  };

  private on<T>(event: string, handler: (p: T) => void): void {
    uiBus.on(event, handler);
    this.handlers.push([event, handler as (p: never) => void]);
  }

  private glow(
    x: number,
    y: number,
    text: string,
    style: Parameters<GlowText['setGlowStyle']>[0],
    scale: 1 | 2 = 1,
  ): GlowText {
    const t = new GlowText(this, x, y, text, style, { scale, stageIndex: Math.max(0, this.stageIndex) });
    this.glows.push(t);
    return t;
  }

  private build(): void {
    const W = this.scale.width;
    const H = this.scale.height;
    const E = LAYOUT.edge;
    const s0 = uiCommands.getUiSnapshot();
    this.stageIndex = Math.max(0, s0.stageIndex);

    // ---- 하단 중앙 묶음
    const px = Math.round(W / 2 - HUD_W / 2);
    const py = H - HUD_H - 12;
    this.panelX = px;
    this.panelY = py;
    inkPanel(this, px, py, HUD_W, HUD_H);
    // 1행: 체력
    icon(this, px + 8, py + 8, ICON.hp);
    this.hpGauge = new Gauge(this, px + 28, py + 11, HP_GAUGE_W, 'frame', this.stageIndex);
    this.hpText = this.glow(px + 28 + HP_GAUGE_W + 8, py + 9, '', 'ink_body');
    this.goldIcon = icon(this, 0, py + 8, ICON.gold);
    this.goldText = this.glow(0, py + 9, '', 'ink_body');
    this.potionIcon = icon(this, 0, py + 8, ICON.potion);
    this.potionText = this.glow(0, py + 9, '', 'ink_body');
    this.potionKey = this.glow(0, py + 9, 'Q', 'ink_faint');
    // 2행: 무기 · 개성
    this.weaponIcon = this.add
      .image(px + 8, py + 36, '__DEFAULT')
      .setOrigin(0, 0)
      .setVisible(false);
    this.weaponText = this.glow(px + 28, py + 37, '', 'ink_body');
    this.senseIcon = icon(this, 0, py + 36, ICON.sense);
    this.personalityGauge = new Gauge(this, 0, py + 39, PERSONALITY_W, 'gray');
    this.personalityText = this.glow(0, py + 37, '', 'ink_faint');
    this.secondaryText = this.glow(0, py + 37, '', 'ink_faint');

    // ---- 보스 게이지 (묶음 위 8px) + 이름
    const by = py - 8 - 14;
    this.bossGauge = new Gauge(this, Math.round(W / 2 - BOSS_W / 2), by, BOSS_W, 'boss', this.stageIndex).setVisible(
      false,
    );
    this.bossIcon = icon(this, Math.round(W / 2 - BOSS_W / 2) - 22, by - 1, ICON.boss).setVisible(false);
    this.bossName = this.glow(0, by - 18, '', 'ink_accent').setVisible(false);

    // ---- 상단 좌: 층 제목·시련
    this.floorText = this.glow(E, 12, '', 'ink_body');

    // ---- 상단 우: 미니맵 + M 음소거 (토글은 시스템 M 키, UI 는 힌트만)
    this.buildMinimap(s0.map.gridW, s0.map.gridH);

    // ---- 우하단 공지
    this.noticePanel = inkPanel(this, 0, H - 12 - 28, 120, 28).setVisible(false);
    this.noticeIcon = icon(this, 0, H - 12 - 28 + 6, ICON.exit).setVisible(false);
    this.noticeText = this.glow(0, H - 12 - 28 + 7, '', 'ink_accent').setVisible(false);

    this.built = true;
  }

  private buildMinimap(gridW: number, gridH: number): void {
    const W = this.scale.width;
    const E = LAYOUT.edge;
    const size = Minimap.size(gridW, gridH);
    this.minimap = new Minimap(this, W - E - size.w, 12, gridW, gridH);
    const hintY = 12 + this.minimap.h + 6;
    icon(this, W - E - 16, hintY - 2, ICON.sound);
    this.glow(0, hintY, 'M 음소거', 'ink_faint').placeRight(W - E - 20, hintY);
  }

  private render(s: UiSnapshot): void {
    if (!this.built) {
      this.pending = s;
      return;
    }
    const si = Math.max(0, s.stageIndex);
    if (si !== this.stageIndex) {
      this.stageIndex = si;
      for (const t of this.glows) t.setStageIndex(si);
      this.hpGauge.setStage(this, si);
      this.bossGauge.setStage(this, si);
    }
    const px = this.panelX;
    // 1행
    this.hpGauge.set(s.maxHp > 0 ? s.hp / s.maxHp : 0);
    this.hpText.setText(`${s.hp} / ${s.maxHp}`);
    let x = Math.max(px + 28 + HP_GAUGE_W + 8 + this.hpText.textW + 16, px + 282);
    this.goldIcon.setX(x);
    this.goldText.setText(String(s.gold)).setX(x + 20);
    x = Math.max(x + 20 + this.goldText.textW + 16, px + 352);
    this.potionIcon.setX(x);
    this.potionText.setText(`${s.potions}/${s.potionMax}`).setX(x + 20);
    this.potionKey.setX(x + 20 + this.potionText.textW + 8);
    // 2행
    this.renderWeaponIcon(s.weapon.name);
    const evo = s.weapon.evolutionName ? ` · ${s.weapon.evolutionName}` : '';
    this.weaponText.setText(`${s.weapon.name}${evo}`);
    x = Math.max(this.weaponText.x + this.weaponText.textW + 14, px + 200);
    this.senseIcon.setX(x);
    const gx = x + 22;
    this.personalityGauge.set(s.weapon.threshold > 0 ? s.weapon.personality / s.weapon.threshold : 0);
    this.personalityGauge.setPositionX(gx);
    this.personalityText.setText(`${s.weapon.personality}/${s.weapon.threshold}`).setX(gx + PERSONALITY_W + 6);
    this.secondaryText.setText(s.weapon.secondaryName ? `우클릭 ${s.weapon.secondaryName}` : '');
    this.secondaryText.placeRight(px + HUD_W - 10, this.secondaryText.y);
    // 보스 (처치 뒤 스냅샷에 hp 0 으로 남는 동안은 숨긴다)
    if (s.boss && s.boss.hp > 0) {
      this.bossGauge.setVisible(true).set(s.boss.maxHp > 0 ? s.boss.hp / s.boss.maxHp : 0);
      this.bossIcon.setVisible(true);
      this.bossName
        .setVisible(true)
        .setText(`${s.boss.name}  ${s.boss.hp}/${s.boss.maxHp}  페이즈 ${s.boss.phase}`)
        .placeCenter(this.scale.width / 2, this.bossName.y);
    } else {
      this.bossGauge.setVisible(false);
      this.bossIcon.setVisible(false);
      this.bossName.setVisible(false);
    }
    // 상단
    this.floorText.setText(`${s.floorTitle || s.stageName}   시련 ${s.trialsCleared}/${s.trialsTotal}`);
    this.minimap.render(s.map, si);
    // 공지: 출구가 열렸으면 출구, 아니면 본영 문
    const kind = s.exitOpen ? 'exit' : s.bossUnlocked ? 'boss' : '';
    if (kind !== this.noticeKind) {
      this.noticeKind = kind;
      const show = kind !== '';
      this.noticePanel.setVisible(show);
      this.noticeIcon.setVisible(show);
      this.noticeText.setVisible(show);
      if (show) {
        const text =
          kind === 'exit' ? uiText('hud', 'exitOpen', '오르는 길 열림') : uiText('hud', 'bossUnlocked', '본영 문 열림');
        this.noticeText.setText(text);
        this.noticeIcon.setFrame(kind === 'exit' ? ICON.exit : ICON.boss);
        const w = 8 + 16 + 6 + this.noticeText.textW + 4 + 10;
        const nx = this.scale.width - LAYOUT.edge - w;
        this.noticePanel.resize(w, 28).setX(nx);
        this.noticeIcon.setX(nx + 8);
        this.noticeText.setX(nx + 8 + 16 + 6);
      }
    }
  }

  /** 무기 아이콘: 이름 매핑 + 텍스처가 있을 때만 보이고, 이름은 아이콘 오른쪽으로 비킨다 */
  private renderWeaponIcon(weaponName: string): void {
    const id = WEAPON_ICON_IDS[weaponName];
    const key = id ? weaponIconKey(id) : '';
    const has = Boolean(key) && this.textures.exists(key);
    if (has && this.weaponIcon.texture.key !== key) this.weaponIcon.setTexture(key);
    this.weaponIcon.setVisible(has);
    const x = this.panelX + (has ? 28 : 8);
    if (this.weaponText.x !== x) this.weaponText.setX(x);
  }

  /** 스토리 자막: 보스 게이지 위(보스전이 아니면 묶음 위) 가운데, 패널 없이 ink_body. 공지 1.8초, 그 외 3.6초 */
  private showCaption(l: UiStoryLine): void {
    if (!this.built) return;
    this.caption?.destroy();
    this.captionTimer?.remove();
    const hold = l.kind === 'notice' ? 1800 : 3600;
    // BOSS_STARTED·STAGE_STARTED 와 같은 프레임에 오므로(STATE 보다 먼저) 스냅샷으로 보스전·층을 본다
    const snap = uiCommands.getUiSnapshot();
    const bossOn = Boolean(snap.boss && snap.boss.hp > 0) || this.bossName.visible;
    const bottom = bossOn ? this.panelY - 8 - 14 - 18 - 4 : this.panelY - 6;
    const c = new GlowText(this, 0, 0, l.text, 'ink_body', {
      wrap: this.scale.width - 240,
      align: 'center',
      stageIndex: Math.max(0, snap.stageIndex),
    }).setDepth(CAPTION_DEPTH);
    c.placeCenter(this.scale.width / 2, bottom - c.displayHeight);
    this.caption = c;
    this.captionTimer = this.time.delayedCall(hold, () => {
      this.tweens.add({ targets: c, alpha: 0, duration: 300, onComplete: () => c.destroy() });
    });
  }

  /** 층 시작·개성 변화 배너: 화면 가운데 발광 큰 글자 (Galmuri11 2배 — 한자 포함 가능) */
  private showBanner(text: string): void {
    if (!this.built) return;
    this.banner?.destroy();
    const stageIndex = Math.max(0, uiCommands.getUiSnapshot().stageIndex);
    const b = new GlowText(this, 0, 0, text, 'ink_body', { scale: 2, stageIndex }).setDepth(CAPTION_DEPTH).setAlpha(0);
    b.placeCenter(this.scale.width / 2, Math.round(this.scale.height / 2 - 70));
    this.banner = b;
    this.tweens.add({
      targets: b,
      alpha: 1,
      duration: 200,
      yoyo: true,
      hold: 1200,
      onComplete: () => b.destroy(),
    });
  }
}
