/**
 * 플레이어 피격 (56라운드 6-1 — Player.ts 에서 분리): 패링 · 56라운드 Q7 퍼펙트 가드(피해 0·튕겨내지 않음·문구) · 가드 감소(울분) ·
 * 슈퍼아머 · 무적 · 넉백 · 사망. 판정 규칙은 `systems/defense`(Phaser 의존 없음).
 */
import { COLORS, FEEL } from '../../core/Constants';
import {
  EventBus,
  Events,
  type PerfectGuardPayload,
  type PlayerDamagedPayload,
  type PlayerSecondaryPayload,
} from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import { PLAYER_DATA } from '../../data';
import { applyDefense } from '../../systems/Combat';
import { resolveDefense } from '../../systems/defense';
import { knockSpeed } from '../../systems/feel';
import type { HitResult, Player } from '../Player';

export class PlayerDefense {
  /** 가드를 누른 시각 (퍼펙트 가드 창) */
  guardStartedAt = -Infinity;
  /** 디버그: 마지막 방어 결과 */
  lastOutcome: string | null = null;
  /** 56라운드: 구간 무적 (일섬 돌진 — 플레이어 시계 `ownNow` 기준, 그 구간 밖은 평소대로) */
  private windows: { from: number; to: number }[] = [];

  constructor(private readonly p: Player) {}

  /** 지금부터 fromMs ~ toMs 동안 무적 (플레이어 시계 — 히트스톱이 끼어도 돌진 구간과 맞는다) */
  addInvulnWindow(fromMs: number, toMs: number): void {
    const t0 = this.p.ownNow;
    this.windows = this.windows.filter((w) => w.to > t0);
    this.windows.push({ from: t0 + fromMs, to: t0 + toMs });
  }

  /** 지금 구간 무적인가 */
  get inWindow(): boolean {
    const t = this.p.ownNow;
    return this.windows.some((w) => t >= w.from && t < w.to);
  }

  clearWindows(): void {
    this.windows = [];
  }

  /**
   * 적의 공격을 받는다. 패링 창이면 'parried'(피해 0), 퍼펙트 가드면 'ignored'(피해 0, 튕겨내지 않음), 무적이면 'ignored'.
   * 가드 중이면 피해 감소(줄인 만큼 울분), 공격 중 슈퍼아머(거인)면 추가 감소. 사망하면 'dead'.
   * `source` 는 가해자 → 플레이어 방향 단위벡터(넉백 방향). 없으면 넉백 없음
   */
  takeHit(attack: number, time: number, source?: { dirX: number; dirY: number }): HitResult {
    const p = this.p;
    if (gameState.gameOver) return 'ignored';
    const S = p.secondary;
    const mods = gameState.weapon.mods;
    const res = p.resource;
    const guarding = p.action === 'guard' && S.kind === 'guard';
    const outcome = resolveDefense({
      action: p.action === 'parry' ? 'parry' : guarding ? 'guard' : 'other',
      guardStartedAt: this.guardStartedAt,
      now: time,
      perfectWindowMs: PLAYER_DATA.perfectGuard?.windowMs ?? 0,
      perfectKind: S.kind === 'guard' ? (S.perfect ?? 'guard') : 'guard',
      guardReduction: S.kind === 'guard' ? (mods.guardReduction ?? S.damageReduction) : 0,
      damage: applyDefense(attack, gameState.defense),
      groggy: Boolean(res?.isGroggy),
    });
    this.lastOutcome = outcome.kind;
    if (outcome.kind === 'parried') {
      // 성공: 창을 닫고 즉시 행동 가능 · 56라운드 Q14 검기 1단 즉시 · Q58 우클릭을 계속 쥐고 있으면 가드로 복귀(창은 다시 열지 않음)
      if (!(p.secondaryHeldNow && S.kind === 'guard')) p.setAction('normal', 0);
      // 2단계 Q40: 간파 반격 창 시작
      p.moves.parriedAt = time;
      p.flashColor(COLORS.PLAYER_PARRY);
      p.poses.playSpecial(time, 'parrySuccess');
      p.gauges.onParried();
      EventBus.emit(Events.PLAYER_PARRIED, { attack, ...toward(source) });
      return 'parried';
    }
    if (p.isInvulnerableAt(time) || this.inWindow) return 'ignored';
    if (outcome.kind === 'perfect') {
      // 56라운드 Q7: 피해 완전 무시, 튕겨내지 않음 (가드 유지) — 무적 시간도 주지 않는다(다음 타는 다시 판정)
      p.gauges.onGuardBlock(outcome.blocked, 'perfect');
      // 2단계 Q41: 막다가 떼면 돌진 창 시작
      p.moves.perfectGuardAt = time;
      p.flashColor(COLORS.PLAYER_PARRY);
      const payload: PerfectGuardPayload = { x: p.x, y: p.y, attack, ...toward(source) };
      EventBus.emit(Events.PLAYER_PERFECT_GUARD, payload);
      EventBus.emit(Events.PLAYER_SECONDARY, { kind: 'guard', phase: 'block' } satisfies PlayerSecondaryPayload);
      return 'ignored';
    }
    p.grantInvulnerable(time + PLAYER_DATA.invulnerableMs);
    let amount = outcome.amount;
    if (outcome.kind === 'guarded') {
      p.gauges.onGuardBlock(outcome.blocked, outcome.groggy ? 'groggy' : 'normal');
      EventBus.emit(Events.PLAYER_SECONDARY, { kind: 'guard', phase: 'block' } satisfies PlayerSecondaryPayload);
    }
    if (mods.superArmorReduction && p.inAttackSlow(time)) amount = Math.round(amount * (1 - mods.superArmorReduction));
    gameState.hp = Math.max(0, gameState.hp - amount);
    p.flashColor(COLORS.PLAYER_HURT);
    // 56라운드 2단계 Q54·Q61 버티기 올려베기 슈퍼아머: 피해는 그대로, 끊기지 않음(넉백·피격 자세 없음), 맞은 피해는 울분으로
    const armored = p.moves.superArmor;
    if (armored) p.gauges.onGuardBlock(amount, 'normal');
    else {
      // 55라운드 Q23: 피격 → 대검 관성 초기화·차지 취소 · 2단계 유지형(대치 일격·난타) 끊김
      p.melee.onHurt();
      p.moves.onHurt();
    }
    if (!armored && source && p.action !== 'dash' && (source.dirX !== 0 || source.dirY !== 0)) {
      const K = FEEL.KNOCKBACK;
      const speed = knockSpeed(K.PLAYER_PX, K.PLAYER_MS);
      const len = Math.hypot(source.dirX, source.dirY) || 1;
      if (speed > 0) p.shove((source.dirX / len) * speed, (source.dirY / len) * speed, K.PLAYER_MS);
    }
    const payload: PlayerDamagedPayload = {
      hp: gameState.hp,
      maxHp: gameState.maxHp,
      amount,
      source,
      ...(armored ? { armored: true } : {}),
    };
    EventBus.emit(Events.PLAYER_DAMAGED, payload);
    if (gameState.hp <= 0) {
      gameState.gameOver = true;
      p.setAction('normal', 0);
      p.deathAnimMs = p.visual.oneShot('death', p.visual.facing, time);
      EventBus.emit(Events.PLAYER_DIED);
      return 'dead';
    }
    if (!armored) p.visual.oneShot('hurt', p.visual.facing, time);
    return 'hit';
  }
}

/** 주인공 → 공격자 방향 (가드·패링 fx 회전). source 는 가해자 → 주인공 */
function toward(source?: { dirX: number; dirY: number }): { dirX?: number; dirY?: number } {
  if (!source) return {};
  const len = Math.hypot(source.dirX, source.dirY);
  return len > 0 ? { dirX: -source.dirX / len, dirY: -source.dirY / len } : {};
}
