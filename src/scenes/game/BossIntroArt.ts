/**
 * 61라운드 E 보스 등장 동작 재생 (아트 2 `<보스>_intro`, 시간표 `systems/boss/introArt`). BossFlow 가 등장 연출 동안 매 프레임 부른다.
 * 보스를 주인공 반대쪽으로 '보폭 × 걸음 반복' 만큼 물려 세우고 걸음 열을 반복하며 제자리(시작 자리)까지 걸어 들어오게 한다 →
 * 딸꾹·건배 올림 → 건배 유지(대사 동안) → 포효(BOSS_ACTION introRoar — 음향·이름 카드 자리) → 대기로.
 * 걸어 들어올 길이 막혀 있으면 막히지 않는 데까지만 물린다. 등장 시트가 없으면 아무것도 하지 않는다(대기 그림).
 */
import { EventBus, Events, type BossActionPayload } from '../../core/EventBus';
import type { BossIntroShow } from '../../data/bossShowTypes';
import type { Boss } from '../../objects/Boss';
import { introArtPlan, type IntroArtPlan } from '../../systems/boss/introArt';
import { artScale, facingOf, type Facing } from '../../systems/sprites/spriteDefs';
import { BOSS_ART } from '../../core/Constants';
import type { Game } from '../Game';

type Stage = 'walk' | 'raise' | 'toast' | 'roar' | 'done';

/** 물림 거리를 줄여 가며 걸을 수 있는 자리를 찾을 때의 걸음 (월드 px) */
const BACKOFF_STEP_PX = 8;

export class BossIntroArt {
  private readonly plan: IntroArtPlan;
  private stage: Stage = 'walk';
  private readonly from: { x: number; y: number };
  /** 걸어 들어와 멈출 자리 (보스 생성 자리) — 카메라 초점 */
  readonly target: { x: number; y: number };
  private readonly dir: Facing;

  static create(g: Game, boss: Boss, show: BossIntroShow): BossIntroArt | null {
    const def = boss.visual.hasAction(BOSS_ART.INTRO_ACTION) ? boss.visual.sheet(BOSS_ART.INTRO_ACTION) : undefined;
    if (!def) return null;
    const plan = introArtPlan(def, { walkLoops: show.walkLoops, roarAtMs: show.roarAtMs, speechAtMs: show.speechAtMs });
    return plan ? new BossIntroArt(g, boss, plan, def.stride ? artScale(def) * boss.visual.drawScale : 0) : null;
  }

  private constructor(
    g: Game,
    private readonly boss: Boss,
    plan: IntroArtPlan,
    dotScale: number,
  ) {
    this.plan = plan;
    this.target = { x: boss.x, y: boss.y };
    const away = Math.sign(boss.x - g.player.x) || 1;
    this.dir = facingOf(-away, 0, 'down');
    let dist = plan.walkDots * dotScale;
    while (dist > 0 && !g.world.isWalkableAt(boss.x + away * dist, boss.y)) dist -= BACKOFF_STEP_PX;
    dist = Math.max(0, dist);
    this.from = { x: boss.x + away * dist, y: boss.y };
    this.place(this.from.x);
    if (plan.walkMs > 0) this.loop(plan.walkCols);
    else this.raise(0);
  }

  private place(x: number): void {
    const b = this.boss;
    if (!b.active) return;
    b.body.reset(x, this.target.y);
  }

  private loop(cols: number[]): void {
    const d = this.boss.visual.sheet(BOSS_ART.INTRO_ACTION)?.frameDurationsMs;
    const avg = cols.reduce((a, c) => a + (d?.[c] ?? 100), 0) / Math.max(1, cols.length);
    this.boss.visual.loopFrames(BOSS_ART.INTRO_ACTION, this.dir, cols, avg);
  }

  private raise(now: number): void {
    this.stage = 'raise';
    this.place(this.target.x);
    this.boss.visual.playFrames(BOSS_ART.INTRO_ACTION, this.dir, this.plan.raiseCols, now);
  }

  /** 등장 경과 ms (BossFlow 의 delta 누적) */
  update(elapsed: number, now: number): void {
    const p = this.plan;
    if (!this.boss.active || this.stage === 'done') return;
    switch (this.stage) {
      case 'walk': {
        const t = p.walkMs > 0 ? Math.min(1, elapsed / p.walkMs) : 1;
        this.place(this.from.x + (this.target.x - this.from.x) * t);
        if (t >= 1) this.raise(now);
        break;
      }
      case 'raise':
        if (elapsed >= p.walkMs + p.raiseMs) {
          this.stage = 'toast';
          this.loop(p.toastCols);
        }
        break;
      case 'toast':
        if (elapsed >= p.roarAtMs) {
          this.stage = 'roar';
          this.boss.visual.playFrames(BOSS_ART.INTRO_ACTION, this.dir, p.roarCols, now);
          EventBus.emit(Events.BOSS_ACTION, {
            id: this.boss.id,
            action: 'introRoar',
          } satisfies BossActionPayload);
        }
        break;
      case 'roar':
        if (elapsed >= p.roarAtMs + p.roarMs) this.finish();
        break;
    }
  }

  /** 끝 (또는 전투 시작): 제자리 · 대기 그림으로 */
  finish(): void {
    if (this.stage === 'done') return;
    this.stage = 'done';
    this.place(this.target.x);
    this.boss.visual.release();
  }

  summary(): Record<string, unknown> {
    return { stage: this.stage, from: this.from, target: this.target, plan: this.plan };
  }
}
