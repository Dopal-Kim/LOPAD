import Phaser from 'phaser';
import {
  UI_EVENTS,
  UI_SCREEN,
  uiBus,
  uiCommands,
  type UiChallengeCleared,
  type UiChallengeStarted,
  type UiConsumableUsed,
  type UiCurse,
  type UiCurseEnded,
  type UiMenu,
  type UiNodeGraded,
  type UiPerfectSuccess,
  type UiRoute,
  type UiRouteEntered,
  type UiRouteNode,
  type UiSnapshot,
  type UiBuildMenuId,
  type UiStructureMenuId,
  type UiStructureResult,
  type UiTagSetChanged,
  type UiWarpDenied,
  type UiWarpDone,
} from '../contract/ui';
import { BuildLayer } from './BuildLayer';
import { GrowthLayer } from './GrowthHud';
import { BuildPeek } from './BuildPeek';
import { KeyGuide } from './keyGuide';
import { snapshotVerbItems } from './keyGuideView';
import { CombatHud } from './CombatHud';
import { cancelChooseCmd, chooseNodeCmd, debugExpose, installUiDebug, withDebug } from './debug';
import { GlowText } from './glow';
import {
  ICON,
  NinePanel,
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
} from './kit';
import { keyTaken, takeKey } from './keyGate';
import { UI_SCENE_KEYS } from './keys';
import { Minimap } from './Minimap';
import { BannerQueue } from './HudBanners';
import { BirthOverlay } from './HudBirth';
import { findNode, regionArtKey } from './regionView';
import { RouteMap } from './RouteMap';
import { RouteStrip } from './RouteStrip';
import { hasRoute } from './routeView';
import { ChallengePanel, InteractBubble, ResultToasts, StatusChips } from './StructureHud';
import { fill, r49Text, r61Text, routeText, uiText, warpText } from './text';
import { LAYOUT, MAP_BG_FLOORS, STRUCT } from './theme';
import { PEEK } from './themeR61';
import { TutorialGuide } from './TutorialHud';
import { DENY_KEY, WarpMap, roomName } from './WarpMap';
import { HudNarrative } from './HudNarrative';

/** 노드를 고르거나 고르기를 취소한 뒤 '고를 차례인데 지도가 없음' 안전망을 쉬는 시간 (ms) — 스냅샷이 따라올 때까지 */
const ROUTE_CANCEL_SUPPRESS_MS = 1500;

/** 가운데 배너 깊이 (자막과 같은 층 — StoryHud STORY_UI.depth) */
const CAPTION_DEPTH = 50;
/**
 * 47라운드 구조물 메뉴 id (계약 §9.4) + 60라운드 §14.7 게임 중 메뉴(저주 2택·이벤트·지도 장수·소모품 바꾸기) —
 * 시스템이 메뉴 씬을 띄우지 않았을 때의 안전망에 쓴다
 */
const STRUCTURE_MENU_IDS: ReadonlySet<string> = new Set<UiStructureMenuId | UiBuildMenuId>([
  'cards',
  'exchange',
  'pawn',
  'grave',
  'ledger',
  'counter',
  'curse',
  'event',
  'mapInfo',
  'consumableSwap',
]);

/**
 * 게임 위에 병렬로 떠 있는 HUD (41라운드 키트 적용). 매 프레임 STATE 스냅샷으로 갱신.
 * 61라운드 P10 다이어트: 전투 중 크게 보이는 것은 왼쪽 아래 전투 묶음(`CombatHud` — 체력·고유 자원 하나·독주·소모품·전표)뿐.
 * 보스 막대는 아래 가운데, 자막·완벽 성공 문구는 그 위(`centerBottom`). 상단 좌 층 제목(흐림)·구조물 상태 칩·빌드 띠(한 줄로 접음),
 * 상단 우 미니맵/노드 띠 + 'M 지도'. 우하단 공지·토스트.
 * Tab: 노드 지도 층·무기 시험장에서는 누르고 있는 동안 빌드 보기(`BuildPeek`, 게임은 안 멈춤), 그 밖의 층은 워프 지도(45라운드).
 * M = 지도(§11.3). 무기 시험장(`lab`)에서는 좌상단에 '무기 시험장 · L 무기 고르기 · Esc 일기장', 우상단 지도·안내는 숨긴다.
 * 60라운드(계약 §14): 빌드 띠·엘리트 이름표·성과 칩·도장 카드·완벽 성공 문구와 §14.11 알림은 `BuildLayer`.
 * 배너 차례·지역 카드는 `BannerQueue`(HudBanners.ts).
 */
export class HudScene extends Phaser.Scene {
  private built = false;
  private alive = false;
  private stageIndex = -1;
  private glows: GlowText[] = [];
  private handlers: [string, (p: never) => void][] = [];
  private pending?: UiSnapshot;

  /** 61라운드 P10: 왼쪽 아래 전투 묶음 */
  private combat?: CombatHud;
  /**
   * 61라운드 단계 2·3: STORY 자막 차례(자막·공지·원한의 한마디·군주 대사·이벤트 문장·조사 쪽지)·신규 적 소개 +
   * 보스 막대(국면 눈금)·이름·국면·파훼·처치 카드·촛대 안내 (HudNarrative.ts)
   */
  private narr?: HudNarrative;
  private growthLayer?: GrowthLayer;
  /** 61라운드 P10: Tab 빌드 보기 (누르고 있는 동안) */
  private peek?: BuildPeek;
  /** 61라운드 P1: 무기 시험장 아래 가운데 4동사 키캡 안내 */
  private labGuide?: KeyGuide;
  /** 57·60라운드 §14: 빌드 띠·완벽 성공·엘리트 이름표·성과 칩·도장 카드 */
  private buildLayer?: BuildLayer;
  /** 53라운드: 튜토리얼 안내 패널·적 등장 경고 */
  private guide?: TutorialGuide;
  /** 61라운드 플레이 점검 #2: '싸우는 법' 패널이 게임을 멈춘 중 (PAUSED 가 와도 일기장을 띄우지 않는다) */
  private guidePaused = false;
  private labMode = false;
  // 상단
  private floorText!: GlowText;
  private minimap!: Minimap;
  // 공지
  private noticePanel!: NinePanel;
  private noticeIcon!: Phaser.GameObjects.Image;
  private noticeText!: GlowText;
  private noticeKind = '';
  // 배너 (배너 차례·지역 카드는 HudBanners.ts, 자막은 StoryHud.ts)
  private banners!: BannerQueue;
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
  private birth!: BirthOverlay;
  /** 50라운드: 큰 그림 미리 읽기 표시 */
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
    this.birth = new BirthOverlay(this, {
      onStart: () => {
        this.closeWarp(false);
        this.closeRoute(false);
        // 같은 프레임에 먼저 온 진입 이벤트로 지역 카드가 떴으면 거두고 연출 뒤로 미룬다
        this.banners.holdRegion();
      },
      onEnd: () => {
        // 연출 중 미뤄 둔 자막(StoryHud 차례)·배너
        this.narr?.story.tick(false);
        this.banners.next();
      },
    });
    this.banners = new BannerQueue(this, () => this.built && !this.birth.active, CAPTION_DEPTH);
    this.narr = new HudNarrative(this, {
      canRun: () => this.built && !this.birth.active,
      menuOpen: () => this.scene.isActive(UI_SCENE_KEYS.MENU),
      combat: () => this.combat,
      stageIndex: () => Math.max(0, this.stageIndex),
      takeTutorialNotice: (text) =>
        this.built &&
        Boolean(
          this.guide?.takeNotice(
            { kind: 'notice', text },
            withDebug(uiCommands.getUiSnapshot()),
            Math.max(0, this.stageIndex),
          ),
        ),
    });
    this.prefetchSig = '';
    installUiDebug(this);
    this.on(UI_EVENTS.STATE, (s: UiSnapshot) => this.render(withDebug(s)));
    this.on(UI_EVENTS.WEAPON_EVOLVED, (p: { name: string }) =>
      this.banners.text(fill(uiText('hud', 'evolvedBanner', '{name}'), { name: p.name })),
    );
    this.on(UI_EVENTS.STAGE_STARTED, (p: { stageName: string }) => this.banners.text(p.stageName));
    // 61 단계 2·3: STORY 자막 차례·보스 카드·신규 적 소개 (HudNarrative.ts)
    this.narr.subscribe((e, h) => this.on(e, h));
    // 61 단계 4 P12 무기 성장: 각성 게이지 반짝 · 각성 배너 · 개성 알림 (GrowthHud.ts)
    this.growthLayer = new GrowthLayer(this, {
      gain: (now) => this.combat?.growthGain(now),
      snapshot: () => withDebug(uiCommands.getUiSnapshot()),
    });
    this.growthLayer.subscribe((e, h) => this.on(e, h));
    // 53라운드 계약: 튜토리얼 단계 카드 · 적 등장 예고('주의' 경고, Q49·Q60)
    this.on(UI_EVENTS.TUTORIAL_STEP, (p: unknown) => this.onTutorialStep(p));
    this.on(UI_EVENTS.ENEMY_INCOMING, (p: unknown) => this.guide?.enemyIncoming(p, Math.max(0, this.stageIndex)));
    this.on(UI_EVENTS.PAUSED, () => {
      // 워프 지도·노드 지도·'싸우는 법' 패널이 연 정지면 일시정지 일기장을 띄우지 않는다
      if (this.warpMap || this.routeMap || this.guidePaused) return;
      if (!this.scene.isActive(UI_SCENE_KEYS.PAUSE)) this.scene.launch(UI_SCENE_KEYS.PAUSE);
    });
    // Esc 는 Key 폴링(JustDown) 대신 keydown 이벤트로 받는다 — 씬이 바뀌는 프레임에 Key 상태가 눌린 채 남아
    // 다음 Esc 가 '반복 입력' 으로 취급돼 무시되는 문제가 있었다 (41라운드 헤드리스 검증)
    this.input.keyboard?.on('keydown-ESC', this.onEsc);
    this.input.keyboard?.on('keydown-ENTER', this.onEnter);
    // 45라운드 Q9: Tab 워프 지도. 브라우저 포커스 이동을 막도록 캡처한다
    this.input.keyboard?.addCapture('TAB');
    this.input.keyboard?.on('keydown-TAB', this.onTabDown);
    this.input.keyboard?.on('keyup-TAB', this.onTabUp);
    // 49라운드: M = 지도 + 현재 위치·위치 정보 (계약 §11.3). 음소거는 Esc 일기장으로 옮겼다
    this.input.keyboard?.on('keydown-M', this.onTab);
    // 61라운드: 창이 포커스를 잃으면 Tab 을 뗀 것으로 (빌드 보기가 남지 않게)
    this.game.events.on(Phaser.Core.Events.BLUR, this.onTabUp);
    this.on(UI_EVENTS.WARP_DENIED, (p: UiWarpDenied) => this.onWarpDenied(p));
    this.on(UI_EVENTS.WARP_DONE, (p: UiWarpDone) => this.toast(fill(warpText('warpDone'), { room: roomName(p.type) })));
    this.on(UI_EVENTS.RESUMED, () => {
      if (this.guidePaused) {
        this.guidePaused = false;
        this.guide?.closeQuiet();
      }
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
      this.banners.region(findNode(s.route, p?.id), s);
      if (p?.name) this.banners.text(p.name);
    });
    this.on(UI_EVENTS.BIRTH_STARTED, () => this.startBirth());
    this.on(UI_EVENTS.BIRTH_DONE, () => {
      // 탄생 노드의 진입 이벤트가 없었어도 첫 지역 카드는 탄생 연출이 끝난 뒤에
      const s = withDebug(uiCommands.getUiSnapshot());
      this.banners.region(findNode(s.route, s.route?.currentId), s);
      this.endBirth();
    });
    this.on(UI_EVENTS.RUN_ENDED, () => {
      this.guide?.reset();
      this.banners.endRun();
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
    // 57·60라운드 §14.11: 빌드 축·2차 묶음 알림 (모두 연출용 — 값은 STATE 로도 온다)
    this.on(UI_EVENTS.TAG_SET_CHANGED, (p: UiTagSetChanged) => this.buildLayer?.tagSetChanged(p));
    this.on(UI_EVENTS.CURSE_GAINED, (p: UiCurse) => this.buildLayer?.curseGained(p));
    this.on(UI_EVENTS.CURSE_ENDED, (p: UiCurseEnded) => this.buildLayer?.curseEnded(p));
    this.on(UI_EVENTS.PERFECT_SUCCESS, (p: UiPerfectSuccess) => this.buildLayer?.perfect(p));
    this.on(UI_EVENTS.NODE_GRADED, (p: UiNodeGraded) =>
      this.buildLayer?.nodeGraded(p, this.scene.isActive(UI_SCENE_KEYS.MENU)),
    );
    this.on(UI_EVENTS.HIDDEN_NODE_FOUND, () => this.buildLayer?.hiddenFound());
    this.on(UI_EVENTS.CONSUMABLE_USED, (p: UiConsumableUsed) => this.buildLayer?.consumableUsed(p));
    this.on(UI_EVENTS.RUN_ENDED, () => this.buildLayer?.reset());
    this.events.once('shutdown', () => {
      this.input.keyboard?.off('keydown-ESC', this.onEsc);
      this.input.keyboard?.off('keydown-ENTER', this.onEnter);
      this.input.keyboard?.off('keydown-TAB', this.onTabDown);
      this.input.keyboard?.off('keyup-TAB', this.onTabUp);
      this.input.keyboard?.off('keydown-M', this.onTab);
      this.input.keyboard?.removeCapture('TAB');
      this.game.events.off(Phaser.Core.Events.BLUR, this.onTabUp);
      this.combat = undefined;
      this.narr?.destroy();
      this.narr = undefined;
      this.growthLayer?.destroy();
      this.growthLayer = undefined;
      this.labGuide = undefined;
      this.peek?.destroy();
      this.peek = undefined;
      this.buildLayer?.destroy();
      this.buildLayer = undefined;
      this.guide?.destroy();
      this.guide = undefined;
      this.warpMap?.destroy();
      this.warpMap = undefined;
      this.routeMap?.destroy();
      this.routeMap = undefined;
      this.routeStrip = undefined;
      this.endBirth();
      this.banners.destroy();
      this.bubble = undefined;
      this.chips = undefined;
      this.toasts = undefined;
      this.challenge = undefined;
      this.alive = false;
      this.built = false;
      for (const [e, h] of this.handlers) uiBus.off(e, h);
      this.handlers = [];
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
    if (this.birth.active) return;
    // 지역 카드는 같은 Esc 의 keydown 으로 이미 건너뛰기를 받았다
    if (this.banners.regionOpen) return;
    // 메뉴·일시정지 씬이 같은 Esc 로 이미 동작했으면(그 씬이 닫힌 뒤 다시 넘어온 이벤트 포함) 넘긴다 (keyGate.ts)
    if (keyTaken(e)) return;
    if (this.guide?.panelOpen) {
      takeKey(e);
      this.guide.dismiss('Escape');
      return;
    }
    // 61 단계 2: 조사 쪽지 덮기
    if (this.narr?.story.noteOpen) {
      takeKey(e);
      this.narr.story.closeNote();
      return;
    }
    if (this.routeMap) {
      if (this.routeMap.mode === 'view') {
        // 보기 모드는 닫고 재개
        takeKey(e);
        this.closeRoute(false);
        this.resumeAfterRelease('Escape');
      } else if (this.routeMap.confirmOpen) {
        // '넘어가시겠습니까?' 확인 창은 같은 Esc 를 '아니오'로 받는다 (RouteMap 이 이 처리기 다음에 받는다).
        // 확인 창이 닫힌 뒤 같은 Esc 가 다시 넘어와 고르기까지 취소하지 않게 여기서 소비한다 (keyGate.ts)
        takeKey(e);
      } else if (takeKey(e)) this.cancelRouteChoose();
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

  /** Enter: 튜토리얼 안내 닫기 · 조사 쪽지 덮기 */
  private onEnter = (e?: KeyboardEvent): void => {
    if (keyTaken(e)) return;
    if (this.guide?.panelOpen) {
      takeKey(e);
      this.guide.dismiss('Enter');
    } else if (this.narr?.story.noteOpen) {
      takeKey(e);
      this.narr.story.closeNote();
    }
  };

  /**
   * 지도를 Esc 로 닫을 때 재개를 키를 뗀 다음 프레임으로 미룬다. 누르는 프레임에 재개하면 게임 씬이 같은 Esc 를 받아
   * 일시정지 일기장이 열렸다 (48라운드 헤드리스 확인, 45라운드 워프 지도도 같은 증상).
   */
  private resumeAfterRelease(key: string): void {
    this.afterRelease(key, () => uiCommands.resume());
  }

  /**
   * 53라운드 Q47: 노드 고르기 중 Esc — 지도를 닫고 `cancelChoose()` (주인공이 출구에서 한 걸음 물러나는 것은 시스템 몫).
   * 취소는 재개와 같은 까닭으로 Esc 를 뗀 다음 프레임에 보낸다(취소로 풀린 게임 입력이 누르고 있는 Esc 를 받지 않게).
   * 그 사이 스냅샷의 `route.choosing` 이 아직 true 라도 안전망이 지도를 다시 열지 않게 잠깐 막는다.
   * 취소가 거부되면(이미 고르는 중이 아님) 그대로 둔다 — 다시 출구에 들어서면 ROUTE_CHOOSE_OPEN 이 다시 온다.
   */
  private cancelRouteChoose(): void {
    this.closeRoute(false);
    this.chooseSuppressUntil = this.time.now + ROUTE_CANCEL_SUPPRESS_MS;
    this.afterRelease('Escape', () => {
      const ok = cancelChooseCmd();
      debugExpose('routeCancel', { ok, at: this.time.now });
    });
  }

  /** 키를 뗀 다음 프레임에 `fn` (떼는 입력을 놓쳐도 1초 뒤). 그때 워프·노드 지도가 다시 떠 있거나 씬이 꺼졌으면 하지 않는다 */
  private afterRelease(key: string, fn: () => void): void {
    const kb = this.input.keyboard;
    if (!kb) {
      fn();
      return;
    }
    let done = false;
    const go = (): void => {
      if (done) return;
      done = true;
      kb.off('keyup', onUp);
      this.time.delayedCall(0, () => {
        if (this.alive && !this.warpMap && !this.routeMap) fn();
      });
    };
    const onUp = (e: KeyboardEvent): void => {
      if (e.key === key) go();
    };
    kb.on('keyup', onUp);
    // 떼는 입력을 놓쳐도 멈춘 채 남지 않게
    this.time.delayedCall(1000, go);
  }

  /** 61라운드: Tab 빌드 보기를 쓰는 곳 (노드 지도 층·무기 시험장). 그 밖의 층은 Tab = 워프 지도 */
  private peekMode(s: UiSnapshot): boolean {
    return Boolean(s.lab) || hasRoute(s.route);
  }

  /**
   * 61라운드 P10: Tab 누름 — 노드 지도 층·시험장이면 빌드 보기(누르고 있는 동안, 게임은 멈추지 않는다), 그 밖은 워프 지도(onTab).
   * 메뉴·일시정지·지도·탄생 연출 중에는 열지 않는다.
   */
  private onTabDown = (e?: KeyboardEvent): void => {
    if (!this.built) return;
    const s = withDebug(uiCommands.getUiSnapshot());
    if (!this.peekMode(s)) {
      this.onTab(e);
      return;
    }
    if (e?.repeat || this.peek?.open) return;
    if (this.birth.active || this.overlayOpen(s)) return;
    if (!takeKey(e)) return;
    this.peek?.show(s, Math.max(0, this.stageIndex), (this.combat?.bundleTop ?? UI_SCREEN.HEIGHT) - PEEK.bottomGap);
    debugExpose('peek', { open: true });
  };

  private onTabUp = (): void => {
    if (!this.peek?.open) return;
    this.peek.hide();
    debugExpose('peek', { open: false });
  };

  /** 메뉴·지도·일시정지·결과 화면이 떠 있는가 */
  private overlayOpen(s: UiSnapshot): boolean {
    return (
      Boolean(this.warpMap) ||
      Boolean(this.routeMap) ||
      Boolean(s.menu) ||
      this.scene.isActive(UI_SCENE_KEYS.MENU) ||
      this.scene.isActive(UI_SCENE_KEYS.PAUSE) ||
      this.scene.isActive(UI_SCENE_KEYS.RESULT)
    );
  }

  /**
   * M(·워프 층의 Tab): 지도 열기·닫기 (45라운드 Q9·Q10 워프 지도, 48라운드 노드 지도, 49라운드 M = 지도 §11.3).
   * 노드 지도 층은 노드 지도(보기), 그 외 층은 워프 지도. 무기 시험장에서는 무시. 61라운드: 노드 지도 층의 Tab 은 빌드 보기.
   */
  private onTab = (e?: KeyboardEvent): void => {
    if (e?.repeat) return;
    if (this.birth.active) return;
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
      this.chooseSuppressUntil = this.time.now + ROUTE_CANCEL_SUPPRESS_MS;
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

  // ---- 탄생 연출 (48라운드 Q6, 계약 §10.3): HudBirth.ts
  private startBirth(): void {
    this.birth.start(this.built, this.stageIndex);
  }

  private endBirth(): void {
    this.birth.end();
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
    this.narr?.story.notice(text);
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

    // ---- 61라운드 P10: 왼쪽 아래 전투 묶음, Tab 빌드 보기 / 단계 3: 아래 가운데 보스 막대·보스 카드
    this.combat = new CombatHud(this, this.stageIndex);
    this.narr?.build(this.stageIndex);
    this.peek = new BuildPeek(this);
    this.labGuide = new KeyGuide(this, 0, H - 12 - 16, 'row', {
      surface: 'ink',
      stageIndex: this.stageIndex,
    }).setVisible(false);

    // ---- 상단 좌: 층 제목·시련, 그 아래 구조물 상태 칩 (47라운드)
    // 61라운드: 층 제목은 흐리게 (전투 중 시선은 왼쪽 아래 묶음으로)
    this.floorText = this.glow(E, 12, '', 'ink_faint');
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
    // 61라운드 플레이 점검 #2: '싸우는 법' 패널이 떠 있는 동안 게임을 멈춘다 (읽는 사이 맞지 않게)
    this.guidePaused = false;
    this.guide = new TutorialGuide(this, {
      onOpen: () => {
        if (this.guidePaused) return;
        this.guidePaused = true;
        uiCommands.pause();
      },
      onClose: (by) => {
        if (!this.guidePaused) return;
        const resume = (): void => {
          if (!this.guidePaused) return;
          this.guidePaused = false;
          uiCommands.resume();
        };
        // 키로 닫았으면 뗀 다음 프레임에 재개 (게임 씬이 같은 Esc 를 받아 일기장을 열지 않게 — resumeAfterRelease 와 같은 까닭)
        if (by === 'Escape' || by === 'Enter') this.afterRelease(by, resume);
        else resume();
      },
    });
    // 57·60라운드 §14: 알림은 구조물 결과 토스트·가운데 배너와 같은 자리로
    this.buildLayer = new BuildLayer(this, {
      toast: (tone, text) => this.toasts?.push({ tone, text }, Math.max(0, this.stageIndex)),
      banner: (text) => this.banners.text(text),
    });

    this.built = true;
    // 글꼴을 기다리는 동안 시작된 탄생 연출·미뤄 둔 배너
    if (this.birth.active) this.startBirth();
    else this.banners.next();
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

  private render(s: UiSnapshot): void {
    if (!this.built) {
      this.pending = s;
      return;
    }
    const si = Math.max(0, s.stageIndex);
    if (si !== this.stageIndex) {
      this.stageIndex = si;
      for (const t of this.glows) t.setStageIndex(si);
    }
    // 61라운드 P10: 왼쪽 아래 전투 묶음 (체력·고유 자원·독주·소모품·전표) + 보스 막대
    this.combat?.setStageIndex(si);
    this.combat?.render(s, this.time.now);
    this.narr?.setStageIndex(si);
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
    const overlay = this.overlayOpen(s);
    // 61 단계 3: 보스 막대(국면 눈금·무너짐)·촛대 안내 / 단계 2: 자막 차례 (막혀 있던 줄을 풀고, 전투가 시작되면 쪽지를 덮는다)
    this.narr?.render(s, this.time.now, overlay);
    // 61라운드: 다른 화면이 뜨면 Tab 빌드 보기를 거둔다
    if (overlay) this.onTabUp();
    // 61라운드 P1: 무기 시험장에서는 아래 가운데에 4동사 키캡 안내 (무기를 바꾸면 따라 바뀐다)
    if (this.labGuide) {
      const showGuide = lab && !overlay;
      this.labGuide.setVisible(showGuide);
      if (showGuide) {
        this.labGuide.setItems(snapshotVerbItems(s, (k) => r61Text(k)));
        const left = Math.max(
          (this.combat?.bundleRight ?? 0) + 12,
          Math.round(UI_SCREEN.WIDTH / 2 - this.labGuide.boxW / 2),
        );
        this.labGuide.setPosition(left, UI_SCREEN.HEIGHT - 12 - 16);
      }
    }
    this.bubble?.update(s.interactable ?? null, !overlay, si);
    this.chips?.render(s.statuses ?? [], si);
    // 57·60라운드 §14: 빌드 칩(상태 칩 아래)·엘리트 이름표·성과 칩
    this.buildLayer?.render(
      s,
      {
        stageIndex: si,
        overlay,
        chipsBottom: this.chips?.bottom() ?? STRUCT.chipTop,
        challengeOn: Boolean(this.challenge?.active),
        tabHint: this.peekMode(s),
      },
      this.narr?.centerBottom() ?? UI_SCREEN.HEIGHT,
    );
    this.challenge?.tick(s.statuses?.find((st) => st.id === 'ring') ?? null, si);
    // 53라운드: 튜토리얼 안내 — 다른 화면·배너·지역 카드·탄생 연출이 없을 때만 새로 띄운다
    const bannersIdle = this.banners.idle;
    this.guide?.update(s, !overlay && !this.birth.active && bannersIdle, si);
    // 48라운드 안전망: 고를 차례인데 지도가 없으면 연다 (이벤트를 놓쳤거나 메뉴가 닫힌 뒤)
    if (route?.choosing && !overlay && !this.birth.active && this.time.now > this.chooseSuppressUntil)
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

  /**
   * 53라운드 TUTORIAL_STEP: 단계 카드 (TutorialHud). 같은 문구의 STORY 공지가 먼저 와서 작은 자막으로 떠 있거나 쌓여 있으면 거둔다
   * (시스템이 두 가지를 함께 보내도 한 번만 보이게)
   */
  private onTutorialStep(p: unknown): void {
    if (!this.guide) return;
    const text = this.guide.takeStep(p, withDebug(uiCommands.getUiSnapshot()), Math.max(0, this.stageIndex));
    if (text === null) return;
    this.narr?.story.dropSame(text);
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
