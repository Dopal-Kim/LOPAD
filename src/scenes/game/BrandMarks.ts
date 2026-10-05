/**
 * 56라운드 Q16·Q18 단검 낙인(烙印): 같은 적을 칠 때마다 표식(등 뒤 2, 최대 5, 과열 단계면 더 빨리) → 그림자 걸음으로 그 적 뒤에 서면
 * 전부 폭발 · 과열 100% → 주변 낙인 일괄 폭발. 표식 = fx `dagger_brand_mark`(행 = 스택 1~5, 적 머리 위, 찍힘 0~1 → 2~5 반복),
 * 폭발 = `dagger_brand_burst`(행 s·m·l = 스택), 과열 = `dagger_overheat_burst`(주인공 발) 뒤 가까운 적부터 40ms 간격.
 * 시트가 없으면 작은 호박 마름모(Graphics)·플레이스홀더.
 * 장부 규칙은 `systems/weapon/weaponGauge.BrandBook`(Phaser 의존 없음).
 */
import Phaser from 'phaser';
import { DEPTH, FEEDBACK, TILE } from '../../core/Constants';
import type { FxHandle } from '../../systems/fx/fx';
import { crackShake, type ShakeHint } from './swingShake';
import { EventBus, Events, type PlayerSkillPayload, type WeaponGaugePayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import type { BrandGaugeDef } from '../../data/types';
import type { UiWeaponGauge } from '../../contract/ui';
import type { Mob } from '../../objects/Mob';
import { BrandBook, isBackHit } from '../../systems/weapon/weaponGauge';
import type { Game } from '../Game';

/** 4방향 → 단위벡터 (적이 바라보는 쪽) */
function facingVec(f: string): { x: number; y: number } {
  return f === 'right'
    ? { x: 1, y: 0 }
    : f === 'left'
      ? { x: -1, y: 0 }
      : f === 'up'
        ? { x: 0, y: -1 }
        : { x: 0, y: 1 };
}

export class BrandMarks {
  private book: BrandBook<Mob> | null = null;
  private bookWeapon = '';
  private readonly gfx: Phaser.GameObjects.Graphics;
  /** 디버그: 마지막 폭발 */
  lastBurst: { marks: number; dmg: number; time: number; cause: string; fx: boolean } | null = null;
  /** 적마다 표식 fx (보이는 스택) */
  private readonly markFx = new Map<Mob, { handle: FxHandle | null; marks: number }>();

  constructor(private readonly g: Game) {
    this.gfx = g.add.graphics().setDepth(DEPTH.DAMAGE_TEXT - 0.2);
  }

  private get def(): BrandGaugeDef | null {
    const gd = gameState.weapon.def.gauge;
    return gd?.kind === 'brand' ? gd : null;
  }

  /** 낙인 최대 (57라운드 표식 세트 2: 5 → 7) */
  get maxMarks(): number {
    const d = this.def;
    return d ? d.max + (this.g.build?.brandMaxAdd() ?? 0) : 0;
  }

  /** 이 적의 낙인 수 (단검이 아니면 0) */
  marksOf(mob: Mob): number {
    return this.ledger?.marks(mob) ?? 0;
  }

  /** 현재 무기의 장부 (단검이 아니면 null — 무기·낙인 최대가 바뀌면 새로) */
  private get ledger(): BrandBook<Mob> | null {
    const d = this.def;
    const key = `${gameState.weapon.id}|${this.maxMarks}`;
    if (this.bookWeapon !== key) {
      this.bookWeapon = key;
      this.book = d ? new BrandBook<Mob>({ ...d, max: this.maxMarks }) : null;
    }
    return this.book;
  }

  /** 근접 적중 (살아 있는 적만): 표식 추가 */
  onHit(mob: Mob, dirX: number, dirY: number): void {
    const book = this.ledger;
    const d = this.def;
    if (!book || !d || !mob.active) return;
    // 56라운드 Q59: 그림자 걸음 착지 뒤 backAfterShadowStepMs 동안은 늘 등 뒤, 그 밖은 적이 바라보는 방향의 등 쪽
    const now = this.g.time.now;
    const afterStep = now - this.g.player.moves.shadowLandedAt <= (d.backAfterShadowStepMs ?? 0);
    const back = afterStep || isBackHit(facingVec(mob.visual.facing), { x: dirX, y: dirY }, d.backAngleDeg);
    const res = this.g.player.resource;
    const heatStage = res?.kind === 'heat' ? res.stage : 0;
    const r = book.add(mob, now, { back, heatStage });
    if (r.after === r.before) return;
    const payload: WeaponGaugePayload = {
      weapon: gameState.weapon.id,
      gauge: 'brand',
      event: 'apply',
      delta: r.after - r.before,
      marks: r.after,
      back,
    };
    EventBus.emit(Events.WEAPON_GAUGE, payload);
  }

  /** 그림자 걸음으로 이 적 뒤에 섬 → 표식 전부 폭발 */
  onShadowStep(target: Mob | null): void {
    if (target) this.burst(target, 'shadowstep');
  }

  /** 과열 100% → 반경 안 낙인 일괄 폭발 */
  onOverheat(): void {
    const book = this.ledger;
    const d = this.def;
    if (!book || !d) return;
    const p = this.g.player;
    // 60라운드 열풍(단검 2단): 과열 폭발 범위 ×burstRangeMult · 반경 안 화상 · 무적
    const r = d.overheatBurstRadiusTiles * TILE * (this.g.build?.branch.overheatRangeMult() ?? 1);
    const dist = (m: Mob) => Math.hypot(m.x - p.x, m.y - p.y);
    const list = book.takeWhere((m) => m.active && dist(m) <= r).sort((a, b) => dist(a[0]) - dist(b[0]));
    const skill: PlayerSkillPayload = { weapon: gameState.weapon.id, move: 'overheat', phase: 'burst' };
    EventBus.emit(Events.PLAYER_SKILL, skill);
    // 전용 fx (주인공 발) — 낙인 적 폭발은 그 시트 열 1 시작부터 가까운 순서로 간격을 두고 (아트 spawnNote)
    const g = this.g;
    const O = FEEDBACK.OVERHEAT;
    let lead = 0;
    if (g.fx.has(O.SHEET)) {
      g.fx.play(O.SHEET, p.x, p.y, { depth: DEPTH.FX_GROUND });
      lead = g.fx.sheet(O.SHEET)?.frameDurationsMs?.[0] ?? 0;
    }
    list.forEach(([mob, marks], i) => {
      this.clearMark(mob);
      const at = lead + i * O.CHAIN_MS;
      if (at <= 0) this.explode(mob, marks, 'overheat');
      else g.time.delayedCall(at, () => this.explode(mob, marks, 'overheat'));
    });
    g.build?.branch.onOverheat(r);
  }

  private burst(mob: Mob, cause: string): void {
    const book = this.ledger;
    if (!book || !mob.active) return;
    const marks = book.take(mob);
    this.clearMark(mob);
    if (marks <= 0) return;
    const skill: PlayerSkillPayload = { weapon: gameState.weapon.id, move: 'brand', phase: 'burst' };
    EventBus.emit(Events.PLAYER_SKILL, skill);
    this.explode(mob, marks, cause);
  }

  private explode(mob: Mob, marks: number, cause: string): void {
    const g = this.g;
    const d = this.def;
    if (!d || !mob.active) return;
    // 57라운드 빌드 축: 쌍격 +30%·표식 6 +40% · 출혈(2단) = 즉시 비율만 (나머지는 출혈)
    const br = g.build.branch;
    const { dmg, crit } = g.combat.rollDamage(
      marks * d.burstDamagePerMark * br.brandBurstMult() * br.brandImmediateRatio(),
      false,
      'other',
      mob,
    );
    const p = g.player;
    const dx = mob.x - p.x;
    const dy = mob.y - p.y;
    const len = Math.hypot(dx, dy) || 1;
    // 폭발 fx (행 = 스택 크기 s·m·l, 적 몸 중심) — 흔들림 = 시트 shakeHint
    const B = FEEDBACK.BRAND;
    const row = marks >= 5 ? 'l' : marks >= 3 ? 'm' : 's';
    const cy = mob.body.center.y - mob.visual.hitLiftPx;
    const fx = g.fx.has(B.BURST_SHEET)
      ? g.fx.play(B.BURST_SHEET, mob.body.center.x, cy, { dir: row, depth: DEPTH.HIT_FX }) !== null
      : false;
    const sh = crackShake((g.fx.sheet(B.BURST_SHEET) as { shakeHint?: ShakeHint } | null)?.shakeHint, row);
    if (fx && sh) g.shake.add(g.time.now, sh.px, sh.ms);
    this.lastBurst = { marks, dmg, time: g.time.now, cause, fx };
    const died = g.combat.hitMob(mob, dmg, { crit, dirX: dx / len, dirY: dy / len, heavy: true, knock: false });
    br.onBrandBurst(mob, marks, dmg, died);
    if (died) g.progress.onKill(mob, 'attack');
  }

  /** 적 머리 위 표식 fx 를 스택에 맞춘다 (스택이 오르면 그 행의 찍힘부터, 시트가 없으면 false) */
  private syncMark(mob: Mob, marks: number): boolean {
    const g = this.g;
    const B = FEEDBACK.BRAND;
    if (!g.fx.has(B.MARK_SHEET)) return false;
    const cur = this.markFx.get(mob);
    if (cur && cur.marks === marks && g.fx.isActive(cur.handle)) return true;
    if (cur) g.fx.stop(cur.handle, 0, false);
    const top = mob.getTopCenter().y ?? mob.y;
    const handle = g.fx.play(B.MARK_SHEET, mob.x, mob.y, {
      dir: String(marks),
      follow: mob,
      followOffset: { x: 0, y: top - mob.y - B.HEAD_GAP_PX },
      depthOffset: DEPTH.OVERLAY_STEP * 4,
      loopFrom: B.MARK_LOOP_FROM,
      hooks: false,
    });
    this.markFx.set(mob, { handle, marks });
    return true;
  }

  private clearMark(mob: Mob): void {
    const cur = this.markFx.get(mob);
    if (!cur) return;
    this.g.fx.stop(cur.handle, 0, false);
    this.markFx.delete(mob);
  }

  /** 매 프레임: 오래된 표식 정리 · 표식 그리기 */
  update(time: number): void {
    const book = this.ledger;
    this.gfx.clear();
    if (!book) return;
    book.expire(time, (m) => m.active);
    const B = FEEDBACK.BRAND;
    const listed = new Set<Mob>();
    for (const [mob, marks] of book.list()) {
      listed.add(mob);
      if (this.syncMark(mob, marks)) continue;
      const top = mob.body.top - B.OFFSET_Y - mob.visual.hitLiftPx * 2;
      const x0 = mob.x - ((marks - 1) * B.GAP_PX) / 2;
      for (let i = 0; i < marks; i++) {
        const x = x0 + i * B.GAP_PX;
        diamond(this.gfx, x, top, B.SIZE_PX + 1, B.EDGE);
        diamond(this.gfx, x, top, B.SIZE_PX, B.COLOR);
      }
    }
    // 표식이 사라진(시간·사망) 적의 fx 정리
    for (const mob of [...this.markFx.keys()]) if (!listed.has(mob)) this.clearMark(mob);
  }

  /** 계약 §13 `UiSnapshot.gauge` (단검): 값 = 지금 가장 많이 쌓인 적의 표식 수 0~max. 단검이 아니면 null */
  toUi(): UiWeaponGauge | null {
    const book = this.ledger;
    const d = this.def;
    if (!book || !d) return null;
    let top = 0;
    for (const [, n] of book.list()) top = Math.max(top, n);
    return { kind: 'brand', label: d.label, value: top, max: d.max };
  }

  /** 디버그 */
  summary(): { weapon: string; marks: { id: string; x: number; y: number; marks: number }[]; lastBurst: unknown } {
    const list = this.ledger?.list() ?? [];
    return {
      weapon: this.bookWeapon,
      marks: list.map(([m, n]) => ({ id: m.spriteId, x: Math.round(m.x), y: Math.round(m.y), marks: n })),
      lastBurst: this.lastBurst,
    };
  }

  destroy(): void {
    this.book?.clear();
    this.markFx.clear();
    this.gfx.destroy();
  }
}

/** 마름모 (삼각형 둘 — 프레임당 할당 없음) */
function diamond(gfx: Phaser.GameObjects.Graphics, x: number, y: number, r: number, color: number): void {
  gfx.fillStyle(color, 1);
  gfx.fillTriangle(x, y - r, x + r, y, x - r, y);
  gfx.fillTriangle(x - r, y, x + r, y, x, y + r);
}
