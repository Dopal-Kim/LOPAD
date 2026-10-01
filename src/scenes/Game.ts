import Phaser from 'phaser';
import { CAMERA, CELL, COLORS, DEBUG, DEPTH, PROTOTYPE, SCENES, TILE } from '../core/Constants';
import { EventBus, Events, type PlayerAttackPayload, type WeaponEvolvedPayload } from '../core/EventBus';
import { gameState } from '../core/GameState';
import { BOSSES, ECONOMY, PLAYER_DATA } from '../data';
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
import { UI_EVENTS, __system } from '../contract/ui';
import { buildSnapshot } from '../contract/snapshot';
import { setMenuSelect, setSnapshotProvider } from '../contract/host';
import { UI_SCENES } from '../ui';
import type { StatKey } from '../data/types';
import { TileWorld } from '../world/TileWorld';
import { exposeDebug } from '../debug';

type GameInitData = { mode?: 'new' | 'next'; weapon?: string };

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

  constructor() {
    super(SCENES.GAME);
  }

  init(data?: GameInitData): void {
    this.initMode = data?.mode;
    this.initWeapon = data?.weapon;
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
    __system.emit(UI_EVENTS.STAGE_STARTED, { stageIndex: gameState.stageIndex, stageName: gameState.stage.name });

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
    this.updateShop();

    __system.emit(UI_EVENTS.STATE, this.snapshot());

    if (this.debugText) {
      const boss =
        gameState.bossMaxHp > 0 ? `  boss ${gameState.bossHp}/${gameState.bossMaxHp} p${gameState.bossPhase}` : '';
      this.debugText.setText(
        `[DEBUG] ${gameState.stage.name} save ${gameState.savesLeft}  P[${gameState.passives.summary() || '-'}]  HP ${gameState.hp}/${gameState.maxHp}  G ${gameState.gold}  potion ${gameState.potions}  pts ${gameState.pointsPending}  atk ${gameState.attack} def ${gameState.defense} crit ${gameState.crit}%  ${this.player.action}  sense ${gameState.senses.sense}  ${gameState.weapon.displayName} ${gameState.weapon.personality}/${gameState.weapon.def.personality.threshold}  room ${gameState.roomId || '-'}  trials ${gameState.trialsCleared}/${gameState.trialsTotal}${gameState.bossUnlocked ? ' (boss open)' : ''}${boss}  seed ${gameState.seed}`,
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
    this.meleeSwing(p);
    if (weapon.evolution?.effect === 'twin') {
      this.time.delayedCall(PROTOTYPE.TWIN_DELAY_MS, () => {
        if (this.scene.isActive()) this.meleeSwing({ ...p, x: this.player.x, y: this.player.y });
      });
    }
  }

  /** 공격력 × 배율 × 치명타 × 패시브. 치명타 확률은 기본 + 보너스 + 무기 */
  private rollDamage(mult: number): { dmg: number; crit: boolean } {
    const crit = rollCrit(gameState.crit, this.rng);
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
    const now = this.time.now;
    this.rapidCount = now - this.lastShotAt <= R.rapidWindowMs ? this.rapidCount + 1 : 0;
    this.lastShotAt = now;
    const rapidMult = Math.max(R.rapidMin, 1 - R.rapidDecay * this.rapidCount);
    const { dmg } = this.rollDamage(p.damageMult * rapidMult);
    const shot = this.playerShots.get() as Projectile | null;
    if (!shot) return;
    const pierce = weapon.evolution?.effect === 'pierce' ? 1 : 0;
    const size = weapon.hitbox.width * p.sizeMult;
    shot.launch(
      p.x + p.dirX * weapon.hitbox.reach,
      p.y + p.dirY * weapon.hitbox.reach,
      p.dirX,
      p.dirY,
      { speedPx: R.projectileSpeedTiles * TILE, attack: dmg, size, lifeMs: R.projectileLifeMs },
      now,
      'player',
      pierce,
    );
  }

  private onPlayerShotHit(shot: Projectile, mob: Mob): void {
    if (!shot.active || shot.owner !== 'player') return;
    if (!shot.registerHit(mob)) return;
    const stunnedByParry = mob.isStunned(this.time.now);
    if (mob.takeDamage(shot.attack)) this.onKill(mob, stunnedByParry ? 'parry' : 'attack');
  }

  private meleeSwing(p: PlayerAttackPayload): void {
    const weapon = gameState.weapon;
    const hb = weapon.hitbox;
    const cx = p.x + p.dirX * hb.reach * p.sizeMult;
    const cy = p.y + p.dirY * hb.reach * p.sizeMult;
    // Arcade 바디는 축 정렬 사각형이라 지배적인 축에 맞춰 폭·높이를 바꿔 근사한다.
    const horizontal = Math.abs(p.dirX) >= Math.abs(p.dirY);
    const w = (horizontal ? hb.width : hb.height) * p.sizeMult;
    const h = (horizontal ? hb.height : hb.width) * p.sizeMult;
    const zone = this.add.rectangle(cx, cy, w, h, COLORS.ATTACK, 0.6).setDepth(DEPTH.ATTACK);
    if (weapon.evolution?.effect === 'slash-trail') this.drawSlashTrail(cx, cy, p.dirX, p.dirY, Math.max(w, h));
    if (weapon.evolution?.effect === 'shockwave') this.drawShockwave(cx, cy, Math.max(w, h));
    this.physics.add.existing(zone);
    (zone.body as Phaser.Physics.Arcade.Body).setAllowGravity(false);

    const hit = new Set<Mob>();
    const overlap = this.physics.add.overlap(zone, this.mobs, (_z, m) => {
      const mob = m as Mob;
      if (hit.has(mob)) return;
      hit.add(mob);
      const stunnedByParry = mob.isStunned(this.time.now);
      const { dmg } = this.rollDamage(p.damageMult);
      const died = mob.takeDamage(dmg);
      if (died) this.onKill(mob, stunnedByParry ? 'parry' : p.kind);
    });

    this.time.delayedCall(hb.activeMs, () => {
      this.physics.world.removeCollider(overlap);
      zone.destroy();
    });
  }

  private onKill(mob: Mob, kind: KillKind): void {
    gameState.kills += 1;
    this.dropLoot(mob);
    const weapon = gameState.weapon;
    const evolved = weapon.gainPersonality(
      Math.round(mob.personalityValue * (1 + gameState.passives.total('personalityMult'))),
    );
    const lifesteal = gameState.passives.total('healOnKill');
    if (lifesteal > 0) this.player.heal(lifesteal);
    EventBus.emit(Events.PERSONALITY_GAINED, {
      value: weapon.personality,
      threshold: weapon.def.personality.threshold,
    });
    if (evolved !== null) {
      const payload: WeaponEvolvedPayload = { weapon: weapon.id, stage: evolved, name: weapon.displayName };
      EventBus.emit(Events.WEAPON_EVOLVED, payload);
      if (!__system.rendererRegistered()) this.showEvolutionBanner(weapon.displayName);
    }
    if (gameState.senses.recordKill(kind)) {
      EventBus.emit(Events.SENSE_GAINED, { kind, sense: gameState.senses.sense });
    }
    this.director.onMobDied(mob);
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
      evolutionNames: w.def.personality.evolutions.slice(0, w.stage).map((e) => e.name),
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
      this.menu.open('reward', `감각 보상: 능력치 포인트 ${gameState.pointsPending}`, lines, (key) => {
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
    this.menu.open('passive', '보스 보상: 패시브 선택', lines, (key) => {
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
        return { key: String(i + 1), label: `${it.name}  ${price}G`, enabled: gameState.gold >= price && !full };
      });
      this.menu.open(
        'shop',
        `상점  (보유 ${gameState.gold}G, 물약 ${gameState.potions})`,
        lines,
        (key) => this.buy(ECONOMY.shop.items[Number(key) - 1].id, render),
        '타일에서 벗어나면 닫힘',
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
      stageName: gameState.stage.name,
      floorReached: gameState.floorReached,
      kills: gameState.kills,
      gold: gameState.gold,
      sense: gameState.senses.sense,
      weaponName: gameState.weapon.displayName,
      soulsGained: gameState.lastSoulGain,
      soulsTotal: metaStore.read().souls,
      seed: gameState.seed,
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

  private onRoomEnteredUi(p: { roomId: string; type: string }): void {
    this.visitedRooms.add(p.roomId);
    __system.emit(UI_EVENTS.ROOM_ENTERED, p);
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
      gameState.startRun(this.pickSeed(), this.initWeapon);
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
    setMenuSelect(null);
    setSnapshotProvider(null);
    this.menu.close();
    this.inputSystem.destroy();
  }
}
