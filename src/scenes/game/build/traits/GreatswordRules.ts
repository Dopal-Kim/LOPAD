/**
 * 대검 개성·셋째 갈래 '광전' 규칙 (61 G → 61 단계 5 P13 전투 양상):
 * 날려 보내기(넷째 타 → 벽·기둥·적에게 처박기) · 쳐내기(연격이 화살·술병을 되쳐 보냄) · 되받는 땅울림(퍼펙트 가드 → 앞줄 띄움) ·
 * 끌어당기기 · 어깨 너머(태클 → 등 뒤로 메침) · 들이받기(태클 → 밀고 나가 처박기) · 끓는 쇠(차지 중 술 웅덩이 흡수 → 균열 불길) ·
 * 빨아들이는 균열 · 띄워 올리기(도약 착지 → 둘레 띄움) / 광전(울분 가득 → 저절로 폭주) · 혈풍 · 철산 · 포효(밀려나 부딪힘) ·
 * 술기운 폭주(폭주 중 웅덩이 점화, 불 위에서 폭주 유지). 짓눌린 숨·술독 짓누르기·갈라진 길은 GreatswordBranch(진동·균열 안).
 */
import { BUILD_FX, DEPTH, TILE } from '../../../../core/Constants';
import { EventBus, Events, type PlayerAttackPayload, type PlayerSkillPayload } from '../../../../core/EventBus';
import type { Mob } from '../../../../objects/Mob';
import type { Projectile } from '../../../../objects/Projectile';
import type { ActiveRule } from '../../../../systems/build/buildMods';
import type { PerfectKind } from '../BuildPerfect';
import { T, type Pt, type RuleKit } from './RuleKit';

const unit = (x: number, y: number): Pt => {
  const l = Math.hypot(x, y) || 1;
  return { x: x / l, y: y / l };
};

export class GreatswordRules {
  /** 폭주: 끝 시각 · 전체 길이(연장 포함) · 연장 합 · 지난 프레임에 둔 울분 값 · 불 위에서 붙든 ms */
  private rage: { until: number; total: number; extra: number; set: number; held: number } | null = null;
  private flashAt = -Infinity;
  private lastTick = -Infinity;
  /** 끓는 쇠: 차지 중 빨아들인 웅덩이 수 · 불붙은 웅덩이가 있었는지 */
  private soaked = 0;
  /** 공명(막고 되치는 대검)이 듣는 '되쳐 냄' */
  onDeflect: (() => void) | null = null;

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
    this.rage = { until: k.now + total, total, extra: 0, set: gr.max, held: 0 };
    gr.value = gr.max;
    const pl = k.g.player;
    pl.flashColor(BUILD_FX.COLOR.RAGE);
    k.rt.fx.callout(BUILD_FX.TEXT.RAGE);
    k.fire('berserk', 'start');
    // 포효: 둘레 적이 겁먹고 밀려나 벽·다른 적에 부딪친다
    const roar = k.rt.rule('rageRoar');
    if (roar) {
      const rad = T(k.p(roar, 'radiusTiles', 3));
      if (!k.moves.fx('g_rageRoar', pl, { fallbacks: ['guard_wave'] }))
        k.rt.fx.ring(pl.x, pl.y, rad, BUILD_FX.COLOR.RAGE, 260);
      for (const m of k.rt.fx.inCircle(pl.x, pl.y, rad))
        k.moves.slam(m, { x: m.x - pl.x, y: m.y - pl.y }, k.p(roar, 'knockTiles', 2), 'g_rageRoar', {
          slamMult: k.p(roar, 'slamMult', 0.4),
          slamStunMs: k.p(roar, 'stunMs', 600),
          endStunMs: k.p(roar, 'stunMs', 600),
        });
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
    const dt = Number.isFinite(this.lastTick) ? Math.max(0, Math.min(100, now - this.lastTick)) : 0;
    this.lastTick = now;
    if (!r || !gr) {
      if (this.rage) this.rage = null;
      return;
    }
    const pl = k.g.player;
    if (!this.rage) {
      const th = k.p(r, 'threshold', 1);
      if (gr.value >= gr.max * th - 1e-6 && !pl.melee.charging) this.startRage();
      return;
    }
    const R = this.rage;
    // 차지 내려찍기가 울분을 다 쓰면 폭주도 끝 (철산 없음)
    if (gr.value < R.set - 1) {
      this.endRage(false);
      return;
    }
    // 술기운 폭주: 밟는 술 웅덩이에 불 · 불타는 웅덩이 위에서는 폭주가 줄지 않는다
    const fire = k.rt.rule('rageFire');
    if (fire) {
      const lit = k.moves.igniteCircle(pl, T(k.p(fire, 'radiusTiles', 0.8)));
      if (lit > 0) {
        if (!k.moves.fx('g_rageFire', pl, { depth: DEPTH.FX_GROUND })) k.moves.sparks(pl);
        k.fire('g_rageFire', 'ignite');
      }
      const onFire = k.g.pools.pools.some((q) => q.rect.contains(pl.x, pl.y) && k.g.pools.burning(q));
      if (onFire && R.held < k.p(fire, 'maxHoldMs', 4000)) {
        R.until += dt;
        R.held += dt;
      }
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
    return this.rage !== null;
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
    if (p.move === 'tackle') this.onTackle(p);
    else if (p.kind === 'attack' && p.comboIndex !== undefined) this.swat(p);
  }

  /** 쳐내기: 휘두름(판정 순간)에 걸린 적 화살을 되쳐 보내고, 날아오는 술병을 던진 자리로 돌려보낸다 */
  private swat(p: PlayerAttackPayload): void {
    const k = this.k;
    const r = k.rt.rule('swingDeflect');
    if (!r) return;
    k.g.time.delayedCall(Math.max(0, p.swingDelayMs), () => {
      if (!k.g.scene.isActive()) return;
      const pl = k.g.player;
      const reach = T(k.p(r, 'reachTiles', 2.2));
      const n = this.deflectIn(pl, { x: p.dirX, y: p.dirY }, reach, k.p(r, 'arcDeg', 150), k.p(r, 'returnMult', 1.5));
      if (n > 0) {
        k.fire('g_swatBack', 'deflect', { n });
        this.onDeflect?.();
      }
    });
  }

  /** 적 탄(앞 부채꼴) · 술병(반경) 되쳐 보내기 — 되친 수 (공명도 쓴다) */
  deflectIn(at: Pt, dir: Pt, reach: number, arcDeg: number, mult: number): number {
    const k = this.k;
    const u = unit(dir.x, dir.y);
    const half = (arcDeg * Math.PI) / 360;
    let n = 0;
    for (const child of k.g.projectiles.getChildren()) {
      const pr = child as Projectile;
      if (!pr.active || pr.reflected || pr.owner !== 'enemy') continue;
      const dx = pr.x - at.x;
      const dy = pr.y - at.y;
      const d = Math.hypot(dx, dy);
      if (d > reach) continue;
      if (d > 4 && Math.acos(Math.max(-1, Math.min(1, (dx * u.x + dy * u.y) / d))) > half) continue;
      pr.reflect(mult);
      k.moves.fx(
        'g_swatBack',
        { x: pr.x, y: pr.y },
        { angle: Math.atan2(-dy, -dx), fallbacks: ['katana_whirl_reflect', 'hit_spark'] },
      );
      n += 1;
    }
    n += k.g.hazards.returnBottlesNear(at.x, at.y, reach, mult);
    return n;
  }

  private onTackle(p: PlayerAttackPayload): void {
    const k = this.k;
    const flip = k.rt.rule('tackleFlip');
    const ram = k.rt.rule('tackleRam');
    if (!flip && !ram) return;
    const at = p.rush?.dashToMs ?? 200;
    k.g.time.delayedCall(Math.max(0, at), () => {
      if (!k.g.scene.isActive()) return;
      const pl = k.g.player;
      const dir = unit(p.dirX, p.dirY);
      const reach = T(k.p(flip ?? ram!, 'reachTiles', 1.4));
      for (const m of k.rt.fx.inCone(pl.x, pl.y, dir.x, dir.y, reach, 140)) {
        if (m.isBoss) continue;
        if (flip) this.flip(m, dir, flip, ram);
        else if (ram)
          k.moves.slam(m, dir, k.p(ram, 'knockTiles', 3), 'g_ramWall', {
            slamMult: k.p(ram, 'slamMult', 0.8),
            slamStunMs: k.p(ram, 'slamStunMs', 900),
            endStunMs: 300,
          });
      }
      if (flip) k.fire('g_shoulderFlip', 'flip');
      if (ram) k.fire('g_ramWall', 'ram');
    });
  }

  /** 어깨 너머: 띄워 등 뒤로 메친다 (들이받기도 있으면 등 뒤 벽·적에게 처박힌다) */
  private flip(m: Mob, dir: Pt, flip: ActiveRule, ram: ActiveRule | null): void {
    const k = this.k;
    const pl = k.g.player;
    const dist = Math.hypot(m.x - pl.x, m.y - pl.y) / TILE + k.p(flip, 'throwTiles', 2);
    k.moves.launch(m, 'g_shoulderFlip', {
      heightTiles: 1,
      airMs: 300,
      landRadiusTiles: k.p(flip, 'landRadiusTiles', 0.8),
      landMult: k.p(flip, 'landMult', 0.4),
    });
    k.moves.slam(m, { x: -dir.x, y: -dir.y }, dist, 'g_shoulderFlip', {
      slamMult: ram ? k.p(ram, 'slamMult', 0.8) : 0.3,
      slamStunMs: ram ? k.p(ram, 'slamStunMs', 900) : k.p(flip, 'stunMs', 500),
      endStunMs: k.p(flip, 'stunMs', 500),
    });
  }

  afterStrike(mob: Mob, p: PlayerAttackPayload & { buildMove?: string }, died: boolean): void {
    const k = this.k;
    this.gainGrudge('hitGain');
    const launch = k.rt.rule('finisherLaunch');
    if (!launch || died || mob.isBoss || p.comboIndex !== k.p(launch, 'comboIndex', 3)) return;
    // 날려 보내기: 크게 날아가 벽·기둥·다른 적에게 처박힌다
    const pl = k.g.player;
    k.moves.fx('g_launch', { x: mob.x, y: mob.y - 8 }, { part: 'launch', fallbacks: ['hit_greatsword_heavy'] });
    k.moves.slam(mob, { x: mob.x - pl.x, y: mob.y - pl.y }, k.p(launch, 'knockTiles', 3), 'g_launch', {
      slamMult: k.p(launch, 'slamMult', 0.7),
      slamStunMs: k.p(launch, 'slamStunMs', 800),
      endStunMs: 250,
    });
    k.fire('g_launch', 'launch');
  }

  // --- 우 (가드) ---

  onPerfect(kind: PerfectKind, dx: number, dy: number): void {
    const k = this.k;
    if (kind !== 'perfectGuard') return;
    this.onDeflect?.();
    const r = k.rt.rule('perfectQuake');
    if (!r) return;
    // 되받는 땅울림: 막은 충격이 앞줄로 번져 적을 띄운다
    const pl = k.g.player;
    const u = unit(dx, dy);
    const len = T(k.p(r, 'lengthTiles', 4));
    const half = T(k.p(r, 'widthTiles', 1.4)) / 2;
    const from = { x: pl.x + u.x * TILE * 0.5, y: pl.y + u.y * TILE * 0.5 };
    if (
      !k.moves.fx('g_quakeGuard', from, {
        angle: Math.atan2(u.y, u.x),
        fallbacks: ['greatsword_charge_crack_line_t2'],
        depth: DEPTH.FX_GROUND,
      })
    )
      k.rt.fx.lineFx(from.x, from.y, u.x, u.y, len, half, BUILD_FX.COLOR.CRACK);
    const hits = k.rt.fx.inLine(from.x, from.y, u.x, u.y, len, half);
    hits.forEach((m, i) => {
      k.g.time.delayedCall(40 + i * 60, () => {
        if (!k.g.scene.isActive() || !m.active) return;
        k.hit(m, k.p(r, 'damageMult', 0.5), u);
        k.moves.launch(m, 'g_quakeGuard', {
          heightTiles: k.p(r, 'heightTiles', 1.2),
          airMs: k.p(r, 'airMs', 700),
          landRadiusTiles: k.p(r, 'landRadiusTiles', 0.8),
          landMult: k.p(r, 'landMult', 0.3),
        });
      });
    });
    k.fire('g_quakeGuard', 'quake', { hits: hits.length });
  }

  onGuardReleased(): void {
    const k = this.k;
    const r = k.rt.rule('guardPull');
    if (!r) return;
    // 밀쳐내기가 끝난 뒤 앞으로 끌어당긴다 (끌려온 적끼리 부딪침)
    k.g.time.delayedCall(90, () => {
      if (!k.g.scene.isActive()) return;
      const pl = k.g.player;
      const rad = T(k.p(r, 'radiusTiles', 2.5));
      const hits = k.rt.fx.inCircle(pl.x, pl.y, rad);
      if (hits.length > 0) k.moves.fx('g_guardPull', pl, { fallbacks: ['greatsword_brace_absorb'] });
      for (const m of hits) {
        k.moves.chainLine(pl, m, BUILD_FX.COLOR.RING, 200);
        k.moves.pull(m, pl, k.p(r, 'pullTiles', 1.5), 'g_guardPull', { stopTiles: 0.6 });
      }
      if (hits.length > 0) k.fire('g_guardPull', 'pull');
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
    for (const m of k.rt.fx.inCircle(pl.x, pl.y, rad))
      k.moves.launch(m, 'g_leapToss', {
        heightTiles: k.p(r, 'heightTiles', 1.6),
        airMs: k.p(r, 'airMs', 800),
        landRadiusTiles: k.p(r, 'landRadiusTiles', 0.8),
        landMult: k.p(r, 'landMult', 0.35),
      });
    k.fire('g_leapToss', 'toss');
  }

  /** 차지 균열 (BranchStrikes.onCrackLine): 빨아들이는 균열 · 끓는 쇠 불길 */
  onCrackLine(origin: Pt, dir: Pt, lengthPx: number, halfPx: number): void {
    const k = this.k;
    if (lengthPx <= 0) return;
    const u = unit(dir.x, dir.y);
    const r = k.rt.rule('crackPull');
    if (r) {
      const side = T(k.p(r, 'sideTiles', 2));
      for (const m of k.rt.fx.inLine(origin.x, origin.y, u.x, u.y, lengthPx, halfPx + side)) {
        const dx = m.x - origin.x;
        const dy = m.y - origin.y;
        const off = dx * u.y - dy * u.x;
        if (Math.abs(off) <= halfPx) continue;
        const onLine = { x: m.x - u.y * off, y: m.y + u.x * off };
        k.moves.chainLine(m, onLine, BUILD_FX.COLOR.CRACK, 220);
        k.moves.fx('g_crackPull', { x: m.x, y: m.y }, { angle: Math.atan2(onLine.y - m.y, onLine.x - m.x) });
        k.moves.pull(m, onLine, Math.abs(off) / TILE, 'g_crackPull', { stopTiles: 0 });
      }
      k.fire('g_crackPull', 'pull');
    }
    // 끓는 쇠: 모은 술이 균열을 따라 불길로
    const soak = k.rt.rule('chargeSoak');
    if (soak && this.soaked > 0) {
      const half = T(k.p(soak, 'widthTiles', 1)) / 2;
      const n = Math.max(1, Math.round(lengthPx / TILE));
      for (let i = 0; i <= n; i++) {
        const at = { x: origin.x + (u.x * lengthPx * i) / n, y: origin.y + (u.y * lengthPx * i) / n };
        k.g.time.delayedCall(i * 50, () => {
          if (!k.g.scene.isActive()) return;
          k.rt.fx.firePatch(
            at.x,
            at.y,
            half,
            k.p(soak, 'fireMs', 2500),
            k.p(soak, 'fireTickMs', 400),
            k.p(soak, 'fireMult', 0.2),
          );
          if (!k.moves.fx('g_boilingSteel', at, { part: 'fire', depth: DEPTH.FX_GROUND })) k.moves.sparks(at);
        });
      }
      k.moves.igniteLine(origin, u, lengthPx, half);
      k.fire('g_boilingSteel', 'flame', { soaked: this.soaked });
      this.soaked = 0;
    }
  }

  /** 끓는 쇠: 차지를 모으는 동안 둘레 술 웅덩이를 빨아들인다 */
  private soakTick(): void {
    const k = this.k;
    const r = k.rt.rule('chargeSoak');
    const pl = k.g.player;
    if (!r || !pl) return;
    if (!pl.melee.charging) return;
    for (const q of k.rt.fx.poolsNear(pl.x, pl.y, T(k.p(r, 'pullTiles', 3.5)))) {
      if (q.until <= k.now) continue;
      k.moves.chainLine({ x: q.rect.centerX, y: q.rect.centerY }, pl, BUILD_FX.COLOR.LIQUOR, 360);
      q.until = k.now;
      this.soaked += 1;
      k.moves.fx('g_boilingSteel', pl, { part: 'soak', fallbacks: ['greatsword_charge_ring'] });
      k.fire('g_boilingSteel', 'soak');
    }
  }

  update(now: number): void {
    this.rageTick(now);
    this.soakTick();
  }

  debug(): Record<string, unknown> {
    return { rage: this.rage ? Math.round(this.rage.until - this.k.now) : 0, soaked: this.soaked };
  }

  destroy(): void {
    EventBus.off(Events.PLAYER_DAMAGED, this.onHurt, this);
    this.rage = null;
    this.onDeflect = null;
  }
}
