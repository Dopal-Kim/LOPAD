import Phaser from 'phaser';
import { CAMERA, CELL, COLORS, DEBUG, DEPTH, PROTOTYPE, SCENES } from '../core/Constants';
import { EventBus, Events, type PlayerAttackPayload, type WeaponEvolvedPayload } from '../core/EventBus';
import { gameState } from '../core/GameState';
import { PLAYER_DATA, STAGES } from '../data';
import type { Mob, ProjectileSpec } from '../objects/Mob';
import { Player } from '../objects/Player';
import { Projectile } from '../objects/Projectile';
import { InputSystem } from '../systems/InputSystem';
import { generateFloor, cellKey, type Cell } from '../systems/mapgen';
import { RoomDirector } from '../systems/RoomDirector';
import { Rng, hashSeed } from '../systems/rng';
import type { KillKind } from '../systems/senses';
import { TileWorld } from '../world/TileWorld';
import { exposeDebug } from '../debug';

const STAGE_ID = 'stage1';

export class Game extends Phaser.Scene {
  private player: Player;
  private mobs: Phaser.Physics.Arcade.Group;
  private projectiles: Phaser.GameObjects.Group;
  private world: TileWorld;
  private director: RoomDirector;
  private inputSystem: InputSystem;
  private rng: Rng;
  private debugText?: Phaser.GameObjects.Text;
  private currentCellKey = '';
  private readonly playerVec = new Phaser.Math.Vector2();

  constructor() {
    super(SCENES.GAME);
  }

  create(): void {
    const seed = this.pickSeed();
    gameState.reset(seed);
    this.rng = new Rng(hashSeed(seed + ':runtime'));
    const stage = STAGES[STAGE_ID];

    // 월드
    const layout = generateFloor(seed, stage.layout);
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

    this.physics.add.collider(this.player, this.world.layer);
    this.physics.add.collider(this.mobs, this.world.layer);
    this.physics.add.collider(this.mobs, this.mobs);
    this.physics.add.overlap(this.player, this.mobs, (_p, m) => this.onMobTouch(m as Mob));
    this.physics.add.overlap(this.player, this.projectiles, (_p, pr) => this.onProjectileHit(pr as Projectile));
    this.physics.add.overlap(this.projectiles, this.mobs, (pr, m) => this.onReflectedHit(pr as Projectile, m as Mob));

    // 방 상태 머신
    this.director = new RoomDirector({
      world: this.world,
      stage,
      rng: this.rng,
      player: this.player,
      mobs: this.mobs,
      heal: (f) => this.player.heal(Math.round(gameState.maxHp * f)),
      onRunCleared: () =>
        this.time.delayedCall(PROTOTYPE.CLEAR_DELAY_MS, () => this.scene.start(SCENES.GAME_OVER, { cleared: true })),
    });

    this.inputSystem = new InputSystem(this);

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
    this.events.once('shutdown', this.cleanup, this);

    this.cameras.main.setRoundPixels(true);
    this.updateCamera(true);

    if (DEBUG.SHOW_TEXT) {
      this.debugText = this.add
        .text(4, 4, '', { font: DEBUG.FONT, color: COLORS.DEBUG_TEXT })
        .setScrollFactor(0)
        .setDepth(DEPTH.DEBUG);
    }
  }

  update(time: number, delta: number): void {
    if (gameState.gameOver || gameState.cleared) return;

    const input = this.inputSystem.read();
    this.player.update(input, time);
    this.updateCamera(false);
    this.director.update();

    this.playerVec.set(this.player.x, this.player.y);
    const ctx = { time, delta, player: this.playerVec, fire: this.fire };
    for (const child of this.mobs.getChildren()) (child as Mob).update(ctx);
    for (const child of this.projectiles.getChildren()) (child as Projectile).tick(time);

    if (this.debugText) {
      const boss =
        gameState.bossMaxHp > 0 ? `  boss ${gameState.bossHp}/${gameState.bossMaxHp} p${gameState.bossPhase}` : '';
      this.debugText.setText(
        `[DEBUG] HP ${gameState.hp}/${gameState.maxHp}  ${this.player.action}  sense ${gameState.senses.sense}  ${gameState.weapon.displayName} ${gameState.weapon.personality}/${gameState.weapon.def.personality.threshold}  room ${gameState.roomId || '-'}  trials ${gameState.trialsCleared}/${gameState.trialsTotal}${gameState.bossUnlocked ? ' (boss open)' : ''}${boss}  seed ${gameState.seed}`,
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
    this.physics.add.existing(zone);
    (zone.body as Phaser.Physics.Arcade.Body).setAllowGravity(false);

    const hit = new Set<Mob>();
    const overlap = this.physics.add.overlap(zone, this.mobs, (_z, m) => {
      const mob = m as Mob;
      if (hit.has(mob)) return;
      hit.add(mob);
      const stunnedByParry = mob.isStunned(this.time.now);
      const died = mob.takeDamage(Math.round(PLAYER_DATA.stats.attack * p.damageMult * weapon.damageMult));
      if (died) this.onKill(mob, stunnedByParry ? 'parry' : p.kind);
    });

    this.time.delayedCall(hb.activeMs, () => {
      this.physics.world.removeCollider(overlap);
      zone.destroy();
    });
  }

  private onKill(mob: Mob, kind: KillKind): void {
    gameState.kills += 1;
    const weapon = gameState.weapon;
    const evolved = weapon.gainPersonality(mob.personalityValue);
    EventBus.emit(Events.PERSONALITY_GAINED, {
      value: weapon.personality,
      threshold: weapon.def.personality.threshold,
    });
    if (evolved !== null) {
      const payload: WeaponEvolvedPayload = { weapon: weapon.id, stage: evolved, name: weapon.displayName };
      EventBus.emit(Events.WEAPON_EVOLVED, payload);
      this.showEvolutionBanner(weapon.displayName);
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
    if (result === 'parried') pr.reflect(PLAYER_DATA.parry.reflectDamageMult);
    else pr.deactivate();
  }

  private onReflectedHit(pr: Projectile, mob: Mob): void {
    if (!pr.active || !pr.reflected) return;
    pr.deactivate();
    if (mob.takeDamage(pr.attack)) this.onKill(mob, 'parry');
  }

  private onPlayerDied(): void {
    this.player.body.setVelocity(0, 0);
    this.scene.start(SCENES.GAME_OVER, { cleared: false });
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

  private pickSeed(): string {
    const fromUrl = typeof location !== 'undefined' ? new URLSearchParams(location.search).get('seed') : null;
    return fromUrl || Date.now().toString(36);
  }

  private cleanup(): void {
    EventBus.off(Events.PLAYER_ATTACKED, this.onPlayerAttacked, this);
    EventBus.off(Events.PLAYER_DIED, this.onPlayerDied, this);
    this.inputSystem.destroy();
  }
}
