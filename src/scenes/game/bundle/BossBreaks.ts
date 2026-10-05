/**
 * 60라운드 (h) 약점 파훼 보너스 — 1층 보스 '만취' 두 겹 (data/bundle2.json break):
 * ① 서로 다른 파훼 n종 (잔 = BOSS_ACTION cupBreak · 기둥 = BOSS_WALL_HIT · 술통 = BOSS_ACTION caskRedirect · 취권 = BOSS_ACTION fall)
 *    → n ≥ senseAt 감각 +1 (능력치 포인트 +1 — 보스 보상 때 쓴다), n ≥ passiveAt 보스 패시브 희귀 이상 보장.
 * ② 결정타 — 파훼 경직 중 마지막 일격(보스가 경직 중 / 파훼 경직 창 안에서 죽음) → 전표 +50 · 개성 +30.
 * 보스 노드에서만. 사건은 BOSS_BREAK (`BossBreakPayload` — 결정타는 kind 'finisher').
 */
import type Phaser from 'phaser';
import { BUNDLE_FX } from '../../../core/Constants';
import { EventBus, Events, type BossActionPayload, type BossBreakPayload } from '../../../core/EventBus';
import { gameState } from '../../../core/GameState';
import { BUNDLE2 } from '../../../data/bundle2';
import type { BreakKind } from '../../../data/bundle2Types';
import type { Boss } from '../../../objects/Boss';
import type { Mob } from '../../../objects/Mob';
import { BreakTracker } from '../../../systems/bundle2/shopStock';
import type { Game } from '../../Game';

const ACTION_KIND: Partial<Record<BossActionPayload['action'], BreakKind>> = {
  cupBreak: 'cup',
  caskRedirect: 'cask',
  fall: 'reel',
};

/** 파훼별 경직 길이를 읽을 보스 패턴 파라미터 */
const STUN_PARAM: Record<BreakKind, [pattern: string, key: string] | null> = {
  cup: ['drink', 'breakStunMs'],
  pillar: ['drunkDash', 'wallStunMs'],
  reel: ['drunkDash', 'fallMs'],
  cask: null,
};

export class BossBreaks {
  private readonly tracker = new BreakTracker();
  private readonly active: boolean;
  private senseGiven = false;
  private passiveGuaranteed = false;

  constructor(private readonly g: Game) {
    this.active = g.nodeKind === 'boss' || !g.routeMode;
    if (!this.active) return;
    EventBus.on(Events.BOSS_ACTION, this.onAction, this);
    EventBus.on(Events.BOSS_WALL_HIT, this.onWallHit, this);
  }

  private boss(): Boss | null {
    for (const m of this.g.mobs.getChildren() as Mob[]) if (m.active && m.isBoss) return m as Boss;
    return null;
  }

  private stunMs(kind: BreakKind): number {
    const p = STUN_PARAM[kind];
    const b = this.boss();
    if (p && b) {
      try {
        const v = (b.params as (n: string) => Record<string, unknown>)(p[0])?.[p[1]];
        if (typeof v === 'number') return v;
      } catch {
        // 그 패턴이 없는 보스 — 기본 창
      }
    }
    return BUNDLE_FX.BREAK_FALLBACK_STUN_MS;
  }

  private onAction(p: BossActionPayload): void {
    const kind = ACTION_KIND[p.action];
    if (kind) this.record(kind);
  }

  private onWallHit(): void {
    this.record('pillar');
  }

  private record(kind: BreakKind): void {
    const B = BUNDLE2.break;
    if (!B.kinds.includes(kind)) return;
    const r = this.tracker.record(kind, this.g.time.now, this.stunMs(kind));
    EventBus.emit(Events.BOSS_BREAK, { kind, distinct: r.distinct, count: r.count } satisfies BossBreakPayload);
    if (!r.distinct) return;
    if (r.count >= B.senseAt && !this.senseGiven) {
      this.senseGiven = true;
      gameState.senses.sense += B.senseValue;
      gameState.pointsPending += B.senseValue;
    }
    if (r.count >= B.passiveAt) this.passiveGuaranteed = true;
  }

  /** 보스 처치 (Progression.onKill — 보스): 결정타 판정 */
  onBossKilled(mob: Mob): void {
    if (!this.active || this.tracker.count === 0) return;
    const now = this.g.time.now;
    if (!mob.isStunned(now) && !this.tracker.inBreak(now)) return;
    const F = BUNDLE2.break.finisher;
    this.g.economy.addGold(F.gold);
    this.g.progress.gainGrowth(F.personality);
    const text = BUNDLE2.break.text.finisher;
    // 61 E 버그 수정: 처치된 보스는 이미 파괴돼 바디가 없다 (결정타마다 TypeError — 헤드리스에서 발견) → 발 자리
    const body = mob.body as Phaser.Physics.Arcade.Body | null | undefined;
    const top = body ? body.top : mob.y;
    this.g.feedback.worldText(mob.x, top, typeof text === 'string' ? text : BUNDLE_FX.FINISHER_TEXT);
    EventBus.emit(Events.BOSS_BREAK, {
      kind: 'finisher',
      distinct: false,
      count: this.tracker.count,
    } satisfies BossBreakPayload);
  }

  /** 보스 보상 패시브 희귀도 (파훼 n ≥ passiveAt 이면 희귀 이상) */
  bossRarities(): readonly string[] | undefined {
    return this.passiveGuaranteed ? BUNDLE2.break.passiveRarities : undefined;
  }

  debug(): Record<string, unknown> {
    return {
      kinds: this.tracker.list(),
      sense: this.senseGiven,
      passive: this.passiveGuaranteed,
      inBreak: this.tracker.inBreak(this.g.time.now),
    };
  }

  destroy(): void {
    EventBus.off(Events.BOSS_ACTION, this.onAction, this);
    EventBus.off(Events.BOSS_WALL_HIT, this.onWallHit, this);
  }
}
