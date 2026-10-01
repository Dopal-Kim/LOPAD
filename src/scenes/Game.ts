import Phaser from 'phaser';
import { COLORS, DEBUG, DEPTH, GAME, PROTOTYPE, SCENES, TILE } from '../core/Constants';
import { EventBus, Events, type EnemyDiedPayload } from '../core/EventBus';
import { gameState } from '../core/GameState';
import { PLAYER_DATA } from '../data';
import { Enemy } from '../objects/Enemy';
import { Player } from '../objects/Player';
import { InputSystem } from '../systems/InputSystem';

type AttackPayload = { x: number; y: number; dirX: number; dirY: number };

export class Game extends Phaser.Scene {
  private player: Player;
  private enemies: Phaser.Physics.Arcade.Group;
  private inputSystem: InputSystem;
  private debugText?: Phaser.GameObjects.Text;
  private readonly targetVec = new Phaser.Math.Vector2();

  constructor() {
    super(SCENES.GAME);
  }

  create(): void {
    gameState.reset();
    this.physics.world.setBounds(0, 0, GAME.WIDTH, GAME.HEIGHT);
    this.drawGrid();

    this.player = new Player(this, GAME.WIDTH / 2, GAME.HEIGHT / 2);
    this.enemies = this.physics.add.group({ runChildUpdate: false });
    this.spawnEnemies('dummy', PROTOTYPE.ENEMY_COUNT);

    this.physics.add.collider(this.enemies, this.enemies);
    this.physics.add.overlap(this.player, this.enemies, (_p, e) => this.onEnemyTouch(e as Enemy));

    this.inputSystem = new InputSystem(this);

    EventBus.on(Events.PLAYER_ATTACKED, this.onPlayerAttacked, this);
    EventBus.on(Events.PLAYER_DIED, this.onPlayerDied, this);
    this.events.once('shutdown', this.cleanup, this);

    if (DEBUG.SHOW_TEXT) {
      this.debugText = this.add
        .text(4, 4, '', { font: DEBUG.FONT, color: COLORS.DEBUG_TEXT })
        .setDepth(DEPTH.DEBUG);
    }
  }

  update(time: number): void {
    if (gameState.gameOver || gameState.cleared) return;

    const input = this.inputSystem.read();
    this.player.update(input, time);

    this.targetVec.set(this.player.x, this.player.y);
    for (const child of this.enemies.getChildren()) {
      (child as Enemy).update(this.targetVec);
    }

    if (this.debugText) {
      this.debugText.setText(
        `[DEBUG] HP ${gameState.hp}/${gameState.maxHp}  enemies ${gameState.enemiesRemaining}  kills ${gameState.enemiesKilled}`,
      );
    }
  }

  // --- 전투 ---

  private onPlayerAttacked(p: AttackPayload): void {
    const hb = PLAYER_DATA.attackHitbox;
    const cx = p.x + p.dirX * hb.reach;
    const cy = p.y + p.dirY * hb.reach;

    // 히트박스: 공격 방향으로 길게 놓인 사각형. 회전 사각형의 Arcade 바디는 AABB이므로
    // 가로/세로가 지배적인 방향에 맞춰 폭·높이를 바꿔 근사한다.
    const horizontal = Math.abs(p.dirX) >= Math.abs(p.dirY);
    const w = horizontal ? hb.width : hb.height;
    const h = horizontal ? hb.height : hb.width;
    const zone = this.add.rectangle(cx, cy, w, h, COLORS.ATTACK, 0.6).setDepth(DEPTH.ATTACK);
    this.physics.add.existing(zone);
    const body = zone.body as Phaser.Physics.Arcade.Body;
    body.setAllowGravity(false);

    const hit = new Set<Enemy>();
    const overlap = this.physics.add.overlap(zone, this.enemies, (_z, e) => {
      const enemy = e as Enemy;
      if (hit.has(enemy)) return;
      hit.add(enemy);
      const died = enemy.takeDamage(PLAYER_DATA.stats.attack);
      if (died) this.onEnemyDied(enemy);
    });

    this.time.delayedCall(hb.activeMs, () => {
      this.physics.world.removeCollider(overlap);
      zone.destroy();
    });
  }

  private onEnemyTouch(enemy: Enemy): void {
    const attack = enemy.tryAttack(this.time.now);
    if (attack > 0) this.player.takeHit(attack, this.time.now);
  }

  private onEnemyDied(enemy: Enemy): void {
    gameState.enemiesKilled += 1;
    gameState.enemiesRemaining = this.enemies.countActive(true);
    const payload: EnemyDiedPayload = { id: enemy.id, remaining: gameState.enemiesRemaining };
    EventBus.emit(Events.ENEMY_DIED, payload);
    if (gameState.enemiesRemaining === 0) {
      gameState.cleared = true;
      EventBus.emit(Events.RUN_CLEARED);
      this.scene.start(SCENES.GAME_OVER, { cleared: true });
    }
  }

  private onPlayerDied(): void {
    this.player.body.setVelocity(0, 0);
    this.scene.start(SCENES.GAME_OVER, { cleared: false });
  }

  // --- 배치 ---

  private spawnEnemies(id: string, count: number): void {
    const margin = TILE;
    for (let i = 0; i < count; i++) {
      let x = 0;
      let y = 0;
      for (let tries = 0; tries < 20; tries++) {
        x = Phaser.Math.Between(margin, GAME.WIDTH - margin);
        y = Phaser.Math.Between(margin, GAME.HEIGHT - margin);
        if (Phaser.Math.Distance.Between(x, y, this.player.x, this.player.y) >= PROTOTYPE.ENEMY_SPAWN_MIN_DIST) break;
      }
      this.enemies.add(new Enemy(this, x, y, id));
    }
    gameState.enemiesRemaining = this.enemies.countActive(true);
  }

  private drawGrid(): void {
    const g = this.add.graphics().setDepth(DEPTH.GRID);
    g.lineStyle(1, COLORS.GRID, 1);
    for (let x = 0; x <= GAME.WIDTH; x += TILE) g.lineBetween(x, 0, x, GAME.HEIGHT);
    for (let y = 0; y <= GAME.HEIGHT; y += TILE) g.lineBetween(0, y, GAME.WIDTH, y);
  }

  private cleanup(): void {
    EventBus.off(Events.PLAYER_ATTACKED, this.onPlayerAttacked, this);
    EventBus.off(Events.PLAYER_DIED, this.onPlayerDied, this);
    this.inputSystem.destroy();
  }
}
