import Phaser from 'phaser';
import {
  CAMERA,
  COLORS,
  DEBUG,
  DEPTH,
  FEEL,
  PLACEHOLDER_UI,
  PROTOTYPE,
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
import { warpDenyReason, warpTargets, type WarpDenyReason } from '../systems/traversal';
import { generateFloor } from '../systems/mapgen';
import { RoomDirector } from '../systems/RoomDirector';
import { Rng, hashSeed } from '../systems/rng';
import { SaveSlot, browserStorage } from '../systems/save';
import type { KillKind } from '../systems/senses';
import { applyStatReward, findReward, rollCrit, rollGold, shopPrice } from '../systems/economy';
import { TextMenu } from '../systems/TextMenu';
import { markUnderstood, metaStore, recordRun } from '../systems/meta';
import { PASSIVES } from '../systems/passives';
import { UI_EVENTS, __system, type StoryKind, type UiWarpDone, type UiWarpState } from '../contract/ui';
import { buildSnapshot } from '../contract/snapshot';
import { setMenuSelect, setSnapshotProvider, setWarpHandler } from '../contract/host';
import { UI_SCENES } from '../ui';
import type { StatKey, WeaponEvolution } from '../data/types';
import { TileWorld } from '../world/TileWorld';
import { TileSkin, tileSkins } from '../world/tileskin';
import { spriteLibrary } from '../systems/sprites';
import { FX_ACTION, arrowFxId, facingOf, hitFrameOffsets, progressFrame, slashFxId } from '../systems/spriteDefs';
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

type GameInitData = { mode?: 'new' | 'next'; weapon?: string; playerName?: string };

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
    this.transitioning = false;
  }

  create(): void {
    this.prepareRun();
    const stage = gameState.stage;
    this.rng = new Rng(hashSeed(gameState.floorSeed + ':runtime'));

    // 월드
    const layout = generateFloor(gameState.floorSeed, stage.layout);
    this.layout = layout;
    this.visitedRooms = new Set(['start']);
    this.clearedRooms = new Set();
    this.bossName = null;
    const floor = gameState.stageIndex + 1;
    this.world = new TileWorld(this, layout, tileSkins.get(floor) ?? TileSkin.placeholder(), gameState.floorSeed);
    this.physics.world.setBounds(0, 0, this.world.widthPx, this.world.heightPx);
    // 층 강조색: 캐릭터 시트의 1층 램프를 현재 층 램프로 치환한 변형 텍스처·애니 (1층은 원본)
    spriteLibrary.activate(this, floor);

    // 플레이어
    const startRoom = layout.rooms.find((r) => r.type === 'start')!;
    const start = this.world.roomCenter(startRoom);
    this.player = new Player(this, start.x, start.y);

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
    });

    this.inputSystem = new InputSystem(this);

    // 계약: 스냅샷 제공, 메뉴 선택 라우팅, HUD 병렬 실행
    setSnapshotProvider(() => this.snapshot());
    setMenuSelect((id, key) => this.menu.select(key, id));
    setWarpHandler({ check: (id) => this.warpDeny(id), run: (id) => this.startWarp(id) });
    if (this.scene.manager.keys[UI_SCENES.HUD] && !this.scene.isActive(UI_SCENES.HUD)) this.scene.launch(UI_SCENES.HUD);
    __system.emit(UI_EVENTS.STAGE_STARTED, {
      stageIndex: gameState.stageIndex,
      stageName: floorText(gameState.stageId)?.title ?? gameState.stage.name,
    });
    this.story('floor', floorText(gameState.stageId)?.enter ?? '');

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

    this.cameras.main.setRoundPixels(true);
    this.updateCamera(true);

    const wantDebugText = typeof location !== 'undefined' && new URLSearchParams(location.search).has('debugtext');
    if (DEBUG.SHOW_TEXT && wantDebugText) {
      this.debugText = this.add
        .text(4, 4, '', { font: DEBUG.FONT, color: COLORS.DEBUG_TEXT })
        .setScrollFactor(0)
        .setDepth(DEPTH.DEBUG);
    }
  }

  update(time: number, delta: number): void {
    if (gameState.gameOver || gameState.cleared) return;

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
    // 워프 연출 동안 입력 잠금 (45라운드)
    const input = time < this.warpLockUntil ? neutralInput(raw) : raw;
    if (input.potionPressed) this.usePotion();
    this.player.sprintAllowed = !this.director.inCombat;
    this.player.update(input, time, delta);
    this.updateSprintDust(time);
    this.updateGale();
    this.updateAimFx(time);
    this.updateDashTrail(time);
    this.updateCamera(false, delta);
    this.director.update();

    if (gameState.exitOpen && !this.transitioning && this.world.isExitAt(this.player.x, this.player.y)) {
      this.transitioning = true;
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
   * 보스 내리찍기 범위 피해: 충격파 연출(crush 시트 재사용, 없으면 링) + 흔들림 + 반경 안 플레이어 피해
   */
  private areaHit = (x: number, y: number, radiusPx: number, attack: number): void => {
    // 플레이어 대검 시트를 빌려 쓰므로 무기색 섬광·흔들림 훅은 끈다 (흔들림은 아래 BOSS_WALL)
    if (this.fx.has('crush')) this.fx.play('crush', x, y, { depth: DEPTH.FX_GROUND, hooks: false });
    else this.drawShockwave(x, y, radiusPx);
    this.shake.add(this.time.now, FEEL.SHAKE.BOSS_WALL.PX, FEEL.SHAKE.BOSS_WALL.MS);
    const c = this.player.body.center;
    const d = Phaser.Math.Distance.Between(x, y, c.x, c.y);
    const hit = d <= radiusPx + this.player.body.halfWidth;
    this.debugLastSlam = { x, y, radiusPx, attack, hit, time: this.time.now };
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
    this.playSwingFx(p);
    this.playGiantFx();
    this.meleeSwing(p);
    // 쌍격·난무: 추가 타격. 시트 hitFrames 가 있으면 그 프레임 시작 간격(43라운드 B), 없으면 TWIN_DELAY_MS 간격
    const hits = Math.max(1, mods.hits ?? 1);
    const multiFx = this.pathFx('dance', 'twin');
    const offsets = FEEL.SYNC_HIT_FRAMES && multiFx ? hitFrameOffsets(this.fx.sheet(multiFx), hits) : null;
    for (let i = 1; i < hits; i++) {
      this.time.delayedCall(offsets?.[i] ?? PROTOTYPE.TWIN_DELAY_MS * i, () => {
        if (this.scene.isActive() && !this.frozen) this.meleeSwing({ ...p, x: this.player.x, y: this.player.y });
      });
    }
    // 지진: 충격파 2단 (quake 시트는 1단에서 한 번만 — 3프레임 시작이 2단 판정 시점)
    const second = mods.shockwaveSecond;
    if (mods.shockwave && second) {
      this.time.delayedCall(second.delayMs, () => {
        if (this.scene.isActive() && !this.frozen)
          this.meleeSwing(
            {
              ...p,
              x: this.player.x,
              y: this.player.y,
              sizeMult: p.sizeMult * second.sizeMult,
              damageMult: p.damageMult * second.damageMult,
            },
            true,
          );
      });
    }
  }

  /** 거인(2차): 공격 애니 동안 플레이어 아래에서 슈퍼아머 오라 루프 (공격 애니 = 쿨다운에 맞춤) */
  private playGiantFx(): void {
    const id = this.pathFx('giant');
    if (!id) return;
    if (this.fx.isActive(this.giantFx)) this.fx.stop(this.giantFx, 0, false);
    this.giantFx = this.fx.play(id, this.player.x, this.player.y, {
      follow: this.player,
      depthOffset: -DEPTH.OVERLAY_STEP,
      durationMs: gameState.weapon.hitbox.cooldownMs,
    });
  }

  /** 공격력 × 배율 × 치명타 × 패시브. 치명타 확률은 기본 + 보너스 + 무기. forceCrit 이면 확정 */
  private rollDamage(mult: number, forceCrit = false): { dmg: number; crit: boolean } {
    const crit = forceCrit || rollCrit(gameState.crit, this.rng);
    const P = gameState.passives;
    const lowHp = P.lowHpThreshold() > 0 && gameState.hp / gameState.maxHp <= P.lowHpThreshold();
    const passiveMult = 1 + P.total('attackMult') + (lowHp ? P.total('lowHpAttackMult') : 0);
    const dmg = Math.round(
      gameState.attack * mult * gameState.weapon.damageMult * passiveMult * (crit ? ECONOMY.critDamageMult : 1),
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
    const { dmg, crit } = this.rollDamage(p.damageMult * rapidMult, p.forceCrit);
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
    // 2차가 1차를 대신한다: 만월(wide) → 거합(iai), 난무(dance) → 쌍격(twin). 그 외는 기본 베기
    const id = this.pathFx('wide', 'iai', 'dance', 'twin') ?? slashFxId(gameState.weapon.id);
    const dir = facingOf(p.dirX, p.dirY, this.player.facingDir);
    const hb = gameState.weapon.hitbox;
    // 잔상 궤적(42라운드, fx-design §6.1): 플레이어 중심의 호를 SLASH_SWEEP_MS 동안 훑는다. 첫 샘플 시각부터 잰다
    const T = FEEL.TRAIL;
    const radius = hb.reach * p.sizeMult * T.SLASH_RADIUS_MULT + hb.width * 0.5;
    const angle = Math.atan2(p.dirY, p.dirX);
    const half = T.SLASH_HALF_ANGLE * (dir === 'left' || dir === 'up' ? -1 : 1);
    const sweep = Math.max(hb.activeMs, T.SLASH_SWEEP_MS);
    const arcSource = () => {
      let t0 = -1;
      return () => {
        if (t0 < 0) t0 = this.time.now;
        const t = (this.time.now - t0) / sweep;
        if (t > 1 || !this.player.active) return null;
        const c = this.player.getCenter();
        return arcPoint(c.x, c.y, radius, angle, half, t);
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
    if (shot.hitStunMs > 0) mob.stun(now, shot.hitStunMs, 'hit');
  }

  private meleeSwing(p: PlayerAttackPayload, secondWave = false): void {
    const weapon = gameState.weapon;
    const mods = weapon.mods;
    const hb = weapon.hitbox;
    const cx = p.x + p.dirX * hb.reach * p.sizeMult;
    const cy = p.y + p.dirY * hb.reach * p.sizeMult;
    // Arcade 바디는 축 정렬 사각형이라 지배적인 축에 맞춰 폭·높이를 바꿔 근사한다.
    const horizontal = Math.abs(p.dirX) >= Math.abs(p.dirY);
    const w = (horizontal ? hb.width : hb.height) * p.sizeMult;
    const h = (horizontal ? hb.height : hb.width) * p.sizeMult;
    // 베기 시트가 있으면 판정 사각형은 보이지 않게(판정만), 없으면 기존 플레이스홀더 표시
    const evoFx = this.evolutionFxId();
    const swingFx = this.pathFx('wide', 'iai', 'dance', 'twin');
    const hasSwingArt = this.fx.has(slashFxId(weapon.id)) || swingFx !== null;
    const zone = this.add.rectangle(cx, cy, w, h, COLORS.ATTACK, hasSwingArt ? 0 : 0.6).setDepth(DEPTH.ATTACK);
    // 궤적·충격파: 시트가 있으면 시트, 없으면 Graphics 플레이스홀더
    if (mods.slashTrail && !swingFx) this.drawSlashTrail(cx, cy, p.dirX, p.dirY, Math.max(w, h));
    if (mods.shockwave) {
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
    const overlap = this.physics.add.overlap(zone, this.mobs, (_z, m) => {
      const mob = m as Mob;
      if (hit.has(mob)) return;
      hit.add(mob);
      this.applyMeleeHit(mob, p);
    });
    // 분쇄: 충격파 범위의 적 투사체 소멸
    const clear =
      mods.shockwave && mods.shockwaveClearsProjectiles
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

    this.time.delayedCall(hb.activeMs, () => {
      this.physics.world.removeCollider(overlap);
      if (clear) this.physics.world.removeCollider(clear);
      zone.destroy();
    });
  }

  /** 근접 타격 1회: 피해 → (사망) 또는 중압 경직·출혈 */
  private applyMeleeHit(mob: Mob, p: PlayerAttackPayload): void {
    const now = this.time.now;
    const mods = gameState.weapon.mods;
    const stunnedByParry = mob.isParryStunned(now);
    const { dmg, crit } = this.rollDamage(p.damageMult, p.forceCrit);
    // 2차 전용 치명 이펙트: 급소(대쉬 베기 적중) → dashcrit, 암살(그림자 걸음 직후) → assassin. 둘 다 crit_burst 대신
    const critFx = p.primed ? this.pathFx('assassin') : p.kind === 'dashAttack' ? this.pathFx('dashcrit') : null;
    if (this.hitMob(mob, dmg, { crit, dirX: p.dirX, dirY: p.dirY, critFx })) {
      this.onKill(mob, stunnedByParry ? 'parry' : p.kind === 'aimed' ? 'attack' : p.kind);
      return;
    }
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
    this.dropLoot(mob);
    this.gainPersonality(Math.round(mob.personalityValue * (1 + gameState.passives.total('personalityMult'))));
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
    const t = this.add
      .text(this.scale.width / 2, this.scale.height / 2 - 40, `개성 변화: ${name}`, {
        font: PLACEHOLDER_UI.FONT_BODY,
        color: COLORS.GAMEOVER_TEXT,
      })
      .setOrigin(0.5)
      .setScrollFactor(0)
      .setDepth(DEPTH.DEBUG);
    this.tweens.add({ targets: t, alpha: 0, delay: PROTOTYPE.BANNER_MS, duration: 400, onComplete: () => t.destroy() });
  }

  // --- 경제: 드랍·획득·물약 ---

  private dropLoot(mob: Mob): void {
    const G = ECONOMY.gold;
    const gold = rollGold(mob.goldValue, G.variance, this.rng);
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
      this.addGold(pk.value);
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
    gameState.lastSoulGain = gained;
  }

  private addGold(amount: number): void {
    gameState.gold += amount;
    EventBus.emit(Events.GOLD_CHANGED, { gold: gameState.gold, delta: amount });
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
    if (!gameState.exitOpen) return;
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
    });
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

  private warpState(): UiWarpState {
    const blocked = this.warpBlock();
    const rooms = this.layout?.rooms ?? [];
    return {
      ready: blocked === null,
      blocked,
      targets: this.director ? warpTargets(rooms, this.visitedRooms, this.director.progress, gameState.roomId) : [],
      warping: this.warping,
    };
  }

  private warpDeny(roomId: string): WarpDenyReason | null {
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
    const region = this.world.cameraRegion(this.player.x, this.player.y);
    const halfW = cam.width / 2;
    const halfH = cam.height / 2;
    let tx = this.player.x;
    let ty = this.player.y;
    if (!force) {
      // 데드존: 중심에서 이만큼 벗어나야 따라간다
      const cx = this.camCenter.x;
      const cy = this.camCenter.y;
      tx =
        this.player.x > cx + CAMERA.DEADZONE_X
          ? this.player.x - CAMERA.DEADZONE_X
          : this.player.x < cx - CAMERA.DEADZONE_X
            ? this.player.x + CAMERA.DEADZONE_X
            : cx;
      ty =
        this.player.y > cy + CAMERA.DEADZONE_Y
          ? this.player.y - CAMERA.DEADZONE_Y
          : this.player.y < cy - CAMERA.DEADZONE_Y
            ? this.player.y + CAMERA.DEADZONE_Y
            : cy;
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
      if (Math.abs(tx - this.camCenter.x) < CAMERA.SNAP_PX) this.camCenter.x = tx;
      if (Math.abs(ty - this.camCenter.y) < CAMERA.SNAP_PX) this.camCenter.y = ty;
    }
    // 흔들림(35라운드): 추종 보간·반올림이 끝난 스크롤에 정수 오프셋만 더한다 (보간과 섞이지 않아 튀지 않음)
    const sh = this.shake.sample(this.time.now);
    cam.setScroll(Math.round(this.camCenter.x - halfW) + sh.x, Math.round(this.camCenter.y - halfH) + sh.y);
  }

  /** 런 시작 모드 결정: 새 런 / 다음 층 / 세이브 이어하기 */
  private prepareRun(): void {
    const params = typeof location !== 'undefined' ? new URLSearchParams(location.search) : new URLSearchParams();
    if (this.initMode === 'next') {
      gameState.nextStage();
      this.saveIfAllowed();
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
    this.fx.destroy();
    audio.stopAllLoops();
    setMenuSelect(null);
    setSnapshotProvider(null);
    setWarpHandler(null);
    this.menu.close();
    this.inputSystem.destroy();
  }
}

/** 화면 절반(half)을 고려해 중심 좌표를 [lo, hi] 영역 안으로. 영역이 화면보다 작으면 가운데 */
function clampCenter(center: number, lo: number, hi: number, half: number): number {
  if (hi - lo <= half * 2) return (lo + hi) / 2;
  return Phaser.Math.Clamp(center, lo + half, hi - half);
}
