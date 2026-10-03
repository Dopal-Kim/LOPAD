import Phaser from 'phaser';
import {
  UI_EVENTS,
  UI_SCREEN,
  uiBus,
  uiCommands,
  type UiChallengeCleared,
  type UiChallengeStarted,
  type UiMenu,
  type UiRoute,
  type UiRouteEntered,
  type UiRouteNode,
  type UiSnapshot,
  type UiStoryLine,
  type UiStructureMenuId,
  type UiStructureResult,
  type UiWarpDenied,
  type UiWarpDone,
} from '../contract/ui';
import { CarryChip } from './CarryHud';
import { carryView } from './carryView';
import { chooseNodeCmd, debugExpose, installUiDebug, withDebug } from './debug';
import { GlowText } from './glow';
import {
  Gauge,
  ICON,
  NinePanel,
  WEAPON_ICON_IDS,
  ensureImage,
  fontsReady,
  icon,
  inkPanel,
  keyartKey,
  keyartUrl,
  mapBgKey,
  mapBgUrl,
  preloadKit,
  setupKit,
  weaponIconKey,
} from './kit';
import { keyTaken, takeKey } from './keyGate';
import { UI_SCENE_KEYS } from './keys';
import { Minimap } from './Minimap';
import { RegionCard } from './RegionCard';
import { findNode, regionArtKey, regionChanged } from './regionView';
import { RouteMap } from './RouteMap';
import { RouteStrip } from './RouteStrip';
import { hasRoute } from './routeView';
import { ResourceGauge } from './ResourceHud';
import { ChallengePanel, InteractBubble, ResultToasts, StatusChips } from './StructureHud';
import { fill, r49Text, regionText, routeText, uiText, warpText } from './text';
import { LAYOUT, MAP_BG_FLOORS, RES, ROUTE, STRUCT } from './theme';
import { TutorialGuide } from './TutorialHud';
import { DENY_KEY, WarpMap, roomName } from './WarpMap';

/** 가운데 배너 차례: 글자 배너(층 제목·노드 이름·진화) 또는 50라운드 지역 카드 */
type BannerItem = { kind: 'text'; text: string } | { kind: 'region'; region: string; art: string | null; desc: string };
/** 글자 배너 대기 상한 (지역 카드는 상한과 관계없이 넣는다) */
const BANNER_QUEUE_MAX = 3;

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
 * 보스 게이지는 묶음 위 8px, 자막은 그 위. 상단 좌 층 제목·시련, 상단 우 미니맵 + 'M 지도'. 우하단 공지.
 * 49라운드: 무기 자원이 있으면 묶음이 80 으로 커지고 3행에 자원 게이지(계약 §11.1). M = 지도(Tab 과 같음, §11.3).
 * 무기 시험장(`lab`)에서는 좌상단에 '무기 시험장 · L 무기 고르기 · Esc 나가기', 우상단 지도·안내는 숨긴다.
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
  private panel!: NinePanel;
  private bundleH = HUD_H;
  /** 하단 묶음과 함께 위아래로 움직이는 것 (보스 게이지 포함) */
  private bundleObjs: { y: number; setY(y: number): unknown }[] = [];
  private bundleGauges: Gauge[] = [];
  private resource?: ResourceGauge;
  /** 53라운드: F 넣기/뽑기 (3행 오른쪽) */
  private carry?: CarryChip;
  /** 53라운드: 튜토리얼 안내 패널·적 등장 경고 */
  private guide?: TutorialGuide;
  private labMode = false;
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
  // 노드 지도 (48라운드)
  private routeMap?: RouteMap;
  private routeStrip?: RouteStrip;
  private routeMode = false;
  /** 49라운드: 음소거 중이면 'M 지도' 오른쪽에 icon_mute */
  private soundIcon?: Phaser.GameObjects.Image;
  private mapHint?: GlowText;
  /** chooseNode 가 받아들여진 뒤 스냅샷이 아직 choosing 인 동안 다시 열지 않는다 */
  private chooseSuppressUntil = 0;
  // 탄생 연출 (48라운드): HUD 를 숨기고 건너뛰기 안내만
  private birthActive = false;
  private birthCam?: Phaser.Cameras.Scene2D.Camera;
  private birthHint?: GlowText;
  private birthFailsafe?: Phaser.Time.TimerEvent;
  private deferredCaption?: UiStoryLine;
  // 배너 차례 (층 제목 → 지역 카드 → 노드 이름이 겹치지 않게)
  private bannerQueue: BannerItem[] = [];
  private bannerBusy = false;
  // 50라운드 지역 카드: 지금 뜬 카드와 그 항목, 마지막으로 카드를 띄운 지역, 큰 그림 미리 읽기 표시
  private regionCard?: RegionCard;
  private regionItem?: BannerItem;
  private lastRegion: string | null = null;
  private prefetchSig = '';

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
    this.routeMode = false;
    this.labMode = false;
    this.bundleH = HUD_H;
    this.bundleObjs = [];
    this.bundleGauges = [];
    this.birthActive = false;
    this.bannerQueue = [];
    this.bannerBusy = false;
    this.lastRegion = null;
    this.prefetchSig = '';
    installUiDebug(this);
    this.on(UI_EVENTS.STATE, (s: UiSnapshot) => this.render(withDebug(s)));
    this.on(UI_EVENTS.WEAPON_EVOLVED, (p: { name: string }) =>
      this.showBanner(fill(uiText('hud', 'evolvedBanner', '{name}'), { name: p.name })),
    );
    this.on(UI_EVENTS.STAGE_STARTED, (p: { stageName: string }) => this.showBanner(p.stageName));
    this.on(UI_EVENTS.STORY, (l: UiStoryLine) => this.showCaption(l));
    this.on(UI_EVENTS.PAUSED, () => {
      // 워프 지도·노드 지도가 연 정지면 일시정지 일기장을 띄우지 않는다
      if (this.warpMap || this.routeMap) return;
      if (!this.scene.isActive(UI_SCENE_KEYS.PAUSE)) this.scene.launch(UI_SCENE_KEYS.PAUSE);
    });
    // Esc 는 Key 폴링(JustDown) 대신 keydown 이벤트로 받는다 — 씬이 바뀌는 프레임에 Key 상태가 눌린 채 남아
    // 다음 Esc 가 '반복 입력' 으로 취급돼 무시되는 문제가 있었다 (41라운드 헤드리스 검증)
    this.input.keyboard?.on('keydown-ESC', this.onEsc);
    this.input.keyboard?.on('keydown-ENTER', this.onEnter);
    // 45라운드 Q9: Tab 워프 지도. 브라우저 포커스 이동을 막도록 캡처한다
    this.input.keyboard?.addCapture('TAB');
    this.input.keyboard?.on('keydown-TAB', this.onTab);
    // 49라운드: M = 지도 + 현재 위치·위치 정보 (Tab 과 같은 지도, 계약 §11.3). 음소거는 Esc 일기장으로 옮겼다
    this.input.keyboard?.on('keydown-M', this.onTab);
    this.on(UI_EVENTS.WARP_DENIED, (p: UiWarpDenied) => this.onWarpDenied(p));
    this.on(UI_EVENTS.WARP_DONE, (p: UiWarpDone) => this.toast(fill(warpText('warpDone'), { room: roomName(p.type) })));
    this.on(UI_EVENTS.RESUMED, () => {
      this.closeWarp(false);
      if (this.routeMap?.mode === 'view') this.closeRoute(false);
    });
    for (const e of [UI_EVENTS.MENU_OPEN, UI_EVENTS.RUN_ENDED, UI_EVENTS.STAGE_STARTED])
      this.on(e, () => {
        this.closeWarp(false);
        this.closeRoute(false);
      });
    // 48라운드: 노드 지도·노드 진입·탄생 연출 (계약 §10)
    this.on(UI_EVENTS.ROUTE_CHOOSE_OPEN, (r: UiRoute) => this.openRouteChoose(r));
    this.on(UI_EVENTS.ROUTE_NODE_ENTERED, (p: UiRouteEntered) => {
      // 50라운드: 지역이 바뀌었으면 지역 카드 먼저, 그 뒤 노드 이름 배너
      const s = withDebug(uiCommands.getUiSnapshot());
      this.queueRegionCard(findNode(s.route, p?.id), s);
      if (p?.name) this.showBanner(p.name);
    });
    this.on(UI_EVENTS.BIRTH_STARTED, () => this.startBirth());
    this.on(UI_EVENTS.BIRTH_DONE, () => {
      // 탄생 노드의 진입 이벤트가 없었어도 첫 지역 카드는 탄생 연출이 끝난 뒤에
      const s = withDebug(uiCommands.getUiSnapshot());
      this.queueRegionCard(findNode(s.route, s.route?.currentId), s);
      this.endBirth();
    });
    this.on(UI_EVENTS.RUN_ENDED, () => {
      this.lastRegion = null;
      this.bannerQueue = this.bannerQueue.filter((b) => b.kind === 'text');
      if (this.regionCard) {
        this.regionCard.cancel();
        this.regionCard = undefined;
        this.regionItem = undefined;
        this.bannerBusy = false;
      }
      this.endBirth();
    });
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
      this.input.keyboard?.off('keydown-ENTER', this.onEnter);
      this.input.keyboard?.off('keydown-TAB', this.onTab);
      this.input.keyboard?.off('keydown-M', this.onTab);
      this.input.keyboard?.removeCapture('TAB');
      this.resource = undefined;
      this.carry = undefined;
      this.guide?.destroy();
      this.guide = undefined;
      this.warpMap?.destroy();
      this.warpMap = undefined;
      this.routeMap?.destroy();
      this.routeMap = undefined;
      this.routeStrip = undefined;
      this.endBirth();
      this.regionCard?.cancel();
      this.regionCard = undefined;
      this.regionItem = undefined;
      this.bannerQueue = [];
      this.bannerBusy = false;
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

  /**
   * 51라운드 §6: Esc = 한 단계 뒤로. 위에 뜬 것부터 하나씩 닫고(지역 카드 → 튜토리얼 안내 → 노드·워프 지도),
   * 열린 화면이 없으면 일시정지 일기장. 메뉴·일시정지 씬이 떠 있으면 그 씬이 Esc 를 받는다.
   */
  private onEsc = (e?: KeyboardEvent): void => {
    if (e?.repeat) return;
    // 탄생 연출 중에는 Esc 도 '아무 키' (건너뛰기는 시스템이 받는다)
    if (this.birthActive) return;
    // 지역 카드는 같은 Esc 의 keydown 으로 이미 건너뛰기를 받았다
    if (this.regionCard) return;
    // 메뉴·일시정지 씬이 같은 Esc 로 이미 동작했으면(그 씬이 닫힌 뒤 다시 넘어온 이벤트 포함) 넘긴다 (keyGate.ts)
    if (keyTaken(e)) return;
    if (this.guide?.panelOpen) {
      takeKey(e);
      this.guide.dismiss();
      return;
    }
    if (this.routeMap) {
      // 보기 모드는 닫고 재개. 고르기 모드는 고를 곳이 없을 때만 닫는다 (고르는 동안은 시스템이 입력을 잠근다)
      if (this.routeMap.mode === 'view') {
        takeKey(e);
        this.closeRoute(false);
        this.resumeAfterRelease('Escape');
      } else if (!this.routeMap.hasChoices) {
        takeKey(e);
        this.closeRoute(false);
      }
      return;
    }
    if (this.warpMap) {
      takeKey(e);
      this.closeWarp(false);
      this.resumeAfterRelease('Escape');
      return;
    }
    if (this.scene.isActive(UI_SCENE_KEYS.MENU) || this.scene.isActive(UI_SCENE_KEYS.PAUSE)) return;
    if (takeKey(e)) uiCommands.pause();
  };

  /** Enter: 튜토리얼 안내 닫기 */
  private onEnter = (e?: KeyboardEvent): void => {
    if (!this.guide?.panelOpen || keyTaken(e)) return;
    takeKey(e);
    this.guide.dismiss();
  };

  /**
   * 지도를 Esc 로 닫을 때 재개를 키를 뗀 다음 프레임으로 미룬다. 누르는 프레임에 재개하면 게임 씬이 같은 Esc 를 받아
   * 일시정지 일기장이 열렸다 (48라운드 헤드리스 확인, 45라운드 워프 지도도 같은 증상).
   */
  private resumeAfterRelease(key: string): void {
    const kb = this.input.keyboard;
    if (!kb) {
      uiCommands.resume();
      return;
    }
    let done = false;
    const go = (): void => {
      if (done) return;
      done = true;
      kb.off('keyup', onUp);
      this.time.delayedCall(0, () => {
        if (this.alive && !this.warpMap && !this.routeMap) uiCommands.resume();
      });
    };
    const onUp = (e: KeyboardEvent): void => {
      if (e.key === key) go();
    };
    kb.on('keyup', onUp);
    // 떼는 입력을 놓쳐도 멈춘 채 남지 않게
    this.time.delayedCall(1000, go);
  }

  /**
   * Tab·M: 지도 열기·닫기 (45라운드 Q9·Q10 워프 지도, 48라운드 노드 지도, 49라운드 M = 지도 §11.3).
   * 노드 지도 층은 M·Tab 모두 노드 지도(보기), 그 외 층은 워프 지도. 무기 시험장에서는 무시.
   */
  private onTab = (e?: KeyboardEvent): void => {
    if (e?.repeat) return;
    if (this.birthActive) return;
    // 같은 Tab·M 이벤트가 다시 넘어와 방금 연 지도를 곧바로 닫지 않게 (keyGate.ts). 열고 닫는 일만 있으므로 처음에 소비한다
    if (!takeKey(e)) return;
    if (this.routeMap) {
      if (this.routeMap.mode === 'view') this.closeRoute(true);
      return;
    }
    if (this.warpMap) {
      this.closeWarp(true);
      return;
    }
    if (!this.built) return;
    const s = withDebug(uiCommands.getUiSnapshot());
    if (s.lab) return;
    const otherUi =
      this.scene.isActive(UI_SCENE_KEYS.MENU) ||
      this.scene.isActive(UI_SCENE_KEYS.PAUSE) ||
      this.scene.isActive(UI_SCENE_KEYS.RESULT);
    // 48라운드: 노드 지도 층이면 Tab = 노드 지도 보기 (워프 비활성, 계약 §10.2)
    if (hasRoute(s.route)) {
      if (otherUi || s.paused || s.menu || s.route.choosing) return;
      this.routeMap = new RouteMap(this, s.route, 'view', this.routeOpts(s));
      uiCommands.pause();
      return;
    }
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

  private routeOpts(s: UiSnapshot): ConstructorParameters<typeof RouteMap>[3] {
    return {
      stageIndex: Math.max(0, s.stageIndex),
      floorTitle: s.floorTitle || s.stageName,
      shopName: s.names?.shop,
      onChoose: (id) => this.chooseRoute(id),
    };
  }

  /** ROUTE_CHOOSE_OPEN: 노드 지도를 고르기 모드로 연다 (게임 입력은 시스템이 잠근다 — 정지하지 않는다) */
  private openRouteChoose(r?: UiRoute | null): void {
    if (!this.built) return;
    const s = withDebug(uiCommands.getUiSnapshot());
    const route = hasRoute(r) ? r : s.route;
    if (!hasRoute(route)) return;
    if (this.routeMap) this.closeRoute(this.routeMap.mode === 'view');
    this.closeWarp(true);
    this.routeMap = new RouteMap(this, route, 'choose', this.routeOpts(s));
  }

  private chooseRoute(id: string): void {
    if (!this.routeMap || this.routeMap.mode !== 'choose') return;
    if (chooseNodeCmd(id)) {
      this.chooseSuppressUntil = this.time.now + 1500;
      this.closeRoute(false);
    } else this.routeMap.showMessage(routeText('chooseDenied'));
  }

  /** 노드 지도를 닫는다. resume=true 면 게임을 재개한다 (보기 모드를 Tab·Esc 로 닫을 때) */
  private closeRoute(resume: boolean): void {
    if (!this.routeMap) return;
    this.routeMap.destroy();
    this.routeMap = undefined;
    if (resume) uiCommands.resume();
  }

  // ---- 탄생 연출 (48라운드 Q6, 계약 §10.3): HUD 를 숨기고 하단에 건너뛰기 안내만 작게
  private startBirth(): void {
    if (!this.birthActive) {
      this.birthActive = true;
      this.closeWarp(false);
      this.closeRoute(false);
      // 같은 프레임에 먼저 온 진입 이벤트로 지역 카드가 떴으면 거두고 연출 뒤로 미룬다
      if (this.regionCard && this.regionItem) {
        this.regionCard.cancel();
        this.bannerQueue.unshift(this.regionItem);
        this.regionCard = undefined;
        this.regionItem = undefined;
        this.bannerBusy = false;
      }
      this.cameras.main.setVisible(false);
      // BIRTH_DONE 이 오지 않아도 HUD 가 영영 숨지 않게
      this.birthFailsafe = this.time.delayedCall(ROUTE.birthFailsafeMs, () => this.endBirth());
    }
    if (!this.built || this.birthHint) return;
    const W = UI_SCREEN.WIDTH;
    const H = UI_SCREEN.HEIGHT;
    const hint = new GlowText(this, 0, 0, routeText('birthSkip'), 'ink_faint', {
      stageIndex: Math.max(0, this.stageIndex),
    });
    hint.placeCenter(W / 2, H - ROUTE.birthHintBottom - hint.displayHeight).setAlpha(0);
    // 지연(delay) 을 준 트윈은 이 이벤트 경로에서 진행되지 않았다 (헤드리스 확인) — 바로 서서히 나타나게
    this.tweens.add({ targets: hint, alpha: 1, duration: 300 });
    // 안내만 그리는 카메라: 지금 있는 것과 연출 중 새로 생기는 것은 모두 무시한다
    // 53라운드 1920 렌더: main 카메라(시스템이 zoom·원점을 맞춤)와 같은 뷰포트·배율로 (UI 는 main 을 바꾸지 않는다)
    const main = this.cameras.main;
    const cam = this.cameras.add(main.x, main.y, main.width, main.height);
    cam.setZoom(main.zoom).setOrigin(main.originX, main.originY).setScroll(main.scrollX, main.scrollY);
    cam.ignore(this.children.list.filter((o) => o !== hint));
    this.events.on(Phaser.Scenes.Events.ADDED_TO_SCENE, this.ignoreInBirthCam);
    this.birthCam = cam;
    this.birthHint = hint;
  }

  private ignoreInBirthCam = (o: Phaser.GameObjects.GameObject): void => {
    this.birthCam?.ignore(o);
  };

  private endBirth(): void {
    if (!this.birthActive) return;
    this.birthActive = false;
    this.birthFailsafe?.remove();
    this.birthFailsafe = undefined;
    this.events.off(Phaser.Scenes.Events.ADDED_TO_SCENE, this.ignoreInBirthCam);
    if (this.birthCam) {
      // 무시 표시를 지운다 (같은 카메라 id 가 나중에 다시 쓰일 수 있다)
      const bit = this.birthCam.id;
      const clear = (list: Phaser.GameObjects.GameObject[]) => {
        for (const o of list) {
          o.cameraFilter &= ~bit;
          if (o instanceof Phaser.GameObjects.Container) clear(o.list);
        }
      };
      clear(this.children.list);
      this.cameras.remove(this.birthCam);
      this.birthCam = undefined;
    }
    this.birthHint?.destroy();
    this.birthHint = undefined;
    if (this.sys.isActive()) this.cameras.main.setVisible(true);
    // 연출 중 미뤄 둔 자막·배너
    const c = this.deferredCaption;
    this.deferredCaption = undefined;
    if (c) this.showCaption(c);
    this.nextBanner();
  }

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
    const W = UI_SCREEN.WIDTH;
    const H = UI_SCREEN.HEIGHT;
    const E = LAYOUT.edge;
    const s0 = uiCommands.getUiSnapshot();
    this.stageIndex = Math.max(0, s0.stageIndex);

    // ---- 하단 중앙 묶음
    const px = Math.round(W / 2 - HUD_W / 2);
    const py = H - HUD_H - 12;
    this.panelX = px;
    this.panelY = py;
    this.bundleH = HUD_H;
    this.panel = inkPanel(this, px, py, HUD_W, HUD_H);
    // 1행: 체력
    const hpIcon = icon(this, px + 8, py + 8, ICON.hp);
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
    // 49라운드: 3행 무기 자원 (묶음이 커질 때만 보인다)
    this.resource = new ResourceGauge(this, px + RES.labelX, py + RES.rowY);
    // 53라운드: F 넣기/뽑기 — 3행 오른쪽 끝 (우클릭 글과 같은 오른쪽 선)
    this.carry = new CarryChip(this, px + HUD_W - 10, py + RES.rowY - 3, this.stageIndex);
    this.bundleObjs = [
      hpIcon,
      this.hpText,
      this.goldIcon,
      this.goldText,
      this.potionIcon,
      this.potionText,
      this.potionKey,
      this.weaponIcon,
      this.weaponText,
      this.senseIcon,
      this.personalityText,
      this.secondaryText,
      this.bossIcon,
      this.bossName,
      this.carry,
    ];
    this.bundleGauges = [this.hpGauge, this.personalityGauge, this.bossGauge];

    // ---- 상단 좌: 층 제목·시련, 그 아래 구조물 상태 칩 (47라운드)
    this.floorText = this.glow(E, 12, '', 'ink_body');
    this.chips = new StatusChips(this, E, STRUCT.chipTop);

    // ---- 상단 우: 미니맵(노드 띠) + 'M 지도' (49라운드: M 음소거 → Esc 일기장)
    this.buildMinimap(s0.map.gridW, s0.map.gridH);

    // ---- 우하단 공지
    this.noticePanel = inkPanel(this, 0, H - 12 - 28, 120, 28).setVisible(false);
    this.noticeIcon = icon(this, 0, H - 12 - 28 + 6, ICON.exit).setVisible(false);
    this.noticeText = this.glow(0, H - 12 - 28 + 7, '', 'ink_accent').setVisible(false);

    // ---- 47라운드: 상호작용 안내·결과 토스트(우하단 공지 위)·도전 판(상단 가운데)
    this.bubble = new InteractBubble(this, this.stageIndex);
    this.toasts = new ResultToasts(this, W - E, H - 12 - 28 - 8);
    this.challenge = new ChallengePanel(this, STRUCT.challengeTop);
    this.guide = new TutorialGuide(this);

    this.built = true;
    // 글꼴을 기다리는 동안 시작된 탄생 연출·미뤄 둔 배너
    if (this.birthActive) this.startBirth();
    else this.nextBanner();
  }

  private buildMinimap(gridW: number, gridH: number): void {
    const W = UI_SCREEN.WIDTH;
    const E = LAYOUT.edge;
    const size = Minimap.size(gridW, gridH);
    this.minimap = new Minimap(this, W - E - size.w, 12, gridW, gridH);
    const hintY = 12 + this.minimap.h + 6;
    this.soundIcon = icon(this, W - E - 16, hintY - 2, ICON.mute).setVisible(false);
    this.mapHint = this.glow(0, hintY, routeText('mapKeyHintM'), 'ink_faint');
    this.mapHint.placeRight(W - E - 20, hintY);
    // 45라운드: 비전투일 때만 'Tab 워프' ('M 지도' 아래 줄, 같은 오른쪽 끝). 노드 지도 층은 M·Tab 이 같은 지도라 숨김
    this.warpHint = this.glow(0, hintY + 16, warpText('warpKeyHint'), 'ink_faint').setVisible(false);
    this.warpHint.placeRight(W - E - 20, hintY + 16);
    // 48라운드: 노드 지도 층이면 방 미니맵 대신 노드 띠 (같은 자리, 오른쪽 끝 고정)
    this.routeStrip = new RouteStrip(this, W - E, 12);
    this.routeStrip.setVisible(false);
  }

  /** 우상단: 미니맵/노드 띠 아래로 'M 지도'·'Tab 워프' 줄을 맞춘다 */
  private layoutTopRight(): void {
    const W = UI_SCREEN.WIDTH;
    const E = LAYOUT.edge;
    const h = this.routeMode && this.routeStrip ? this.routeStrip.h : this.minimap.h;
    const hintY = 12 + h + 6;
    this.soundIcon?.setY(hintY - 2);
    this.mapHint?.placeRight(W - E - 20, hintY);
    this.warpHint?.setText(warpText('warpKeyHint')).placeRight(W - E - 20, hintY + 16);
  }

  /**
   * 49라운드: 하단 묶음 높이 (자원이 있으면 RES.bundleH). 아래 여백 12 를 지키며 위로 늘고, 묶음·보스 게이지를 함께 옮긴다.
   */
  private setBundleHeight(h: number): void {
    if (h === this.bundleH) return;
    const py = UI_SCREEN.HEIGHT - h - 12;
    const dy = py - this.panelY;
    this.bundleH = h;
    this.panelY = py;
    this.panel.resize(HUD_W, h).setY(py);
    for (const o of this.bundleObjs) o.setY(o.y + dy);
    for (const g of this.bundleGauges) g.setPositionY(g.top + dy);
    this.resource?.shiftY(dy);
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
      this.carry?.setStageIndex(si);
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
    // 3행 (49라운드): 무기 자원 + 53라운드 F 넣기/뽑기. 둘 다 없으면 묶음을 원래 높이로
    const res = s.resource && s.resource.kind ? s.resource : null;
    const carry = carryView(s.carry);
    this.setBundleHeight(res || carry ? RES.bundleH : HUD_H);
    this.resource?.render(res, si, this.time.now);
    this.carry?.render(carry);
    // 보스 (처치 뒤 스냅샷에 hp 0 으로 남는 동안은 숨긴다)
    if (s.boss && s.boss.hp > 0) {
      this.bossGauge.setVisible(true).set(s.boss.maxHp > 0 ? s.boss.hp / s.boss.maxHp : 0);
      this.bossIcon.setVisible(true);
      this.bossName
        .setVisible(true)
        .setText(`${s.boss.name}  ${s.boss.hp}/${s.boss.maxHp}  페이즈 ${s.boss.phase}`)
        .placeCenter(UI_SCREEN.WIDTH / 2, this.bossName.y);
    } else {
      this.bossGauge.setVisible(false);
      this.bossIcon.setVisible(false);
      this.bossName.setVisible(false);
    }
    // 상단
    // 48라운드: 노드 지도 층이면 층 제목 옆에 지금 노드 이름, 우상단은 노드 띠, 'Tab 지도' 는 늘 보인다
    // 49라운드: 무기 시험장은 층 제목·노드 띠·지도 안내 대신 시험장 안내 한 줄
    const lab = Boolean(s.lab);
    const route = !lab && hasRoute(s.route) ? s.route : null;
    if (Boolean(route) !== this.routeMode || lab !== this.labMode) {
      this.routeMode = Boolean(route);
      this.labMode = lab;
      this.minimap.setVisible(!this.routeMode && !lab);
      this.routeStrip?.setVisible(this.routeMode);
      this.mapHint?.setVisible(!lab);
      this.layoutTopRight();
    }
    this.soundIcon?.setVisible(Boolean(s.muted) && !lab);
    if (lab) {
      this.floorText.setText(r49Text('labHud'));
      this.warpHint?.setVisible(false);
    } else if (route) {
      this.prefetchRouteArt(route, route.nodes.find((n) => n.id === route.currentId) ?? null);
      const cur = route.nodes.find((n) => n.id === route.currentId);
      const where = cur ? [cur.region, cur.name].filter(Boolean).join(' · ') : '';
      this.floorText.setText(`${s.floorTitle || s.stageName}${where ? `   ${where}` : ''}`);
      if (this.routeStrip?.render(route, si)) this.layoutTopRight();
      // 노드 지도 층은 M·Tab 이 같은 지도 — 'M 지도' 한 줄만
      this.warpHint?.setVisible(false);
    } else {
      this.floorText.setText(`${s.floorTitle || s.stageName}   시련 ${s.trialsCleared}/${s.trialsTotal}`);
      this.minimap.render(s.map, si);
      this.warpHint?.setVisible(!s.inCombat && s.warp.blocked !== 'combat');
    }
    // 47라운드: 구조물 안내·상태·도전 시간
    const overlay =
      Boolean(this.warpMap) ||
      Boolean(this.routeMap) ||
      Boolean(s.menu) ||
      this.scene.isActive(UI_SCENE_KEYS.MENU) ||
      this.scene.isActive(UI_SCENE_KEYS.PAUSE) ||
      this.scene.isActive(UI_SCENE_KEYS.RESULT);
    this.bubble?.update(s.interactable ?? null, !overlay, si);
    this.chips?.render(s.statuses ?? [], si);
    this.challenge?.tick(s.statuses?.find((st) => st.id === 'ring') ?? null, si);
    // 53라운드: 튜토리얼 안내 — 다른 화면·배너·지역 카드·탄생 연출이 없을 때만 새로 띄운다
    const bannersIdle = !this.bannerBusy && this.bannerQueue.length === 0 && !this.regionCard;
    this.guide?.update(s, !overlay && !this.birthActive && bannersIdle, si);
    // 48라운드 안전망: 고를 차례인데 지도가 없으면 연다 (이벤트를 놓쳤거나 메뉴가 닫힌 뒤)
    if (route?.choosing && !overlay && !this.birthActive && this.time.now > this.chooseSuppressUntil)
      this.openRouteChoose(route);
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
        const nx = UI_SCREEN.WIDTH - LAYOUT.edge - w;
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
    if (this.birthActive) {
      // 탄생 연출 중 자막은 끝난 뒤 마지막 한 줄만
      this.deferredCaption = l;
      return;
    }
    // 53라운드: 튜토리얼 노드의 공지는 위쪽 가운데 단계 카드로 (작은 자막 대신)
    if (this.guide?.takeNotice(l, withDebug(uiCommands.getUiSnapshot()), Math.max(0, this.stageIndex))) return;
    this.caption?.destroy();
    this.captionTimer?.remove();
    const hold = l.kind === 'notice' ? 1800 : 3600;
    // BOSS_STARTED·STAGE_STARTED 와 같은 프레임에 오므로(STATE 보다 먼저) 스냅샷으로 보스전·층을 본다
    const snap = uiCommands.getUiSnapshot();
    const bossOn = Boolean(snap.boss && snap.boss.hp > 0) || this.bossName.visible;
    const bottom = bossOn ? this.panelY - 8 - 14 - 18 - 4 : this.panelY - 6;
    const c = new GlowText(this, 0, 0, l.text, 'ink_body', {
      wrap: UI_SCREEN.WIDTH - 240,
      align: 'center',
      stageIndex: Math.max(0, snap.stageIndex),
    }).setDepth(CAPTION_DEPTH);
    c.placeCenter(UI_SCREEN.WIDTH / 2, bottom - c.displayHeight);
    this.caption = c;
    this.captionTimer = this.time.delayedCall(hold, () => {
      this.tweens.add({ targets: c, alpha: 0, duration: 300, onComplete: () => c.destroy() });
    });
  }

  /** 층 시작·개성 변화 배너: 화면 가운데 발광 큰 글자 (Galmuri11 2배 — 한자 포함 가능) */
  private showBanner(text: string): void {
    this.enqueueBanner({ kind: 'text', text });
  }

  /** 48라운드: 층 제목 → 노드 이름이 같은 때 오면 차례로 (덮어쓰지 않게). 탄생 연출 중이면 끝난 뒤 */
  private enqueueBanner(item: BannerItem): void {
    if (!this.built || this.birthActive || this.bannerBusy) {
      const texts = this.bannerQueue.filter((b) => b.kind === 'text').length;
      if (item.kind === 'region' || texts < BANNER_QUEUE_MAX) this.bannerQueue.push(item);
      this.exposeBanners();
      return;
    }
    this.runBanner(item);
    this.exposeBanners();
  }

  private runBanner(item: BannerItem): void {
    this.bannerBusy = true;
    const stageIndex = Math.max(0, uiCommands.getUiSnapshot().stageIndex);
    if (item.kind === 'region') {
      this.regionItem = item;
      const card = new RegionCard(this, {
        region: item.region,
        desc: item.desc,
        art: item.art,
        stageIndex,
        onDone: () => {
          if (this.regionCard !== card) return;
          this.regionCard = undefined;
          this.regionItem = undefined;
          this.bannerBusy = false;
          this.nextBanner();
        },
      });
      this.regionCard = card;
      return;
    }
    this.banner?.destroy();
    const b = new GlowText(this, 0, 0, item.text, 'ink_body', { scale: 2, stageIndex })
      .setDepth(CAPTION_DEPTH)
      .setAlpha(0);
    b.placeCenter(UI_SCREEN.WIDTH / 2, Math.round(UI_SCREEN.HEIGHT / 2 - 70));
    this.banner = b;
    this.tweens.add({
      targets: b,
      alpha: 1,
      duration: 200,
      yoyo: true,
      hold: 1200,
      onComplete: () => {
        b.destroy();
        if (this.banner === b) this.banner = undefined;
        this.bannerBusy = false;
        this.nextBanner();
      },
    });
  }

  private nextBanner(): void {
    if (!this.built || this.birthActive || this.bannerBusy) {
      this.exposeBanners();
      return;
    }
    const next = this.bannerQueue.shift();
    if (next !== undefined) this.runBanner(next);
    this.exposeBanners();
  }

  /** 헤드리스 확인용: 배너 차례 상태 (`uidebug=1` 일 때만) */
  private exposeBanners(): void {
    debugExpose('banners', {
      busy: this.bannerBusy,
      queued: this.bannerQueue.map((b) => (b.kind === 'text' ? b.text : `[${b.region}]`)),
    });
  }

  /**
   * 50라운드 지역 카드 (계약 §12): 들어온 노드의 지역이 마지막으로 카드를 띄운 지역과 다르면 차례에 넣는다.
   * 키아트는 지금부터 읽기 시작한다 (카드 차례가 오면 대개 다 읽혀 있다). 무기 시험장에서는 띄우지 않는다.
   */
  private queueRegionCard(node: UiRouteNode | null, s: UiSnapshot): void {
    if (!node || s.lab || !regionChanged(node.region, this.lastRegion)) return;
    const region = (node.region ?? '').trim();
    this.lastRegion = region;
    const art = regionArtKey(region);
    if (art) ensureImage(this, keyartKey(art), keyartUrl(art));
    this.enqueueBanner({ kind: 'region', region, art, desc: regionText(art, node.desc) });
  }

  /**
   * 50라운드: 노드 지도 층의 큰 그림을 필요해진 때 한 번 읽어 둔다 — 그 층 지도 배경(MAP_BG_FLOORS), 지금 지역 키아트,
   * 바로 다음 단계(지금 노드의 links) 지역 키아트(다음 지역 카드가 기다리지 않게). 층·지금 노드가 바뀔 때만 확인한다.
   */
  private prefetchRouteArt(route: UiRoute, cur: UiRouteNode | null): void {
    const sig = `${route.floor}|${cur?.id ?? ''}`;
    if (sig === this.prefetchSig) return;
    this.prefetchSig = sig;
    if (MAP_BG_FLOORS.includes(route.floor)) ensureImage(this, mapBgKey(route.floor), mapBgUrl(route.floor));
    const next = cur ? route.nodes.filter((n) => cur.links.includes(n.id)) : [];
    const arts = new Set([cur, ...next].map((n) => regionArtKey(n?.region)).filter((a): a is string => Boolean(a)));
    for (const art of arts) ensureImage(this, keyartKey(art), keyartUrl(art));
  }
}
