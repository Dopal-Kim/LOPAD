import Phaser from 'phaser';
import {
  CAMERA,
  COLORS,
  DEBUG,
  DEPTH,
  ENEMY_INCOMING,
  GAME,
  PROTOTYPE,
  SCENES,
  TILE,
  WEAPON_LOAD,
} from '../core/Constants';
import { screenFixed, worldZoom } from '../systems/display';
import { EventBus, Events } from '../core/EventBus';
import { gameState } from '../core/GameState';
import { floorText } from '../systems/story';
import type { Mob } from '../objects/Mob';
import { Player } from '../objects/Player';
import { Projectile } from '../objects/Projectile';
import { Pickup } from '../objects/Pickup';
import { InputSystem, neutralInput } from '../systems/InputSystem';
import type { FloorLayout } from '../systems/mapgen';
import type { RouteKind, RouteNode } from '../systems/route';
import type { Lighting } from '../systems/lighting/Lighting';
import type { RoomDirector } from '../systems/RoomDirector';
import type { Rng } from '../systems/rng';
import { SaveSlot, browserStorage } from '../systems/save';
import { TextMenu } from '../systems/TextMenu';
import { UI_EVENTS, __system } from '../contract/ui';
import {
  setChooseCanceler,
  setMenuSelect,
  setNodeChooser,
  setSnapshotProvider,
  setWarpHandler,
} from '../contract/host';
import { UI_SCENES } from '../ui';
import type { TileWorld } from '../world/TileWorld';
import type { BorderView } from '../world/BorderView';
import type { SetPieceView } from '../world/SetPieceView';
import type { NodeArenaPlan } from '../systems/routeArena';
import { TutorialDirector } from '../systems/tutorialDirector';
import type { FxPool } from '../systems/fx/fx';
import { HitStop, PauseClock, Shake } from '../systems/feel';
import type { RibbonRenderer } from '../systems/fx/ribbon';
import type { AshParticles } from '../systems/fx/ashParticles';
import type { ScreenFx } from '../systems/fx/screenFx';
import type { AimLine } from '../systems/fx/aimFx';
import type { DamageNumberPool } from '../systems/fx/damageNumbers';
import type { HitFx } from '../systems/fx/hitFx';
import type { TelegraphFx } from '../systems/telegraph';
import { PackCharge } from '../systems/packCharge';
import { audio } from '../systems/audio/audio';
import { StructureSystem } from '../systems/structures/StructureSystem';
import { LiquorPools } from '../systems/hazards/LiquorPools';
import { BossArena } from '../systems/boss/BossArena';
import { BOSSES } from '../data';
import { propSkinFor } from '../world/tileskin';
import type { StructurePlacement } from '../systems/structures/placement';
import { BirthFlow } from './game/BirthFlow';
import { exposeGameDebug } from './game/DebugHooks';
import { Economy } from './game/Economy';
import { createFx } from './game/FxWiring';
import { GameCamera } from './game/GameCamera';
import { GameCombat } from './game/GameCombat';
import { LabMode } from './game/LabMode';
import { MotionFx } from './game/MotionFx';
import { PlayerStrikes } from './game/PlayerStrikes';
import { Progression } from './game/Progression';
import { RouteFlow } from './game/RouteFlow';
import { WeaponFeedback } from './game/WeaponFeedback';
import { UiRelay } from './game/UiRelay';
import { WorldSetup } from './game/WorldSetup';
import { createDirector } from './game/directorHost';
import { SENSE_BONUS_MAX, urlParams, type GameInitData } from './game/shared';
import { AnchorDebug } from './game/AnchorDebug';
import { runWeaponFor } from './game/runWeapon';
import { preloadWeaponSheets } from '../systems/sprites/sheetLoader';
import { BuildRuntime } from './game/build/BuildRuntime';
import { BuildMenus } from './game/build/BuildMenus';
import { BundleRuntime } from './game/bundle/BundleRuntime';

export type { GameInitData } from './game/shared';

/** EventBus 구독 한 줄: 이벤트 · 처리기 · this (shutdown 에서 같은 표로 해제) */
type Subscription = [event: string, fn: (p: never) => void, ctx: object];

/**
 * 메인 플레이 씬 (50라운드 1단계: 책임별 분리 — 구조 지도는 parts/system/README.md 50라운드 절).
 * 이 파일은 씬 생애주기(만들기·매 프레임 순서·정리)와 공유 상태만 갖고, 일은 `scenes/game/*` 모듈이 한다.
 * 모듈은 create() 마다 새로 만들어져 노드·층 재시작 때 상태가 깨끗하다.
 */
export class Game extends Phaser.Scene {
  // --- 월드 · 개체 ---
  player: Player;
  mobs: Phaser.Physics.Arcade.Group;
  projectiles: Phaser.GameObjects.Group;
  pickups: Phaser.GameObjects.Group;
  playerShots: Phaser.GameObjects.Group;
  world: TileWorld;
  layout?: FloorLayout;
  director: RoomDirector;
  /** 47라운드 상호작용 구조물 */
  structures: StructureSystem;
  /** 54라운드: 술 웅덩이·불바다 (구조물·보스방 공용) */
  pools: LiquorPools;
  /** 54라운드: 보스방 환경 (보스 정의에 arena 가 있는 보스 노드에서만) */
  bossArena: BossArena | null = null;
  inputSystem: InputSystem;
  rng: Rng;
  menu: TextMenu;
  // --- 48·49라운드 노드 지도: 노드 전투장인지 · 현재 노드(층 진입 갈림 선택 대기 중이면 null) · 설계도 · 세트 그림 · 조작 안내 ---
  routeMode = false;
  node: RouteNode | null = null;
  nodeKind: RouteKind | null = null;
  nodeArena: NodeArenaPlan | null = null;
  setPieceView: SetPieceView | null = null;
  /** 53라운드 Q6: Gemini 외벽 테두리 (그 지역에 border.json 이 있을 때) */
  border: BorderView | null = null;
  tutorial: TutorialDirector | null = null;
  // --- 연출 (35·42라운드) ---
  fx: FxPool;
  numbers: DamageNumberPool;
  hitFx: HitFx;
  telegraph: TelegraphFx;
  /** 55라운드 Q7 칼끝 잔상 리본 (42라운드 흰 리본 대체) · Q8 재 파편 입자 */
  ribbons: RibbonRenderer;
  ash: AshParticles;
  screenFx: ScreenFx;
  aimLine: AimLine;
  /** 50라운드 동적 조명 + 어둠 (지역 조명이 없으면 꺼진 채) */
  lighting: Lighting;
  readonly hitStop = new HitStop();
  /** 55라운드 Q14 ②: 히트스톱 동안 멈추는 플레이 시계 (리본·칼끝·입자) */
  readonly playClock = new PauseClock();
  readonly shake = new Shake();
  /** 적 집단 돌격 공유 상태 */
  readonly pack = new PackCharge();
  // --- 진행 상태 ---
  /** 개성 3지선다·엔딩 선택·시험장 메뉴 중: 게임 진행(이동·적·물리) 정지 */
  frozen = false;
  hitStopped = false;
  transitioning = false;
  visitedRooms = new Set<string>();
  clearedRooms = new Set<string>();
  readonly saveSlot = new SaveSlot(browserStorage());
  /** 49라운드 계약 §11.4 무기 시험장 모드 (씬 키 WeaponLab — scenes/WeaponLab.ts) */
  readonly lab: boolean;
  // --- 책임별 모듈 (scenes/game/*) ---
  cam: GameCamera;
  combat: GameCombat;
  strikes: PlayerStrikes;
  motion: MotionFx;
  progress: Progression;
  economy: Economy;
  route: RouteFlow;
  birth: BirthFlow;
  labMode: LabMode | null = null;
  ui: UiRelay;
  /** 56라운드 무기 피드백 연출 (월드 문구·숨 집중·과열 낙인 폭발) */
  feedback: WeaponFeedback;
  /** 57라운드 빌드 축: 태그 세트·패시브 규칙·이중 개성·갈래 수단·각성·저주 (런 상태는 gameState.build) · 선택 메뉴 */
  build: BuildRuntime;
  buildMenus: BuildMenus;
  /** 60라운드 2차 묶음: 노드 보상·위험·성소·등급·이벤트·숨은 노드·상점 진열·엘리트·소모품·보스 파훼 (런 상태는 gameState.bundle) */
  bundle: BundleRuntime;

  initData: GameInitData = {};
  private senseBonus = 0;
  private debugText?: Phaser.GameObjects.Text;
  /** 52라운드 `?anchors`: v3 손·칼 앵커 표시 */
  private anchorDebug: AnchorDebug | null = null;
  private subs: Subscription[] = [];
  private readonly playerVec = new Phaser.Math.Vector2();

  /** key·lab 은 무기 시험장(WeaponLab)이 넘긴다. 일반 게임은 인자 없이 */
  constructor(key: string = SCENES.GAME, lab = false) {
    super(key);
    this.lab = lab;
  }

  init(data?: GameInitData): void {
    this.initData = { ...(data ?? {}) };
    this.senseBonus = Phaser.Math.Clamp(Math.floor(Number(data?.senseBonus) || 0), 0, SENSE_BONUS_MAX);
    this.transitioning = false;
  }

  /**
   * 57라운드 A2: 런 무기의 시트만 로드 (새 런·이어하기·시험장 무기 교체 — 같은 무기의 다음 노드는 아무것도 안 함).
   * 전환 암전 안에서 짧게 '불러오는 중' 을 보이고 로드가 끝나면(create 전) 지운다
   */
  preload(): void {
    // 60라운드: 같은 런의 각성 런이면 각성 외형 오버레이도 (새 런은 아님 — 이어하기는 create 에서 BuildRuntime 이)
    const awaken = this.initData.mode !== 'new' && gameState.build.awakened;
    if (!preloadWeaponSheets(this, runWeaponFor(this.initData, this.lab, this.saveSlot), awaken)) return;
    const at = screenFixed(this.cameras.main, GAME.WIDTH / 2, GAME.HEIGHT / 2);
    const label = this.add
      .text(at.x, at.y, WEAPON_LOAD.TEXT, { font: WEAPON_LOAD.FONT, color: WEAPON_LOAD.COLOR })
      .setOrigin(0.5)
      .setScale(at.scale)
      .setScrollFactor(0)
      .setDepth(DEPTH.DEBUG);
    this.load.once(Phaser.Loader.Events.COMPLETE, () => label.destroy());
  }

  create(): void {
    this.cam = new GameCamera(this);
    this.combat = new GameCombat(this);
    this.strikes = new PlayerStrikes(this);
    this.motion = new MotionFx(this);
    this.progress = new Progression(this);
    this.economy = new Economy(this);
    this.birth = new BirthFlow(this);
    this.ui = new UiRelay(this);
    this.feedback = new WeaponFeedback(this);
    this.labMode = this.lab ? new LabMode(this, this.initData) : null;
    this.frozen = false;
    this.hitStopped = false;
    this.time.paused = false;
    this.playClock.reset();

    // 49라운드: 무기 시험장은 런·세이브와 무관한 연습 런으로 시작한다
    const floorStart = this.labMode
      ? this.labMode.prepareRun()
      : this.progress.prepareRun(this.initData, this.senseBonus);
    const floor = gameState.stageIndex + 1;
    const worldSetup = new WorldSetup(this);
    const nodeSalt = worldSetup.enterRoute(floor, this.initData.slice);
    const structurePlan = worldSetup.buildWorld(floor, nodeSalt);

    // 플레이어 (노드 진행 상태는 플레이어 뒤 — 48라운드 노드 씬 초기화 순서)
    const layout = this.layout!;
    const start = layout.arena
      ? new Phaser.Math.Vector2((layout.arena.spawn.x + 0.5) * TILE, (layout.arena.spawn.y + 0.5) * TILE)
      : this.world.roomCenter(layout.rooms.find((r) => r.type === 'start')!);
    this.player = new Player(this, start.x, start.y);
    this.route = new RouteFlow(this);
    // 57라운드 빌드 축 (bindEvents 보다 먼저 — 공격 페이로드의 갈래 한 타 변화를 판정보다 먼저 건다)
    this.buildMenus = new BuildMenus(this);
    this.build = new BuildRuntime(this);
    this.player.buildHooks = this.build.defense;

    this.createActors();
    createFx(this, floor);
    // 55라운드 Q14 ②: 지연 효과음(휘두름 소리)도 씬 시계로 — 히트스톱 동안 함께 멈춘다
    audio.setDelayScheduler((ms, fire) => this.time.delayedCall(ms, fire));
    this.menu = new TextMenu(this);
    this.wirePhysics();

    // 방 상태 머신 (scenes/game/directorHost)
    this.director = createDirector(this);
    if (gameState.route && this.routeMode) this.route.syncProgress();
    this.createTutorial();
    this.pools = new LiquorPools({
      scene: this,
      player: this.player,
      mobs: this.mobs,
      fx: this.fx,
      hitMob: (m, dmg, o) => this.combat.hitMob(m, dmg, o),
      onKill: (m, kind) => this.progress.onKill(m, kind),
    });
    this.createStructures(structurePlan);
    this.bundle = new BundleRuntime(this);
    this.createBossArena();
    this.inputSystem = new InputSystem(this);

    // 계약: 스냅샷 제공, 메뉴 선택 라우팅, HUD 병렬 실행
    setSnapshotProvider(() => this.ui.snapshot());
    setMenuSelect((id, key) => this.menu.select(key, id));
    setWarpHandler({ check: () => this.ui.warpDeny(), run: () => this.ui.warpDeny() });
    setNodeChooser((id) => this.route.chooseNode(id));
    setChooseCanceler(() => this.route.cancelChoose());
    if (this.scene.manager.keys[UI_SCENES.HUD] && !this.scene.isActive(UI_SCENES.HUD)) this.scene.launch(UI_SCENES.HUD);
    // 층 시작만 (같은 층의 다음 노드는 ROUTE_NODE_ENTERED)
    if (floorStart) {
      __system.emit(UI_EVENTS.STAGE_STARTED, {
        stageIndex: gameState.stageIndex,
        stageName: floorText(gameState.stageId)?.title ?? gameState.stage.name,
      });
      this.ui.story('floor', floorText(gameState.stageId)?.enter ?? '');
    }

    exposeGameDebug(this);
    this.bindEvents();
    this.events.once('shutdown', this.cleanup, this);
    this.events.on(Phaser.Scenes.Events.POST_UPDATE, this.renderLate, this);

    // 48라운드 Q1: 게임 월드 카메라 확대 (UI 씬은 자기 카메라라 무관)
    this.cameras.main.setRoundPixels(true);
    this.cameras.main.setZoom(worldZoom(CAMERA.ZOOM));
    this.cam.update(true);
    this.lighting = worldSetup.createLighting();
    if (this.routeMode) {
      this.route.enterNode();
      this.bundle.onEnter(this.route.enterLockUntil);
    }
    this.labMode?.setup();
    this.createDebugText();
    this.anchorDebug = urlParams().has('anchors') ? new AnchorDebug(this) : null;
  }

  // --- create 단계 ---

  /** 적·투사체·드랍 풀 */
  private createActors(): void {
    this.mobs = this.physics.add.group({ runChildUpdate: false });
    const pool = (classType: typeof Projectile | typeof Pickup, maxSize: number) =>
      this.add.group({ classType, maxSize, runChildUpdate: false });
    this.projectiles = pool(Projectile, PROTOTYPE.PROJECTILE_POOL);
    this.pickups = pool(Pickup, PROTOTYPE.PICKUP_POOL);
    this.playerShots = pool(Projectile, PROTOTYPE.PROJECTILE_POOL);
  }

  private wirePhysics(): void {
    for (const layer of this.world.collisionLayers) {
      this.physics.add.collider(this.player, layer);
      this.physics.add.collider(this.mobs, layer);
    }
    const c = this.combat;
    this.physics.add.collider(this.mobs, this.mobs);
    this.physics.add.overlap(this.player, this.mobs, (_p, m) => c.onMobTouch(m as Mob));
    this.physics.add.overlap(this.player, this.projectiles, (_p, pr) => c.onProjectileHit(pr as Projectile));
    this.physics.add.overlap(this.projectiles, this.mobs, (pr, m) => c.onReflectedHit(pr as Projectile, m as Mob));
    this.physics.add.overlap(this.player, this.pickups, (_p, pk) => this.economy.onPickup(pk as Pickup));
    this.physics.add.overlap(this.playerShots, this.mobs, (pr, m) => c.onPlayerShotHit(pr as Projectile, m as Mob));
  }

  /** 49라운드 3: 탄생 전장 조작 안내 (표식 → 이동·공격·대쉬·보조 동작 → 약한 적 → 출구) */
  private createTutorial(): void {
    this.tutorial?.destroy();
    this.tutorial = null;
    const tut = this.nodeArena?.tutorial;
    if (!tut || !this.nodeArena) return;
    const sec = gameState.weapon.def.secondary;
    const roomId = this.layout!.rooms[0].id;
    const sp = this.nodeArena.setPiece;
    this.tutorial = new TutorialDirector(
      tut,
      { center: sp.center, signs: sp.signs, dummies: sp.dummies },
      {
        notice: (text) => this.ui.story('notice', text),
        // 53라운드 Q49: 튜토리얼 적은 예고(ENEMY_INCOMING) 뒤 잠시 있다가 나온다
        startFight: (spawns, at, onDone) =>
          this.director.startChallenge(roomId, spawns, onDone, at, ENEMY_INCOMING.TUTORIAL_DELAY_MS),
        step: (info) => this.ui.tutorialStep(info),
        highlightSign: (i) => this.setPieceView?.highlightSign(i),
        pokeDummy: (i) => this.setPieceView?.pokeDummy(i),
      },
      {
        ranged: gameState.weapon.def.kind === 'ranged',
        vars: { name: sec.name, description: ('description' in sec ? sec.description : undefined) ?? '' },
      },
    );
    if (urlParams().has('notutorial')) this.tutorial.skip();
  }

  private createStructures(plan: StructurePlacement[]): void {
    this.structures = new StructureSystem(
      {
        scene: this,
        world: this.world,
        director: this.director,
        player: this.player,
        mobs: this.mobs,
        menu: this.menu,
        fx: this.fx,
        pools: this.pools,
        rng: this.rng,
        stageId: gameState.stageId,
        addGold: (n) => this.economy.addGold(n),
        spendGold: (n) => this.economy.spendGold(n),
        spawnPickup: (x, y, kind, value) => this.economy.spawnPickup(x, y, kind, value),
        gainPersonality: (n) => this.progress.gainPersonality(n),
        heal: (n) => this.player.heal(n),
        hitMob: (m, dmg, o) => this.combat.hitMob(m, dmg, o),
        onKill: (m, kind) => this.progress.onKill(m, kind),
        potionCarry: () => this.economy.potionCarry,
        isBusy: () =>
          this.frozen ||
          this.transitioning ||
          this.menu.isOpen ||
          gameState.rewardPending ||
          gameState.gameOver ||
          gameState.cleared,
        openStatChooser: () => {
          if (gameState.pointsPending > 0) this.progress.openStatChooser(() => {});
        },
        story: (kind, text) => this.ui.story(kind, text),
        nodeMode: this.routeMode,
        // 57라운드 빌드 축: 구조물 저주 줄 · 궤짝 2택
        build: {
          curseLine: (kind, key) => this.buildMenus.structureCurseLine(kind, key),
          grantCurse: (kind) => this.buildMenus.grantStructureCurse(kind),
          chestPick: (onDone) => this.buildMenus.openPassiveMenu('chest', {}, onDone),
        },
      },
      plan,
    );
    // 48라운드: 앞 노드의 층 상태(빚·취기·판돈·불씨 등)를 이어받는다
    if (this.routeMode) this.structures.importFloorState(gameState.structureCarry);
  }

  /** 54라운드: 보스 노드 + 보스 정의에 arena 가 있으면 보스방 환경 (기둥·촛대·술통·술·화면 효과) */
  private createBossArena(): void {
    this.bossArena?.destroy();
    this.bossArena = null;
    const id = gameState.stage.boss;
    const def = BOSSES[id];
    if (this.nodeKind !== 'boss' || !def?.arena || !this.nodeArena) return;
    const sp = this.nodeArena.setPiece;
    this.bossArena = new BossArena(
      {
        scene: this,
        world: this.world,
        player: this.player,
        mobs: this.mobs,
        fx: this.fx,
        pools: this.pools,
        lighting: () => this.lighting ?? null,
        hitMob: (m, dmg, o) => this.combat.hitMob(m, dmg, o),
        onKill: (m, kind) => this.progress.onKill(m, kind),
        shake: (px, ms) => this.shake.add(this.time.now, px, ms),
        propSkin: propSkinFor(this.nodeArena.tileset),
      },
      id,
      def,
      { pillars: sp.pillars, candles: sp.candles, centerX: (sp.center.x + 0.5) * TILE },
    );
  }

  private bindEvents(): void {
    const { strikes: s, progress: p, combat: c, ui, motion: m, feedback: f } = this;
    this.subs = [
      [Events.PLAYER_ATTACKED, s.onPlayerAttacked, s],
      [Events.PLAYER_CHARGE, s.onPlayerCharge, s],
      [Events.PLAYER_DIED, p.onPlayerDied, p],
      [Events.TRIAL_CLEARED, p.onTrialCleared, p],
      [Events.ROOM_ENTERED, ui.onRoomEntered, ui],
      [Events.PLAYER_DAMAGED, c.onPlayerDamaged, c],
      [Events.BOSS_WALL_HIT, c.onBossWallHit, c],
      [Events.PLAYER_HEALED, ui.relayHealed, ui],
      [Events.GOLD_CHANGED, ui.relayGold, ui],
      [Events.WEAPON_EVOLVED, ui.relayEvolved, ui],
      [Events.BOSS_STARTED, ui.relayBossStarted, ui],
      [Events.BOSS_PHASE, ui.relayBossPhase, ui],
      [Events.BOSS_DIED, ui.relayBossDied, ui],
      [Events.PLAYER_GUARD_RELEASED, m.onGuardReleased, m],
      [Events.PLAYER_SHADOW_STEP, m.onShadowStep, m],
      [Events.PLAYER_DASHED, m.onPlayerDashed, m],
      [Events.ENEMY_INCOMING, ui.relayEnemyIncoming, ui],
      [Events.PLAYER_PERFECT_GUARD, f.onPerfectGuard, f],
      [Events.PLAYER_PARRIED, f.onParried, f],
      [Events.WEAPON_GAUGE, f.onGauge, f],
      [Events.WEAPON_RESOURCE, f.onResource, f],
      // 56라운드 2단계 새 기본기: 화살비 · 준비 반짝임 · 슈퍼아머 흡수
      [Events.PLAYER_ARROW_RAIN, s.rain.start, s.rain],
      [Events.PLAYER_SKILL, s.moves.onSkill, s.moves],
      [Events.PLAYER_DAMAGED, s.moves.onPlayerDamaged, s.moves],
    ];
    for (const [event, fn, ctx] of this.subs) EventBus.on(event, fn, ctx);
  }

  private createDebugText(): void {
    this.debugText = undefined;
    if (!DEBUG.SHOW_TEXT || !urlParams().has('debugtext')) return;
    // 카메라 확대(48라운드)는 scrollFactor 0 개체도 화면 가운데 기준으로 키운다 → 역배율·역위치로 논리 화면 (4,4)
    const at = screenFixed(this.cameras.main, 4, 4);
    this.debugText = this.add
      .text(at.x, at.y, '', {
        font: DEBUG.FONT,
        color: COLORS.DEBUG_TEXT,
      })
      .setScale(at.scale)
      .setScrollFactor(0)
      .setDepth(DEPTH.DEBUG);
  }

  /** 플레이 시계 ms (히트스톱 동안 멈춘 시간을 뺀 씬 시계) */
  playNow(): number {
    return this.playClock.now(this.time.now);
  }

  // --- 매 프레임 ---

  update(time: number, delta: number): void {
    if (gameState.gameOver || gameState.cleared) return;

    // 48라운드 Q6 탄생 연출: 조작 잠금, 카메라 배율은 연출이 정한다. 아무 키로 건너뛰기 (keydown·pointerdown)
    if (this.birth.active) {
      this.birth.update(time);
      this.fx.update(time);
      this.ash.update(this.playNow());
      this.screenFx.update(time);
      this.ui.emitState();
      return;
    }

    // 개성 임계 도달 → 다른 메뉴(보스 보상 등)가 닫힌 뒤 3지선다 (게임 정지)
    this.progress.maybeOpenEvolveMenu();
    if (this.frozen) {
      this.inputSystem.read(); // 큐 비우기
      this.motion.stopLoops();
      this.fx.update(time);
      this.ribbons.update();
      this.ash.update(this.playNow());
      this.screenFx.update(time);
      this.ui.emitState();
      return;
    }

    // 히트스톱(35라운드): 물리·개체 애니·적 AI·입력 소비를 멈추고 카메라 흔들림·데미지 숫자·UI 만 진행
    const stopped = this.hitStop.active(time);
    if (stopped !== this.hitStopped) this.setHitStopped(stopped);
    if (stopped) {
      this.cam.update(false, delta);
      this.screenFx.update(time);
      this.ui.emitState();
      return;
    }

    const raw = this.inputSystem.read();
    // 구조물 메뉴 동안 입력 잠금 (47라운드 계약 §9.3) · 48라운드: 노드 진입 직후(밝아지는 동안)·다음 노드 선택 중·전환 중에도 잠금
    let input = this.structures.inputLocked || this.route.locked(time) ? neutralInput(raw) : raw;
    if (input.potionPressed) this.economy.usePotion();
    this.structures.update(input, time, delta);
    this.bundle.update(input, time);
    this.pools.update(time);
    this.bossArena?.update(input, time, delta);
    input = this.structures.adjustAim(input, time);
    this.player.sprintAllowed = !this.director.inCombat;
    this.build.update(time);
    this.player.update(input, time, delta);
    this.motion.update(time);
    this.cam.update(false, delta);
    // 48라운드: 노드 진입 직후에는 전투를 시작하지 않는다 (밝아지는 동안). 49라운드 시험장은 방 상태 머신이 없다
    if (time >= this.route.enterLockUntil && !this.lab) this.director.update();
    this.labMode?.update();
    if (this.tutorial && !this.route.locked(time)) this.tutorial.update(this.player.x, this.player.y);
    if (this.routeMode) this.route.update(time);
    if (this.route.checkFloorExit()) return;

    this.updateActors(time, delta);
    this.economy.updateShop();
    this.ui.emitState();
    this.updateDebugText();
  }

  /** 적 AI · 투사체 · 드랍 · 플레이어 공격 부가 효과 · 연출 */
  private updateActors(time: number, delta: number): void {
    const c = this.combat;
    this.playerVec.set(this.player.x, this.player.y);
    const ctx = {
      time,
      delta,
      player: this.playerVec,
      fire: c.fire,
      telegraph: this.telegraph,
      playFx: c.playMobFx,
      countMobs: c.countMobs,
      areaHit: c.areaHit,
      summon: c.summon,
      pack: this.pack,
      arena: this.bossArena,
    };
    for (const child of [...this.mobs.getChildren()]) (child as Mob).update(ctx);
    this.bundle.lateUpdate(time);
    this.telegraph.update(time);
    for (const child of this.projectiles.getChildren()) (child as Projectile).tick(time);
    for (const child of this.pickups.getChildren()) (child as Pickup).tick(time);
    for (const child of this.playerShots.getChildren()) (child as Projectile).tick(time);
    this.structures.tickShots(this.playerShots.getChildren() as Projectile[]);
    this.bossArena?.tickShots(this.playerShots.getChildren() as Projectile[]);
    this.strikes.update(time, delta);
    this.fx.update(time);
    this.ribbons.update();
    this.ash.update(this.playNow());
    this.screenFx.update(time);
  }

  private updateDebugText(): void {
    if (!this.debugText) return;
    const s = gameState;
    const boss = s.bossMaxHp > 0 ? `  boss ${s.bossHp}/${s.bossMaxHp} p${s.bossPhase}` : '';
    this.debugText.setText(
      `[DEBUG] ${s.stage.name} save ${s.savesLeft}  P[${s.passives.summary() || '-'}]  HP ${s.hp}/${s.maxHp}  G ${s.gold}  potion ${s.potions}  pts ${s.pointsPending}  atk ${s.attack} def ${s.defense} crit ${s.crit}%  ${this.player.action}  sense ${s.senses.sense}  ${s.weapon.displayName} ${s.weapon.personality}/${s.weapon.threshold}  room ${s.roomId || '-'}  trials ${s.trialsCleared}/${s.trialsTotal}${s.bossUnlocked ? ' (boss open)' : ''}${boss}  seed ${s.seed}`,
    );
  }

  /** 매 프레임 마지막 (카메라 스크롤이 정해진 뒤): 조명 · 쿼터뷰 벽 가림 비침 */
  private renderLate(time: number, delta: number): void {
    if (!this.player?.active) return;
    this.lighting?.update(time);
    const p = this.player;
    this.anchorDebug?.update(p);
    const target = { x: p.x, y: p.y, w: p.displayWidth, h: p.displayHeight, depth: p.depth };
    this.world.quarter?.updateOcclusion([target]);
    this.border?.update(target, delta);
  }

  // --- 정지 ---

  /** 3지선다·엔딩 선택·시험장 메뉴 동안 게임 정지 (물리·적·플레이어). 메뉴는 UI 가 그린다 */
  setFrozen(on: boolean): void {
    if (this.frozen === on) return;
    this.frozen = on;
    this.syncPhysicsPause();
  }

  /**
   * 히트스톱 시작·끝: 물리 정지(frozen 과 합산), 플레이어·적·이펙트 애니 정지.
   * 55라운드 Q14 ②: 씬 시계의 예약 호출(판정·추가 타·효과음·리본 시작)과 플레이 시계도 멈춘다 — 끝나면 멈춘 만큼 미뤄져 이어진다
   */
  private setHitStopped(on: boolean): void {
    this.hitStopped = on;
    this.time.paused = on;
    this.playClock.setPaused(on, this.time.now);
    this.syncPhysicsPause();
    this.player.setAnimPaused(on);
    for (const m of this.mobs.getChildren() as Mob[]) m.setAnimPaused(on);
    this.fx.setPaused(on);
    this.telegraph.setPaused(on);
    this.screenFx.setHitStopped(on);
    for (const p of this.projectiles.getChildren() as Projectile[]) if (p.active) p.setAnimPaused(on);
  }

  private syncPhysicsPause(): void {
    const world = this.physics.world;
    if (!world) return;
    if (this.frozen || this.hitStopped) world.pause();
    else world.resume();
  }

  private cleanup(): void {
    this.events.off(Phaser.Scenes.Events.POST_UPDATE, this.renderLate, this);
    for (const [event, fn, ctx] of this.subs) EventBus.off(event, fn, ctx);
    this.subs = [];
    // 엔딩 선택 뒤 정지 상태로 씬이 끝나면 물리 플러그인이 먼저 정리돼 world 가 없을 수 있다
    if ((this.frozen || this.hitStopped) && this.physics.world) this.physics.world.resume();
    this.numbers.destroy();
    this.build.destroy();
    this.feedback.destroy();
    this.strikes.brands.destroy();
    this.strikes.moves.destroy();
    this.strikes.rain.destroy();
    this.telegraph.destroy();
    this.ribbons.destroy();
    this.ash.destroy();
    this.time.paused = false;
    audio.setDelayScheduler(null);
    this.screenFx.destroy();
    this.aimLine.destroy();
    this.structures.destroy();
    this.bundle.destroy();
    this.bossArena?.destroy();
    this.bossArena = null;
    this.pools.destroy();
    this.fx.destroy();
    this.lighting.destroy();
    audio.stopAllLoops();
    setMenuSelect(null);
    setSnapshotProvider(null);
    setWarpHandler(null);
    setNodeChooser(null);
    setChooseCanceler(null);
    this.birth.destroy();
    this.labMode?.destroy();
    this.tutorial?.destroy();
    this.tutorial = null;
    this.setPieceView?.destroy();
    this.setPieceView = null;
    this.border?.destroy();
    this.border = null;
    this.menu.close();
    this.inputSystem.destroy();
  }
}
