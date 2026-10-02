import Phaser from 'phaser';
import { CAMERA, COLORS, DEBUG, DEPTH, FEEL, PROTOTYPE, SCENES, TILE } from '../core/Constants';
import { EventBus, Events } from '../core/EventBus';
import { gameState } from '../core/GameState';
import { LIGHTING, PALETTE } from '../data';
import type { LightingAmbient } from '../data/types';
import { floorText } from '../systems/story';
import type { Mob } from '../objects/Mob';
import { Player } from '../objects/Player';
import { Projectile } from '../objects/Projectile';
import { Pickup } from '../objects/Pickup';
import { InputSystem, neutralInput } from '../systems/InputSystem';
import { generateFloor, type FloorLayout } from '../systems/mapgen';
import {
  RouteState,
  generateRoute,
  kindDef,
  regionIdOf,
  routeEnabled,
  type RouteKind,
  type RouteNode,
} from '../systems/route';
import { Lighting } from '../systems/lighting/Lighting';
import { RoomDirector } from '../systems/RoomDirector';
import { Rng, hashSeed } from '../systems/rng';
import { SaveSlot, browserStorage } from '../systems/save';
import { TextMenu } from '../systems/TextMenu';
import { UI_EVENTS, __system } from '../contract/ui';
import { setMenuSelect, setNodeChooser, setSnapshotProvider, setWarpHandler } from '../contract/host';
import { UI_SCENES } from '../ui';
import { TileWorld } from '../world/TileWorld';
import { TileSkin, skinFor, tileSkins } from '../world/tileskin';
import { SetPieceView } from '../world/SetPieceView';
import { planNodeArena, setPieceTiles, type NodeArenaPlan } from '../systems/routeArena';
import { TutorialDirector } from '../systems/tutorialDirector';
import { spriteLibrary } from '../systems/sprites';
import { FxPool } from '../systems/fx';
import { HitStop, Shake } from '../systems/feel';
import { TrailRenderer } from '../systems/trail';
import { ScreenFx } from '../systems/screenFx';
import { AimLine } from '../systems/aimFx';
import { resolveFxColor } from '../systems/palette';
import { DamageNumberPool } from '../systems/damageNumbers';
import { HitFx } from '../systems/hitFx';
import { TelegraphFx } from '../systems/telegraph';
import { PackCharge } from '../systems/packCharge';
import { audio } from '../systems/audio';
import { StructureSystem } from '../systems/structures/StructureSystem';
import { planStructures, structureTiles, type StructurePlacement } from '../systems/structures/placement';
import { BirthFlow } from './game/BirthFlow';
import { exposeGameDebug } from './game/DebugHooks';
import { Economy } from './game/Economy';
import { GameCamera } from './game/GameCamera';
import { GameCombat } from './game/GameCombat';
import { LabMode } from './game/LabMode';
import { MotionFx } from './game/MotionFx';
import { PlayerStrikes } from './game/PlayerStrikes';
import { Progression } from './game/Progression';
import { RouteFlow } from './game/RouteFlow';
import { UiRelay } from './game/UiRelay';
import { SENSE_BONUS_MAX, urlParams, type GameInitData } from './game/shared';

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
  inputSystem: InputSystem;
  rng: Rng;
  menu: TextMenu;
  // --- 48·49라운드 노드 지도: 노드 전투장인지 · 현재 노드(층 진입 갈림 선택 대기 중이면 null) · 설계도 · 세트 그림 · 조작 안내 ---
  routeMode = false;
  node: RouteNode | null = null;
  nodeKind: RouteKind | null = null;
  nodeArena: NodeArenaPlan | null = null;
  setPieceView: SetPieceView | null = null;
  tutorial: TutorialDirector | null = null;
  // --- 연출 (35·42라운드) ---
  fx: FxPool;
  numbers: DamageNumberPool;
  hitFx: HitFx;
  telegraph: TelegraphFx;
  trails: TrailRenderer;
  screenFx: ScreenFx;
  aimLine: AimLine;
  /** 50라운드 동적 조명 + 어둠 (지역 조명이 없으면 꺼진 채) */
  lighting: Lighting;
  readonly hitStop = new HitStop();
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

  private initData: GameInitData = {};
  private senseBonus = 0;
  private debugText?: Phaser.GameObjects.Text;
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

  create(): void {
    this.cam = new GameCamera(this);
    this.combat = new GameCombat(this);
    this.strikes = new PlayerStrikes(this);
    this.motion = new MotionFx(this);
    this.progress = new Progression(this);
    this.economy = new Economy(this);
    this.birth = new BirthFlow(this);
    this.ui = new UiRelay(this);
    this.labMode = this.lab ? new LabMode(this, this.initData) : null;
    this.frozen = false;
    this.hitStopped = false;

    // 49라운드: 무기 시험장은 런·세이브와 무관한 연습 런으로 시작한다
    const floorStart = this.labMode
      ? this.labMode.prepareRun()
      : this.progress.prepareRun(this.initData, this.senseBonus);
    const floor = gameState.stageIndex + 1;
    const nodeSalt = this.enterRoute(floor);
    const structurePlan = this.buildWorld(floor, nodeSalt);

    // 플레이어 (노드 진행 상태는 플레이어 뒤 — 48라운드 노드 씬 초기화 순서)
    const layout = this.layout!;
    const start = layout.arena
      ? new Phaser.Math.Vector2((layout.arena.spawn.x + 0.5) * TILE, (layout.arena.spawn.y + 0.5) * TILE)
      : this.world.roomCenter(layout.rooms.find((r) => r.type === 'start')!);
    this.player = new Player(this, start.x, start.y);
    this.route = new RouteFlow(this);

    this.createActors();
    this.createFx(floor);
    this.menu = new TextMenu(this);
    this.wirePhysics();

    // 방 상태 머신
    const kd = this.nodeKind ? kindDef(this.nodeKind) : null;
    this.director = new RoomDirector({
      world: this.world,
      stage: gameState.stage,
      rng: this.rng,
      player: this.player,
      mobs: this.mobs,
      heal: (f) => this.player.heal(Math.round(gameState.maxHp * f)),
      onRunCleared: () => this.progress.beginEnding(),
      onStageCleared: (room) => this.progress.beginStageReward(room),
      isLastStage: () => gameState.isLastStage,
      waveMods: (room) => this.structures?.waveMods(room) ?? { hpMult: 1, countMult: 1, extra: 0 },
      waves: kd?.waves,
    });
    if (gameState.route && this.routeMode) this.route.syncProgress();
    this.createTutorial();
    this.createStructures(structurePlan);
    this.inputSystem = new InputSystem(this);

    // 계약: 스냅샷 제공, 메뉴 선택 라우팅, HUD 병렬 실행
    setSnapshotProvider(() => this.ui.snapshot());
    setMenuSelect((id, key) => this.menu.select(key, id));
    setWarpHandler({ check: () => this.ui.warpDeny(), run: () => this.ui.warpDeny() });
    setNodeChooser((id) => this.route.chooseNode(id));
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
    this.cameras.main.setZoom(CAMERA.ZOOM);
    this.cam.update(true);
    this.lighting = new Lighting(this, {
      ambient: this.lightingAmbient(),
      player: this.player,
      telegraphs: () => this.telegraph.lightPoints(),
    });
    if (this.routeMode) this.route.enterNode();
    this.labMode?.setup();
    this.createDebugText();
  }

  // --- create 단계 ---

  /** 48라운드 노드 지도 (1~2층): 층 그래프는 층 시드로 한 번 만들고 노드마다 씬을 다시 연다. 반환 = 노드 시드 접미 */
  private enterRoute(floor: number): string {
    this.routeMode = !this.lab && routeEnabled(gameState.stageId);
    if (this.routeMode && !gameState.route)
      gameState.route = new RouteState(generateRoute(gameState.stageId, gameState.floorSeed), floor);
    const route = this.routeMode ? gameState.route : null;
    // 50라운드 시범 확인 (?slice=<지역>): 새 런에서 그 지역의 전투 노드로 바로 (탄생 생략)
    if (route && !route.currentId && this.initData.slice) this.jumpToSlice(route, this.initData.slice);
    // 진입 노드가 하나뿐이면(1층 탄생지) 바로 들어간다. 여럿이면(2층 갈림) 빈 전투장에서 고른다
    if (route && !route.currentId) {
      const entries = route.nextOptions();
      if (entries.length === 1) route.enter(entries[0].id);
    }
    this.node = route?.current ?? null;
    this.nodeKind = this.node?.kind ?? null;
    const nodeSalt = this.node ? `:${this.node.id}` : route ? ':entry' : '';
    this.rng = new Rng(hashSeed(gameState.floorSeed + ':runtime' + nodeSalt));
    this.nodeArena = !this.lab && route ? planNodeArena(this.node, gameState.stageId, gameState.floorSeed) : null;
    return nodeSalt;
  }

  /** `?slice=<지역>`: 그 지역의 전투 노드(없으면 그 지역 아무 노드)를 현재 노드로 */
  private jumpToSlice(route: RouteState, region: string): void {
    const inRegion = route.graph.nodes.filter((n) => regionIdOf(gameState.stageId, n.col) === region);
    const node = inRegion.find((n) => n.kind === 'battle') ?? inRegion[0];
    if (!node) return;
    route.currentId = node.id;
    route.path.push(node.id);
    gameState.birthPending = false;
  }

  /**
   * 50라운드 지역 조명: data/lighting.json regions 에 있는 지역의 노드 전투장만 어둡게 (시범: 외곽 거리).
   * `?light=0` 끔 · `?light=1` 이면 그 밖의 전투장·시험장에도 default (검증용)
   */
  private lightingAmbient(): LightingAmbient | null {
    const flag = urlParams().get('light');
    if (flag === '0') return null;
    const region = this.nodeArena?.regionId;
    const own = region ? LIGHTING.regions[region] : undefined;
    if (own) return own;
    return flag === '1' && (this.nodeArena || this.lab) ? LIGHTING.default : null;
  }

  /** 월드 (노드 지도면 노드 전투장 하나, 시험장이면 작은 아레나, 아니면 방+복도) · 구조물 배치 · 세트 그림 */
  private buildWorld(floor: number, nodeSalt: string): StructurePlacement[] {
    const layout = this.labMode
      ? this.labMode.buildArena()
      : this.nodeArena
        ? this.nodeArena.layout
        : generateFloor(gameState.floorSeed, gameState.stage.layout);
    this.layout = layout;
    this.visitedRooms = new Set(['start']);
    this.clearedRooms = new Set();
    // 47라운드: 구조물을 소품보다 먼저 배치하고 그 칸은 소품에서 뺀다. ?structures=all 이면 이 층 종류 전부(데모·검증)
    // 데모 배포본은 빌드 시 VITE_DEMO_STRUCTURES=all 로 같은 효과(주소 옵션을 붙일 수 없어서, 47라운드 데모 결정)
    // 48라운드: 노드 전투장이면 그 노드 종류에 허용된 구조물만 (forceAll = 허용 종류 전부)
    const forceAll = urlParams().get('structures') === 'all' || import.meta.env.VITE_DEMO_STRUCTURES === 'all';
    const structurePlan = this.lab
      ? []
      : planStructures(layout, gameState.stageId, gameState.floorSeed + nodeSalt, {
          forceAll,
          node: this.nodeArena ? this.nodeArena.structureNode : undefined,
        });
    this.world = new TileWorld(
      this,
      layout,
      this.nodeArena ? skinFor(floor, this.nodeArena.tileset) : (tileSkins.get(floor) ?? TileSkin.placeholder()),
      gameState.floorSeed + nodeSalt,
      this.nodeArena
        ? new Set([...structureTiles(structurePlan), ...setPieceTiles(this.nodeArena)])
        : structureTiles(structurePlan),
    );
    this.physics.world.setBounds(0, 0, this.world.widthPx, this.world.heightPx);
    // 층 강조색: 캐릭터 시트의 1층 램프를 현재 층 램프로 치환한 변형 텍스처·애니 (1층은 원본)
    spriteLibrary.activate(this, floor);
    // 49라운드 세트 배치 그림 (층 램프 변형 시트를 쓰므로 activate 뒤)
    this.setPieceView?.destroy();
    this.setPieceView = this.nodeArena ? new SetPieceView(this, this.nodeArena.setPiece) : null;
    // 저장고가 있으면 카메라 경계에 넣는다 (부수면 그 안으로 들어간다)
    for (const p of structurePlan) if (p.cellar) this.world.extendCamera(p.cellar.inner, 1);
    const kd = this.nodeKind ? kindDef(this.nodeKind) : null;
    if (kd?.shopTiles && layout.arena) this.world.placeShopAt(layout.arena.shop.x, layout.arena.shop.y);
    return structurePlan;
  }

  /** 적·투사체·드랍 풀 */
  private createActors(): void {
    this.mobs = this.physics.add.group({ runChildUpdate: false });
    const pool = (classType: typeof Projectile | typeof Pickup, maxSize: number) =>
      this.add.group({ classType, maxSize, runChildUpdate: false });
    this.projectiles = pool(Projectile, PROTOTYPE.PROJECTILE_POOL);
    this.pickups = pool(Pickup, PROTOTYPE.PICKUP_POOL);
    this.playerShots = pool(Projectile, PROTOTYPE.PROJECTILE_POOL);
  }

  /** 연출 풀·렌더러 (층 램프) + 시트 JSON §3.2 필드(shake·flash·secondStage·trail)를 감각 계층으로 연결 */
  private createFx(floor: number): void {
    this.fx = new FxPool(this);
    this.numbers = new DamageNumberPool(this);
    this.numbers.setFloor(floor);
    this.hitFx = new HitFx(this, this.fx);
    this.hitFx.setFloor(floor);
    this.telegraph = new TelegraphFx(this);
    this.telegraph.setFloor(floor);
    this.trails = new TrailRenderer(this);
    this.trails.setContext(floor, gameState.weapon.id);
    this.screenFx = new ScreenFx(this);
    this.screenFx.setFloor(floor);
    this.aimLine = new AimLine(this);
    // 색은 '#hex' 와 팔레트 경로 둘 다 (resolveFxColor)
    const SF = FEEL.SCREEN.DEFAULT_FLASH;
    this.fx.hooks = {
      shake: (spec) => this.shake.add(this.time.now, spec.px, spec.ms),
      flash: (spec) =>
        this.screenFx.flash(resolveFxColor(PALETTE, spec.color) ?? SF.COLOR, spec.ms ?? SF.MS, spec.alpha ?? SF.ALPHA),
      trail: (req) => {
        const T = FEEL.TRAIL;
        const h = this.trails.start('sheet', req.source, {
          depth: req.depth - DEPTH.OVERLAY_STEP / 2, // 시트 바로 아래(캐릭터 위)
          color: resolveFxColor(PALETTE, req.spec.color) ?? undefined,
          alpha: req.spec.alpha,
          lifeMs: req.spec.ms,
          width: Math.max(1, Math.round(T.BAND_PX * (req.spec.widthRatio ?? T.WIDTH_RATIO))),
        });
        return h ? () => h.stop() : null;
      },
      bodyCenterUpPx: FEEL.SECONDARY.BODY_CENTER_UP_PX,
    };
    this.pack.reset();
    this.hitStop.reset();
    this.shake.reset();
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
        startFight: (spawns, at, onDone) => this.director.startChallenge(roomId, spawns, onDone, at),
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
      },
      plan,
    );
    // 48라운드: 앞 노드의 층 상태(빚·취기·판돈·불씨 등)를 이어받는다
    if (this.routeMode) this.structures.importFloorState(gameState.structureCarry);
  }

  private bindEvents(): void {
    const { strikes: s, progress: p, combat: c, ui, motion: m } = this;
    this.subs = [
      [Events.PLAYER_ATTACKED, s.onPlayerAttacked, s],
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
    ];
    for (const [event, fn, ctx] of this.subs) EventBus.on(event, fn, ctx);
  }

  private createDebugText(): void {
    this.debugText = undefined;
    if (!DEBUG.SHOW_TEXT || !urlParams().has('debugtext')) return;
    // 카메라 확대(48라운드)는 scrollFactor 0 개체도 화면 가운데 기준으로 키운다 → 역배율·역위치로 화면 (4,4)
    const cam = this.cameras.main;
    const z = CAMERA.ZOOM;
    this.debugText = this.add
      .text((4 - cam.width / 2) / z + cam.width / 2, (4 - cam.height / 2) / z + cam.height / 2, '', {
        font: DEBUG.FONT,
        color: COLORS.DEBUG_TEXT,
      })
      .setScale(1 / z)
      .setScrollFactor(0)
      .setDepth(DEPTH.DEBUG);
  }

  // --- 매 프레임 ---

  update(time: number, delta: number): void {
    if (gameState.gameOver || gameState.cleared) return;

    // 48라운드 Q6 탄생 연출: 조작 잠금, 카메라 배율은 연출이 정한다. 아무 키로 건너뛰기 (keydown·pointerdown)
    if (this.birth.active) {
      this.birth.update(time);
      this.fx.update(time);
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
      this.trails.update(time);
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
    input = this.structures.adjustAim(input, time);
    this.player.sprintAllowed = !this.director.inCombat;
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
    };
    for (const child of [...this.mobs.getChildren()]) (child as Mob).update(ctx);
    this.telegraph.update(time);
    for (const child of this.projectiles.getChildren()) (child as Projectile).tick(time);
    for (const child of this.pickups.getChildren()) (child as Pickup).tick(time);
    for (const child of this.playerShots.getChildren()) (child as Projectile).tick(time);
    this.structures.tickShots(this.playerShots.getChildren() as Projectile[]);
    this.strikes.update(time, delta);
    this.fx.update(time);
    this.trails.update(time);
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
  private renderLate(time: number): void {
    if (!this.player?.active) return;
    this.lighting?.update(time);
    const p = this.player;
    this.world.quarter?.updateOcclusion([{ x: p.x, y: p.y, w: p.displayWidth, h: p.displayHeight, depth: p.depth }]);
  }

  // --- 정지 ---

  /** 3지선다·엔딩 선택·시험장 메뉴 동안 게임 정지 (물리·적·플레이어). 메뉴는 UI 가 그린다 */
  setFrozen(on: boolean): void {
    if (this.frozen === on) return;
    this.frozen = on;
    this.syncPhysicsPause();
  }

  /** 히트스톱 시작·끝: 물리 정지(frozen 과 합산), 플레이어·적·이펙트 애니 정지 */
  private setHitStopped(on: boolean): void {
    this.hitStopped = on;
    this.syncPhysicsPause();
    this.player.setAnimPaused(on);
    for (const m of this.mobs.getChildren() as Mob[]) m.setAnimPaused(on);
    this.fx.setPaused(on);
    this.telegraph.setPaused(on);
    this.trails.setPaused(on);
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
    this.telegraph.destroy();
    this.trails.destroy();
    this.screenFx.destroy();
    this.aimLine.destroy();
    this.structures.destroy();
    this.fx.destroy();
    this.lighting.destroy();
    audio.stopAllLoops();
    setMenuSelect(null);
    setSnapshotProvider(null);
    setWarpHandler(null);
    setNodeChooser(null);
    this.birth.destroy();
    this.labMode?.destroy();
    this.tutorial?.destroy();
    this.tutorial = null;
    this.setPieceView?.destroy();
    this.setPieceView = null;
    this.menu.close();
    this.inputSystem.destroy();
  }
}
