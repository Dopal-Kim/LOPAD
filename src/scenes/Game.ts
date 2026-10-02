import Phaser from 'phaser';
import {
  BIRTH,
  CAMERA,
  COLORS,
  DEBUG,
  DEPTH,
  ENEMY_FX,
  FEEL,
  PLACEHOLDER_UI,
  PROTOTYPE,
  ROUTE_FX,
  SCENES,
  SPRITES,
  TILE,
  TRAVERSAL,
  entityDepth,
} from '../core/Constants';
import {
  EventBus,
  Events,
  type BossWallHitPayload,
  type GuardReleasedPayload,
  type PlayerAttackPayload,
  type PlayerDamagedPayload,
  type RunEndedPayload,
  type ShadowStepPayload,
  type WarpPayload,
  type WeaponEvolvedPayload,
  type WeaponReinforcedPayload,
} from '../core/EventBus';
import { gameState, type EndingChoice } from '../core/GameState';
import { BOSSES, ECONOMY, PALETTE, PLAYER_DATA, STORY, WEAPON_RULES } from '../data';
import { deathLine, evolutionLine, fill, floorText } from '../systems/story';
import type { Mob, MobContext, ProjectileSpec } from '../objects/Mob';
import { Player } from '../objects/Player';
import { Projectile } from '../objects/Projectile';
import { Pickup } from '../objects/Pickup';
import { InputSystem, neutralInput } from '../systems/InputSystem';
import { warpDenyReason, type WarpDenyReason } from '../systems/traversal';
import { generateArena, generateFloor, type FloorLayout } from '../systems/mapgen';
import {
  RouteState,
  arenaSize,
  generateRoute,
  kindDef,
  minBattlesOnAnyPath,
  routeEnabled,
  ROUTE,
  type RouteKind,
  type RouteNode,
} from '../systems/route';
import { comboShape, facingAngle, hitShapeBounds, rotateDir, shapeHit, type HitShape } from '../systems/combo';
import { BirthSequence } from '../systems/birth';
import { RoomDirector } from '../systems/RoomDirector';
import { Rng, hashSeed } from '../systems/rng';
import { SaveSlot, browserStorage } from '../systems/save';
import type { KillKind } from '../systems/senses';
import { applyStatReward, findReward, rollCrit, rollGold, shopPrice } from '../systems/economy';
import { TextMenu } from '../systems/TextMenu';
import { markUnderstood, metaStore, recordRun } from '../systems/meta';
import { PASSIVES } from '../systems/passives';
import {
  UI_EVENTS,
  __system,
  type StoryKind,
  type UiRouteEntered,
  type UiWarpDone,
  type UiWarpState,
} from '../contract/ui';
import { buildSnapshot } from '../contract/snapshot';
import { setMenuSelect, setNodeChooser, setSnapshotProvider, setWarpHandler } from '../contract/host';
import { UI_SCENES } from '../ui';
import type { StatKey, WeaponEvolution } from '../data/types';
import { TileWorld } from '../world/TileWorld';
import { TileSkin, tileSkins } from '../world/tileskin';
import { spriteLibrary } from '../systems/sprites';
import {
  FX_ACTION,
  arrowFxId,
  comboAction,
  comboFxId,
  facingOf,
  hitFrameOffsets,
  progressFrame,
  radiusFitScale,
  slashFxId,
  type Facing,
} from '../systems/spriteDefs';
import { FxPool, type FxHandle } from '../systems/fx';
import { HitStop, Shake, feelSettings, setFeel } from '../systems/feel';
import { TrailRenderer } from '../systems/trail';
import { arcPoint } from '../systems/trailMath';
import { ScreenFx } from '../systems/screenFx';
import { AimLine } from '../systems/aimFx';
import { fxWeaponColor, hexToInt, resolveFxColor } from '../systems/palette';
import { DamageNumberPool } from '../systems/damageNumbers';
import { HitFx } from '../systems/hitFx';
import { TelegraphFx } from '../systems/telegraph';
import { PackCharge } from '../systems/packCharge';
import type { Enemy } from '../objects/Enemy';
import type { Boss } from '../objects/Boss';
import { fontStatus } from '../systems/fonts';
import { audio } from '../systems/audio';
import { exposeDebug } from '../debug';
import { StructureSystem } from '../systems/structures/StructureSystem';
import { planStructures, structureTiles } from '../systems/structures/placement';

/** mode 'floor' = 디버그·검증용 층 이동 (47라운드, 세이브 없음) · 'node' = 같은 층 안 다음 노드 (48라운드) */
type GameInitData = { mode?: 'new' | 'next' | 'floor' | 'node'; weapon?: string; playerName?: string; floor?: number };

/** 48라운드 (계약 §10.2): 45라운드 워프는 비활성 (노드 지도에는 방 간 이동이 없다) */
const WARP_DISABLED = true;

/** 판정 원점 = 몸 중심 (발 위 10px, 48라운드 아트 메모 hitOrigin) */
const HIT_ORIGIN_UP_PX = 10;

export class Game extends Phaser.Scene {
  private player: Player;
  private mobs: Phaser.Physics.Arcade.Group;
  private projectiles: Phaser.GameObjects.Group;
  private pickups: Phaser.GameObjects.Group;
  private menu: TextMenu;
  private shopOpen = false;
  private world: TileWorld;
  private director: RoomDirector;
  private inputSystem: InputSystem;
  private rng: Rng;
  private debugText?: Phaser.GameObjects.Text;
  /** 카메라 중심 (반올림 전). 스크롤은 매 프레임 여기서 반올림해 적용 */
  private readonly camCenter = new Phaser.Math.Vector2();
  private initMode: GameInitData['mode'];
  private initWeapon?: string;
  private initName?: string;
  private initFloor = 0;
  /** 47라운드 상호작용 구조물 */
  private structures: StructureSystem;
  private playerShots: Phaser.GameObjects.Group;
  private lastShotAt = -Infinity;
  /** 디버그: 마지막 공격 이벤트 · 마지막 결과 화면 페이로드 */
  private debugLastAttack: unknown = null;
  private debugLastResult: unknown = null;
  private rapidCount = 0;
  private readonly saveSlot = new SaveSlot(browserStorage());
  private transitioning = false;
  private visitedRooms = new Set<string>();
  private clearedRooms = new Set<string>();
  private layout?: ReturnType<typeof generateFloor>;
  private bossName: string | null = null;
  private readonly playerVec = new Phaser.Math.Vector2();
  /** 개성 3지선다·엔딩 선택 중: 게임 진행(이동·적·물리) 정지 */
  private frozen = false;
  /** 공격 이펙트 풀 (아트 시트가 있을 때만 재생) */
  private fx: FxPool;
  /** 질풍: 이동·대쉬 중 루프 이펙트 */
  private galeFx: FxHandle | null = null;
  /** 피격 피드백 (35라운드): 히트스톱·흔들림·데미지 숫자·피격 이펙트 */
  private readonly hitStop = new HitStop();
  private readonly shake = new Shake();
  private hitStopped = false;
  private numbers: DamageNumberPool;
  private hitFx: HitFx;
  /** 적·보스 공격 양상 (35라운드 2단계): 예고 마커·집단 돌격 공유 상태 */
  private telegraph: TelegraphFx;
  private readonly pack = new PackCharge();
  /** 디버그: 최근 보스 내리찍기 */
  private debugLastSlam: unknown = null;
  /** 42라운드 Q3: 잔상 궤적 리본·화면 섬광/오버레이. 35라운드 3단계: 조준 점선·차지 게이지·거인 루프·대쉬 잔상 */
  private trails: TrailRenderer;
  private screenFx: ScreenFx;
  private aimLine: AimLine;
  private aimChargeFx: FxHandle | null = null;
  private giantFx: FxHandle | null = null;
  private dashTrailNextAt = 0;
  /** 45라운드 워프: 연출 중 · 입력 잠금 끝 시각 · 디버그 기록 */
  private warping = false;
  private warpLockUntil = 0;
  private debugLastWarp: unknown = null;
  /** 45라운드 달리기: 다음 발밑 먼지 시각 · 디버그 횟수 */
  private sprintDustNextAt = 0;
  private sprintDustCount = 0;
  /** 잔월: 남아 있는 베기 궤적 (지속 피해 영역) */
  private dotZones: {
    x: number;
    y: number;
    w: number;
    h: number;
    until: number;
    nextAt: number;
    tickMs: number;
    dmg: number;
  }[] = [];
  /** 48라운드 노드 지도: 이 씬이 노드 전투장인지 · 현재 노드(층 진입 갈림 선택 대기 중이면 null) · 출구 열림 · 입력 잠금 */
  private routeMode = false;
  private node: RouteNode | null = null;
  private nodeKind: RouteKind | null = null;
  private nodeExitOpen = false;
  private nodeExitScheduled = false;
  private enterLockUntil = 0;
  /** 출구에서 벗어나야 다시 선택을 연다 (UI 없이 메뉴로 고를 때) */
  private exitArmed = true;
  /** 48라운드 Q6 탄생 연출 */
  private birth: BirthSequence | null = null;
  private birthStartedAt = 0;
  private readonly onBirthKey = () => this.skipBirth();
  /** 디버그: 최근 근접 판정 (모양·원점·맞은 수) */
  private debugLastSwing: unknown = null;
  /** 출혈: 적별 지속 피해 (+ 적에 붙은 bleed 루프 이펙트) */
  private bleeds: { mob: Mob; dmg: number; ticksLeft: number; nextAt: number; tickMs: number; fx: FxHandle | null }[] =
    [];

  constructor() {
    super(SCENES.GAME);
  }

  init(data?: GameInitData): void {
    this.initMode = data?.mode;
    this.initWeapon = data?.weapon;
    this.initName = data?.playerName;
    this.initFloor = data?.floor ?? 0;
    this.transitioning = false;
  }

  create(): void {
    const floorStart = this.prepareRun();
    const stage = gameState.stage;
    const floor = gameState.stageIndex + 1;
    // 48라운드 노드 지도 (1~2층): 층 그래프는 층 시드로 한 번 만들고 노드마다 씬을 다시 연다
    this.routeMode = routeEnabled(gameState.stageId);
    if (this.routeMode && !gameState.route)
      gameState.route = new RouteState(generateRoute(gameState.stageId, gameState.floorSeed), floor);
    const route = this.routeMode ? gameState.route : null;
    // 진입 노드가 하나뿐이면(1층 탄생지) 바로 들어간다. 여럿이면(2층 갈림) 빈 전투장에서 고른다
    if (route && !route.currentId) {
      const entries = route.nextOptions();
      if (entries.length === 1) route.enter(entries[0].id);
    }
    this.node = route?.current ?? null;
    this.nodeKind = this.node?.kind ?? null;
    const nodeSalt = this.node ? `:${this.node.id}` : route ? ':entry' : '';
    this.rng = new Rng(hashSeed(gameState.floorSeed + ':runtime' + nodeSalt));

    // 월드 (노드 지도면 노드 전투장 하나, 아니면 방+복도)
    const layout = route ? this.buildArena(this.node) : generateFloor(gameState.floorSeed, stage.layout);
    this.layout = layout;
    this.visitedRooms = new Set(['start']);
    this.clearedRooms = new Set();
    this.bossName = null;
    // 47라운드: 구조물을 소품보다 먼저 배치하고 그 칸은 소품에서 뺀다. ?structures=all 이면 이 층 종류 전부(데모·검증)
    // 데모 배포본은 빌드 시 VITE_DEMO_STRUCTURES=all 로 같은 효과(주소 옵션을 붙일 수 없어서, 47라운드 데모 결정)
    // 48라운드: 노드 전투장이면 그 노드 종류에 허용된 구조물만 (forceAll = 허용 종류 전부)
    const urlParams = typeof location !== 'undefined' ? new URLSearchParams(location.search) : new URLSearchParams();
    const forceAll = urlParams.get('structures') === 'all' || import.meta.env.VITE_DEMO_STRUCTURES === 'all';
    const kd = this.nodeKind ? kindDef(this.nodeKind) : null;
    const structurePlan = planStructures(layout, gameState.stageId, gameState.floorSeed + nodeSalt, {
      forceAll,
      node: route
        ? { kinds: kd?.structures ?? [], budget: kd?.budget ?? [0, 0], reserve: this.arenaReserve(layout) }
        : undefined,
    });
    this.world = new TileWorld(
      this,
      layout,
      tileSkins.get(floor) ?? TileSkin.placeholder(),
      gameState.floorSeed + nodeSalt,
      structureTiles(structurePlan),
    );
    this.physics.world.setBounds(0, 0, this.world.widthPx, this.world.heightPx);
    // 층 강조색: 캐릭터 시트의 1층 램프를 현재 층 램프로 치환한 변형 텍스처·애니 (1층은 원본)
    spriteLibrary.activate(this, floor);
    // 저장고가 있으면 카메라 경계에 넣는다 (부수면 그 안으로 들어간다)
    for (const p of structurePlan) if (p.cellar) this.world.extendCamera(p.cellar.inner, 1);
    if (kd?.shopTiles && layout.arena) this.world.placeShopAt(layout.arena.shop.x, layout.arena.shop.y);

    // 플레이어
    const start = layout.arena
      ? new Phaser.Math.Vector2((layout.arena.spawn.x + 0.5) * TILE, (layout.arena.spawn.y + 0.5) * TILE)
      : this.world.roomCenter(layout.rooms.find((r) => r.type === 'start')!);
    this.player = new Player(this, start.x, start.y);
    this.routeResetFields();

    // 적·투사체
    this.mobs = this.physics.add.group({ runChildUpdate: false });
    this.projectiles = this.add.group({
      classType: Projectile,
      maxSize: PROTOTYPE.PROJECTILE_POOL,
      runChildUpdate: false,
    });
    this.pickups = this.add.group({ classType: Pickup, maxSize: PROTOTYPE.PICKUP_POOL, runChildUpdate: false });
    this.playerShots = this.add.group({
      classType: Projectile,
      maxSize: PROTOTYPE.PROJECTILE_POOL,
      runChildUpdate: false,
    });
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
    this.aimChargeFx = null;
    this.giantFx = null;
    this.dashTrailNextAt = 0;
    // 시트 JSON §3.2 필드(shake·flash·secondStage·trail)를 감각 계층으로 연결. 색은 '#hex' 와 팔레트 경로 둘 다 (resolveFxColor)
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
    this.debugLastSlam = null;
    this.hitStop.reset();
    this.shake.reset();
    this.hitStopped = false;
    this.galeFx = null;
    this.lastShotAt = -Infinity;
    this.rapidCount = 0;
    this.frozen = false;
    this.dotZones = [];
    this.bleeds = [];
    this.menu = new TextMenu(this);
    this.shopOpen = false;
    this.warping = false;
    this.warpLockUntil = 0;
    this.debugLastWarp = null;
    this.sprintDustNextAt = 0;
    this.sprintDustCount = 0;

    for (const layer of this.world.collisionLayers) {
      this.physics.add.collider(this.player, layer);
      this.physics.add.collider(this.mobs, layer);
    }
    this.physics.add.collider(this.mobs, this.mobs);
    this.physics.add.overlap(this.player, this.mobs, (_p, m) => this.onMobTouch(m as Mob));
    this.physics.add.overlap(this.player, this.projectiles, (_p, pr) => this.onProjectileHit(pr as Projectile));
    this.physics.add.overlap(this.projectiles, this.mobs, (pr, m) => this.onReflectedHit(pr as Projectile, m as Mob));
    this.physics.add.overlap(this.player, this.pickups, (_p, pk) => this.onPickup(pk as Pickup));
    this.physics.add.overlap(this.playerShots, this.mobs, (pr, m) => this.onPlayerShotHit(pr as Projectile, m as Mob));

    // 방 상태 머신
    this.director = new RoomDirector({
      world: this.world,
      stage,
      rng: this.rng,
      player: this.player,
      mobs: this.mobs,
      heal: (f) => this.player.heal(Math.round(gameState.maxHp * f)),
      onRunCleared: () => this.beginEnding(),
      onStageCleared: (room) => this.beginStageReward(room),
      isLastStage: () => gameState.isLastStage,
      waveMods: (room) => this.structures?.waveMods(room) ?? { hpMult: 1, countMult: 1, extra: 0 },
      waves: kd?.waves,
    });
    if (route) this.syncRouteProgress();

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
        addGold: (n) => this.addGold(n),
        spendGold: (n) => this.spendGold(n),
        spawnPickup: (x, y, kind, value) => this.spawnPickup(x, y, kind, value),
        gainPersonality: (n) => this.gainPersonality(n),
        heal: (n) => this.player.heal(n),
        hitMob: (m, dmg, o) => this.hitMob(m, dmg, o),
        onKill: (m, kind) => this.onKill(m, kind),
        potionCarry: () => this.potionCarry,
        isBusy: () =>
          this.frozen ||
          this.warping ||
          this.transitioning ||
          this.menu.isOpen ||
          gameState.rewardPending ||
          gameState.gameOver ||
          gameState.cleared,
        openStatChooser: () => {
          if (gameState.pointsPending > 0) this.openStatChooser(() => {});
        },
        story: (kind, text) => this.story(kind, text),
        nodeMode: this.routeMode,
      },
      structurePlan,
    );
    // 48라운드: 앞 노드의 층 상태(빚·취기·판돈·불씨 등)를 이어받는다
    if (this.routeMode) this.structures.importFloorState(gameState.structureCarry);

    this.inputSystem = new InputSystem(this);

    // 계약: 스냅샷 제공, 메뉴 선택 라우팅, HUD 병렬 실행
    setSnapshotProvider(() => this.snapshot());
    setMenuSelect((id, key) => this.menu.select(key, id));
    setWarpHandler({ check: (id) => this.warpDeny(id), run: (id) => this.startWarp(id) });
    setNodeChooser((id) => this.chooseNode(id));
    if (this.scene.manager.keys[UI_SCENES.HUD] && !this.scene.isActive(UI_SCENES.HUD)) this.scene.launch(UI_SCENES.HUD);
    // 층 시작만 (같은 층의 다음 노드는 ROUTE_NODE_ENTERED)
    if (floorStart) {
      __system.emit(UI_EVENTS.STAGE_STARTED, {
        stageIndex: gameState.stageIndex,
        stageName: floorText(gameState.stageId)?.title ?? gameState.stage.name,
      });
      this.story('floor', floorText(gameState.stageId)?.enter ?? '');
    }

    exposeDebug({
      world: this.world,
      director: this.director,
      player: this.player,
      mobs: () => [...(this.mobs.getChildren() as Mob[])],
      hurt: (m, amount, crit) => {
        if (this.hitMob(m, amount, { crit: Boolean(crit), dirX: 1, dirY: 0 })) this.onKill(m, 'attack');
      },
      fireAtPlayer: (distPx, speedPx, attack) => {
        const x = this.player.x + distPx;
        const y = this.player.y;
        this.fire(x, y, -1, 0, { speedPx, attack, size: 4, lifeMs: 5000 });
      },
      playerInfo: () => ({
        x: this.player.x,
        y: this.player.y,
        action: this.player.action,
        anim: this.player.animKey,
        dir: this.player.facingDir,
        animated: this.player.visual.animated,
        overlayFrame: this.player.overlay.frame,
        moving: this.player.moving,
      }),
      sprites: () => spriteLibrary.summary(this),
      fx: () => this.fx.summary(),
      nextStage: () => {
        if (this.transitioning) return;
        this.transitioning = true;
        this.scene.restart({ mode: 'next' } satisfies GameInitData);
      },
      now: () => this.time.now,
      stage: () => ({
        index: gameState.stageIndex,
        id: gameState.stageId,
        name: gameState.stage.name,
        savesLeft: gameState.savesLeft,
        exitOpen: gameState.exitOpen,
        isLast: gameState.isLastStage,
      }),
      save: () => this.saveSlot.read(),
      lastAttack: () => this.debugLastAttack,
      lastResult: () => this.debugLastResult,
      shots: () =>
        (this.playerShots.getChildren() as Projectile[])
          .filter((p) => p.active)
          .map((p) => ({
            x: p.x,
            y: p.y,
            vx: p.body.velocity.x,
            vy: p.body.velocity.y,
            attack: p.attack,
            pierce: p.pierceLeft,
            texture: p.texture.key,
            rotation: p.rotation,
          })),
      meta: () => metaStore.read(),
      economy: () => ({
        gold: gameState.gold,
        potions: gameState.potions,
        points: gameState.pointsPending,
        bonus: { ...gameState.bonus },
        rewardPending: gameState.rewardPending,
        shopOpen: this.shopOpen,
        menuOpen: this.menu.isOpen,
        passives: { ...gameState.passives.owned },
      }),
      addPassive: (id: string) => gameState.passives.add(id),
      scenes: () => this.scene.manager.getScenes(true).map((s) => s.scene.key),
      pickups: () =>
        (this.pickups.getChildren() as Pickup[])
          .filter((p) => p.active)
          .map((p) => ({ kind: p.kind, value: p.value, x: p.x, y: p.y })),
      camera: () => {
        const r = this.world.cameraRegion(this.player.x, this.player.y);
        return {
          scrollX: this.cameras.main.scrollX,
          scrollY: this.cameras.main.scrollY,
          zoom: this.scale.zoom,
          camZoom: this.cameras.main.zoom,
          width: this.cameras.main.width,
          height: this.cameras.main.height,
          region: { x: r.x, y: r.y, w: r.width, h: r.height },
        };
      },
      stunAll: (ms) => {
        for (const m of this.mobs.getChildren() as Mob[]) m.stun(this.time.now, ms);
      },
      kill: (m) => {
        if (m.takeDamage(m.hp)) this.onKill(m, 'attack');
      },
      setPersonality: (value) => {
        const w = gameState.weapon;
        w.personality = 0;
        this.gainPersonality(value);
      },
      weapon: () => {
        const w = gameState.weapon;
        return {
          id: w.id,
          displayName: w.displayName,
          path: [...w.path],
          stage: w.stage,
          reinforce: w.reinforce,
          personality: w.personality,
          threshold: w.threshold,
          choicePending: w.choicePending,
          canEvolve: w.canEvolve,
          options: w.options.map((o) => ({ id: o.id, name: o.name })),
          mods: { ...w.mods },
          damageMult: w.damageMult,
          hitboxWidth: w.hitbox.width,
          secondary: w.def.secondary.name,
          frozen: this.frozen,
        };
      },
      playerExtra: () => ({
        action: this.player.action,
        guarding: this.player.isGuarding,
        shadowPrimed: this.player.isShadowPrimed(this.time.now),
        aim: this.player.aimProgress(this.time.now),
        aimReady: this.player.isAimReady,
        shoved: this.player.isShoved,
      }),
      audio: () => audio.summary(),
      feel: () => ({
        settings: { ...feelSettings },
        constants: FEEL,
        hitstop: {
          active: this.hitStop.active(this.time.now),
          remainingMs: this.hitStop.remaining(this.time.now),
          count: this.hitStop.count,
          physicsPaused: this.physics.world.isPaused,
        },
        shake: {
          offset: { ...this.shake.offset },
          active: this.shake.activeCount,
          count: this.shake.count,
          last: this.shake.last,
        },
        numbers: this.numbers.summary(),
        numbersCount: this.numbers.count,
        font: { family: this.numbers.fontFamily, loaded: fontStatus(FEEL.DAMAGE_TEXT.FONT_FAMILY) ?? null },
        hitFx: this.hitFx.summary(),
      }),
      setFeel: (patch) => setFeel(patch),
      shoved: () => (this.mobs.getChildren() as Mob[]).filter((m) => m.isShoved).length,
      telegraph: () => ({
        markers: this.telegraph.summary(),
        sheets: {
          line: this.telegraph.has('line'),
          circle: this.telegraph.has('circle'),
          cone: this.telegraph.has('cone'),
          aura: this.telegraph.has('aura'),
        },
      }),
      projectiles: () =>
        (this.projectiles.getChildren() as Projectile[])
          .filter((p) => p.active)
          .map((p) => ({
            x: p.x,
            y: p.y,
            vx: p.body.velocity.x,
            vy: p.body.velocity.y,
            attack: p.attack,
            texture: p.texture.key,
            frame: p.frame.name,
            anim: p.anims.currentAnim?.key ?? null,
            rotation: p.rotation,
            reflected: p.reflected,
          })),
      behavior: () =>
        (this.mobs.getChildren() as Mob[])
          .filter((m) => m.active)
          .map((m) => {
            const e = m as unknown as Partial<Enemy> & Partial<Boss>;
            return {
              id: m.spriteId,
              state: e.behaviorState ?? e.patternState ?? '?',
              shots: e.shotsSinceReload ?? null,
              pattern: e.pattern ?? null,
              patternLog: e.patternLog ? [...e.patternLog] : null,
              summoned: e.summoned ?? null,
              phase: e.phase ? gameState.bossPhase : null,
              vx: m.body.velocity.x,
              vy: m.body.velocity.y,
              x: m.x,
              y: m.y,
            };
          }),
      lastSlam: () => this.debugLastSlam,
      trails: () => ({ active: this.trails.activeCount, count: this.trails.count, list: this.trails.summary() }),
      screen: () => this.screenFx.summary(),
      aimFx: () => ({
        line: this.aimLine.visible,
        lineSheet: this.aimLine.sheet,
        charge: this.fx.isActive(this.aimChargeFx) ? this.aimChargeFx!.sprite.frame.name : null,
      }),
      evolveTo: (id) => {
        if (!gameState.weapon.choicePending) return false;
        const before = gameState.weapon.path.length;
        this.applyEvolution(id);
        return gameState.weapon.path.length > before;
      },
      spawnEnemy: (id, x, y) => this.director.spawnExtra(id, x, y),
      warpInfo: () => ({
        ...this.warpState(),
        inCombat: this.director.inCombat,
        currentRoomId: gameState.roomId,
        lockedMs: Math.max(0, this.warpLockUntil - this.time.now),
        last: this.debugLastWarp,
      }),
      sprintInfo: () => ({
        allowed: this.player.sprintAllowed,
        sprinting: this.player.sprinting,
        mult: this.player.sprintMult,
        speedPx: this.player.speedPx * this.player.sprintMult,
        vx: this.player.body.velocity.x,
        vy: this.player.body.velocity.y,
        dust: this.sprintDustCount,
      }),
      structures: {
        list: () => this.structures.debugList(),
        state: () => this.structures.debugState(),
        standPoint: (id) => this.structures.standPoint(id),
        pressE: () => this.structures.debugPressE(),
        hit: (id) => this.structures.debugHit(id),
        interactable: () => this.structures.interactable(),
        statuses: () => this.structures.statuses(),
      },
      gotoFloor: (n) => {
        if (this.transitioning) return;
        this.transitioning = true;
        this.scene.restart({ mode: 'floor', floor: n - 1 } satisfies GameInitData);
      },
      route: () => {
        const route = gameState.route;
        if (!route) return null;
        return {
          ...route.toUi(),
          kind: this.nodeKind,
          cleared: route.currentCleared,
          exitOpen: this.nodeExitOpen,
          path: [...route.path],
          options: route.nextOptions().map((n) => ({ id: n.id, kind: n.kind, name: n.name })),
          kinds: route.graph.nodes.map((n) => ({ id: n.id, kind: n.kind, col: n.col, row: n.row })),
          arena: this.layout?.arena ?? null,
          room: this.layout?.rooms[0]
            ? { id: this.layout.rooms[0].id, type: this.layout.rooms[0].type, floor: this.layout.rooms[0].floor }
            : null,
          locked: this.routeLocked(this.time.now),
        };
      },
      openRouteChooser: () => this.openRouteChooser(),
      chooseNode: (id) => this.chooseNode(id),
      gotoNode: (id) => {
        const route = gameState.route;
        if (!route || this.transitioning || !route.node(id)) return false;
        this.transitioning = true;
        gameState.structureCarry = this.structures.exportFloorState();
        route.currentId = id;
        route.path.push(id);
        route.choosing = false;
        this.scene.restart({ mode: 'node' } satisfies GameInitData);
        return true;
      },
      gotoExit: () => {
        const e = this.layout?.arena?.exit;
        if (!e || !this.nodeExitOpen) return false;
        this.player.body.reset((e.x + 1) * TILE, (e.y + 1) * TILE);
        return true;
      },
      combo: () => {
        const c = this.player.combo;
        return {
          weapon: gameState.weapon.id,
          hasCombo: Boolean(c),
          lastIndex: c?.lastIndex ?? null,
          lastStartedAt: c?.lastStartedAt ?? null,
          readyAt: c ? c.readyAt() : null,
          nextIndex: c ? c.nextIndex(this.time.now) : null,
          now: this.time.now,
          lastSwing: this.debugLastSwing,
          overlay: { frame: this.player.overlay.frame, action: this.player.overlay.action },
          anim: this.player.animKey,
        };
      },
      birth: () => ({
        active: Boolean(this.birth?.active),
        pending: gameState.birthPending,
        ...(this.birth?.state ?? {}),
        camZoom: this.cameras.main.zoom,
        playerVisible: this.player.visible,
        playerAlpha: this.player.alpha,
      }),
      skipBirth: () => {
        if (this.birth?.active) this.birth.skip();
      },
      setBossHp: (hp) => {
        for (const m of this.mobs.getChildren() as Mob[]) {
          if (m.isBoss && m.active) {
            m.takeDamage(Math.max(0, m.hp - hp));
            return true;
          }
        }
        return false;
      },
    });

    EventBus.on(Events.PLAYER_ATTACKED, this.onPlayerAttacked, this);
    EventBus.on(Events.PLAYER_DIED, this.onPlayerDied, this);
    EventBus.on(Events.TRIAL_CLEARED, this.onTrialCleared, this);
    EventBus.on(Events.ROOM_ENTERED, this.onRoomEnteredUi, this);
    EventBus.on(Events.PLAYER_DAMAGED, this.onPlayerDamaged, this);
    EventBus.on(Events.BOSS_WALL_HIT, this.onBossWallHit, this);
    EventBus.on(Events.PLAYER_HEALED, this.relayHealed, this);
    EventBus.on(Events.GOLD_CHANGED, this.relayGold, this);
    EventBus.on(Events.WEAPON_EVOLVED, this.relayEvolved, this);
    EventBus.on(Events.BOSS_STARTED, this.relayBossStarted, this);
    EventBus.on(Events.BOSS_PHASE, this.relayBossPhase, this);
    EventBus.on(Events.BOSS_DIED, this.relayBossDied, this);
    EventBus.on(Events.PLAYER_GUARD_RELEASED, this.onGuardReleased, this);
    EventBus.on(Events.PLAYER_SHADOW_STEP, this.onShadowStep, this);
    EventBus.on(Events.PLAYER_DASHED, this.onPlayerDashed, this);
    this.events.once('shutdown', this.cleanup, this);

    // 48라운드 Q1: 게임 월드 카메라 2배 (UI 씬은 자기 카메라라 무관)
    this.cameras.main.setRoundPixels(true);
    this.cameras.main.setZoom(CAMERA.ZOOM);
    this.updateCamera(true);
    if (this.routeMode) this.enterNode();

    const wantDebugText = typeof location !== 'undefined' && new URLSearchParams(location.search).has('debugtext');
    if (DEBUG.SHOW_TEXT && wantDebugText) {
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
  }

  update(time: number, delta: number): void {
    if (gameState.gameOver || gameState.cleared) return;

    // 48라운드 Q6 탄생 연출: 조작 잠금, 카메라 배율은 연출이 정한다. 아무 키로 건너뛰기 (keydown·pointerdown)
    if (this.birth?.active) {
      this.inputSystem.read(); // 큐 비우기
      this.birth.update(time);
      this.cameras.main.setZoom(this.birth.zoom);
      this.updateCamera(true);
      this.fx.update(time);
      this.screenFx.update(time);
      __system.emit(UI_EVENTS.STATE, this.snapshot());
      return;
    }

    // 개성 임계 도달 → 다른 메뉴(보스 보상 등)가 닫힌 뒤 3지선다 (게임 정지)
    if (gameState.weapon.choicePending && !this.menu.isOpen && !this.frozen) this.openEvolveMenu();
    if (this.frozen) {
      this.inputSystem.read(); // 큐 비우기
      this.stopGale();
      this.stopAimFx(false);
      this.fx.update(time);
      this.trails.update(time);
      this.screenFx.update(time);
      __system.emit(UI_EVENTS.STATE, this.snapshot());
      return;
    }

    // 히트스톱(35라운드): 물리·개체 애니·적 AI·입력 소비를 멈추고 카메라 흔들림·데미지 숫자·UI 만 진행
    const stopped = this.hitStop.active(time);
    if (stopped !== this.hitStopped) this.setHitStopped(stopped);
    if (stopped) {
      this.updateCamera(false, delta);
      this.screenFx.update(time);
      __system.emit(UI_EVENTS.STATE, this.snapshot());
      return;
    }

    const raw = this.inputSystem.read();
    // 워프 연출 동안 입력 잠금 (45라운드) · 구조물 메뉴 동안 입력 잠금 (47라운드 계약 §9.3)
    // 48라운드: 노드 진입 직후(밝아지는 동안)·다음 노드 선택 중·전환 중에도 잠금
    let input =
      time < this.warpLockUntil || this.structures.inputLocked || this.routeLocked(time) ? neutralInput(raw) : raw;
    if (input.potionPressed) this.usePotion();
    this.structures.update(input, time, delta);
    input = this.structures.adjustAim(input, time);
    this.player.sprintAllowed = !this.director.inCombat;
    this.player.update(input, time, delta);
    this.updateSprintDust(time);
    this.updateGale();
    this.updateAimFx(time);
    this.updateDashTrail(time);
    this.updateCamera(false, delta);
    // 48라운드: 노드 진입 직후에는 전투를 시작하지 않는다 (밝아지는 동안)
    if (time >= this.enterLockUntil) this.director.update();
    if (this.routeMode) this.updateRoute(time);

    // 다음 층 출구: 방+복도 층 · 노드 지도의 보스 노드 (그 밖의 노드 출구는 updateRoute 가 노드 선택을 연다)
    const floorExit = !this.routeMode || this.nodeKind === 'boss';
    if (floorExit && gameState.exitOpen && !this.transitioning && this.world.isExitAt(this.player.x, this.player.y)) {
      this.transitioning = true;
      if (this.routeMode) {
        this.fadeThen(() => this.scene.restart({ mode: 'next' } satisfies GameInitData));
        return;
      }
      this.scene.restart({ mode: 'next' } satisfies GameInitData);
      return;
    }

    this.playerVec.set(this.player.x, this.player.y);
    const ctx = {
      time,
      delta,
      player: this.playerVec,
      fire: this.fire,
      telegraph: this.telegraph,
      playFx: this.playMobFx,
      countMobs: this.countMobs,
      areaHit: this.areaHit,
      summon: this.summon,
      pack: this.pack,
    };
    for (const child of [...this.mobs.getChildren()]) (child as Mob).update(ctx);
    this.telegraph.update(time);
    for (const child of this.projectiles.getChildren()) (child as Projectile).tick(time);
    for (const child of this.pickups.getChildren()) (child as Pickup).tick(time);
    for (const child of this.playerShots.getChildren()) (child as Projectile).tick(time);
    this.structures.tickShots(this.playerShots.getChildren() as Projectile[]);
    this.tickHoming(delta);
    this.tickDotZones(time);
    this.tickBleeds(time);
    this.fx.update(time);
    this.trails.update(time);
    this.screenFx.update(time);
    this.updateShop();

    __system.emit(UI_EVENTS.STATE, this.snapshot());

    if (this.debugText) {
      const boss =
        gameState.bossMaxHp > 0 ? `  boss ${gameState.bossHp}/${gameState.bossMaxHp} p${gameState.bossPhase}` : '';
      this.debugText.setText(
        `[DEBUG] ${gameState.stage.name} save ${gameState.savesLeft}  P[${gameState.passives.summary() || '-'}]  HP ${gameState.hp}/${gameState.maxHp}  G ${gameState.gold}  potion ${gameState.potions}  pts ${gameState.pointsPending}  atk ${gameState.attack} def ${gameState.defense} crit ${gameState.crit}%  ${this.player.action}  sense ${gameState.senses.sense}  ${gameState.weapon.displayName} ${gameState.weapon.personality}/${gameState.weapon.threshold}  room ${gameState.roomId || '-'}  trials ${gameState.trialsCleared}/${gameState.trialsTotal}${gameState.bossUnlocked ? ' (boss open)' : ''}${boss}  seed ${gameState.seed}`,
      );
    }
  }

  // --- 전투 ---

  private fire = (x: number, y: number, dirX: number, dirY: number, spec: ProjectileSpec): void => {
    const p = this.projectiles.get() as Projectile | null;
    if (!p) return;
    // 탄 시트 (35라운드 2단계, 계약 §3.1 projectile 앵커): 회전·원점·루프 애니는 시트 JSON 을 따른다
    const def = spec.sprite ? spriteLibrary.sheet(spec.sprite, FX_ACTION) : undefined;
    const texture = spec.sprite ? spriteLibrary.textureKey(spec.sprite, FX_ACTION) : null;
    const visual = def
      ? {
          texture,
          rotate: Boolean(def.rotate),
          originX: def.pivot.x / def.frameWidth,
          originY: def.pivot.y / def.frameHeight,
          anim: def.loop && def.frames > 1 ? spriteLibrary.animKey(spec.sprite!, FX_ACTION, 'down') : null,
        }
      : {};
    p.launch(x, y, dirX, dirY, spec, this.time.now, 'enemy', 0, visual);
  };

  /** 적이 요청하는 시트 이펙트 1회 (총구 화염). 시트가 없으면 무시 */
  private playMobFx = (id: string, x: number, y: number, opts: Parameters<MobContext['playFx']>[3]): void => {
    if (!this.fx.has(id)) return;
    this.fx.play(id, x, y, opts);
  };

  /** 같은 id 의 살아 있는 적 수 (집단 돌격 머릿수·소환 상한) */
  private countMobs = (id: string): number => {
    let n = 0;
    for (const child of this.mobs.getChildren()) {
      const m = child as Mob;
      if (m.active && m.spriteId === id) n++;
    }
    return n;
  };

  /**
   * 보스 내리찍기 범위 피해: 충격파 연출 + 흔들림 + 반경 안 플레이어 피해.
   * 46라운드 Q2: 보스 전용 `boss_slam` 시트(층 램프 + 코어, 보조색 없음)를 피벗 = 슬램 지점에 바닥 깊이로 재생하고
   * JSON flash·shake 훅을 쓴다(흔들림은 이것 하나 — BOSS_WALL 은 생략). 시트가 없으면 링 + BOSS_WALL 흔들림
   */
  private areaHit = (x: number, y: number, radiusPx: number, attack: number): void => {
    const id = ENEMY_FX.SLAM_ID;
    const def = this.fx.sheet(id);
    const fxScale = radiusFitScale(radiusPx, def?.hitRadiusPx ?? ENEMY_FX.SLAM_BASE_RADIUS_PX);
    const handle = this.fx.has(id) ? this.fx.play(id, x, y, { depth: DEPTH.FX_GROUND, scaleMult: fxScale }) : null;
    if (!handle) {
      this.drawShockwave(x, y, radiusPx);
      this.shake.add(this.time.now, FEEL.SHAKE.BOSS_WALL.PX, FEEL.SHAKE.BOSS_WALL.MS);
    }
    const c = this.player.body.center;
    const d = Phaser.Math.Distance.Between(x, y, c.x, c.y);
    const hit = d <= radiusPx + this.player.body.halfWidth;
    this.debugLastSlam = {
      x,
      y,
      radiusPx,
      attack,
      hit,
      time: this.time.now,
      fx: handle ? handle.sprite.texture.key : 'ring',
      fxScale: handle ? handle.sprite.scaleX : null,
    };
    if (!hit) return;
    const source = d > 0 ? { dirX: (c.x - x) / d, dirY: (c.y - y) / d } : undefined;
    this.player.takeHit(attack, this.time.now, source);
  };

  /** 보스 소환 → 방 상태 머신이 적을 추가하고 처치 대기 목록에 넣는다 */
  private summon = (enemyId: string, x: number, y: number): boolean => this.director.spawnExtra(enemyId, x, y);

  private onPlayerAttacked(p: PlayerAttackPayload): void {
    this.debugLastAttack = { ...p, time: this.time.now };
    const weapon = gameState.weapon;
    if (weapon.def.kind === 'ranged') {
      this.fireArrow(p);
      return;
    }
    const mods = weapon.mods;
    // 48라운드 3연격: 판정은 휘두름 프레임(hitFrames[0]) 시작에, 지진 2단·충격파는 마지막 타에서만
    const combo = p.comboIndex !== undefined;
    const finisher = !combo || p.comboIndex === (p.comboCount ?? 1) - 1;
    this.playSwingFx(p);
    this.playGiantFx(p);
    const strike = () => {
      if (!this.scene.isActive() || this.frozen || gameState.gameOver) return;
      const at = combo ? { ...p, x: this.player.x, y: this.player.y } : p;
      this.meleeSwing(at);
      // 쌍격·난무: 추가 타격. 시트 hitFrames 가 있으면 그 프레임 시작 간격(43라운드 B), 없으면 TWIN_DELAY_MS 간격
      const hits = Math.max(1, mods.hits ?? 1);
      const multiFx = this.pathFx('dance', 'twin');
      const offsets = FEEL.SYNC_HIT_FRAMES && multiFx ? hitFrameOffsets(this.fx.sheet(multiFx), hits) : null;
      for (let i = 1; i < hits; i++) {
        this.time.delayedCall(offsets?.[i] ?? PROTOTYPE.TWIN_DELAY_MS * i, () => {
          if (this.scene.isActive() && !this.frozen) this.meleeSwing({ ...at, x: this.player.x, y: this.player.y });
        });
      }
      // 지진: 충격파 2단 (quake 시트는 1단에서 한 번만 — 3프레임 시작이 2단 판정 시점)
      const second = mods.shockwaveSecond;
      if (mods.shockwave && second && finisher) {
        this.time.delayedCall(second.delayMs, () => {
          if (this.scene.isActive() && !this.frozen)
            this.meleeSwing(
              {
                ...at,
                x: this.player.x,
                y: this.player.y,
                sizeMult: at.sizeMult * second.sizeMult,
                damageMult: at.damageMult * second.damageMult,
              },
              true,
            );
        });
      }
    };
    const hitDelay = combo ? p.swingDelayMs : 0;
    if (hitDelay > 0) this.time.delayedCall(hitDelay, strike);
    else strike();
  }

  /** 48라운드: 연격 한 타의 판정 모양 (아트 메모가 있으면 그린 대로 — 타 크기 배율은 빼고 대쉬 배율만). 연격이 아니면 null */
  private swingShape(p: PlayerAttackPayload): HitShape | null {
    const w = gameState.weapon;
    const c = w.def.combo;
    if (!c || p.comboIndex === undefined) return null;
    const n = p.comboIndex + 1;
    const memo = this.fx.sheet(comboFxId(w.id, n)) ?? spriteLibrary.sheet('player', comboAction(w.id, n)) ?? null;
    const drawn = Boolean(memo && (typeof memo.hitRadiusPx === 'number' || memo.thrust));
    const hbScale = w.def.hitbox.reach > 0 ? w.hitbox.reach / w.def.hitbox.reach : 1;
    const hitSize = c.hits[p.comboIndex]?.sizeMult ?? 1;
    const size = drawn ? p.sizeMult / hitSize : p.sizeMult;
    const shape = comboShape(c, w.def.hitbox, hbScale * size, drawn ? memo : null);
    // 아트 메모에 휘두름 방향이 없으면 짝수 번째 타(2타)는 반대로
    if (shape.kind === 'arc' && !(memo && typeof memo.arcFromDeg === 'number') && p.comboIndex % 2 === 1)
      return { ...shape, fromDeg: shape.toDeg, toDeg: shape.fromDeg };
    return shape;
  }

  /** 거인(2차): 공격 애니 동안 플레이어 아래에서 슈퍼아머 오라 루프 (공격 애니 = 쿨다운에 맞춤) */
  private playGiantFx(p: PlayerAttackPayload): void {
    const id = this.pathFx('giant');
    if (!id) return;
    if (this.fx.isActive(this.giantFx)) this.fx.stop(this.giantFx, 0, false);
    this.giantFx = this.fx.play(id, this.player.x, this.player.y, {
      follow: this.player,
      depthOffset: -DEPTH.OVERLAY_STEP,
      durationMs: p.durationMs ?? gameState.weapon.hitbox.cooldownMs,
    });
  }

  /** 공격력 × 배율 × 치명타 × 패시브. 치명타 확률은 기본 + 보너스 + 무기. forceCrit 이면 확정 */
  private rollDamage(
    mult: number,
    forceCrit = false,
    kind: 'attack' | 'dashAttack' | 'aimed' | 'other' = 'other',
  ): { dmg: number; crit: boolean } {
    const crit = forceCrit || rollCrit(gameState.crit + this.structures.critBonus(), this.rng);
    const P = gameState.passives;
    const lowHp = P.lowHpThreshold() > 0 && gameState.hp / gameState.maxHp <= P.lowHpThreshold();
    const passiveMult = 1 + P.total('attackMult') + (lowHp ? P.total('lowHpAttackMult') : 0);
    const dmg = Math.round(
      gameState.attack *
        mult *
        gameState.weapon.damageMult *
        passiveMult *
        (crit ? ECONOMY.critDamageMult : 1) *
        this.structures.damageMult(kind, crit),
    );
    return { dmg, crit };
  }

  /** 활: 화살은 attack 3프레임(시위 놓음) 시작에 맞춰 생성 (시트가 없으면 즉시). 연사 판정은 입력 시점 */
  private fireArrow(p: PlayerAttackPayload): void {
    const R = gameState.weapon.def.ranged!;
    const now = this.time.now;
    const aimed = p.kind === 'aimed';
    let rapidMult = 1;
    if (!aimed) {
      this.rapidCount = now - this.lastShotAt <= R.rapidWindowMs ? this.rapidCount + 1 : 0;
      this.lastShotAt = now;
      rapidMult = Math.max(R.rapidMin, 1 - R.rapidDecay * this.rapidCount);
    }
    const release = () => {
      if (!this.scene.isActive() || this.frozen || gameState.gameOver) return;
      this.spawnArrows({ ...p, x: this.player.x, y: this.player.y }, rapidMult);
    };
    if (p.releaseDelayMs > 0) this.time.delayedCall(p.releaseDelayMs, release);
    else release();
  }

  private spawnArrows(p: PlayerAttackPayload, rapidMult: number): void {
    const weapon = gameState.weapon;
    const R = weapon.def.ranged!;
    const mods = weapon.mods;
    const now = this.time.now;
    const aimed = p.kind === 'aimed';
    const { dmg, crit } = this.rollDamage(p.damageMult * rapidMult, p.forceCrit, p.kind);
    // 조준 사격·섬광: 무한 관통
    const pierce = aimed || mods.pierceInfinite ? Infinity : (mods.pierce ?? 0);
    const size = weapon.hitbox.width * p.sizeMult;
    const speed = R.projectileSpeedTiles * TILE * (mods.projectileSpeedMult ?? 1);
    const base = Math.atan2(p.dirY, p.dirX);
    // 화살 텍스처 (계약 §3.1 projectile 앵커, 진행 각도 회전). 없으면 사각형. 중시(2차)는 조준 화살 대신 heavyarrow
    const heavy = aimed ? this.pathFx('heavyarrow') : null;
    const arrowTexture = heavy
      ? spriteLibrary.textureKey(heavy, FX_ACTION)
      : spriteLibrary.textureKey(arrowFxId(weapon.id, aimed), FX_ACTION);
    // 화살 꼬리 루프: 섬광(flash) / 추적(seek) 이 관통(pierce) 대신
    const tailFx = this.pathFx('flash', 'seek', 'pierce');
    // 산탄·폭우: 부채꼴 (조준 사격은 한 발). 발사 이펙트는 발사점에 1회 (폭우 rain 이 scatter 대신)
    const spread = !aimed && mods.spread ? mods.spread : { count: 1, spreadDeg: 0 };
    const burstFx = this.pathFx('rain', 'scatter');
    if (spread.count > 1 && burstFx) {
      this.fx.play(burstFx, p.x + p.dirX * weapon.hitbox.reach, p.y + p.dirY * weapon.hitbox.reach, {
        angle: base,
        depth: DEPTH.PROJECTILE,
      });
    }
    const n = Math.max(1, spread.count);
    for (let i = 0; i < n; i++) {
      const t = n === 1 ? 0 : i / (n - 1) - 0.5;
      const a = base + Phaser.Math.DegToRad(spread.spreadDeg) * t;
      const dx = Math.cos(a);
      const dy = Math.sin(a);
      const shot = this.playerShots.get() as Projectile | null;
      if (!shot) return;
      shot.launch(
        p.x + dx * weapon.hitbox.reach,
        p.y + dy * weapon.hitbox.reach,
        dx,
        dy,
        { speedPx: speed, attack: dmg, size, lifeMs: R.projectileLifeMs },
        now,
        'player',
        pierce,
        { texture: arrowTexture, rotate: true },
      );
      shot.crit = crit;
      if (mods.homingTurnDeg) shot.homingTurn = Phaser.Math.DegToRad(mods.homingTurnDeg);
      if (aimed && mods.aimedShotStunMs) shot.hitStunMs = mods.aimedShotStunMs;
      // 중시: 적중 시 번개 낙하(heavyarrow_hit, 섬광·흔들림은 시트 JSON)
      if (heavy && this.fx.has('heavyarrow_hit')) shot.impactFx = 'heavyarrow_hit';
      // 관통·섬광·추적: 화살 뒤에 빛줄 루프, 화살이 사라지면 함께 사라진다
      if (tailFx) {
        this.fx.play(tailFx, shot.x, shot.y, {
          angle: a,
          follow: shot,
          followRotation: true,
          depth: DEPTH.PROJECTILE - 0.01,
        });
      }
    }
  }

  /**
   * 현재 개성 경로에 있고 시트가 로드된 첫 후보 id. 2차 노드를 앞에, 그것이 대신하는 1차 노드를 뒤에 적는다
   * (예: `pathFx('wide', 'iai')` = 만월이 있으면 만월, 아니면 거합). 아무것도 없으면 null → 호출 쪽 플레이스홀더
   */
  private pathFx(...candidates: string[]): string | null {
    const path = gameState.weapon.path;
    for (const id of candidates) if (path.includes(id) && this.fx.has(id)) return id;
    return null;
  }

  /** 1차 진화 이펙트 id = 경로의 첫 노드. 시트가 없으면 null (질풍·발도술 루프 판정용) */
  private evolutionFxId(): string | null {
    const first = gameState.weapon.path[0];
    return first && this.fx.has(first) ? first : null;
  }

  /**
   * 근접 베기 이펙트 (계약 §3.1): 플레이어 attack 2프레임(휘두름) 시작에 발 피벗 앵커로 재생.
   * 거합·쌍격은 기본 베기를 대신하고, 파쇄·중압은 적중 판정 쪽(meleeSwing)에서 따로 나온다.
   */
  private playSwingFx(p: PlayerAttackPayload): void {
    const weapon = gameState.weapon;
    // 2차가 1차를 대신한다: 만월(wide) → 거합(iai), 난무(dance) → 쌍격(twin). 그 외는 기본 베기
    const evo = this.pathFx('wide', 'iai', 'dance', 'twin');
    // 48라운드 3연격: 연격 시트가 있으면 타마다 그 시트, 진화 베기는 마지막 타에 (연격 시트가 없으면 기존처럼 매 타 진화 베기)
    const combo = p.comboIndex !== undefined;
    const finisher = !combo || p.comboIndex === (p.comboCount ?? 1) - 1;
    const comboId = combo ? comboFxId(weapon.id, p.comboIndex! + 1) : null;
    const id = comboId && this.fx.has(comboId) ? (finisher && evo ? evo : comboId) : (evo ?? slashFxId(weapon.id));
    const dir = facingOf(p.dirX, p.dirY, this.player.facingDir);
    const hb = weapon.hitbox;
    const shape = this.swingShape(p);
    // 잔상 궤적(42라운드, fx-design §6.1): 플레이어 중심의 호를 SLASH_SWEEP_MS 동안 훑는다. 첫 샘플 시각부터 잰다
    const T = FEEL.TRAIL;
    const base = Math.atan2(p.dirY, p.dirX);
    let radius = hb.reach * p.sizeMult * T.SLASH_RADIUS_MULT + hb.width * 0.5;
    let mid = base;
    let half = T.SLASH_HALF_ANGLE * (dir === 'left' || dir === 'up' ? -1 : 1);
    if (shape?.kind === 'arc') {
      // 48라운드: 판정 호 그대로 (from→to = 휘두름 방향, left 는 좌우 반전)
      const from = base + Phaser.Math.DegToRad(facingAngle(shape.fromDeg, dir));
      const to = base + Phaser.Math.DegToRad(facingAngle(shape.toDeg, dir));
      radius = shape.radius;
      mid = (from + to) / 2;
      half = (to - from) / 2;
    }
    const sweep = Math.max(p.activeMs ?? hb.activeMs, T.SLASH_SWEEP_MS);
    const centerUp = combo ? HIT_ORIGIN_UP_PX : 0;
    const arcSource = () => {
      let t0 = -1;
      return () => {
        if (t0 < 0) t0 = this.time.now;
        const t = (this.time.now - t0) / sweep;
        if (t > 1 || !this.player.active) return null;
        const c = combo ? { x: this.player.x, y: this.player.y - centerUp } : this.player.getCenter();
        if (shape?.kind === 'thrust') {
          // 찌르기: 몸 중심에서 앞으로 뻗는 직선
          const d = rotateDir(p.dirX, p.dirY, facingAngle(shape.angleDeg, dir));
          const r = shape.fromPx + shape.length * Math.min(1, t * 1.5);
          return { x: c.x + d.x * r, y: c.y + d.y * r };
        }
        return arcPoint(c.x, c.y, radius, mid, half, t);
      };
    };
    const play = () => {
      if (!this.scene.isActive() || this.frozen || gameState.gameOver) return;
      // 시트 JSON trail 이 있으면 FxPool 이 fromFrame 에 같은 호로 리본을 시작(색·수명·폭은 JSON). 없으면 기본 리본을 바로
      const sheetTrail = this.fx.has(id) && Boolean(this.fx.sheet(id)?.trail);
      if (this.fx.has(id))
        this.fx.play(id, this.player.x, this.player.y, {
          dir,
          follow: this.player,
          depthOffset: DEPTH.OVERLAY_STEP * 2,
          trailSource: sheetTrail ? arcSource() : undefined,
        });
      if (!sheetTrail)
        this.trails.start('slash', arcSource(), { depth: entityDepth(this.player.y) + DEPTH.OVERLAY_STEP * 3 });
    };
    const lead = this.fx.leadMs(id);
    const delay = Math.max(0, p.swingDelayMs - lead);
    if (delay > 0) this.time.delayedCall(delay, play);
    else play();
  }

  /** 질풍: 이동·대쉬 중 플레이어 아래에서 바람 루프, 멈추면 끈다 */
  private updateGale(): void {
    const want =
      this.evolutionFxId() === 'gale' && (this.player.moving || this.player.action === 'dash') && !gameState.gameOver;
    if (!want) {
      this.stopGale();
      return;
    }
    const dir = this.player.facingDir;
    if (this.fx.isActive(this.galeFx)) this.fx.setDir(this.galeFx, 'gale', dir);
    else
      this.galeFx = this.fx.play('gale', this.player.x, this.player.y, {
        dir,
        follow: this.player,
        depth: DEPTH.FX_GROUND,
      });
  }

  private stopGale(): void {
    if (this.fx.isActive(this.galeFx)) this.fx.stop(this.galeFx);
    this.galeFx = null;
  }

  private onPlayerShotHit(shot: Projectile, mob: Mob): void {
    if (!shot.active || shot.owner !== 'player') return;
    const v = shot.body.velocity;
    const dirX = v.x;
    const dirY = v.y;
    if (!shot.registerHit(mob)) return;
    const now = this.time.now;
    const stunnedByParry = mob.isParryStunned(now);
    // 중시: 적중 번개 낙하 (히트박스 중심, 개체 위)
    if (shot.impactFx && this.fx.has(shot.impactFx)) {
      const c = mob.body.center;
      this.fx.play(shot.impactFx, c.x, c.y, { depth: DEPTH.HIT_FX + 0.02 });
    }
    if (this.hitMob(mob, shot.attack, { crit: shot.crit, dirX, dirY })) {
      this.onKill(mob, stunnedByParry ? 'parry' : 'attack');
      return;
    }
    this.structures.onMobHit(mob, shot.fire);
    if (shot.hitStunMs > 0) mob.stun(now, shot.hitStunMs, 'hit');
  }

  private meleeSwing(p: PlayerAttackPayload, secondWave = false): void {
    const weapon = gameState.weapon;
    const mods = weapon.mods;
    const hb = weapon.hitbox;
    // 48라운드 3연격: 몸 중심(발 위 10px) 부채꼴·찌르기 판정. 물리 영역은 외접 사각형이고 겹친 적을 모양으로 다시 거른다
    const shape = this.swingShape(p);
    const facing = facingOf(p.dirX, p.dirY, this.player.facingDir);
    const ox = p.x;
    const oy = p.y - HIT_ORIGIN_UP_PX;
    let cx: number;
    let cy: number;
    let w: number;
    let h: number;
    if (shape) {
      const b = hitShapeBounds(ox, oy, p.dirX, p.dirY, shape, facing);
      cx = b.x + b.w / 2;
      cy = b.y + b.h / 2;
      w = Math.max(1, b.w);
      h = Math.max(1, b.h);
    } else {
      cx = p.x + p.dirX * hb.reach * p.sizeMult;
      cy = p.y + p.dirY * hb.reach * p.sizeMult;
      // Arcade 바디는 축 정렬 사각형이라 지배적인 축에 맞춰 폭·높이를 바꿔 근사한다.
      const horizontal = Math.abs(p.dirX) >= Math.abs(p.dirY);
      w = (horizontal ? hb.width : hb.height) * p.sizeMult;
      h = (horizontal ? hb.height : hb.width) * p.sizeMult;
    }
    const finisher = p.comboIndex === undefined || p.comboIndex === (p.comboCount ?? 1) - 1;
    const activeMs = p.activeMs ?? hb.activeMs;
    // 47라운드: 타격형 구조물·화로 점화·불붙은 무기의 웅덩이 점화
    this.structures.onMeleeSwing(cx, cy, w, h, p.dirX, p.dirY);
    // 베기 시트가 있으면 판정 사각형은 보이지 않게(판정만), 없으면 기존 플레이스홀더 표시
    const evoFx = this.evolutionFxId();
    const swingFx = this.pathFx('wide', 'iai', 'dance', 'twin');
    const comboFx = p.comboIndex !== undefined ? comboFxId(weapon.id, p.comboIndex + 1) : null;
    const hasSwingArt =
      this.fx.has(slashFxId(weapon.id)) || swingFx !== null || (comboFx !== null && this.fx.has(comboFx));
    // 연격 판정은 모양이라 사각형 플레이스홀더를 그리지 않는다 (시트가 없으면 모양 윤곽)
    const zone = this.add.rectangle(cx, cy, w, h, COLORS.ATTACK, hasSwingArt || shape ? 0 : 0.6).setDepth(DEPTH.ATTACK);
    if (shape && !hasSwingArt) this.drawShapeOutline(ox, oy, p.dirX, p.dirY, shape, facing);
    // 궤적·충격파: 시트가 있으면 시트, 없으면 Graphics 플레이스홀더
    if (mods.slashTrail && !swingFx) this.drawSlashTrail(cx, cy, p.dirX, p.dirY, Math.max(w, h));
    if (mods.shockwave && finisher) {
      // 지진(quake)·분쇄(pulverize) 가 파쇄(crush) 대신. quake 는 1단에서 한 번(3프레임 = 2단 시점), 2단은 다시 안 그린다
      const shockFx = this.pathFx('quake', 'pulverize', 'crush');
      if (shockFx === 'quake' && secondWave) {
        /* 1단에서 재생한 quake 의 3~5프레임이 2단 링 */
      } else if (shockFx) this.fx.play(shockFx, cx, cy, { depth: DEPTH.FX_GROUND });
      else this.drawShockwave(cx, cy, Math.max(w, h));
      this.shake.add(this.time.now, FEEL.SHAKE.SHOCKWAVE.PX, FEEL.SHAKE.SHOCKWAVE.MS);
    }
    // 중압: 적중 판정 시작에 히트박스 중심 아래 6px (피벗 = 바닥 타격점)
    if (evoFx === 'weight') this.fx.play('weight', cx, cy + PROTOTYPE.WEIGHT_FX_DROP_PX, { depth: DEPTH.ATTACK });
    this.physics.add.existing(zone);
    (zone.body as Phaser.Physics.Arcade.Body).setAllowGravity(false);

    const hit = new Set<Mob>();
    const swingLog = {
      shape,
      origin: { x: ox, y: oy },
      dir: { x: p.dirX, y: p.dirY },
      facing,
      bounds: { cx, cy, w, h },
      comboIndex: p.comboIndex ?? null,
      activeMs,
      hits: 0,
      time: this.time.now,
    };
    this.debugLastSwing = swingLog;
    const overlap = this.physics.add.overlap(zone, this.mobs, (_z, m) => {
      const mob = m as Mob;
      if (hit.has(mob)) return;
      if (shape) {
        const b = mob.body;
        const target = { x: b.center.x, y: b.center.y, r: Math.min(b.halfWidth, b.halfHeight) };
        if (!shapeHit(ox, oy, p.dirX, p.dirY, shape, target, facing)) return;
      }
      hit.add(mob);
      swingLog.hits += 1;
      this.applyMeleeHit(mob, p);
    });
    // 분쇄: 충격파 범위의 적 투사체 소멸
    const clear =
      mods.shockwave && finisher && mods.shockwaveClearsProjectiles
        ? this.physics.add.overlap(zone, this.projectiles, (_z, pr) => {
            const proj = pr as Projectile;
            if (proj.active && !proj.reflected) proj.deactivate();
          })
        : null;
    // 잔월: 궤적이 남아 지속 피해
    if (mods.trailDot) {
      const now = this.time.now;
      const { dmg } = this.rollDamage(p.damageMult * mods.trailDot.damageMult);
      this.dotZones.push({
        x: cx,
        y: cy,
        w,
        h,
        until: now + mods.trailDot.lingerMs,
        nextAt: now + mods.trailDot.tickMs,
        tickMs: mods.trailDot.tickMs,
        dmg,
      });
      const zangetsu = this.pathFx('zangetsu');
      const dot = this.dotZones[this.dotZones.length - 1];
      if (zangetsu && swingFx) {
        // 잔월(2차 전용 시트): 거합이 끝난 자리(고정)에 루프, 한 바퀴 = 틱 간격이 되도록 틱을 루프 시작에 맞춘다. 바닥 깊이
        const start = p.swingDelayMs + this.fx.durationOf(swingFx);
        const linger = mods.trailDot.lingerMs - start;
        if (linger > 0) {
          const dir = facingOf(p.dirX, p.dirY, this.player.facingDir);
          const at = { x: p.x, y: p.y };
          this.time.delayedCall(start, () => {
            if (!this.scene.isActive()) return;
            this.fx.play(zangetsu, at.x, at.y, { dir, depth: DEPTH.FX_GROUND, durationMs: linger });
            dot.nextAt = this.time.now + dot.tickMs;
          });
        }
      } else if (swingFx === 'iai') {
        // 잔월(시트 없음): 거합 이펙트의 꼬리(마지막 3프레임)를 본 재생이 끝난 뒤 남은 시간 동안 반복
        const start = p.swingDelayMs + this.fx.durationOf('iai');
        const linger = mods.trailDot.lingerMs - start;
        if (linger > 0) {
          const dir = facingOf(p.dirX, p.dirY, this.player.facingDir);
          const at = { x: p.x, y: p.y, depth: entityDepth(p.y) + DEPTH.OVERLAY_STEP * 2 };
          this.time.delayedCall(start, () => {
            if (this.scene.isActive())
              this.fx.play('iai', at.x, at.y, { dir, depth: at.depth, durationMs: linger, tailFrames: 3 });
          });
        }
      } else {
        const g = this.add.rectangle(cx, cy, w, h, COLORS.TRAIL_DOT, 0.35).setDepth(DEPTH.ATTACK);
        this.tweens.add({ targets: g, alpha: 0, duration: mods.trailDot.lingerMs, onComplete: () => g.destroy() });
      }
    }

    this.time.delayedCall(activeMs, () => {
      this.physics.world.removeCollider(overlap);
      if (clear) this.physics.world.removeCollider(clear);
      zone.destroy();
    });
  }

  /** 연격 판정 모양 윤곽 (시트가 없을 때 플레이스홀더) */
  private drawShapeOutline(ox: number, oy: number, dirX: number, dirY: number, shape: HitShape, facing: Facing): void {
    const g = this.add.graphics().setDepth(DEPTH.ATTACK);
    g.lineStyle(1, COLORS.ATTACK, 0.8);
    g.fillStyle(COLORS.ATTACK, 0.25);
    if (shape.kind === 'arc') {
      const c = rotateDir(dirX, dirY, facingAngle(shape.centerDeg, facing));
      const a = Math.atan2(c.y, c.x);
      const half = Phaser.Math.DegToRad(shape.arcDeg / 2);
      g.slice(ox, oy, shape.radius, a - half, a + half, false);
      g.fillPath();
      g.strokePath();
    } else {
      const d = rotateDir(dirX, dirY, facingAngle(shape.angleDeg, facing));
      const px = -d.y * (shape.width / 2);
      const py = d.x * (shape.width / 2);
      const sx = ox + d.x * shape.fromPx;
      const sy = oy + d.y * shape.fromPx;
      const ex = sx + d.x * shape.length;
      const ey = sy + d.y * shape.length;
      const pts = [
        new Phaser.Math.Vector2(sx + px, sy + py),
        new Phaser.Math.Vector2(ex + px, ey + py),
        new Phaser.Math.Vector2(ex - px, ey - py),
        new Phaser.Math.Vector2(sx - px, sy - py),
      ];
      g.fillPoints(pts, true);
      g.strokePoints(pts, true);
    }
    this.tweens.add({ targets: g, alpha: 0, duration: PROTOTYPE.SLASH_TRAIL_MS, onComplete: () => g.destroy() });
  }

  /** 근접 타격 1회: 피해 → (사망) 또는 중압 경직·출혈 */
  private applyMeleeHit(mob: Mob, p: PlayerAttackPayload): void {
    const now = this.time.now;
    const mods = gameState.weapon.mods;
    const stunnedByParry = mob.isParryStunned(now);
    const { dmg, crit } = this.rollDamage(p.damageMult, p.forceCrit, p.kind);
    // 2차 전용 치명 이펙트: 급소(대쉬 베기 적중) → dashcrit, 암살(그림자 걸음 직후) → assassin. 둘 다 crit_burst 대신
    const critFx = p.primed ? this.pathFx('assassin') : p.kind === 'dashAttack' ? this.pathFx('dashcrit') : null;
    if (this.hitMob(mob, dmg, { crit, dirX: p.dirX, dirY: p.dirY, critFx })) {
      this.onKill(mob, stunnedByParry ? 'parry' : p.kind === 'aimed' ? 'attack' : p.kind);
      return;
    }
    this.structures.onMobHit(mob, false);
    if (mods.hitStunMs) mob.stun(now, mods.hitStunMs, 'hit');
    if (mods.bleed) {
      const B = mods.bleed;
      const tick = Math.max(1, Math.round(gameState.attack * gameState.weapon.damageMult * B.damageMult));
      const cur = this.bleeds.find((b) => b.mob === mob);
      if (cur) {
        cur.ticksLeft = B.ticks;
        cur.dmg = Math.max(cur.dmg, tick);
        // 재적중: 루프를 다시 시작해 0프레임(글린트) = 다음 틱에 맞춘다
        cur.nextAt = now + B.tickMs;
        if (this.fx.isActive(cur.fx)) this.fx.stop(cur.fx, 0, false);
        cur.fx = this.playBleedFx(mob);
      } else
        this.bleeds.push({
          mob,
          dmg: tick,
          ticksLeft: B.ticks,
          nextAt: now + B.tickMs,
          tickMs: B.tickMs,
          fx: this.playBleedFx(mob),
        });
    }
  }

  /** 출혈(2차): 적 히트박스 중심에 붙어 루프 (한 바퀴 = 틱 간격, 아트 JSON). 시트가 없으면 null */
  private playBleedFx(mob: Mob): FxHandle | null {
    const id = this.pathFx('bleed');
    if (!id) return null;
    const c = mob.body.center;
    return this.fx.play(id, c.x, c.y, {
      follow: mob,
      followOffset: { x: c.x - mob.x, y: c.y - mob.y },
      depthOffset: DEPTH.OVERLAY_STEP * 3,
    });
  }

  /** 추적: 플레이어 화살이 가장 가까운 적을 향해 선회 */
  private tickHoming(delta: number): void {
    for (const child of this.playerShots.getChildren()) {
      const shot = child as Projectile;
      if (!shot.active || shot.homingTurn <= 0) continue;
      const target = this.nearestMob(shot.x, shot.y, Infinity);
      if (target) shot.steerToward(target.x, target.y, delta);
    }
  }

  /** 잔월: 남은 궤적 영역이 주기마다 겹친 적에게 피해 */
  private tickDotZones(time: number): void {
    if (this.dotZones.length === 0) return;
    for (const z of this.dotZones) {
      if (time < z.nextAt) continue;
      z.nextAt = time + z.tickMs;
      const bodies = this.physics.overlapRect(z.x - z.w / 2, z.y - z.h / 2, z.w, z.h, true, false);
      for (const b of bodies) {
        const go = (b as Phaser.Physics.Arcade.Body).gameObject as unknown;
        if (!this.mobs.contains(go as Phaser.GameObjects.GameObject)) continue;
        const mob = go as Mob;
        if (!mob.active) continue;
        if (this.hitMob(mob, z.dmg, { crit: false, dirX: 0, dirY: 0, tick: true })) this.onKill(mob, 'attack');
      }
    }
    this.dotZones = this.dotZones.filter((z) => time < z.until);
  }

  /** 출혈: 주기마다 피해, 횟수 소진·적 사망 시 제거 */
  private tickBleeds(time: number): void {
    if (this.bleeds.length === 0) return;
    for (const b of this.bleeds) {
      if (!b.mob.active || time < b.nextAt) continue;
      b.nextAt = time + b.tickMs;
      b.ticksLeft -= 1;
      if (this.hitMob(b.mob, b.dmg, { crit: false, dirX: 0, dirY: 0, tick: true })) this.onKill(b.mob, 'attack');
      else b.mob.flashColor(COLORS.BLEED);
    }
    for (const b of this.bleeds) {
      if (b.mob.active && b.ticksLeft > 0) continue;
      if (this.fx.isActive(b.fx)) this.fx.stop(b.fx);
    }
    this.bleeds = this.bleeds.filter((b) => b.mob.active && b.ticksLeft > 0);
  }

  private nearestMob(x: number, y: number, maxDist: number): Mob | null {
    let best: Mob | null = null;
    let bestD = maxDist * maxDist;
    for (const child of this.mobs.getChildren()) {
      const m = child as Mob;
      if (!m.active) continue;
      const d = (m.x - x) ** 2 + (m.y - y) ** 2;
      if (d < bestD) {
        bestD = d;
        best = m;
      }
    }
    return best;
  }

  // --- 우클릭 보조 동작 (27라운드): 가드 해제 밀쳐내기 · 그림자 걸음 · 잔상 ---

  private onGuardReleased(p: GuardReleasedPayload): void {
    const S = gameState.weapon.def.secondary;
    if (S.kind !== 'guard') return;
    const now = this.time.now;
    const radius = S.pushRadiusTiles * TILE;
    const counter = gameState.weapon.mods.guardCounterMult ?? 0;
    // 가드 밀쳐내기 충격파(guard_wave, 발 피벗·바라보는 방향·바닥 깊이) + 철벽이면 ironwall 벽 섬광(위) 동시. 시트가 없으면 링
    const dir = this.player.facingDir;
    if (this.fx.has('guard_wave')) this.fx.play('guard_wave', p.x, p.y, { dir, depth: DEPTH.FX_GROUND });
    else {
      const g = this.add.graphics().setDepth(DEPTH.ATTACK);
      g.lineStyle(2, COLORS.GUARD_PUSH, 0.9);
      g.strokeCircle(p.x, p.y, radius);
      this.tweens.add({ targets: g, alpha: 0, duration: PROTOTYPE.GUARD_PUSH_MS, onComplete: () => g.destroy() });
    }
    this.structures.onPush(p.x, p.y, radius);
    const ironwall = counter > 0 ? this.pathFx('ironwall') : null;
    if (ironwall) this.fx.play(ironwall, p.x, p.y, { dir, depth: entityDepth(p.y) + DEPTH.OVERLAY_STEP * 3 });
    for (const child of [...this.mobs.getChildren()]) {
      const m = child as Mob;
      if (!m.active) continue;
      const dx = m.x - p.x;
      const dy = m.y - p.y;
      const d = Math.hypot(dx, dy);
      if (d > radius) continue;
      const nx = d > 0 ? dx / d : 1;
      const ny = d > 0 ? dy / d : 0;
      m.knockback(now, nx, ny, S.pushSpeedTiles * TILE, S.pushMs);
      if (counter > 0) {
        // 철벽: 밀쳐내며 반격
        const { dmg } = this.rollDamage(counter);
        if (this.hitMob(m, dmg, { crit: false, dirX: nx, dirY: ny, knock: false })) this.onKill(m, 'attack');
      }
    }
  }

  private onShadowStep(p: ShadowStepPayload): void {
    const S = gameState.weapon.def.secondary;
    if (S.kind !== 'shadowstep') return;
    const target = this.nearestMob(p.x, p.y, S.rangeTiles * TILE);
    const [pw, ph] = PLAYER_DATA.size;
    const half = Math.max(pw, ph) / 2;
    let dest: { x: number; y: number } | null = null;
    if (target) {
      const dx = target.x - p.x;
      const dy = target.y - p.y;
      const d = Math.hypot(dx, dy) || 1;
      const nx = dx / d;
      const ny = dy / d;
      const off = Math.max(target.body.width, target.body.height) / 2 + half + 2;
      const behind = { x: target.x + nx * off, y: target.y + ny * off };
      const front = { x: target.x - nx * off, y: target.y - ny * off };
      dest = this.world.isWalkableAt(behind.x, behind.y)
        ? behind
        : this.world.isWalkableAt(front.x, front.y)
          ? front
          : null;
    } else {
      const fx = p.facingX || 1;
      const fy = p.facingY;
      // 바라보는 방향으로 fallbackTiles, 막히면 한 칸씩 줄인다
      for (let tiles = S.fallbackTiles; tiles > 0; tiles -= 1) {
        const c = { x: p.x + fx * tiles * TILE, y: p.y + fy * tiles * TILE };
        if (this.world.isWalkableAt(c.x, c.y)) {
          dest = c;
          break;
        }
      }
    }
    if (!dest) return;
    // 출발 잔상: shadowstep_ghost(출발 위치 고정, 보던 방향, 플레이어 아래). 시트가 없으면 사각형
    if (this.fx.has('shadowstep_ghost')) {
      this.fx.play('shadowstep_ghost', p.x, p.y, {
        dir: facingOf(p.facingX, p.facingY, this.player.facingDir),
        depth: entityDepth(p.y) - DEPTH.OVERLAY_STEP,
      });
    } else {
      const ghost = this.add.rectangle(p.x, p.y, pw, ph, COLORS.PLAYER_SHADOW, 0.6).setDepth(DEPTH.ATTACK);
      this.tweens.add({
        targets: ghost,
        alpha: 0,
        duration: PROTOTYPE.SHADOW_STEP_MS,
        onComplete: () => ghost.destroy(),
      });
    }
    this.player.teleportTo(dest.x, dest.y);
  }

  /**
   * 대쉬 시작: 출발 먼지(dash_dust, 고정) · 발도술(플레이어 아래, 따라감, JSON 리본) · 허보(longinvuln, 따라감, 위, JSON 리본) ·
   * 잔상(afterimage, 출발점 고정 분신) · 잔상 피해 영역(대쉬 경로)
   */
  private onPlayerDashed(p: { dirX: number; dirY: number; x: number; y: number }): void {
    const dir = facingOf(p.dirX, p.dirY, this.player.facingDir);
    const now = this.time.now;
    if (this.fx.has('dash_dust')) this.fx.play('dash_dust', p.x, p.y, { dir, depth: DEPTH.FX_GROUND });
    this.dashTrailNextAt = now; // 첫 dash_trail 은 다음 update 에서
    // 대쉬 베기 리본은 batto·longinvuln 시트 JSON trail 이 그린다(fx-design §6.1: 대쉬 베기만). 허보가 있으면 리본은 허보 쪽 하나만
    const longinvuln = this.pathFx('longinvuln');
    if (this.evolutionFxId() === 'batto') {
      this.fx.play('batto', p.x, p.y, { dir, follow: this.player, depth: DEPTH.FX_GROUND, hooks: !longinvuln });
    }
    if (longinvuln)
      this.fx.play(longinvuln, p.x, p.y, { dir, follow: this.player, depthOffset: DEPTH.OVERLAY_STEP * 3 });
    this.structures.onDash(p.x, p.y, p.dirX, p.dirY, PLAYER_DATA.dash.distanceTiles * TILE);
    const afterimage = this.pathFx('afterimage');
    if (afterimage) this.fx.play(afterimage, p.x, p.y, { dir, depth: entityDepth(p.y) - DEPTH.OVERLAY_STEP });
    const mult = gameState.weapon.mods.dashTrailDamageMult;
    if (!mult) return;
    const D = PLAYER_DATA.dash;
    const len = D.distanceTiles * TILE;
    const [pw] = PLAYER_DATA.size;
    const cx = p.x + p.dirX * len * 0.5;
    const cy = p.y + p.dirY * len * 0.5;
    const horizontal = Math.abs(p.dirX) >= Math.abs(p.dirY);
    const w = horizontal ? len : pw;
    const h = horizontal ? pw : len;
    const zone = this.add.rectangle(cx, cy, w, h, COLORS.DASH_TRAIL, 0.35).setDepth(DEPTH.ATTACK);
    this.physics.add.existing(zone);
    (zone.body as Phaser.Physics.Arcade.Body).setAllowGravity(false);
    const hit = new Set<Mob>();
    const overlap = this.physics.add.overlap(zone, this.mobs, (_z, m) => {
      const mob = m as Mob;
      if (hit.has(mob)) return;
      hit.add(mob);
      const { dmg } = this.rollDamage(mult);
      if (this.hitMob(mob, dmg, { crit: false, dirX: p.dirX, dirY: p.dirY })) this.onKill(mob, 'dashAttack');
    });
    this.time.delayedCall(D.durationMs, () => {
      this.physics.world.removeCollider(overlap);
      this.tweens.add({
        targets: zone,
        alpha: 0,
        duration: PROTOTYPE.SLASH_TRAIL_MS,
        onComplete: () => zone.destroy(),
      });
    });
  }

  // --- 개성: 적립 → 임계 → 3지선다 (변환 A / 변환 B / 강화) ---

  private onKill(mob: Mob, kind: KillKind): void {
    gameState.kills += 1;
    // 47라운드: 판돈 종·룰렛 '배수 판' 배율
    const km = this.structures.killMods();
    this.dropLoot(mob, km.goldMult);
    this.gainPersonality(
      Math.round(mob.personalityValue * (1 + gameState.passives.total('personalityMult')) * km.personalityMult),
    );
    const lifesteal = gameState.passives.total('healOnKill');
    if (lifesteal > 0) this.player.heal(lifesteal);
    if (gameState.senses.recordKill(kind)) {
      EventBus.emit(Events.SENSE_GAINED, { kind, sense: gameState.senses.sense });
    }
    this.director.onMobDied(mob);
  }

  /** 개성 수치 적립. 임계에 닿으면 선택 대기 → update 에서 메뉴를 연다 */
  private gainPersonality(amount: number): void {
    const weapon = gameState.weapon;
    const reached = weapon.gainPersonality(amount);
    EventBus.emit(Events.PERSONALITY_GAINED, { value: weapon.personality, threshold: weapon.threshold });
    if (reached) EventBus.emit(Events.WEAPON_CHOICE_PENDING, { weapon: weapon.id, stage: weapon.stage });
  }

  private openEvolveMenu(): void {
    const w = gameState.weapon;
    const options = w.options;
    if (!w.canEvolve) {
      w.choicePending = false;
      return;
    }
    this.setFrozen(true);
    const lines = [0, 1].map((i) => {
      const o = options[i] as WeaponEvolution | undefined;
      return {
        key: String(i + 1),
        label: o ? o.name : '변환 (완료)',
        enabled: Boolean(o),
        detail: o?.description,
      };
    });
    const cur = w.evolution ? w.evolution.name : w.def.name;
    const bonusPct = Math.round(WEAPON_RULES.reinforceBonus * 100);
    lines.push({
      key: '3',
      label: `${fill(STORY.ui.evolveMenu.reinforceItem, { n: w.reinforce + 1 })} — ${cur}`,
      enabled: w.canReinforce,
      detail: `피해·범위 +${bonusPct}% · 강화 ${w.reinforce}/${WEAPON_RULES.reinforceMax}`,
    });
    this.menu.open(
      'evolve',
      fill(STORY.ui.evolveMenu.title, { weapon: w.def.name, threshold: w.threshold }),
      lines,
      (key) => {
        if (key === '3') this.applyReinforce();
        else {
          const pick = options[Number(key) - 1];
          if (pick) this.applyEvolution(pick.id);
        }
      },
      STORY.ui.evolveMenu.footer,
    );
  }

  private applyEvolution(id: string): void {
    const weapon = gameState.weapon;
    const node = weapon.choose(id);
    if (!node) return;
    this.menu.close();
    this.setFrozen(false);
    this.screenFx.evolve();
    const payload: WeaponEvolvedPayload = { weapon: weapon.id, stage: weapon.stage, name: weapon.displayName };
    EventBus.emit(Events.WEAPON_EVOLVED, payload);
    if (!__system.rendererRegistered()) this.showEvolutionBanner(weapon.displayName);
    this.story('evolution', evolutionLine(node.name));
  }

  private applyReinforce(): void {
    const weapon = gameState.weapon;
    if (!weapon.reinforceNow()) return;
    this.menu.close();
    this.setFrozen(false);
    const payload: WeaponReinforcedPayload = {
      weapon: weapon.id,
      reinforce: weapon.reinforce,
      name: weapon.displayName,
    };
    EventBus.emit(Events.WEAPON_REINFORCED, payload);
    __system.emit(UI_EVENTS.WEAPON_EVOLVED, { name: weapon.displayName });
    if (!__system.rendererRegistered()) this.showEvolutionBanner(weapon.displayName);
    this.story(
      'evolution',
      STORY.reinforce[weapon.reinforce - 1] ??
        fill(STORY.reinforceBanner, { evolution: weapon.displayName, n: weapon.reinforce }),
    );
  }

  // --- 엔딩 (23라운드): 황제 처치 직후 2지선다, 선택 전까지 정지 ---

  private beginEnding(): void {
    this.setFrozen(true);
    this.player.body.setVelocity(0, 0);
    this.stopGale();
    const E = STORY.endings;
    const lines = [
      { key: '1', label: E.choice[0], enabled: true, detail: E.destroy },
      { key: '2', label: E.choice[1], enabled: true, detail: E.understand },
    ];
    this.menu.open('ending', E.title, lines, (key) => this.chooseEnding(key === '2' ? 'understand' : 'destroy'));
  }

  /** 선택: 세이브 삭제·정산(공통) → '이해한다' 는 도감에 기록 → 자막 → 결과 화면 */
  private chooseEnding(choice: EndingChoice): void {
    if (gameState.ending) return;
    gameState.ending = choice;
    this.menu.close();
    EventBus.emit(Events.ENDING_CHOSEN, { choice });
    this.saveSlot.clear();
    this.settleRun(true);
    if (choice === 'understand') metaStore.write(markUnderstood(metaStore.read()));
    this.story('death', STORY.endings[choice]);
    this.time.delayedCall(PROTOTYPE.CLEAR_DELAY_MS, () => this.endRunScene(true));
  }

  /** 3지선다·엔딩 선택 동안 게임 정지 (물리·적·플레이어). 메뉴는 UI 가 그린다 */
  private setFrozen(on: boolean): void {
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

  // --- 피격 피드백 (35라운드 1단계): 적중점 → 피해 → 숫자·섬광·피·치명 버스트 → 히트스톱·흔들림·넉백 ---

  /**
   * 적 피격 공통 경로. `dir` 은 공격 진행 방향(넉백 방향). `tick` 이면 작은 숫자만.
   * `knock: false` 면 넉백 생략(가드 밀쳐내기처럼 이미 밀고 있을 때). 반환: 사망
   */
  private hitMob(
    mob: Mob,
    dmgIn: number,
    opts: {
      crit: boolean;
      dirX: number;
      dirY: number;
      tick?: boolean;
      knock?: boolean;
      /** 2차 전용 치명 이펙트 id (대상 히트박스 중심에) */
      critFx?: string | null;
    },
  ): boolean {
    let dmg = dmgIn;
    const body = mob.body;
    const c = body.center;
    const hw = body.halfWidth;
    const hh = body.halfHeight;
    const len = Math.hypot(opts.dirX, opts.dirY) || 1;
    const nx = opts.dirX / len;
    const ny = opts.dirY / len;
    // 적중점 = 공격이 들어온 쪽 가장자리, 피는 반대쪽(뒤)으로
    const hitX = c.x - nx * hw * 0.6;
    const hitY = c.y - ny * hh * 0.6;
    const backX = c.x + nx * hw * 0.5;
    const backY = c.y + ny * hh * 0.5;
    const isBoss = mob.isBoss;
    const now = this.time.now;
    // 방패 막기(35라운드 2단계): 정면에서 온 공격은 피해 감소, 섬광만, 넉백·피 없음. 틱 피해는 막지 않는다
    const block = opts.tick ? 0 : mob.guardReduction(nx, ny, now);
    if (block > 0) dmg = Math.max(1, Math.round(dmg * (1 - block)));
    const died = mob.takeDamage(dmg, { crit: opts.crit, tick: opts.tick });
    if (opts.tick) {
      this.numbers.show(hitX, hitY, dmg, 'tick');
      return died;
    }
    this.numbers.show(hitX, hitY, dmg, opts.crit ? 'crit' : 'hit');
    if (block > 0) {
      this.hitFx.spark(hitX, hitY, nx, ny);
      this.hitStop.request(now, FEEL.HITSTOP.HIT_MS);
      this.shake.add(now, FEEL.SHAKE.HIT.PX, FEEL.SHAKE.HIT.MS);
      return died;
    }
    this.hitFx.impact(hitX, hitY, nx, ny, opts.crit, opts.critFx ? { id: opts.critFx, x: c.x, y: c.y } : null);
    this.hitFx.blood(c.x, c.y, backX, backY, nx, ny);
    if (opts.crit) this.screenFx.crit();
    const H = FEEL.HITSTOP;
    this.hitStop.request(now, Math.max(opts.crit ? H.CRIT_MS : H.HIT_MS, isBoss ? H.BOSS_MS : 0));
    const S = opts.crit ? FEEL.SHAKE.CRIT : FEEL.SHAKE.HIT;
    this.shake.add(now, S.PX, S.MS);
    if (!died && opts.knock !== false) {
      const K = FEEL.KNOCKBACK;
      const dist = (opts.crit ? K.CRIT_PX : K.HIT_PX) * (isBoss ? K.BOSS_MULT : 1);
      mob.shove(nx, ny, dist, K.MS, isBoss, isBoss ? undefined : (m, dx, dy) => this.onShoveEnd(m, dx, dy));
    }
    return died;
  }

  /** 넉백 끝: 발밑 먼지 */
  private onShoveEnd(mob: Mob, dirX: number, dirY: number): void {
    if (!this.scene.isActive() || !mob.active) return;
    this.hitFx.knockDust(mob.x, mob.body.bottom, dirX, dirY);
  }

  /** 플레이어 피격: 계약 이벤트 중계(source 는 내부용이라 뺀다) + 히트스톱·흔들림·숫자 */
  private onPlayerDamaged(p: PlayerDamagedPayload): void {
    __system.emit(UI_EVENTS.PLAYER_DAMAGED, { hp: p.hp, maxHp: p.maxHp, amount: p.amount });
    const now = this.time.now;
    this.hitStop.request(now, FEEL.HITSTOP.PLAYER_HURT_MS);
    this.shake.add(now, FEEL.SHAKE.PLAYER_HURT.PX, FEEL.SHAKE.PLAYER_HURT.MS);
    const b = this.player.body;
    this.numbers.show(b.center.x, b.top - 6, p.amount, 'player');
    const center = this.player.getCenter();
    this.hitFx.playerHit(center.x, center.y, this.player.y);
  }

  /** 보스 돌진 벽 충돌: 큰 흔들림 */
  private onBossWallHit(_p: BossWallHitPayload): void {
    this.shake.add(this.time.now, FEEL.SHAKE.BOSS_WALL.PX, FEEL.SHAKE.BOSS_WALL.MS);
  }

  /** 진화 무기의 베기 궤적 (플레이스홀더 연출. 정식 이펙트는 아트 파트) */
  private drawSlashTrail(cx: number, cy: number, dirX: number, dirY: number, length: number): void {
    const g = this.add.graphics().setDepth(DEPTH.ATTACK);
    const angle = Math.atan2(dirY, dirX);
    g.lineStyle(2, COLORS.ATTACK, 0.9);
    g.beginPath();
    g.arc(cx - dirX * length * 0.3, cy - dirY * length * 0.3, length * 0.9, angle - 0.6, angle + 0.6, false);
    g.strokePath();
    this.tweens.add({ targets: g, alpha: 0, duration: PROTOTYPE.SLASH_TRAIL_MS, onComplete: () => g.destroy() });
  }

  /** 대검 진화 충격파 (플레이스홀더 연출) */
  private drawShockwave(cx: number, cy: number, radius: number): void {
    const g = this.add.graphics().setDepth(DEPTH.ATTACK);
    g.lineStyle(2, COLORS.SHOCKWAVE, 0.9);
    g.strokeCircle(cx, cy, radius * 0.4);
    this.tweens.add({
      targets: g,
      scaleX: 2.2,
      scaleY: 2.2,
      alpha: 0,
      duration: PROTOTYPE.SHOCKWAVE_MS,
      onComplete: () => g.destroy(),
    });
    g.setPosition(cx, cy);
    g.strokeCircle(0, 0, radius * 0.4);
  }

  /** 개성 변화 알림 (시스템 파트 임시 텍스트. 정식 연출·UI는 UI 파트) */
  private showEvolutionBanner(name: string): void {
    const z = this.cameras.main.zoom || 1;
    const t = this.add
      .text(this.scale.width / 2, this.scale.height / 2 - 40 / z, `개성 변화: ${name}`, {
        font: PLACEHOLDER_UI.FONT_BODY,
        color: COLORS.GAMEOVER_TEXT,
      })
      .setOrigin(0.5)
      .setScale(1 / z)
      .setScrollFactor(0)
      .setDepth(DEPTH.DEBUG);
    this.tweens.add({ targets: t, alpha: 0, delay: PROTOTYPE.BANNER_MS, duration: 400, onComplete: () => t.destroy() });
  }

  // --- 경제: 드랍·획득·물약 ---

  private dropLoot(mob: Mob, goldMult = 1): void {
    const G = ECONOMY.gold;
    const gold = Math.round(rollGold(mob.goldValue, G.variance, this.rng) * goldMult);
    this.spawnPickup(mob.x, mob.y, 'gold', gold);
    if (this.rng.chance(ECONOMY.drops.potion.chance)) this.spawnPickup(mob.x + 10, mob.y, 'potion', 1);
  }

  private spawnPickup(x: number, y: number, kind: 'gold' | 'potion', value: number): void {
    const pk = this.pickups.get() as Pickup | null;
    if (!pk) return;
    const jx = (this.rng.next() - 0.5) * 12;
    const jy = (this.rng.next() - 0.5) * 12;
    pk.spawn(x + jx, y + jy, kind, value, ECONOMY.gold.dropLifeMs, this.time.now);
  }

  private onPickup(pk: Pickup): void {
    if (!pk.active) return;
    if (pk.kind === 'gold') {
      pk.deactivate();
      // 47라운드 1-3: 빚이 있으면 일부 자동 상환
      const kept = this.structures.onGoldPickup(pk.value);
      if (kept > 0) this.addGold(kept);
    } else if (gameState.potions < this.potionCarry) {
      pk.deactivate();
      gameState.potions += 1;
      EventBus.emit(Events.ITEM_PICKED, { kind: pk.kind, value: pk.value });
      EventBus.emit(Events.POTION_CHANGED, { potions: gameState.potions });
    }
  }

  /** 물약 최대 소지 = 기본 + 영구 강화 */
  private get potionCarry(): number {
    return ECONOMY.drops.potion.maxCarry + gameState.meta.potionCarry;
  }

  /** 런 종료 정산: 영혼 지급·도감 기록 (사망·클리어 공통, 1회) */
  private settleRun(cleared: boolean): void {
    if (gameState.runSettled) return;
    gameState.runSettled = true;
    const w = gameState.weapon;
    const { meta, gained } = recordRun(metaStore.read(), {
      weaponId: w.id,
      weaponStage: w.stage,
      evolutionNames: w.nodes.map((e) => e.name),
      floorReached: gameState.floorReached,
      kills: gameState.kills,
      cleared,
    });
    metaStore.write(meta);
    // 47라운드 C3 묘 '기록한다' 영혼은 이미 메타에 적립 — 결과 화면에 합산만
    gameState.lastSoulGain = gained + gameState.bonusSouls;
  }

  private addGold(amount: number): void {
    gameState.gold += amount;
    EventBus.emit(Events.GOLD_CHANGED, { gold: gameState.gold, delta: amount });
  }

  /** 47라운드 구조물 지불 (궤짝·잔·판돈 등) */
  private spendGold(amount: number): void {
    if (amount <= 0) return;
    gameState.gold = Math.max(0, gameState.gold - amount);
    EventBus.emit(Events.GOLD_CHANGED, { gold: gameState.gold, delta: -amount });
  }

  private usePotion(): void {
    if (gameState.potions <= 0 || gameState.hp >= gameState.maxHp) return;
    gameState.potions -= 1;
    EventBus.emit(Events.POTION_USED, { potions: gameState.potions });
    this.player.heal(ECONOMY.drops.potion.heal);
    EventBus.emit(Events.POTION_CHANGED, { potions: gameState.potions });
  }

  private onTrialCleared(p: { roomId: string }): void {
    this.clearedRooms.add(p.roomId);
    this.addGold(ECONOMY.gold.trialBonus);
    this.story('notice', gameState.bossUnlocked ? STORY.notices.bossUnlocked : STORY.notices.trialClear);
  }

  // --- 스테이지 보상(감각 → 능력치 포인트) → 출구·상점 ---

  private beginStageReward(room: ReturnType<TileWorld['room']>): void {
    this.addGold(ECONOMY.gold.bossBonus);
    gameState.pointsPending += gameState.senses.gainedThisStage;
    gameState.rewardPending = true;
    const finish = () => {
      gameState.rewardPending = false;
      gameState.route?.markCleared();
      this.world.placeExit(room);
      this.world.placeShop(room);
      gameState.exitOpen = true;
      EventBus.emit(Events.EXIT_OPENED, { stageIndex: gameState.stageIndex });
    };
    const passiveStep = () => this.openPassiveChooser(finish);
    if (gameState.pointsPending > 0) this.openStatChooser(passiveStep);
    else passiveStep();
  }

  /** 능력치 포인트를 모두 쓸 때까지 선택 메뉴를 보여준다 (임시 텍스트) */
  private openStatChooser(onDone: () => void): void {
    const lines = ECONOMY.statRewards.map((r, i) => ({ key: String(i + 1), label: r.name, enabled: true }));
    const show = () => {
      this.menu.open('reward', fill(STORY.ui.hud.rewardTitle, { n: gameState.pointsPending }), lines, (key) => {
        const reward = ECONOMY.statRewards[Number(key) - 1];
        this.applyReward(reward.id);
        if (gameState.pointsPending > 0) show();
        else {
          this.menu.close();
          onDone();
        }
      });
    };
    show();
  }

  /** 보스 보상 패시브 3지선다 (임시 텍스트) */
  private openPassiveChooser(onDone: () => void): void {
    const choices = gameState.passives.rollChoices(this.rng, ECONOMY.rarity, PASSIVES.choices);
    if (choices.length === 0) {
      onDone();
      return;
    }
    const lines = choices.map((p, i) => ({
      key: String(i + 1),
      label: `[${p.rarity}] ${p.name}${gameState.passives.level(p.id) > 0 ? ` (Lv${gameState.passives.level(p.id)} → ${gameState.passives.level(p.id) + 1})` : ''} — ${p.description}`,
      enabled: true,
    }));
    this.menu.open('passive', STORY.ui.hud.passiveTitle, lines, (key) => {
      const pick = choices[Number(key) - 1];
      gameState.passives.add(pick.id);
      EventBus.emit(Events.PASSIVE_GAINED, { id: pick.id, level: gameState.passives.level(pick.id) });
      this.menu.close();
      onDone();
    });
  }

  private applyReward(id: StatKey): void {
    const reward = findReward(ECONOMY, id);
    gameState.bonus = applyStatReward(gameState.bonus, reward);
    if (reward.maxHp) {
      gameState.maxHp += reward.maxHp;
      gameState.hp += reward.maxHp;
    }
    gameState.pointsPending -= 1;
    EventBus.emit(Events.STAT_REWARD, { id, bonus: gameState.bonus, pointsLeft: gameState.pointsPending });
  }

  /** 상점 타일 위에 서 있으면 메뉴를 열고, 벗어나면 닫는다 */
  private updateShop(): void {
    // 48라운드: 상점 노드는 들어서면 바로 (보스 뒤 상점은 출구가 열린 뒤)
    const shopNode = this.nodeKind !== null && Boolean(kindDef(this.nodeKind).shopTiles);
    if (!gameState.exitOpen && !shopNode) return;
    if (gameState.route?.choosing) return;
    const onTile = this.world.isShopAt(this.player.x, this.player.y);
    if (onTile && !this.shopOpen && !this.menu.isOpen) this.openShop();
    else if (!onTile && this.shopOpen) this.closeShop();
  }

  private openShop(): void {
    this.shopOpen = true;
    EventBus.emit(Events.SHOP_OPENED);
    const render = () => {
      const lines = ECONOMY.shop.items.map((it, i) => {
        const price = shopPrice(it, gameState.stageIndex);
        const full = it.id === 'potion' && gameState.potions >= this.potionCarry;
        const name = it.id === 'potion' ? `${STORY.names.potion} +1` : it.name;
        return {
          key: String(i + 1),
          label: `${name}  ${price} ${STORY.names.gold}`,
          enabled: gameState.gold >= price && !full,
        };
      });
      this.menu.open(
        'shop',
        `${STORY.names.shop}  (${STORY.names.gold} ${gameState.gold}, ${STORY.names.potion} ${gameState.potions})`,
        lines,
        (key) => this.buy(ECONOMY.shop.items[Number(key) - 1].id, render),
        STORY.ui.hud.shopFooter,
      );
    };
    render();
  }

  private closeShop(): void {
    this.shopOpen = false;
    this.menu.close();
    EventBus.emit(Events.SHOP_CLOSED);
  }

  private buy(id: 'heal' | 'sense' | 'stat' | 'potion', rerender: () => void): void {
    const item = ECONOMY.shop.items.find((i) => i.id === id)!;
    const price = shopPrice(item, gameState.stageIndex);
    if (gameState.gold < price) return;
    gameState.gold -= price;
    EventBus.emit(Events.GOLD_CHANGED, { gold: gameState.gold, delta: -price });
    EventBus.emit(Events.SHOP_BOUGHT, { id, price });
    switch (id) {
      case 'heal':
        this.player.heal(Math.round(gameState.maxHp * ECONOMY.shop.healFraction));
        rerender();
        break;
      case 'potion':
        gameState.potions = Math.min(this.potionCarry, gameState.potions + 1);
        EventBus.emit(Events.POTION_CHANGED, { potions: gameState.potions });
        rerender();
        break;
      case 'sense':
        gameState.senses.sense += 1;
        gameState.pointsPending += 1;
        this.closeShop();
        this.openStatChooser(() => {});
        break;
      case 'stat':
        gameState.pointsPending += 1;
        this.closeShop();
        this.openStatChooser(() => {});
        break;
    }
  }

  private onMobTouch(mob: Mob): void {
    const now = this.time.now;
    // 넉백 방향: 가해자 → 플레이어
    const source = { dirX: this.player.x - mob.x, dirY: this.player.y - mob.y };
    // 패링 창이면 접촉 공격 주기와 무관하게 막는다 (돌진 포함)
    if (this.player.isParrying && !mob.isStunned(now)) {
      const attack = mob.tryContactAttack(now);
      if (attack > 0 || mob.body.velocity.lengthSq() > 0) {
        if (this.player.takeHit(attack || 1, now, source) === 'parried') {
          mob.stun(now, PLAYER_DATA.parry.stunMs);
          // 접점 ≈ 플레이어 몸 중심과 적 바디 중심의 중간
          const pc = this.player.getCenter();
          const mc = mob.body.center;
          this.onParried((pc.x + mc.x) / 2, (pc.y + mc.y) / 2);
        }
      }
      return;
    }
    const attack = mob.tryContactAttack(now);
    if (attack > 0) this.player.takeHit(attack, now, source);
  }

  private onProjectileHit(pr: Projectile): void {
    if (!pr.active || pr.reflected) return;
    const source = { dirX: pr.body.velocity.x, dirY: pr.body.velocity.y };
    const result = this.player.takeHit(pr.attack, this.time.now, source);
    if (result === 'parried') {
      pr.reflect(PLAYER_DATA.parry.reflectDamageMult + gameState.passives.total('reflectMult'));
      this.onParried(pr.x, pr.y);
    } else pr.deactivate();
  }

  /** 패링 성공: 접점에 parry_flash(개체 위) + 짧은 히트스톱 (1프레임이 멈춤 동안 보이도록) */
  private onParried(x: number, y: number): void {
    if (this.fx.has('parry_flash')) this.fx.play('parry_flash', x, y, { depth: DEPTH.HIT_FX + 0.02 });
    this.hitStop.request(this.time.now, FEEL.SECONDARY.PARRY_HITSTOP_MS);
  }

  // --- 35라운드 3단계: 조준 점선·차지 게이지 (유지형) · 대쉬 잔상 (주기형) ---

  /**
   * 조준 중: aim_line(몸 중심 → 커서, 길이 AIM_LINE_TILES) + aim_charge(진행도 프레임 = min(5, floor(progress×5))).
   * 차지 완료 후 발사되면 5프레임을 AIM_CHARGE_HOLD_MS 유지, 취소면 즉시 제거
   */
  private updateAimFx(time: number): void {
    const S = FEEL.SECONDARY;
    if (this.player.action !== 'aim') {
      if (this.aimLine.visible || this.aimChargeFx) this.stopAimFx(this.lastAimReady);
      return;
    }
    const progress = this.player.aimProgress(time);
    this.lastAimReady = progress >= 1;
    const c = this.player.getCenter();
    const cx = c.x;
    const cy = this.player.y - S.BODY_CENTER_UP_PX;
    const angle = this.player.aimAngle;
    // aim_line stateFrames: 차지 중 f0 / 완료 f1 (43라운드 B)
    this.aimLine.show(cx, cy, angle, S.AIM_LINE_TILES * TILE, progress >= 1 ? 'complete' : 'charging');
    if (!this.fx.has('aim_charge')) return;
    // aim_charge 진행도 프레임 = min(마지막, floor(progress × 5)) — 6프레임 시트의 f5 = 완료
    const frame = progressFrame(progress, this.fx.framesOf('aim_charge'), S.AIM_CHARGE_DIVISOR);
    if (!this.fx.isActive(this.aimChargeFx)) {
      this.aimChargeFx = this.fx.play('aim_charge', cx, cy, {
        staticFrame: frame,
        follow: this.player,
        followOffset: { x: 0, y: -S.BODY_CENTER_UP_PX },
        depthOffset: DEPTH.OVERLAY_STEP * 3,
      });
    } else this.fx.setFrame(this.aimChargeFx, 'aim_charge', frame);
  }

  private lastAimReady = false;

  /** 조준 끝: 점선 제거, 차지 게이지는 발사(완료)면 짧게 유지 후 제거, 취소면 즉시 */
  private stopAimFx(fired: boolean): void {
    this.aimLine.hide();
    if (this.fx.isActive(this.aimChargeFx))
      this.fx.stop(this.aimChargeFx, fired ? FEEL.SECONDARY.AIM_CHARGE_HOLD_MS : 0, false);
    this.aimChargeFx = null;
    this.lastAimReady = false;
  }

  /**
   * 대쉬 중 DASH_TRAIL_INTERVAL_MS 마다 현재 위치에 dash_trail(고정, 대쉬 방향, 플레이어 아래).
   * 발도술·허보·잔상 노드일 때만 그 무기 W1 로 틴트 (JSON tint.when). 시트가 어두운 무채라 JSON tint.method 의 setTintFill(평면)
   */
  private updateDashTrail(time: number): void {
    if (this.player.action !== 'dash' || time < this.dashTrailNextAt || !this.fx.has('dash_trail')) return;
    const S = FEEL.SECONDARY;
    this.dashTrailNextAt = time + S.DASH_TRAIL_INTERVAL_MS;
    const d = this.player.dashDir;
    const tinted = S.DASH_TRAIL_TINT_NODES.some((id) => gameState.weapon.path.includes(id));
    const hex = tinted ? fxWeaponColor(PALETTE, gameState.weapon.id, S.DASH_TRAIL_RAMP_INDEX) : null;
    const method = this.fx.sheet('dash_trail')?.tint?.method ?? '';
    this.fx.play('dash_trail', this.player.x, this.player.y, {
      dir: facingOf(d.x, d.y, this.player.facingDir),
      depth: entityDepth(this.player.y) - DEPTH.OVERLAY_STEP,
      tint: hex ? hexToInt(hex) : undefined,
      tintFill: method.includes('setTintFill'),
    });
  }

  private onReflectedHit(pr: Projectile, mob: Mob): void {
    if (!pr.active || !pr.reflected) return;
    const dirX = pr.body.velocity.x;
    const dirY = pr.body.velocity.y;
    pr.deactivate();
    if (this.hitMob(mob, pr.attack, { crit: false, dirX, dirY })) this.onKill(mob, 'parry');
  }

  private onPlayerDied(): void {
    this.saveSlot.clear(); // 영구 사망 (기획 3장)
    this.settleRun(false);
    this.player.body.setVelocity(0, 0);
    for (const m of this.mobs.getChildren() as Mob[]) m.body.setVelocity(0, 0);
    // 사망 애니가 있으면 끝 프레임을 보여준 뒤 결과 화면으로
    const delay = this.player.deathAnimMs > 0 ? this.player.deathAnimMs + SPRITES.DEATH_EXTRA_MS : 0;
    this.stopAimFx(false);
    this.screenFx.death(delay);
    if (delay > 0) this.time.delayedCall(delay, () => this.endRunScene(false));
    else this.endRunScene(false);
  }

  /** 결과 화면: UI 렌더러가 있으면 UI 결과 씬, 아니면 시스템 임시 화면 */
  private endRunScene(cleared: boolean): void {
    const result = {
      cleared,
      stageName: floorText(gameState.stageId)?.title ?? gameState.stage.name,
      floorReached: gameState.floorReached,
      kills: gameState.kills,
      gold: gameState.gold,
      sense: gameState.senses.sense,
      weaponName: gameState.weapon.displayName,
      soulsGained: gameState.lastSoulGain,
      soulsTotal: metaStore.read().souls,
      seed: gameState.seed,
      playerName: gameState.playerName,
      line: cleared
        ? STORY.endings[gameState.ending ?? 'destroy']
        : deathLine(gameState.playerName, gameState.floorReached, gameState.kills),
      ending: cleared ? (gameState.ending ?? 'destroy') : undefined,
    };
    this.debugLastResult = result;
    EventBus.emit(Events.RUN_ENDED, { cleared } satisfies RunEndedPayload);
    __system.emit(UI_EVENTS.RUN_ENDED, result);
    if (__system.rendererRegistered() && this.scene.manager.keys[UI_SCENES.RESULT]) {
      if (this.scene.isActive(UI_SCENES.HUD)) this.scene.stop(UI_SCENES.HUD);
      this.scene.start(UI_SCENES.RESULT, result);
    } else {
      this.scene.start(SCENES.GAME_OVER, { cleared });
    }
  }

  private snapshot() {
    return buildSnapshot({
      layout: this.layout ?? null,
      visited: this.visitedRooms,
      cleared: this.clearedRooms,
      bossName: this.bossName,
      paused: false,
      menu: this.menu.menu,
      inCombat: this.director.inCombat,
      sprinting: this.player.sprinting,
      warp: this.warpState(),
      interactable: this.structures?.interactable() ?? null,
      statuses: this.structures?.statuses() ?? [],
      structureRooms: this.structures?.structureRooms(),
      route: gameState.route?.toUi() ?? null,
    });
  }

  // --- 48라운드 노드 지도 (계약 §10): 노드 전투장 · 출구 · 다음 노드 선택 · 전환 ---

  /** 노드 전투장 레이아웃. 현재 노드가 없으면(2층 진입 갈림 선택 대기) 비전투 빈 전투장 */
  private buildArena(node: RouteNode | null): FloorLayout {
    const kind: RouteKind = node?.kind ?? 'birth';
    const d = kindDef(kind);
    const [w, h] = arenaSize(kind);
    const A = ROUTE.arena;
    return generateArena({
      roomId: node?.id ?? 'entry',
      type: node ? d.room : 'start',
      floor: node ? d.floor : 'start',
      w,
      h,
      margin: A.voidMarginTiles,
      spawnInset: A.spawnInsetTiles,
      exitInset: A.exitInsetTiles,
      spawnCenter: kind === 'birth' && node !== null,
    });
  }

  /** 구조물을 놓지 않을 칸: 시작점·출구 (+ 상점 노드면 상점) 둘레 */
  private arenaReserve(layout: FloorLayout): { x: number; y: number; w: number; h: number }[] {
    const A = layout.arena;
    if (!A) return [];
    const c = ROUTE.arena.clearTiles;
    const out = [
      { x: A.spawn.x - c, y: A.spawn.y - c, w: c * 2 + 1, h: c * 2 + 1 },
      { x: A.exit.x - c, y: A.exit.y - c, w: c * 2 + 2, h: c * 2 + 2 },
    ];
    if (this.nodeKind && kindDef(this.nodeKind).shopTiles)
      out.push({ x: A.shop.x - c, y: A.shop.y - c, w: c * 2 + 2, h: c * 2 + 2 });
    return out;
  }

  /** 노드 씬마다 초기화 */
  private routeResetFields(): void {
    this.nodeExitOpen = false;
    this.nodeExitScheduled = false;
    this.enterLockUntil = 0;
    this.exitArmed = true;
    this.birth?.destroy();
    this.birth = null;
    this.debugLastSwing = null;
    if (this.routeMode) {
      gameState.exitOpen = false;
      gameState.rewardPending = false;
    }
  }

  /** HUD 진행 표시 재해석 (임시): 시련 총수 = 어느 길로 가도 거치는 최소 전투 수, 보스 해금 = 다음이 보스 */
  private syncRouteProgress(): void {
    const route = gameState.route;
    if (!route) return;
    gameState.trialsTotal = minBattlesOnAnyPath(route.graph);
    gameState.bossUnlocked = this.nodeKind === 'boss' || route.nextOptions().some((n) => n.kind === 'boss');
  }

  /** 노드 진입: 밝아짐 · 입력 잠금 · ROUTE_NODE_ENTERED · 새 런 첫 노드면 탄생 · 진입 갈림이면 바로 선택 */
  private enterNode(): void {
    const now = this.time.now;
    this.cameras.main.fadeIn(ROUTE_FX.FADE_IN_MS, ROUTE_FX.FADE_COLOR.R, ROUTE_FX.FADE_COLOR.G, ROUTE_FX.FADE_COLOR.B);
    this.enterLockUntil = now + ROUTE_FX.ENTER_LOCK_MS;
    this.syncRouteProgress();
    const node = this.node;
    if (node)
      __system.emit(UI_EVENTS.ROUTE_NODE_ENTERED, {
        id: node.id,
        type: node.type,
        name: node.name,
      } satisfies UiRouteEntered);
    const params = typeof location !== 'undefined' ? new URLSearchParams(location.search) : new URLSearchParams();
    if (this.nodeKind === 'birth' && gameState.birthPending && !params.has('nobirth')) this.startBirth();
    else if (this.nodeKind === 'birth') gameState.birthPending = false;
    if (!node) this.time.delayedCall(ROUTE_FX.ENTER_LOCK_MS, () => this.openRouteChooser());
  }

  /** 진입 직후 · 선택 중 · 전환 중 입력 잠금 */
  private routeLocked(time: number): boolean {
    if (!this.routeMode) return false;
    return time < this.enterLockUntil || Boolean(gameState.route?.choosing) || this.transitioning;
  }

  /** 노드 클리어 → (잠시 뒤) 출구. 출구에 서면 다음 노드 선택 */
  private updateRoute(time: number): void {
    const route = gameState.route;
    if (!route || !this.node || this.transitioning || time < this.enterLockUntil) return;
    const room = this.layout?.rooms[0];
    if (!room) return;
    if (
      !route.currentCleared &&
      this.nodeKind !== 'boss' &&
      this.director.stateOf(room.id) === 'cleared' &&
      !this.director.inCombat
    ) {
      route.markCleared();
      this.clearedRooms.add(room.id);
      this.syncRouteProgress();
      if (!this.nodeExitScheduled) {
        this.nodeExitScheduled = true;
        this.time.delayedCall(ROUTE_FX.EXIT_DELAY_MS, () => this.openNodeExit());
      }
    }
    if (!this.nodeExitOpen || route.choosing) return;
    const onExit = this.world.isExitAt(this.player.x, this.player.y);
    if (onExit && this.exitArmed && !this.director.inCombat && !this.menu.isOpen && !this.frozen) {
      this.exitArmed = false;
      this.openRouteChooser();
    } else if (!onExit) this.exitArmed = true;
  }

  /** 노드 출구 (오른쪽 2×2) */
  private openNodeExit(): void {
    if (!this.scene.isActive() || this.nodeExitOpen || !this.layout?.arena) return;
    const e = this.layout.arena.exit;
    this.world.placeExitAt(e.x, e.y);
    this.nodeExitOpen = true;
    gameState.exitOpen = true;
    EventBus.emit(Events.EXIT_OPENED, { stageIndex: gameState.stageIndex });
  }

  /** 다음 노드 선택 열기 (계약 §10.2): 입력 잠금 + ROUTE_CHOOSE_OPEN. UI 렌더러가 없으면 숫자 키로 고른다 */
  private openRouteChooser(): boolean {
    const route = gameState.route;
    if (!route || route.choosing || this.transitioning || this.director.inCombat) return false;
    const options = route.nextOptions();
    if (options.length === 0) return false;
    route.choosing = true;
    this.player.haltForWarp();
    this.stopAimFx(false);
    this.stopGale();
    if (this.shopOpen) this.closeShop();
    __system.emit(UI_EVENTS.ROUTE_CHOOSE_OPEN, route.toUi());
    if (!__system.rendererRegistered()) {
      const onKey = (e: KeyboardEvent) => {
        const n = options[Number(e.key) - 1];
        if (n && this.chooseNode(n.id)) this.input.keyboard?.off('keydown', onKey);
      };
      this.input.keyboard?.on('keydown', onKey);
    }
    return true;
  }

  /** uiCommands.chooseNode (계약 §10.2): available 노드만. 층 상태를 들고 암전 뒤 그 노드 전투장을 연다 */
  private chooseNode(id: string): boolean {
    const route = gameState.route;
    if (!route || !route.choosing || this.transitioning || !route.canChoose(id)) return false;
    this.transitioning = true;
    gameState.structureCarry = this.structures.exportFloorState();
    route.enter(id);
    this.fadeThen(() => this.scene.restart({ mode: 'node' } satisfies GameInitData));
    return true;
  }

  /** 짧은 암전 뒤 실행 */
  private fadeThen(fn: () => void): void {
    const C = ROUTE_FX.FADE_COLOR;
    this.cameras.main.fadeOut(ROUTE_FX.FADE_OUT_MS, C.R, C.G, C.B);
    this.time.delayedCall(ROUTE_FX.FADE_OUT_MS, () => {
      if (this.scene.isActive()) fn();
    });
  }

  // --- 48라운드 Q6 탄생 연출 (계약 §10.3) ---

  private startBirth(): void {
    gameState.birthPending = false;
    const now = this.time.now;
    this.player.body.setVelocity(0, 0);
    this.birth = new BirthSequence({
      scene: this,
      x: this.player.x,
      y: this.player.y,
      hidePlayer: (on) => this.player.visual.setHidden(on),
      setPlayerAlpha: (a) => this.player.setAlpha(a),
      burst: () => {
        const B = BIRTH;
        this.screenFx.flash(B.BURST_FLASH.COLOR, B.BURST_FLASH.MS, B.BURST_FLASH.ALPHA);
        this.shake.add(this.time.now, B.BURST_SHAKE.PX, B.BURST_SHAKE.MS);
      },
      done: (skipped) => this.finishBirth(skipped),
    });
    this.birthStartedAt = now;
    this.birth.start(now);
    // HUD 는 같은 create 안에서 launch 되어 아직 구독 전일 수 있다 → HUD 생성이 끝난 뒤에 알린다
    const hud = this.scene.manager.keys[UI_SCENES.HUD] ? this.scene.get(UI_SCENES.HUD) : null;
    if (hud && !hud.sys.isActive()) {
      hud.sys.events.once(Phaser.Scenes.Events.CREATE, () => {
        if (this.birth?.active) __system.emit(UI_EVENTS.BIRTH_STARTED);
      });
    } else {
      __system.emit(UI_EVENTS.BIRTH_STARTED);
    }
    this.input.keyboard?.on('keydown', this.onBirthKey);
    this.input.on('pointerdown', this.onBirthKey);
  }

  /** 아무 키: 건너뛰기 (씬 진입 직후 눌려 있던 입력은 무시) */
  private skipBirth(): void {
    if (!this.birth?.active) return;
    if (this.time.now - this.birthStartedAt < BIRTH.SKIP_GRACE_MS) return;
    this.birth.skip();
  }

  private finishBirth(skipped: boolean): void {
    this.input.keyboard?.off('keydown', this.onBirthKey);
    this.input.off('pointerdown', this.onBirthKey);
    this.cameras.main.setZoom(CAMERA.ZOOM);
    this.player.setAlpha(1);
    this.updateCamera(true);
    // 조작 해제: 건너뛴 키가 바로 공격·대쉬로 새지 않게 아주 짧게 잠근다
    this.enterLockUntil = Math.max(this.enterLockUntil, this.time.now + (skipped ? BIRTH.SKIP_GRACE_MS : 0));
    this.inputSystem.read();
    __system.emit(UI_EVENTS.BIRTH_DONE);
  }

  // --- 비전투 이동 (45라운드): 달리기 먼지 · 워프 ---

  /** 달리는 동안 발밑에 dash_dust 를 작게·옅게 주기적으로 (시트가 없으면 작은 회색 점) */
  private updateSprintDust(time: number): void {
    if (!this.player.sprinting || time < this.sprintDustNextAt) return;
    const D = TRAVERSAL.SPRINT_DUST;
    this.sprintDustNextAt = time + D.INTERVAL_MS;
    this.sprintDustCount += 1;
    const v = this.player.body.velocity;
    const x = this.player.x;
    const y = this.player.y;
    if (this.fx.has(D.SHEET)) {
      this.fx.play(D.SHEET, x, y, {
        dir: facingOf(v.x, v.y, this.player.facingDir),
        depth: DEPTH.FX_GROUND,
        scaleMult: D.SCALE_MULT,
        alpha: D.ALPHA,
        hooks: false,
      });
      return;
    }
    const [, h] = PLAYER_DATA.size;
    const dot = this.add.circle(x, y + h / 2, D.DOT_RADIUS, D.DOT_COLOR, D.ALPHA).setDepth(DEPTH.FX_GROUND);
    this.tweens.add({ targets: dot, alpha: 0, duration: D.DOT_MS, onComplete: () => dot.destroy() });
  }

  /** 씬 상태로 본 공통 거부 사유: 연출·메뉴·전환은 busy, 활성 전투 방이 있으면 combat */
  private warpBlock(): 'combat' | 'busy' | null {
    if (!this.director || gameState.gameOver || gameState.cleared || this.transitioning || this.warping) return 'busy';
    if (this.director.inCombat) return 'combat';
    if (this.frozen || gameState.rewardPending || (this.menu.isOpen && !this.shopOpen)) return 'busy';
    return null;
  }

  /** 48라운드 (계약 §10.2): 워프 비활성 — targets 는 항상 [], ready=false (Tab 은 노드 지도 보기) */
  private warpState(): UiWarpState {
    return {
      ready: false,
      blocked: this.warpBlock() ?? 'busy',
      targets: [],
      warping: this.warping,
    };
  }

  private warpDeny(roomId: string): WarpDenyReason | null {
    if (WARP_DISABLED) return this.warpBlock() ?? 'busy';
    return warpDenyReason({
      roomId,
      block: this.warpBlock(),
      rooms: this.layout?.rooms ?? [],
      visited: this.visitedRooms,
      progress: this.director?.progress ?? new Map(),
      currentRoomId: gameState.roomId,
    });
  }

  /**
   * 워프 시작 (계약 §8.2): 퇴장 섬광·먼지 → OUT_MS 뒤 안전 착지점으로 이동·카메라 즉시 이동·도착 섬광.
   * 시작부터 OUT_MS + IN_LOCK_MS 입력 잠금, INVULN_MS 무적
   */
  private startWarp(roomId: string): WarpDenyReason | null {
    const reason = this.warpDeny(roomId);
    if (reason) return reason;
    const W = TRAVERSAL.WARP;
    const room = this.world.room(roomId);
    const dest = this.world.safePointInRoom(room, W.SAFE_BODY_TILES, W.SAFE_HAZARD_TILES);
    const fromRoomId = gameState.roomId;
    const now = this.time.now;
    this.warping = true;
    this.warpLockUntil = now + W.OUT_MS + W.IN_LOCK_MS;
    this.player.grantInvulnerable(now + W.INVULN_MS);
    this.player.haltForWarp();
    this.stopAimFx(false);
    this.stopGale();
    if (this.shopOpen) this.closeShop();
    this.screenFx.flash(W.FLASH_OUT.COLOR, W.FLASH_OUT.MS, W.FLASH_OUT.ALPHA);
    if (this.fx.has(W.DUST_SHEET))
      this.fx.play(W.DUST_SHEET, this.player.x, this.player.y, { depth: DEPTH.FX_GROUND, hooks: false });
    const payload: WarpPayload = { fromRoomId, roomId, x: dest.x, y: dest.y };
    EventBus.emit(Events.WARP_STARTED, payload);
    this.debugLastWarp = { ...payload, phase: 'out', startedAt: now };
    this.time.delayedCall(W.OUT_MS, () => this.finishWarp(payload, room.type));
    return null;
  }

  private finishWarp(p: WarpPayload, type: UiWarpDone['type']): void {
    this.warping = false;
    if (gameState.gameOver || gameState.cleared || this.transitioning) return;
    const W = TRAVERSAL.WARP;
    this.player.haltForWarp();
    this.player.body.reset(p.x, p.y);
    this.updateCamera(true);
    this.screenFx.flash(W.FLASH_IN.COLOR, W.FLASH_IN.MS, W.FLASH_IN.ALPHA);
    if (this.fx.has(W.DUST_SHEET)) this.fx.play(W.DUST_SHEET, p.x, p.y, { depth: DEPTH.FX_GROUND, hooks: false });
    // 방 진입(ROOM_ENTERED)을 이번 프레임에 처리해 currentRoomId 를 바로 바꾼다
    this.director.update();
    EventBus.emit(Events.WARP_ARRIVED, p);
    this.debugLastWarp = { ...p, phase: 'done', arrivedAt: this.time.now };
    __system.emit(UI_EVENTS.WARP_DONE, { fromRoomId: p.fromRoomId, roomId: p.roomId, type } satisfies UiWarpDone);
  }

  /** 스토리 자막 (계약 STORY 이벤트) */
  private story(kind: StoryKind, text: string): void {
    if (text) __system.emit(UI_EVENTS.STORY, { kind, text });
  }

  private onRoomEnteredUi(p: { roomId: string; type: string }): void {
    const firstVisit = !this.visitedRooms.has(p.roomId);
    this.visitedRooms.add(p.roomId);
    __system.emit(UI_EVENTS.ROOM_ENTERED, p);
    if (firstVisit && p.type === 'rest') this.story('rest', floorText(gameState.stageId)?.restNote ?? '');
    if (firstVisit && p.type === 'trial') this.story('notice', STORY.notices.trialStart);
  }

  private relayHealed(p: unknown): void {
    __system.emit(UI_EVENTS.PLAYER_HEALED, p);
  }

  private relayGold(p: unknown): void {
    __system.emit(UI_EVENTS.GOLD_CHANGED, p);
  }

  private relayEvolved(p: { name: string }): void {
    __system.emit(UI_EVENTS.WEAPON_EVOLVED, { name: p.name });
  }

  private relayBossStarted(p: { boss: string }): void {
    this.bossName = BOSSES[p.boss]?.name ?? '보스';
    this.story('boss', floorText(gameState.stageId)?.bossIntro ?? '');
    __system.emit(UI_EVENTS.BOSS_STARTED, {
      name: this.bossName,
      hp: gameState.bossHp,
      maxHp: gameState.bossMaxHp,
      phase: gameState.bossPhase,
    });
  }

  private relayBossPhase(p: { phase: number; hp: number; maxHp: number }): void {
    this.screenFx.bossPhase();
    __system.emit(UI_EVENTS.BOSS_PHASE, { name: this.bossName ?? '보스', ...p });
  }

  private relayBossDied(): void {
    __system.emit(UI_EVENTS.BOSS_DIED, {
      name: this.bossName ?? '보스',
      hp: 0,
      maxHp: gameState.bossMaxHp,
      phase: gameState.bossPhase,
    });
  }

  // --- 카메라: 플레이어 부드러운 추종 (32라운드). 목표만 영역으로 클램프하므로 방 전환 시 미끄러진다 ---

  private updateCamera(force: boolean, deltaMs = 0): void {
    const cam = this.cameras.main;
    // 48라운드 Q1: 확대 배율만큼 보이는 월드가 작다 → 클램프는 보이는 반폭, 스크롤은 (중심 - 캔버스 반폭)
    const zoom = cam.zoom || 1;
    const region = this.world.cameraRegion(this.player.x, this.player.y);
    const halfW = cam.width / (2 * zoom);
    const halfH = cam.height / (2 * zoom);
    const dzX = CAMERA.DEADZONE_X / zoom;
    const dzY = CAMERA.DEADZONE_Y / zoom;
    let tx = this.player.x;
    let ty = this.player.y;
    if (!force) {
      // 데드존: 중심에서 이만큼 벗어나야 따라간다 (화면 px 기준)
      const cx = this.camCenter.x;
      const cy = this.camCenter.y;
      tx = this.player.x > cx + dzX ? this.player.x - dzX : this.player.x < cx - dzX ? this.player.x + dzX : cx;
      ty = this.player.y > cy + dzY ? this.player.y - dzY : this.player.y < cy - dzY ? this.player.y + dzY : cy;
    }
    tx = clampCenter(tx, region.left, region.right, halfW);
    ty = clampCenter(ty, region.top, region.bottom, halfH);
    if (force) {
      this.camCenter.set(tx, ty);
    } else {
      // 60fps 기준 lerp 비율을 프레임 시간에 맞춰 보정
      const t = 1 - Math.pow(1 - CAMERA.FOLLOW_LERP, deltaMs / (1000 / 60));
      this.camCenter.x += (tx - this.camCenter.x) * t;
      this.camCenter.y += (ty - this.camCenter.y) * t;
      const snap = CAMERA.SNAP_PX / zoom;
      if (Math.abs(tx - this.camCenter.x) < snap) this.camCenter.x = tx;
      if (Math.abs(ty - this.camCenter.y) < snap) this.camCenter.y = ty;
    }
    // 흔들림(35라운드): 추종 보간·반올림이 끝난 스크롤에 오프셋만 더한다. 진폭은 화면 px → 월드 px 로 ÷zoom (체감 유지)
    const sh = this.shake.sample(this.time.now);
    const snapTo = (v: number) => Math.round(v * zoom) / zoom;
    cam.setScroll(
      snapTo(this.camCenter.x - cam.width / 2) + sh.x / zoom,
      snapTo(this.camCenter.y - cam.height / 2) + sh.y / zoom,
    );
  }

  /** 런 시작 모드 결정: 새 런 / 다음 층 / 세이브 이어하기 / 같은 층 다음 노드(48라운드). 층 시작이면 true */
  private prepareRun(): boolean {
    const params = typeof location !== 'undefined' ? new URLSearchParams(location.search) : new URLSearchParams();
    if (this.initMode === 'node') {
      // 같은 층의 다음 노드: 층 상태 유지, 층 시작 이벤트 없음
      if (gameState.route) return false;
      gameState.gotoStage(gameState.stageIndex);
    } else if (this.initMode === 'next') {
      gameState.nextStage();
      this.saveIfAllowed();
    } else if (this.initMode === 'floor') {
      gameState.gotoStage(this.initFloor);
    } else if (this.initMode === 'new') {
      gameState.startRun(this.pickSeed(), this.initWeapon, this.initName ?? '');
      this.saveSlot.clear();
    } else {
      const save = params.has('new') || params.has('seed') ? null : this.saveSlot.read();
      if (save) {
        gameState.applySave(save);
      } else {
        gameState.startRun(this.pickSeed());
        this.saveSlot.clear();
      }
    }
    EventBus.emit(Events.STAGE_STARTED, { stageIndex: gameState.stageIndex, stageId: gameState.stageId });
    return true;
  }

  /** 스테이지 전환 세이브: 런당 최대 maxSaves 회 */
  private saveIfAllowed(): void {
    if (gameState.savesLeft <= 0) return;
    gameState.savesLeft -= 1;
    this.saveSlot.write(gameState.toSave());
    EventBus.emit(Events.STAGE_SAVED, { stageIndex: gameState.stageIndex, savesLeft: gameState.savesLeft });
    this.story('notice', fill(STORY.notices.saved, { savesLeft: gameState.savesLeft }));
  }

  private pickSeed(): string {
    const fromUrl = typeof location !== 'undefined' ? new URLSearchParams(location.search).get('seed') : null;
    return fromUrl || Date.now().toString(36);
  }

  private cleanup(): void {
    EventBus.off(Events.PLAYER_ATTACKED, this.onPlayerAttacked, this);
    EventBus.off(Events.PLAYER_DIED, this.onPlayerDied, this);
    EventBus.off(Events.TRIAL_CLEARED, this.onTrialCleared, this);
    EventBus.off(Events.ROOM_ENTERED, this.onRoomEnteredUi, this);
    EventBus.off(Events.PLAYER_DAMAGED, this.onPlayerDamaged, this);
    EventBus.off(Events.BOSS_WALL_HIT, this.onBossWallHit, this);
    EventBus.off(Events.PLAYER_HEALED, this.relayHealed, this);
    EventBus.off(Events.GOLD_CHANGED, this.relayGold, this);
    EventBus.off(Events.WEAPON_EVOLVED, this.relayEvolved, this);
    EventBus.off(Events.BOSS_STARTED, this.relayBossStarted, this);
    EventBus.off(Events.BOSS_PHASE, this.relayBossPhase, this);
    EventBus.off(Events.BOSS_DIED, this.relayBossDied, this);
    EventBus.off(Events.PLAYER_GUARD_RELEASED, this.onGuardReleased, this);
    EventBus.off(Events.PLAYER_SHADOW_STEP, this.onShadowStep, this);
    EventBus.off(Events.PLAYER_DASHED, this.onPlayerDashed, this);
    // 엔딩 선택 뒤 정지 상태로 씬이 끝나면 물리 플러그인이 먼저 정리돼 world 가 없을 수 있다
    if ((this.frozen || this.hitStopped) && this.physics.world) this.physics.world.resume();
    this.numbers.destroy();
    this.telegraph.destroy();
    this.trails.destroy();
    this.screenFx.destroy();
    this.aimLine.destroy();
    this.structures.destroy();
    this.fx.destroy();
    audio.stopAllLoops();
    setMenuSelect(null);
    setSnapshotProvider(null);
    setWarpHandler(null);
    setNodeChooser(null);
    this.input.keyboard?.off('keydown', this.onBirthKey);
    this.input.off('pointerdown', this.onBirthKey);
    this.birth?.destroy();
    this.birth = null;
    this.menu.close();
    this.inputSystem.destroy();
  }
}

/** 화면 절반(half)을 고려해 중심 좌표를 [lo, hi] 영역 안으로. 영역이 화면보다 작으면 가운데 */
function clampCenter(center: number, lo: number, hi: number, half: number): number {
  if (hi - lo <= half * 2) return (lo + hi) / 2;
  return Phaser.Math.Clamp(center, lo + half, hi - half);
}
