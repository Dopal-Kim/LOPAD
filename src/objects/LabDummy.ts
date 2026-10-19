/**
 * 49라운드 계약 §11.4 무기 시험장 허수아비 (적 v3 시트 dummy·archer 로 그림 + 누적 피해 표시, 시트가 없으면 단색 사각형).
 * target = 중앙 허수아비(무한 체력, 맞으면 데미지 숫자 — Game.hitMob 공통 경로), turret = 일정 방향으로 투사체를 쏘는 허수아비.
 * 움직이지 않고(넉백·밀쳐내기 무시) 접촉 피해도 없다. 개성·골드를 주지 않는다.
 */
import Phaser from 'phaser';
import { goreHooksOf } from '../systems/gore/goreHooks';
import { ENEMY_FX, FEEDBACK, LAB, COLORS } from '../core/Constants';
import { EventBus, Events, type EnemyDamagedPayload } from '../core/EventBus';
import { Mob, type DamageInfo, type MobContext } from './Mob';

export type LabDummyRole = 'target' | 'turret';

/** 사실상 무한 체력 (표시용 최대치) */
const LAB_HP = 1_000_000;

/** 팻말 위치 계산용 (매 프레임 할당 방지) */
const boundsScratch = new Phaser.Geom.Rectangle();

/** 62 D (P1-17) 팻말 이름 (자리표시 — 수련장 문장 팩이 생기면 데이터로) */
const SIGN_TITLE: Record<LabDummyRole, string> = { target: '허수아비', turret: '사수 허수아비' };

export class LabDummy extends Mob {
  /** 누적 피해 · 맞은 횟수 · 쏜 탄 수 (디버그·표시) */
  totalDamage = 0;
  hits = 0;
  shots = 0;
  private nextShotAt = 0;

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
      role === 'target' ? LAB.DUMMY_SHEET : LAB.TURRET_SHEET,
      LAB.DUMMY_SIZE,
      role === 'target' ? LAB.DUMMY_COLOR : LAB.TURRET_COLOR,
      LAB_HP,
    );
    this.body.setImmovable(true);
  }

  /**
   * 62 D (P1-17): 옛 디버그 이름표 대신 UI 나무 팻말 정보 (계약 `UiWorldSign`) — 머리 위 끝 월드 좌표.
   * 시트가 있으면 그림 위, 없으면 사각형 위
   */
  sign(): { id: string; kind: 'dummy' | 'turret'; title: string; value: string; x: number; y: number } {
    const top = this.visual.animated ? this.getBounds(boundsScratch).top : this.y - LAB.DUMMY_SIZE[1];
    return {
      id: `${this.role}:${Math.round(this.x)},${Math.round(this.y)}`,
      kind: this.role === 'target' ? 'dummy' : 'turret',
      title: SIGN_TITLE[this.role],
      value: this.role === 'target' ? `누적 ${this.totalDamage} · ${this.hits}타` : `${this.shots}발`,
      x: this.x,
      y: top,
    };
  }

  /** 움직이지 않는다: AI 는 사수 발사만, 바라보는 방향은 사수면 발사 방향 */
  update(ctx: MobContext): void {
    if (!this.active) return;
    this.body.setVelocity(0, 0);
    this.think(ctx);
    const facing = this.role === 'turret' ? (LAB.TURRET_DIR.x < 0 ? 'left' : 'right') : 'down';
    this.visual.loop('idle', facing, ctx.time);
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
      weapon: info.weapon,
    } satisfies EnemyDamagedPayload);
    // P21: 시험장 허수아비도 피·튐은 보인다 (죽지 않으니 상처 단계·사망 변형은 없음)
    goreHooksOf(this.scene)?.onMobDamaged(this, {
      amount,
      hpBefore: this.hp,
      died: false,
      crit: Boolean(info.crit),
      tick: Boolean(info.tick),
      heavy: Boolean(info.heavy),
      dirX: info.dirX,
      dirY: info.dirY,
      weapon: info.weapon,
      cause: info.cause,
    });
    // 56라운드 Q36: 호박 반투명 80ms (히트스톱에 늘어나지 않음)
    this.visual.flashOverlay(COLORS.MOB_HURT, FEEDBACK.MOB_HURT.ALPHA, FEEDBACK.MOB_HURT.MS, FEEDBACK.MOB_HURT.ADD);
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
