/**
 * 54라운드 Q6 '한 잔 더' (+ Q1 페이즈 전환 들이켜기 phaseDrink).
 * 큰 잔 들기(liftMs, 예고) → 들이켜기(gulpMs, 잔 = 약점) → 다 마심(finishMs).
 * - 들이켜는 동안 잔을 한 번이라도 맞히면: 잔이 깨지고 술을 뒤집어써 breakStunMs 경직, 이어질 화면 패턴 취소
 * - 다 마시면: 얼큰(empowerNext) = 다음 패턴 강화, 만취·인사불성 = triggers 중 쿨타임이 끝난 화면 패턴 발동
 */
import { COLORS } from '../../../core/Constants';
import type { BossPatternName } from '../../../data/bossPatterns';
import type { MobContext } from '../../Mob';
import type { BossArenaApi, BossHost, BossPatternModule, PatternEnd, PatternRun } from '../types';

export interface DrinkParams {
  liftMs: number;
  gulpMs: number;
  finishMs: number;
  breakStunMs: number;
  cooldownMs: number;
  /** 잔 시트 앵커가 없을 때 임시 약점 사각형 (월드 px): 폭·높이·발에서 위로 */
  cupW: number;
  cupH: number;
  cupLiftPx: number;
  /** 61 E: 깨지기까지 맞혀야 하는 수 (기본 1 — 그 전 맞음은 struck 표시) */
  cupHits?: number;
  empowerNext?: boolean;
  triggers?: BossPatternName[];
}

/** 다 마신 뒤 발동할 화면 패턴: 쿨타임이 끝난 후보 중 시드 RNG. 없으면 undefined */
export function drinkTrigger(
  host: BossHost,
  ctx: MobContext,
  triggers: readonly BossPatternName[],
): BossPatternName | undefined {
  const ready = triggers.filter((t) => ctx.time >= host.readyAt(t));
  return ready.length > 0 ? host.rng.pick(ready) : undefined;
}

class DrinkRun implements PatternRun {
  state: 'drinkLift' | 'drinkGulp' | 'drinkFinish' = 'drinkLift';
  private until: number;
  private broken = false;
  private readonly arena: BossArenaApi | null;

  constructor(
    private readonly host: BossHost,
    ctx: MobContext,
  ) {
    const P = this.P;
    this.arena = ctx.arena ?? null;
    this.until = ctx.time + P.liftMs;
    host.setVelocity(0, 0);
    if (!host.pose.phase('drink', 'lift', ctx.time, { fitMs: P.liftMs, target: ctx.player })) host.pose.lean(-0.12);
    host.paint(COLORS.BOSS_DRINK);
    host.emitTelegraph('drink');
    host.emitAction('drinkLift');
  }

  private get P(): DrinkParams {
    return this.host.params<DrinkParams>('drink');
  }

  update(ctx: MobContext): PatternEnd | null {
    const h = this.host;
    const P = this.P;
    h.setVelocity(0, 0);
    if (this.broken) {
      // 잔이 깨짐: 보스 경직으로 끝 (화면 패턴 없음)
      this.cleanup();
      h.markBroken(P.breakStunMs);
      h.emitAction('cupBreak');
      return {
        finish: true,
        stunMs: P.breakStunMs,
        stunPose: { action: 'drink_break', phase: 'break', thenLoop: 'stagger' },
      };
    }
    if (ctx.time < this.until) return null;
    switch (this.state) {
      case 'drinkLift':
        this.state = 'drinkGulp';
        this.until = ctx.time + P.gulpMs;
        if (!h.pose.phase('drink', 'gulp', ctx.time, { loop: true })) h.pose.lean(-0.22);
        h.emitLoop('gulp', true);
        this.arena?.setWeakPoint({
          rect: () => h.pose.cupRect({ w: P.cupW, h: P.cupH, lift: P.cupLiftPx }),
          drawCup: !h.pose.cupArt,
          hits: P.cupHits,
          visible: () => h.pose.cupVisible(),
          onHit: () => {
            if (this.state === 'drinkGulp') this.broken = true;
          },
        });
        return null;
      case 'drinkGulp':
        this.state = 'drinkFinish';
        this.until = ctx.time + P.finishMs;
        this.arena?.setWeakPoint(null);
        h.emitLoop('gulp', false);
        h.emitAction('drinkFinish');
        if (!h.pose.phase('drink', 'finish', ctx.time, { fitMs: P.finishMs })) h.pose.lean(0.1);
        return null;
      case 'drinkFinish': {
        this.cleanup();
        h.pose.release();
        h.restoreColor();
        if (P.empowerNext) return { finish: true, empower: true };
        const next = drinkTrigger(h, ctx, P.triggers ?? []);
        return { finish: true, next };
      }
    }
  }

  private cleanup(): void {
    this.arena?.setWeakPoint(null);
    if (this.state === 'drinkGulp') this.host.emitLoop('gulp', false);
    this.host.pose.lean(0);
  }

  cancel(): void {
    this.cleanup();
  }
}

export const drinkPattern: BossPatternModule = {
  name: 'drink',
  start: (host, ctx) => new DrinkRun(host, ctx),
};

/**
 * 페이즈 전환 들이켜기 (Q1): 멈춰 들이켬, invulnerable 이면 그동안 피해 무시.
 * 61라운드 P6: 끝나면 `next` (인사불성 = 등불 끄기 확정 — 국면 진입 때 한 번)
 */
class PhaseDrinkRun implements PatternRun {
  readonly state = 'phaseDrink';
  private readonly until: number;
  private readonly next: BossPatternName | undefined;

  constructor(
    private readonly host: BossHost,
    ctx: MobContext,
  ) {
    const P = host.params<{ durationMs: number; invulnerable?: boolean; next?: BossPatternName }>('phaseDrink');
    this.until = ctx.time + P.durationMs;
    this.next = P.next;
    host.setVelocity(0, 0);
    if (P.invulnerable) host.setInvulnerable(this.until);
    // 아트 v3 phase_drink 한 번(전환 길이에 맞춤) → 없으면 drink 들이켜기 루프
    const ok =
      host.pose.play('phase_drink', ctx.time, { fitMs: P.durationMs, target: ctx.player }) ||
      host.pose.phase('drink', 'gulp', ctx.time, { loop: true });
    if (!ok) host.pose.lean(-0.22);
    host.paint(COLORS.BOSS_DRINK);
    host.emitAction('phaseDrink');
  }

  update(ctx: MobContext): PatternEnd | null {
    this.host.setVelocity(0, 0);
    if (ctx.time < this.until) return null;
    this.cancel();
    return { finish: true, next: this.next };
  }

  cancel(): void {
    this.host.setInvulnerable(0);
    this.host.pose.lean(0);
    this.host.pose.release();
    this.host.restoreColor();
  }
}

export const phaseDrinkPattern: BossPatternModule = {
  name: 'phaseDrink',
  start: (host, ctx) => new PhaseDrinkRun(host, ctx),
};

/**
 * 세상이 돈다 (Q7): 카메라 기울기 시작 → 곧바로 next. 방이 없으면(시험장 등) 효과만 생략.
 * 61라운드 P6: 국면 전환 연출로만 쓴다 (국면 enterPattern = spin → phaseDrink). 설정 tilt 0 이면 기울기만 빠진다
 */
export const spinPattern: BossPatternModule = {
  name: 'spin',
  start(host, ctx) {
    const P = host.params<{
      durationMs: number;
      tiltDeg: number;
      periodMs: number;
      rampMs: number;
      blur?: number;
      next?: BossPatternName;
    }>('spin');
    ctx.arena?.startTilt(P);
    host.emitAttack('spin');
    return { finish: true, next: P.next };
  },
};
