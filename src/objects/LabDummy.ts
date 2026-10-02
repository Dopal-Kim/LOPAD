/**
 * 49라운드 계약 §11.4 무기 시험장 허수아비 (임시: 단색 사각형 + 누적 피해 표시).
 * target = 중앙 허수아비(무한 체력, 맞으면 데미지 숫자 — Game.hitMob 공통 경로), turret = 일정 방향으로 투사체를 쏘는 허수아비.
 * 움직이지 않고(넉백·밀쳐내기 무시) 접촉 피해도 없다. 개성·골드를 주지 않는다.
 */
import Phaser from 'phaser';
import { ENEMY_FX, LAB, PLACEHOLDER_UI, COLORS } from '../core/Constants';
import { EventBus, Events, type EnemyDamagedPayload } from '../core/EventBus';
import { Mob, type DamageInfo, type MobContext } from './Mob';

export type LabDummyRole = 'target' | 'turret';

/** 사실상 무한 체력 (표시용 최대치) */
const LAB_HP = 1_000_000;

export class LabDummy extends Mob {
  /** 누적 피해 · 맞은 횟수 · 쏜 탄 수 (디버그·표시) */
  totalDamage = 0;
  hits = 0;
  shots = 0;
  private nextShotAt = 0;
  private readonly label: Phaser.GameObjects.Text;

  constructor(
    scene: Phaser.Scene,
    x: number,
    y: number,
    readonly role: LabDummyRole,
  ) {
    super(
      scene,
      x,
      y,
      role === 'target' ? 'lab_dummy' : 'lab_turret',
      LAB.DUMMY_SIZE,
      role === 'target' ? LAB.DUMMY_COLOR : LAB.TURRET_COLOR,
      LAB_HP,
    );
    this.body.setImmovable(true);
    this.label = scene.add
      .text(x, y - LAB.DUMMY_SIZE[1], role === 'target' ? '허수아비' : '사수 허수아비', {
        font: PLACEHOLDER_UI.FONT_BODY,
        color: COLORS.GAMEOVER_TEXT,
      })
      .setOrigin(0.5, 1)
      .setScale(0.5)
      .setDepth(this.depth + 1);
    this.once(Phaser.GameObjects.Events.DESTROY, () => this.label.destroy());
  }

  /** 움직이지 않는다: AI 는 사수 발사만, 바라보는 방향은 사수면 발사 방향 */
  update(ctx: MobContext): void {
    if (!this.active) return;
    this.body.setVelocity(0, 0);
    this.think(ctx);
    const facing = this.role === 'turret' ? (LAB.TURRET_DIR.x < 0 ? 'left' : 'right') : 'down';
    this.visual.loop('idle', facing, ctx.time);
    this.label.setPosition(this.x, this.y - LAB.DUMMY_SIZE[1]).setDepth(this.depth + 1);
    this.label.setText(
      this.role === 'target'
        ? `허수아비 · 누적 ${this.totalDamage} (${this.hits}타)`
        : `사수 허수아비 · ${this.shots}발`,
    );
  }

  protected think(ctx: MobContext): void {
    if (this.role !== 'turret' || this.isStunned(ctx.time)) return;
    if (ctx.time < this.nextShotAt) return;
    this.nextShotAt = ctx.time + LAB.TURRET_INTERVAL_MS;
    const d = LAB.TURRET_DIR;
    const len = Math.hypot(d.x, d.y) || 1;
    const c = this.body.center;
    ctx.fire(c.x + (d.x / len) * LAB.DUMMY_SIZE[0], c.y + (d.y / len) * LAB.DUMMY_SIZE[0], d.x / len, d.y / len, {
      ...LAB.TURRET_SHOT,
      sprite: ENEMY_FX.BULLET,
    });
    this.shots += 1;
    this.playAttack(ctx.time);
  }

  /** 무한 체력: 피해는 기록만 하고 죽지 않는다 (피격 이벤트·번쩍임은 그대로) */
  takeDamage(amount: number, info: DamageInfo = {}): boolean {
    if (!this.active) return false;
    this.totalDamage += amount;
    this.hits += 1;
    EventBus.emit(Events.ENEMY_DAMAGED, {
      id: this.spriteId,
      amount,
      crit: Boolean(info.crit),
      died: false,
      tick: Boolean(info.tick),
    } satisfies EnemyDamagedPayload);
    this.flash(COLORS.MOB_HURT);
    return false;
  }

  /** 넉백·밀쳐내기 무시 */
  shove(): void {}

  knockback(): void {}

  resetStats(): void {
    this.totalDamage = 0;
    this.hits = 0;
    this.shots = 0;
  }

  get isBoss(): boolean {
    return false;
  }

  get personalityValue(): number {
    return 0;
  }

  get goldValue(): number {
    return 0;
  }

  protected currentContactAttack(): number {
    return 0;
  }

  protected contactIntervalMs(): number {
    return Number.MAX_SAFE_INTEGER;
  }
}
