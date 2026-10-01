import Phaser from 'phaser';
import { CAMERA, CELL, COLORS, DEBUG, DEPTH, PROTOTYPE, SCENES, TILE } from '../core/Constants';
import {
  EventBus,
  Events,
  type GuardReleasedPayload,
  type PlayerAttackPayload,
  type ShadowStepPayload,
  type WeaponEvolvedPayload,
  type WeaponReinforcedPayload,
} from '../core/EventBus';
import { gameState } from '../core/GameState';
import { BOSSES, ECONOMY, PLAYER_DATA, STORY, WEAPON_RULES } from '../data';
import { deathLine, evolutionLine, fill, floorText } from '../systems/story';
import type { Mob, ProjectileSpec } from '../objects/Mob';
import { Player } from '../objects/Player';
import { Projectile } from '../objects/Projectile';
import { Pickup } from '../objects/Pickup';
import { InputSystem } from '../systems/InputSystem';
import { generateFloor, cellKey, type Cell } from '../systems/mapgen';
import { RoomDirector } from '../systems/RoomDirector';
import { Rng, hashSeed } from '../systems/rng';
import { SaveSlot, browserStorage } from '../systems/save';
import type { KillKind } from '../systems/senses';
import { applyStatReward, findReward, rollCrit, rollGold, shopPrice } from '../systems/economy';
import { TextMenu } from '../systems/TextMenu';
import { metaStore, recordRun } from '../systems/meta';
import { PASSIVES } from '../systems/passives';
import { UI_EVENTS, __system, type StoryKind } from '../contract/ui';
import { buildSnapshot } from '../contract/snapshot';
import { setMenuSelect, setSnapshotProvider } from '../contract/host';
import { UI_SCENES } from '../ui';
import type { StatKey, WeaponEvolution } from '../data/types';
import { TileWorld } from '../world/TileWorld';
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
  private currentCellKey = '';
  private initMode: GameInitData['mode'];
  private initWeapon?: string;
  private initName?: string;
  private playerShots: Phaser.GameObjects.Group;
  private lastShotAt = -Infinity;
  /** 디버그: 마지막 공격 이벤트 */
  private debugLastAttack: unknown = null;
  private rapidCount = 0;
  private readonly saveSlot = new SaveSlot(browserStorage());
  private transitioning = false;
  private visitedRooms = new Set<string>();
  private clearedRooms = new Set<string>();
  private layout?: ReturnType<typeof generateFloor>;
  private bossName: string | null = null;
  private readonly playerVec = new Phaser.Math.Vector2();
  /** 개성 3지선다 중: 게임 진행(이동·적·물리) 정지 */
  private frozen = false;
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
  /** 출혈: 적별 지속 피해 */
  private bleeds: { mob: Mob; dmg: number; ticksLeft: number; nextAt: number; tickMs: number }[] = [];

  constructor() {
    super(SCENES.GAME);
  }

  init(data?: GameInitData): void {
    this.initMode = data?.mode;
    this.initWeapon = data?.weapon;
    this.initName = data?.playerName;
    this.transitioning = false;
    this.currentCellKey = '';
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
    this.world = new TileWorld(this, layout);
    this.physics.world.setBounds(0, 0, this.world.widthPx, this.world.heightPx);

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
    this.lastShotAt = -Infinity;
    this.rapidCount = 0;
    this.frozen = false;
    this.dotZones = [];
    this.bleeds = [];
    this.menu = new TextMenu(this);
    this.shopOpen = false;

    this.physics.add.collider(this.player, this.world.layer);
    this.physics.add.collider(this.mobs, this.world.layer);
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
      onRunCleared: () => {
        this.saveSlot.clear();
        this.settleRun(true);
        this.time.delayedCall(PROTOTYPE.CLEAR_DELAY_MS, () => this.endRunScene(true));
      },
      onStageCleared: (room) => this.beginStageReward(room),
      isLastStage: () => gameState.isLastStage,
    });

    this.inputSystem = new InputSystem(this);

    // 계약: 스냅샷 제공, 메뉴 선택 라우팅, HUD 병렬 실행
    setSnapshotProvider(() => this.snapshot());
    setMenuSelect((id, key) => this.menu.select(key, id));
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
      hurt: (m, amount) => {
        if (m.takeDamage(amount)) this.onKill(m, 'attack');
      },
      fireAtPlayer: (distPx, speedPx, attack) => {
        const x = this.player.x + distPx;
        const y = this.player.y;
        this.fire(x, y, -1, 0, { speedPx, attack, size: 4, lifeMs: 5000 });
      },
      playerInfo: () => ({ x: this.player.x, y: this.player.y, action: this.player.action }),
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
      camera: () => ({ scrollX: this.cameras.main.scrollX, scrollY: this.cameras.main.scrollY, zoom: this.scale.zoom }),
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
      }),
    });

    EventBus.on(Events.PLAYER_ATTACKED, this.onPlayerAttacked, this);
    EventBus.on(Events.PLAYER_DIED, this.onPlayerDied, this);
    EventBus.on(Events.TRIAL_CLEARED, this.onTrialCleared, this);
    EventBus.on(Events.ROOM_ENTERED, this.onRoomEnteredUi, this);
    EventBus.on(Events.PLAYER_DAMAGED, this.relayDamaged, this);
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
      __system.emit(UI_EVENTS.STATE, this.snapshot());
      return;
    }

    const input = this.inputSystem.read();
    if (input.potionPressed) this.usePotion();
    this.player.update(input, time);
    this.updateCamera(false);
    this.director.update();

    if (gameState.exitOpen && !this.transitioning && this.world.isExitAt(this.player.x, this.player.y)) {
      this.transitioning = true;
      this.scene.restart({ mode: 'next' } satisfies GameInitData);
      return;
    }

    this.playerVec.set(this.player.x, this.player.y);
    const ctx = { time, delta, player: this.playerVec, fire: this.fire };
    for (const child of this.mobs.getChildren()) (child as Mob).update(ctx);
    for (const child of this.projectiles.getChildren()) (child as Projectile).tick(time);
    for (const child of this.pickups.getChildren()) (child as Pickup).tick(time);
    for (const child of this.playerShots.getChildren()) (child as Projectile).tick(time);
    this.tickHoming(delta);
    this.tickDotZones(time);
    this.tickBleeds(time);
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
    p.launch(x, y, dirX, dirY, spec, this.time.now);
  };

  private onPlayerAttacked(p: PlayerAttackPayload): void {
    this.debugLastAttack = { ...p, time: this.time.now };
    const weapon = gameState.weapon;
    if (weapon.def.kind === 'ranged') {
      this.fireArrow(p);
      return;
    }
    const mods = weapon.mods;
    this.meleeSwing(p);
    // 쌍격·난무: 추가 타격
    const hits = Math.max(1, mods.hits ?? 1);
    for (let i = 1; i < hits; i++) {
      this.time.delayedCall(PROTOTYPE.TWIN_DELAY_MS * i, () => {
        if (this.scene.isActive() && !this.frozen) this.meleeSwing({ ...p, x: this.player.x, y: this.player.y });
      });
    }
    // 지진: 충격파 2단
    const second = mods.shockwaveSecond;
    if (mods.shockwave && second) {
      this.time.delayedCall(second.delayMs, () => {
        if (this.scene.isActive() && !this.frozen)
          this.meleeSwing({
            ...p,
            x: this.player.x,
            y: this.player.y,
            sizeMult: p.sizeMult * second.sizeMult,
            damageMult: p.damageMult * second.damageMult,
          });
      });
    }
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

  private fireArrow(p: PlayerAttackPayload): void {
    const weapon = gameState.weapon;
    const R = weapon.def.ranged!;
    const mods = weapon.mods;
    const now = this.time.now;
    const aimed = p.kind === 'aimed';
    let rapidMult = 1;
    if (!aimed) {
      this.rapidCount = now - this.lastShotAt <= R.rapidWindowMs ? this.rapidCount + 1 : 0;
      this.lastShotAt = now;
      rapidMult = Math.max(R.rapidMin, 1 - R.rapidDecay * this.rapidCount);
    }
    const { dmg } = this.rollDamage(p.damageMult * rapidMult, p.forceCrit);
    // 조준 사격·섬광: 무한 관통
    const pierce = aimed || mods.pierceInfinite ? Infinity : (mods.pierce ?? 0);
    const size = weapon.hitbox.width * p.sizeMult;
    const speed = R.projectileSpeedTiles * TILE * (mods.projectileSpeedMult ?? 1);
    const base = Math.atan2(p.dirY, p.dirX);
    // 산탄·폭우: 부채꼴 (조준 사격은 한 발)
    const spread = !aimed && mods.spread ? mods.spread : { count: 1, spreadDeg: 0 };
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
      );
      if (mods.homingTurnDeg) shot.homingTurn = Phaser.Math.DegToRad(mods.homingTurnDeg);
      if (aimed && mods.aimedShotStunMs) shot.hitStunMs = mods.aimedShotStunMs;
    }
  }

  private onPlayerShotHit(shot: Projectile, mob: Mob): void {
    if (!shot.active || shot.owner !== 'player') return;
    if (!shot.registerHit(mob)) return;
    const now = this.time.now;
    const stunnedByParry = mob.isParryStunned(now);
    if (mob.takeDamage(shot.attack)) {
      this.onKill(mob, stunnedByParry ? 'parry' : 'attack');
      return;
    }
    if (shot.hitStunMs > 0) mob.stun(now, shot.hitStunMs, 'hit');
  }

  private meleeSwing(p: PlayerAttackPayload): void {
    const weapon = gameState.weapon;
    const mods = weapon.mods;
    const hb = weapon.hitbox;
    const cx = p.x + p.dirX * hb.reach * p.sizeMult;
    const cy = p.y + p.dirY * hb.reach * p.sizeMult;
    // Arcade 바디는 축 정렬 사각형이라 지배적인 축에 맞춰 폭·높이를 바꿔 근사한다.
    const horizontal = Math.abs(p.dirX) >= Math.abs(p.dirY);
    const w = (horizontal ? hb.width : hb.height) * p.sizeMult;
    const h = (horizontal ? hb.height : hb.width) * p.sizeMult;
    const zone = this.add.rectangle(cx, cy, w, h, COLORS.ATTACK, 0.6).setDepth(DEPTH.ATTACK);
    if (mods.slashTrail) this.drawSlashTrail(cx, cy, p.dirX, p.dirY, Math.max(w, h));
    if (mods.shockwave) this.drawShockwave(cx, cy, Math.max(w, h));
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
      const g = this.add.rectangle(cx, cy, w, h, COLORS.TRAIL_DOT, 0.35).setDepth(DEPTH.ATTACK);
      this.tweens.add({ targets: g, alpha: 0, duration: mods.trailDot.lingerMs, onComplete: () => g.destroy() });
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
    const { dmg } = this.rollDamage(p.damageMult, p.forceCrit);
    if (mob.takeDamage(dmg)) {
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
      } else this.bleeds.push({ mob, dmg: tick, ticksLeft: B.ticks, nextAt: now + B.tickMs, tickMs: B.tickMs });
    }
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
        if (mob.takeDamage(z.dmg)) this.onKill(mob, 'attack');
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
      if (b.mob.takeDamage(b.dmg)) this.onKill(b.mob, 'attack');
      else b.mob.flashColor(COLORS.BLEED);
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
    const g = this.add.graphics().setDepth(DEPTH.ATTACK);
    g.lineStyle(2, COLORS.GUARD_PUSH, 0.9);
    g.strokeCircle(p.x, p.y, radius);
    this.tweens.add({ targets: g, alpha: 0, duration: PROTOTYPE.GUARD_PUSH_MS, onComplete: () => g.destroy() });
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
        if (m.takeDamage(dmg)) this.onKill(m, 'attack');
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
      const off = Math.max(target.width, target.height) / 2 + half + 2;
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
    const ghost = this.add.rectangle(p.x, p.y, pw, ph, COLORS.PLAYER_SHADOW, 0.6).setDepth(DEPTH.ATTACK);
    this.tweens.add({
      targets: ghost,
      alpha: 0,
      duration: PROTOTYPE.SHADOW_STEP_MS,
      onComplete: () => ghost.destroy(),
    });
    this.player.teleportTo(dest.x, dest.y);
  }

  /** 잔상: 대쉬 경로에 피해 영역 */
  private onPlayerDashed(p: { dirX: number; dirY: number; x: number; y: number }): void {
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
      if (mob.takeDamage(dmg)) this.onKill(mob, 'dashAttack');
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
        label: o ? fill(STORY.ui.evolveMenu.itemFormat, { name: o.name, menu: o.description }) : '변환 (완료)',
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

  /** 3지선다 동안 게임 정지 (물리·적·플레이어). 메뉴는 UI 가 그린다 */
  private setFrozen(on: boolean): void {
    if (this.frozen === on) return;
    this.frozen = on;
    if (on) this.physics.world.pause();
    else this.physics.world.resume();
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
        font: '14px monospace',
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
    // 패링 창이면 접촉 공격 주기와 무관하게 막는다 (돌진 포함)
    if (this.player.isParrying && !mob.isStunned(now)) {
      const attack = mob.tryContactAttack(now);
      if (attack > 0 || mob.body.velocity.lengthSq() > 0) {
        if (this.player.takeHit(attack || 1, now) === 'parried') mob.stun(now, PLAYER_DATA.parry.stunMs);
      }
      return;
    }
    const attack = mob.tryContactAttack(now);
    if (attack > 0) this.player.takeHit(attack, now);
  }

  private onProjectileHit(pr: Projectile): void {
    if (!pr.active || pr.reflected) return;
    const result = this.player.takeHit(pr.attack, this.time.now);
    if (result === 'parried') pr.reflect(PLAYER_DATA.parry.reflectDamageMult + gameState.passives.total('reflectMult'));
    else pr.deactivate();
  }

  private onReflectedHit(pr: Projectile, mob: Mob): void {
    if (!pr.active || !pr.reflected) return;
    pr.deactivate();
    if (mob.takeDamage(pr.attack)) this.onKill(mob, 'parry');
  }

  private onPlayerDied(): void {
    this.saveSlot.clear(); // 영구 사망 (기획 3장)
    this.settleRun(false);
    this.player.body.setVelocity(0, 0);
    this.endRunScene(false);
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
      line: cleared ? STORY.endings.destroy : deathLine(gameState.playerName, gameState.floorReached, gameState.kills),
    };
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
    });
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

  private relayDamaged(p: unknown): void {
    __system.emit(UI_EVENTS.PLAYER_DAMAGED, p);
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

  // --- 카메라: 방은 고정, 보스 방만 추적 ---

  private updateCamera(force: boolean): void {
    const cell: Cell = this.world.cellAt(this.player.x, this.player.y);
    const key = cellKey(cell);
    if (!force && key === this.currentCellKey) return;
    this.currentCellKey = key;
    const cam = this.cameras.main;
    const room = this.world.roomAtCell(cell);
    if (room?.type === 'boss') {
      const r = this.world.roomCellsRect(room);
      cam.setBounds(r.x, r.y, r.width, r.height);
      cam.startFollow(this.player, true, CAMERA.FOLLOW_LERP, CAMERA.FOLLOW_LERP);
    } else {
      cam.stopFollow();
      cam.removeBounds();
      cam.setScroll(cell.cx * CELL.W_PX, cell.cy * CELL.H_PX + CAMERA.CELL_OFFSET_Y);
    }
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
    EventBus.off(Events.PLAYER_DAMAGED, this.relayDamaged, this);
    EventBus.off(Events.PLAYER_HEALED, this.relayHealed, this);
    EventBus.off(Events.GOLD_CHANGED, this.relayGold, this);
    EventBus.off(Events.WEAPON_EVOLVED, this.relayEvolved, this);
    EventBus.off(Events.BOSS_STARTED, this.relayBossStarted, this);
    EventBus.off(Events.BOSS_PHASE, this.relayBossPhase, this);
    EventBus.off(Events.BOSS_DIED, this.relayBossDied, this);
    EventBus.off(Events.PLAYER_GUARD_RELEASED, this.onGuardReleased, this);
    EventBus.off(Events.PLAYER_SHADOW_STEP, this.onShadowStep, this);
    EventBus.off(Events.PLAYER_DASHED, this.onPlayerDashed, this);
    if (this.frozen) this.physics.world.resume();
    setMenuSelect(null);
    setSnapshotProvider(null);
    this.menu.close();
    this.inputSystem.destroy();
  }
}
