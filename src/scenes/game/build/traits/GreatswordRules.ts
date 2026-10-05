/**
 * 61 G 대검 개성·셋째 갈래 '광전' 규칙: 날려 보내기 · 휘두르며 막기 · 되받는 벽 · 끌어당기기 · 어깨 너머 · 넘어뜨리기 · 버티며 모으기 ·
 * 빨아들이는 균열 · 띄워 올리기 / 광전(울분 가득 → 저절로 폭주: 연격이 끊기지 않고 빨라지며 울분이 빠져나감 — 적중·피격도 울분) ·
 * 혈풍(폭주 중 처치 → 연장) · 철산(폭주 끝 → 가장 깊은 내려찍기) · 포효 · 술기운 폭주. 그림이 없으면 윤곽·몸 깜빡임.
 */
import { BUILD_FX, TILE } from '../../../../core/Constants';
import { EventBus, Events, type PlayerAttackPayload, type PlayerSkillPayload } from '../../../../core/EventBus';
import type { Mob } from '../../../../objects/Mob';
import type { PerfectKind } from '../BuildPerfect';
import { T, type Pt, type RuleKit } from './RuleKit';

export class GreatswordRules {
  /** 폭주: 끝 시각 · 전체 길이(연장 포함) · 연장 합 · 지난 프레임에 둔 울분 값 */
  private rage: { until: number; total: number; extra: number; set: number } | null = null;
  private flashAt = -Infinity;
  private swingGuardAt = -Infinity;

  constructor(private readonly k: RuleKit) {
    EventBus.on(Events.PLAYER_DAMAGED, this.onHurt, this);
  }

  private get grudge() {
    return this.k.g.player?.gauges.grudge ?? null;
  }

  // --- 광전 (폭주) ---

  get raging(): boolean {
    return this.rage !== null;
  }

  private startRage(): void {
    const k = this.k;
    const r = k.rt.rule('rage');
    const gr = this.grudge;
    if (!r || !gr) return;
    const total = k.p(r, 'durationMs', 5000);
    this.rage = { until: k.now + total, total, extra: 0, set: gr.max };
    gr.value = gr.max;
    const pl = k.g.player;
    pl.flashColor(BUILD_FX.COLOR.RAGE);
    k.rt.fx.callout(BUILD_FX.TEXT.RAGE);
    k.fire('berserk', 'start');
    // 포효: 둘레 적이 겁먹고 밀려난다
    const roar = k.rt.rule('rageRoar');
    if (roar) {
      const rad = T(k.p(roar, 'radiusTiles', 3));
      k.rt.fx.ring(pl.x, pl.y, rad, BUILD_FX.COLOR.RAGE, 260);
      for (const m of k.rt.fx.inCircle(pl.x, pl.y, rad)) {
        k.push(m, { x: m.x - pl.x, y: m.y - pl.y }, k.p(roar, 'knockTiles', 1.5), 200);
        k.stun(m, k.p(roar, 'stunMs', 600));
      }
      k.fire('g_rageRoar', 'roar');
    }
  }

  private endRage(finale: boolean): void {
    const k = this.k;
    this.rage = null;
    k.fire('berserk', 'end');
    const fin = k.rt.rule('rageFinale');
    if (!fin || !finale || !k.g.scene.isActive()) return;
    // 철산: 폭주가 끝나는 순간 조준 방향으로 가장 깊은 내려찍기 (균열 + 찍은 자리 고리)
    const pl = k.g.player;
    const f = pl.facingVec;
    const dir = { x: f.x, y: f.y };
    const at = { x: pl.x + dir.x * TILE, y: pl.y + dir.y * TILE };
    pl.flashColor(BUILD_FX.COLOR.RAGE);
    const len = T(k.p(fin, 'lengthTiles', 5));
    const half = T(k.p(fin, 'widthTiles', 1.2)) / 2;
    k.rt.fx.lineFx(at.x, at.y, dir.x, dir.y, len, half, BUILD_FX.COLOR.CRACK);
    for (const m of k.rt.fx.inLine(at.x, at.y, dir.x, dir.y, len, half))
      k.hit(m, k.p(fin, 'damageMult', 2.4), dir, { heavy: true });
    k.ring(at, T(k.p(fin, 'radiusTiles', 2)), k.p(fin, 'ringMult', 1.2), BUILD_FX.COLOR.RAGE);
    k.fire('ironpeak', 'slam');
  }

  private rageTick(now: number): void {
    const k = this.k;
    const r = k.rt.rule('rage');
    const gr = this.grudge;
    if (!r || !gr) {
      if (this.rage) this.rage = null;
      return;
    }
    const pl = k.g.player;
    if (!this.rage) {
      const drunk = k.rt.rule('rageDrunk');
      const th = drunk && k.rt.drunkActive ? k.p(drunk, 'threshold', 0.5) : k.p(r, 'threshold', 1);
      if (gr.value >= gr.max * th - 1e-6 && !pl.melee.charging) this.startRage();
      return;
    }
    const R = this.rage;
    // 차지 내려찍기가 울분을 다 쓰면 폭주도 끝 (철산 없음)
    if (gr.value < R.set - 1) {
      this.endRage(false);
      return;
    }
    if (now >= R.until) {
      gr.value = 0;
      this.endRage(true);
      return;
    }
    gr.value = gr.max * Math.max(0, Math.min(1, (R.until - now) / R.total));
    R.set = gr.value;
    if (now - this.flashAt >= 420) {
      this.flashAt = now;
      pl.flashColor(BUILD_FX.COLOR.RAGE);
    }
  }

  /** 광전 울분 규칙: 적중마다 울분 */
  private gainGrudge(key: 'hitGain' | 'hurtGain'): void {
    const r = this.k.rt.rule('rage');
    const gr = this.grudge;
    if (!r || !gr || this.rage) return;
    gr.value = Math.min(gr.max, gr.value + this.k.p(r, key, 0));
  }

  private onHurt(): void {
    this.gainGrudge('hurtGain');
  }

  noFlinch(): boolean {
    const k = this.k;
    if (this.rage) return true;
    return Boolean(k.rt.rule('chargeUnbroken') && k.g.player?.melee.charging);
  }

  attackSpeedMult(): number {
    const r = this.k.rt.rule('rage');
    return this.rage && r ? 1 + this.k.p(r, 'attackSpeed', 0.3) : 1;
  }

  onKill(): void {
    const k = this.k;
    const ext = k.rt.rule('rageExtend');
    if (!ext || !this.rage) return;
    const add = Math.min(k.p(ext, 'perKillMs', 700), k.p(ext, 'maxExtraMs', 5000) - this.rage.extra);
    if (add <= 0) return;
    this.rage.until += add;
    this.rage.total += add;
    this.rage.extra += add;
    k.fire('bloodwind', 'extend');
  }

  // --- 연격 · 태클 ---

  onAttack(p: PlayerAttackPayload): void {
    const k = this.k;
    if (p.move !== 'tackle') return;
    const flip = k.rt.rule('tackleFlip');
    const down = k.rt.rule('tackleStun');
    if (!flip && !down) return;
    const at = p.rush?.dashToMs ?? 200;
    k.g.time.delayedCall(Math.max(0, at), () => {
      if (!k.g.scene.isActive()) return;
      const pl = k.g.player;
      const dir = { x: p.dirX, y: p.dirY };
      const reach = T(k.p(flip ?? down!, 'reachTiles', 1.4));
      for (const m of k.rt.fx.inCone(pl.x, pl.y, dir.x, dir.y, reach, 140)) {
        if (flip && !m.isBoss) {
          // 어깨 너머: 등 뒤로 넘긴다
          m.shove(-dir.x, -dir.y, Math.hypot(m.x - pl.x, m.y - pl.y) + T(k.p(flip, 'throwTiles', 2)), 220);
          k.stun(m, k.p(flip, 'stunMs', 400));
        }
        if (down) k.stun(m, k.p(down, 'stunMs', 1000));
      }
      if (flip) k.fire('g_shoulderFlip', 'flip');
      if (down) k.fire('g_tackleStun', 'down');
    });
  }

  afterStrike(mob: Mob, p: PlayerAttackPayload & { buildMove?: string }, died: boolean): void {
    const k = this.k;
    this.gainGrudge('hitGain');
    const launch = k.rt.rule('finisherLaunch');
    if (!launch || died || mob.isBoss || p.comboIndex !== k.p(launch, 'comboIndex', 3)) return;
    // 날려 보내기: 크게 날아가 떨어진 자리 둘레에 피해
    const pl = k.g.player;
    const dir = { x: mob.x - pl.x, y: mob.y - pl.y };
    k.push(mob, dir, k.p(launch, 'knockTiles', 2.5), 240);
    k.g.time.delayedCall(250, () => {
      if (!k.g.scene.isActive() || !mob.active) return;
      const r = T(k.p(launch, 'splashTiles', 1));
      k.rt.fx.ring(mob.x, mob.y, r, BUILD_FX.COLOR.RING, 160);
      for (const m of k.rt.fx.inCircle(mob.x, mob.y, r, new Set([mob])))
        k.hit(m, k.p(launch, 'damageMult', 0.5), { x: m.x - mob.x, y: m.y - mob.y });
      k.fire('g_launch', 'land');
    });
  }

  /** 휘두르며 막기: 연격 중 처음 맞는 한 번 (쿨) */
  adjustDamage(amount: number): number {
    const k = this.k;
    const r = k.rt.rule('swingGuard');
    const pl = k.g.player;
    if (!r || !pl?.inAttackSlow(k.now) || k.now - this.swingGuardAt < k.p(r, 'cooldownMs', 3000)) return amount;
    this.swingGuardAt = k.now;
    pl.flashColor(BUILD_FX.COLOR.ECHO);
    k.fire('g_swingGuard', 'block');
    return amount * (1 - k.p(r, 'reduction', 0.7));
  }

  // --- 우 (가드) ---

  onPerfect(kind: PerfectKind, dx: number, dy: number): void {
    const k = this.k;
    const r = k.rt.rule('perfectGuardStun');
    if (!r || kind !== 'perfectGuard') return;
    const pl = k.g.player;
    for (const m of k.rt.fx.inCone(pl.x, pl.y, dx, dy, T(k.p(r, 'rangeTiles', 2.5)), k.p(r, 'arcDeg', 120)))
      k.stun(m, k.p(r, 'stunMs', 900));
    k.fire('g_perfectStun', 'stun');
  }

  onGuardReleased(): void {
    const k = this.k;
    const r = k.rt.rule('guardPull');
    if (!r) return;
    // 밀쳐내기가 끝난 뒤 앞으로 끌어당긴다
    k.g.time.delayedCall(90, () => {
      if (!k.g.scene.isActive()) return;
      const pl = k.g.player;
      const rad = T(k.p(r, 'radiusTiles', 2.5));
      for (const m of k.rt.fx.inCircle(pl.x, pl.y, rad)) {
        const d = Math.hypot(m.x - pl.x, m.y - pl.y);
        k.push(
          m,
          { x: pl.x - m.x, y: pl.y - m.y },
          Math.min(k.p(r, 'pullTiles', 1.5), Math.max(0, d / TILE - 0.6)),
          180,
        );
      }
      k.fire('g_guardPull', 'pull');
    });
  }

  // --- 좌 홀드 · 대쉬 공격 ---

  onSkill(p: PlayerSkillPayload): void {
    const k = this.k;
    const r = k.rt.rule('leapStun');
    if (!r || p.move !== 'leap' || p.phase !== 'land') return;
    const pl = k.g.player;
    const rad = T(k.p(r, 'radiusTiles', 2));
    k.rt.fx.ring(pl.x, pl.y, rad, BUILD_FX.COLOR.RING, 220);
    for (const m of k.rt.fx.inCircle(pl.x, pl.y, rad)) k.stun(m, k.p(r, 'stunMs', 800));
    k.fire('g_leapToss', 'toss');
  }

  /** 빨아들이는 균열: 양옆 적을 균열 위로 */
  onCrackLine(origin: Pt, dir: Pt, lengthPx: number, halfPx: number): void {
    const k = this.k;
    const r = k.rt.rule('crackPull');
    if (!r || lengthPx <= 0) return;
    const l = Math.hypot(dir.x, dir.y) || 1;
    const u = { x: dir.x / l, y: dir.y / l };
    const side = T(k.p(r, 'sideTiles', 2));
    for (const m of k.rt.fx.inLine(origin.x, origin.y, u.x, u.y, lengthPx, halfPx + side)) {
      const dx = m.x - origin.x;
      const dy = m.y - origin.y;
      const off = dx * u.y - dy * u.x;
      if (Math.abs(off) <= halfPx) continue;
      k.push(m, { x: -u.y * Math.sign(off), y: u.x * Math.sign(off) }, (Math.abs(off) - halfPx * 0.5) / TILE, 160);
    }
    k.fire('g_crackPull', 'pull');
  }

  update(now: number): void {
    this.rageTick(now);
  }

  debug(): Record<string, unknown> {
    return { rage: this.rage ? Math.round(this.rage.until - this.k.now) : 0 };
  }

  destroy(): void {
    EventBus.off(Events.PLAYER_DAMAGED, this.onHurt, this);
    this.rage = null;
  }
}
