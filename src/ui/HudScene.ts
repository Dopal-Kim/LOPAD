import Phaser from 'phaser';
import {
  UI_EVENTS,
  uiBus,
  uiCommands,
  type UiChallengeCleared,
  type UiChallengeStarted,
  type UiMenu,
  type UiSnapshot,
  type UiStoryLine,
  type UiStructureMenuId,
  type UiStructureResult,
  type UiWarpDenied,
  type UiWarpDone,
} from '../contract/ui';
import { installUiDebug, withDebug } from './debug';
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
import { ChallengePanel, InteractBubble, ResultToasts, StatusChips } from './StructureHud';
import { fill, uiText, warpText } from './text';
import { LAYOUT, STRUCT } from './theme';
import { DENY_KEY, WarpMap, roomName } from './WarpMap';

/** 하단 중앙 묶음 (33라운드 Q3) */
const HUD_W = 480;
const HUD_H = 64;
const BOSS_W = 360;
const HP_GAUGE_W = 170;
const PERSONALITY_W = 100;
const CAPTION_DEPTH = 50;
/** 47라운드 구조물 메뉴 id (계약 §9.4) — 시스템이 메뉴 씬을 띄우지 않았을 때의 안전망에 쓴다 */
const STRUCTURE_MENU_IDS: ReadonlySet<string> = new Set<UiStructureMenuId>([
  'cards',
  'exchange',
  'pawn',
  'grave',
  'ledger',
  'counter',
]);

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
  // 워프 지도 (45라운드)
  private warpMap?: WarpMap;
  private warpHint?: GlowText;
  // 상호작용 구조물 (47라운드)
  private bubble?: InteractBubble;
  private chips?: StatusChips;
  private toasts?: ResultToasts;
  private challenge?: ChallengePanel;

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
    installUiDebug(this);
    this.on(UI_EVENTS.STATE, (s: UiSnapshot) => this.render(withDebug(s)));
    this.on(UI_EVENTS.WEAPON_EVOLVED, (p: { name: string }) =>
      this.showBanner(fill(uiText('hud', 'evolvedBanner', '{name}'), { name: p.name })),
    );
    this.on(UI_EVENTS.STAGE_STARTED, (p: { stageName: string }) => this.showBanner(p.stageName));
    this.on(UI_EVENTS.STORY, (l: UiStoryLine) => this.showCaption(l));
    this.on(UI_EVENTS.PAUSED, () => {
      // 워프 지도가 연 정지면 일시정지 일기장을 띄우지 않는다
      if (this.warpMap) return;
      if (!this.scene.isActive(UI_SCENE_KEYS.PAUSE)) this.scene.launch(UI_SCENE_KEYS.PAUSE);
    });
    // Esc 는 Key 폴링(JustDown) 대신 keydown 이벤트로 받는다 — 씬이 바뀌는 프레임에 Key 상태가 눌린 채 남아
    // 다음 Esc 가 '반복 입력' 으로 취급돼 무시되는 문제가 있었다 (41라운드 헤드리스 검증)
    this.input.keyboard?.on('keydown-ESC', this.onEsc);
    // 45라운드 Q9: Tab 워프 지도. 브라우저 포커스 이동을 막도록 캡처한다
    this.input.keyboard?.addCapture('TAB');
    this.input.keyboard?.on('keydown-TAB', this.onTab);
    this.on(UI_EVENTS.WARP_DENIED, (p: UiWarpDenied) => this.onWarpDenied(p));
    this.on(UI_EVENTS.WARP_DONE, (p: UiWarpDone) => this.toast(fill(warpText('warpDone'), { room: roomName(p.type) })));
    this.on(UI_EVENTS.RESUMED, () => this.closeWarp(false));
    for (const e of [UI_EVENTS.MENU_OPEN, UI_EVENTS.RUN_ENDED, UI_EVENTS.STAGE_STARTED])
      this.on(e, () => this.closeWarp(false));
    // 47라운드: 구조물 결과·도전 (계약 §9.6)
    this.on(UI_EVENTS.STRUCTURE_RESULT, (r: UiStructureResult) => this.toasts?.push(r, this.stageIndex));
    this.on(UI_EVENTS.CHALLENGE_STARTED, (c: UiChallengeStarted) => this.challenge?.start(c, this.stageIndex));
    this.on(UI_EVENTS.CHALLENGE_CLEARED, (c: UiChallengeCleared) => this.challenge?.finish(c, this.stageIndex));
    for (const e of [UI_EVENTS.RUN_ENDED, UI_EVENTS.STAGE_STARTED])
      this.on(e, () => {
        this.challenge?.reset();
        this.toasts?.clear();
      });
    this.on(UI_EVENTS.MENU_OPEN, (m: UiMenu) => this.ensureStructureMenu(m));
    this.events.once('shutdown', () => {
      this.input.keyboard?.off('keydown-ESC', this.onEsc);
      this.input.keyboard?.off('keydown-TAB', this.onTab);
      this.input.keyboard?.removeCapture('TAB');
      this.warpMap?.destroy();
      this.warpMap = undefined;
      this.bubble = undefined;
      this.chips = undefined;
      this.toasts = undefined;
      this.challenge = undefined;
      this.alive = false;
      this.built = false;
      for (const [e, h] of this.handlers) uiBus.off(e, h);
      this.handlers = [];
      this.captionTimer?.remove();
    });
    fontsReady().then(() => {
      if (!this.alive) return;
      this.build();
      this.render(withDebug(this.pending ?? uiCommands.getUiSnapshot()));
    });
  }

  private onEsc = (): void => {
    if (this.warpMap) {
      this.closeWarp(true);
      return;
    }
    if (!this.scene.isActive(UI_SCENE_KEYS.MENU) && !this.scene.isActive(UI_SCENE_KEYS.PAUSE)) uiCommands.pause();
  };

  /** Tab: 워프 지도 열기·닫기 (45라운드 Q9·Q10, 계약 §8.4) */
  private onTab = (e?: KeyboardEvent): void => {
    if (e?.repeat) return;
    if (this.warpMap) {
      this.closeWarp(true);
      return;
    }
    if (!this.built) return;
    const s = withDebug(uiCommands.getUiSnapshot());
    const otherUi =
      this.scene.isActive(UI_SCENE_KEYS.MENU) ||
      this.scene.isActive(UI_SCENE_KEYS.PAUSE) ||
      this.scene.isActive(UI_SCENE_KEYS.RESULT);
    // 메뉴·개성 선택·보상·일시정지·워프 연출 중에는 조용히 무시
    if (otherUi || s.paused || s.menu || s.warp.warping || s.warp.blocked === 'busy') return;
    if (s.inCombat || s.warp.blocked === 'combat') {
      this.toast(warpText('warpDeniedCombat'));
      return;
    }
    if (!s.warp.ready) return;
    // 정지 → PAUSED 가 오기 전에 지도를 먼저 만들어 둔다 (PAUSED 처리기가 일시정지 일기장을 띄우지 않게)
    this.warpMap = new WarpMap(this, s, { onChoose: (id) => this.chooseWarp(id) });
    uiCommands.pause();
  };

  /**
   * 구조물 메뉴 안전망: 시스템이 MENU_OPEN 뒤 메뉴 씬을 띄우는 것이 기본(계약 §5). 잠시 뒤에도 메뉴 씬이 없고
   * 스냅샷의 열린 메뉴가 같은 id 면 UI 가 직접 띄운다 (구조물 메뉴만).
   */
  private ensureStructureMenu(m: UiMenu): void {
    if (!STRUCTURE_MENU_IDS.has(m.id)) return;
    this.time.delayedCall(60, () => {
      if (!this.alive) return;
      const status = this.scene.get(UI_SCENE_KEYS.MENU).sys.settings.status;
      const busy = status >= Phaser.Scenes.INIT && status <= Phaser.Scenes.SLEEPING;
      if (busy) return;
      const open = withDebug(uiCommands.getUiSnapshot()).menu;
      if (open && open.id === m.id) this.scene.launch(UI_SCENE_KEYS.MENU, open);
    });
  }

  private chooseWarp(roomId: string): void {
    if (!this.warpMap) return;
    // 허용되면 시스템이 재개(RESUMED)한 뒤 워프한다 (계약 §8.2). 거부면 WARP_DENIED 가 먼저 와서 지도 안에 사유를 보인다
    const ok = uiCommands.warpTo(roomId);
    if (ok) this.closeWarp(false);
  }

  /** 지도를 닫는다. resume=true 면 게임을 재개한다 (Tab·Esc 로 닫을 때) */
  private closeWarp(resume: boolean): void {
    if (!this.warpMap) return;
    this.warpMap.destroy();
    this.warpMap = undefined;
    if (resume) uiCommands.resume();
  }

  private onWarpDenied(p: UiWarpDenied): void {
    const text = warpText(DENY_KEY[p.reason] ?? 'warpDeniedBusy');
    if (this.warpMap) this.warpMap.showMessage(text);
    else this.toast(text);
  }

  /** 짧은 안내 한 줄: 자막 자리(공지와 같은 1.8초) */
  private toast(text: string): void {
    this.showCaption({ kind: 'notice', text });
  }

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

    // ---- 상단 좌: 층 제목·시련, 그 아래 구조물 상태 칩 (47라운드)
    this.floorText = this.glow(E, 12, '', 'ink_body');
    this.chips = new StatusChips(this, E, STRUCT.chipTop);

    // ---- 상단 우: 미니맵 + M 음소거 (토글은 시스템 M 키, UI 는 힌트만)
    this.buildMinimap(s0.map.gridW, s0.map.gridH);

    // ---- 우하단 공지
    this.noticePanel = inkPanel(this, 0, H - 12 - 28, 120, 28).setVisible(false);
    this.noticeIcon = icon(this, 0, H - 12 - 28 + 6, ICON.exit).setVisible(false);
    this.noticeText = this.glow(0, H - 12 - 28 + 7, '', 'ink_accent').setVisible(false);

    // ---- 47라운드: 상호작용 안내·결과 토스트(우하단 공지 위)·도전 판(상단 가운데)
    this.bubble = new InteractBubble(this, this.stageIndex);
    this.toasts = new ResultToasts(this, W - E, H - 12 - 28 - 8);
    this.challenge = new ChallengePanel(this, STRUCT.challengeTop);

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
    // 45라운드: 비전투일 때만 'Tab 워프' ('M 음소거' 아래 줄, 같은 오른쪽 끝)
    this.warpHint = this.glow(0, hintY + 16, warpText('warpKeyHint'), 'ink_faint').setVisible(false);
    this.warpHint.placeRight(W - E - 20, hintY + 16);
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
    this.warpHint?.setVisible(!s.inCombat && s.warp.blocked !== 'combat');
    // 47라운드: 구조물 안내·상태·도전 시간
    const overlay =
      Boolean(this.warpMap) ||
      Boolean(s.menu) ||
      this.scene.isActive(UI_SCENE_KEYS.MENU) ||
      this.scene.isActive(UI_SCENE_KEYS.PAUSE) ||
      this.scene.isActive(UI_SCENE_KEYS.RESULT);
    this.bubble?.update(s.interactable ?? null, !overlay, si);
    this.chips?.render(s.statuses ?? [], si);
    this.challenge?.tick(s.statuses?.find((st) => st.id === 'ring') ?? null, si);
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
