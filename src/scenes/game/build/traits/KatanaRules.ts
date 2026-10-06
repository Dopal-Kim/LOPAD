/**
 * 칼 개성·셋째 갈래 '만월' 규칙 (61 G → 61 단계 5 P13 전투 양상):
 * 그림자 찌르기(분신 찌르기) · 칼등 띄우기(비틀거리는 적 → 띄움·착지 충격) · 흘려 밀기(패링 → 둘레 적 처박기) ·
 * 칼 감기(가드 → 앞 적 끌어당김) · 그림자 넘기(완벽 회피 → 적 등 뒤로 넘어가 벰) · 물러서며 베기 · 발도풍(검풍) ·
 * 연쇄 발도(발도 처치 → 다음 적 앞으로 미끄러짐) · 땅에 박기(투구가르기 → 묶음, 다시 치면 튕겨 나감) /
 * 만월(패링 → 달 분신 베기 + 검기) · 삭월 · 보름 · 달빛 잇기 · 취월(패링 → 술 웅덩이마다 달 분신).
 * 불똥 내려베기·피바람·술 회오리는 KatanaBranch(갈래 수단 안). 그림: 만월 `katana_fullmoon`(분신 자리, 없으면 윤곽).
 */
import { BUILD_ART, BUILD_FX, TILE } from '../../../../core/Constants';
import type { PlayerAttackPayload, PlayerSkillPayload } from '../../../../core/EventBus';
import type { Mob } from '../../../../objects/Mob';
import type { ActiveRule } from '../../../../systems/build/buildMods';
import { PLAYER_RENDER_SCALE } from '../../../../systems/weapon/playerScale';
import { traitFxId } from '../../../../systems/growth/traitArt';
import { HIT_ORIGIN_UP_PX } from '../../shared';
import type { PerfectKind } from '../BuildPerfect';
import { T, type Pt, type RuleKit } from './RuleKit';

export class KatanaRules {
  /** 발도를 뗀 시각 (연쇄 발도 창) */
  private iaiAt = -Infinity;
  /** 달 분신에 베인 적 → 시각 (달빛 잇기) */
  private readonly moonHit = new Map<Mob, number>();
  /** 칼등 띄우기: 적 → 다시 띄울 수 있는 시각 */
  private readonly liftReady = new WeakMap<Mob, number>();
  /** 땅에 박기: 박힌 적 */
  private readonly pinned = new Set<Mob>();
  private bindReadyAt = -Infinity;

  constructor(private readonly k: RuleKit) {}

  private dirOf(dx: number, dy: number): Pt {
    const l = Math.hypot(dx, dy) || 1;
    return { x: dx / l, y: dy / l };
  }

  // --- 좌 홀드 (발도) ---

  onSkill(p: PlayerSkillPayload): void {
    if (p.move !== 'iai' || p.phase !== 'release') return;
    const k = this.k;
    const pl = k.g.player;
    this.iaiAt = k.now;
    const f = pl.facingVec;
    const dir = { x: f.x, y: f.y };
    const stage = p.kenkiStage ?? 0;
    // 발도풍: 검기 가득 발도 → 앞으로 검풍 (관통)
    const wave = k.rt.rule('iaiWave');
    if (wave && stage >= k.p(wave, 'minStage', 3)) {
      const from = { x: pl.x, y: pl.y - HIT_ORIGIN_UP_PX };
      k.shot(from, dir, k.p(wave, 'damageMult', 1), {
        tag: 'iaiWave',
        speedTiles: k.p(wave, 'speedTiles', 14),
        rangeTiles: k.p(wave, 'rangeTiles', 6),
        pierce: 99,
        tint: BUILD_FX.COLOR.MOON,
        sprite: traitFxId('katana', 'k_iaiWave', 'wave'),
      });
      k.moves.fx('k_iaiWave', from, {
        part: 'launch',
        angle: Math.atan2(dir.y, dir.x),
        fallbacks: ['katana_crescent'],
      });
      k.fire('k_iaiWave', 'wave');
    }
    // 보름: 달 분신이 함께 발도 (앞 부채꼴, 쓴 검기만큼 세짐)
    const draw = k.rt.rule('moonDraw');
    if (draw) {
      k.g.time.delayedCall(k.p(draw, 'delayMs', 120), () => {
        if (!k.g.scene.isActive()) return;
        const r = T(k.p(draw, 'rangeTiles', 2.5));
        const mult = k.p(draw, 'damageMult', 0.6) * (1 + stage * k.p(draw, 'perKenki', 0.2));
        const back = { x: pl.x - dir.x * TILE * 0.6, y: pl.y - dir.y * TILE * 0.6 };
        if (!k.rt.art.once(BUILD_ART.FULLMOON, back.x, back.y, { scaleMult: PLAYER_RENDER_SCALE }))
          k.rt.fx.clone(back.x, back.y);
        k.rt.fx.coneFx(pl.x, pl.y, dir.x, dir.y, r, k.p(draw, 'arcDeg', 140), BUILD_FX.COLOR.MOON);
        for (const m of k.rt.fx.inCone(pl.x, pl.y, dir.x, dir.y, r, k.p(draw, 'arcDeg', 140))) {
          this.moonHit.set(m, k.now);
          k.hit(m, mult, dir, { heavy: true });
        }
        k.fire('hozuki', 'draw', { stage });
      });
    }
  }

  // --- 우 (가드 · 패링) ---

  /** 칼 감기: 가드로 막으면 앞의 적을 끌어당겨 비틀거리게 (사슬 선) */
  onGuardBlock(): void {
    const k = this.k;
    const r = k.rt.rule('guardBind');
    if (!r || k.now < this.bindReadyAt) return;
    const pl = k.g.player;
    const f = pl.facingVec;
    const near = k.rt.fx
      .inCone(pl.x, pl.y, f.x, f.y, T(k.p(r, 'rangeTiles', 2.5)), k.p(r, 'arcDeg', 120))
      .filter((m) => !m.isBoss)
      .sort((a, b) => Math.hypot(a.x - pl.x, a.y - pl.y) - Math.hypot(b.x - pl.x, b.y - pl.y))[0];
    if (!near) return;
    this.bindReadyAt = k.now + k.p(r, 'cooldownMs', 600);
    k.moves.chainLine({ x: pl.x, y: pl.y - HIT_ORIGIN_UP_PX }, { x: near.x, y: near.y - 8 }, BUILD_FX.COLOR.SPIN);
    k.moves.fx('k_bladeBind', { x: near.x, y: near.y - 8 }, { fallbacks: ['katana_counter', 'hit_spark'] });
    k.moves.pull(near, { x: pl.x, y: pl.y }, k.p(r, 'pullTiles', 1.5), 'k_bladeBind', {
      stopTiles: 0.8,
      endStunMs: k.p(r, 'stunMs', 800),
    });
    k.rt.art.stagger(near, k.p(r, 'stunMs', 800));
    k.fire('k_bladeBind', 'pull');
  }

  onPerfect(kind: PerfectKind, dx: number, dy: number): void {
    const k = this.k;
    if (kind === 'perfectEvade') {
      this.vault();
      return;
    }
    if (kind !== 'parry') return;
    const pl = k.g.player;
    // 흘려 밀기: 둘레 적을 벽·기둥·다른 적에게 처박는다
    const shove = k.rt.rule('parryShove');
    if (shove) {
      const r = T(k.p(shove, 'radiusTiles', 2));
      if (!k.moves.fx('k_parryShove', pl, { fallbacks: ['guard_wave'] }))
        k.rt.fx.ring(pl.x, pl.y, r, BUILD_FX.COLOR.ECHO, 200);
      for (const m of k.rt.fx.inCircle(pl.x, pl.y, r))
        k.moves.slam(m, { x: m.x - pl.x, y: m.y - pl.y }, k.p(shove, 'knockTiles', 2.5), 'k_parryShove', {
          slamMult: k.p(shove, 'slamMult', 0.6),
          slamStunMs: k.p(shove, 'slamStunMs', 700),
          endStunMs: 300,
        });
      k.fire('k_parryShove', 'push');
    }
    // 만월: 달 분신이 공격한 적을 따라 벤다
    const moon = k.rt.rule('moonClone');
    if (moon) k.g.time.delayedCall(k.p(moon, 'delayMs', 220), () => this.moonSlash(dx, dy));
    // 취월: 둘레 술 웅덩이마다 달 분신이 비쳐 나와 함께 벤다
    const pools = k.rt.rule('moonPools');
    if (pools) this.moonPools(pools);
  }

  /** 그림자 넘기: 완벽 회피 → 가장 가까운 적의 등 뒤로 넘어가 벤다 */
  private vault(): void {
    const k = this.k;
    const r = k.rt.rule('evadeBehind');
    if (!r) return;
    const pl = k.g.player;
    const target = k.rt.fx.nearest(pl.x, pl.y, T(k.p(r, 'rangeTiles', 3)));
    if (!target) return;
    const u = this.dirOf(target.x - pl.x, target.y - pl.y);
    const behind = { x: target.x + u.x * T(k.p(r, 'behindTiles', 1)), y: target.y + u.y * T(k.p(r, 'behindTiles', 1)) };
    if (!k.g.world.isWalkableAt(behind.x, behind.y)) return;
    const from = { x: pl.x, y: pl.y };
    k.rt.fx.clone(from.x, from.y);
    k.moves.fx('k_shadowVault', from, { part: 'out', fallbacks: ['shadowstep_ghost', 'afterimage'] });
    pl.teleportTo(behind.x, behind.y);
    pl.grantInvulnerable(k.now + 200);
    k.moves.fx(
      'k_shadowVault',
      { x: behind.x, y: behind.y - HIT_ORIGIN_UP_PX },
      { part: 'in', fallbacks: ['katana_counter'] },
    );
    // 돌아서 벤다 (등 뒤 → 앞으로)
    const back = { x: -u.x, y: -u.y };
    const rad = T(k.p(r, 'radiusTiles', 1));
    k.rt.fx.coneFx(behind.x, behind.y, back.x, back.y, rad + TILE * 0.4, 160, BUILD_FX.COLOR.SPIN);
    for (const m of k.rt.fx.inCone(behind.x, behind.y, back.x, back.y, rad + TILE * 0.4, 160))
      k.hit(m, k.p(r, 'damageMult', 0.9), back, { heavy: true });
    k.fire('k_shadowVault', 'vault');
  }

  /** 만월 분신 한 번: 패링 자리에서 공격한 쪽(가장 가까운 적)으로 선 베기 → 맞으면 검기 */
  private moonSlash(dx: number, dy: number): void {
    const k = this.k;
    const moon = k.rt.rule('moonClone');
    if (!moon || !k.g.scene.isActive()) return;
    const pl = k.g.player;
    const range = T(k.p(moon, 'rangeTiles', 4));
    const target = k.rt.fx.nearest(pl.x, pl.y, range);
    const dir = target ? this.dirOf(target.x - pl.x, target.y - pl.y) : this.dirOf(dx, dy);
    const from = { x: pl.x, y: pl.y };
    k.rt.art.once(BUILD_ART.FULLMOON, from.x, from.y, { scaleMult: PLAYER_RENDER_SCALE });
    const hits = k.cloneLine(from, dir, range, T(k.p(moon, 'widthTiles', 1)) / 2, k.p(moon, 'damageMult', 1.2));
    for (const m of hits) this.moonHit.set(m, k.now);
    if (hits.length > 0) k.rt.combat.restoreResource({ kenkiStage: k.p(moon, 'kenkiStage', 0.34) });
    k.fire('mangetsu', 'clone', { hits: hits.length });
  }

  /** 취월: 둘레 술 웅덩이(가까운 순 최대 maxClones)마다 달 분신 — 웅덩이에서 가장 가까운 적으로 선 베기 */
  private moonPools(r: ActiveRule): void {
    const k = this.k;
    const pl = k.g.player;
    const range = T(k.p(r, 'poolRangeTiles', 4));
    const list = k.g.pools.pools
      .filter((q) => Math.hypot(q.rect.centerX - pl.x, q.rect.centerY - pl.y) <= range)
      .sort(
        (a, b) =>
          Math.hypot(a.rect.centerX - pl.x, a.rect.centerY - pl.y) -
          Math.hypot(b.rect.centerX - pl.x, b.rect.centerY - pl.y),
      )
      .slice(0, k.p(r, 'maxClones', 3));
    list.forEach((q, i) => {
      k.g.time.delayedCall(k.p(r, 'delayMs', 260) + i * 120, () => {
        if (!k.g.scene.isActive()) return;
        const at = { x: q.rect.centerX, y: q.rect.centerY };
        const target = k.rt.fx.nearest(at.x, at.y, T(k.p(r, 'rangeTiles', 3)));
        k.moves.fx('k_moonPools', at, { fallbacks: [BUILD_ART.FULLMOON, 'katana_crescent'] });
        if (!target) return;
        const hits = k.cloneLine(
          at,
          { x: target.x - at.x, y: target.y - at.y },
          Math.hypot(target.x - at.x, target.y - at.y) + TILE * 0.5,
          TILE * 0.5,
          k.p(r, 'damageMult', 0.5),
        );
        for (const m of hits) this.moonHit.set(m, k.now);
      });
    });
    if (list.length > 0) k.fire('k_moonPools', 'clone', { pools: list.length });
  }

  // --- 대쉬 (일섬) ---

  onIssenEnd(start: Pt, dir: Pt, travel: number): void {
    const k = this.k;
    const pl = k.g.player;
    // 물러서며 베기: 뒤로 반 걸음 + 둘레 한 번 더
    const back = k.rt.rule('issenBackstep');
    if (back) {
      pl.startLunge(-dir.x, -dir.y, T(k.p(back, 'backTiles', 1)), 140, k.now);
      k.g.time.delayedCall(150, () => {
        if (!k.g.scene.isActive()) return;
        const at = { x: pl.x, y: pl.y - HIT_ORIGIN_UP_PX };
        k.moves.fx('k_issenBack', at, { fallbacks: ['katana_spin'] });
        k.ring(at, T(k.p(back, 'radiusTiles', 1.5)), k.p(back, 'damageMult', 0.6), BUILD_FX.COLOR.SPIN);
        k.fire('k_issenBack', 'slash');
      });
    }
    // 삭월: 달 분신이 같은 길을 한 번 더 달린다
    const moon = k.rt.rule('moonIssen');
    if (moon && travel > 0) {
      k.g.time.delayedCall(k.p(moon, 'delayMs', 180), () => {
        if (!k.g.scene.isActive()) return;
        const from = { x: start.x, y: start.y - HIT_ORIGIN_UP_PX };
        const hits = k.cloneLine(
          from,
          dir,
          travel + TILE,
          T(k.p(moon, 'widthTiles', 1)) / 2,
          k.p(moon, 'damageMult', 0.6),
        );
        for (const m of hits) this.moonHit.set(m, k.now);
        k.fire('sakugetsu', 'issen', { hits: hits.length });
      });
    }
  }

  // --- 타격 · 처치 ---

  afterStrike(mob: Mob, p: PlayerAttackPayload & { buildMove?: string }, died: boolean): void {
    const k = this.k;
    if (died) {
      this.pinned.delete(mob);
      return;
    }
    // 땅에 박기: 투구가르기에 맞고 버팀 → 묶음 / 묶인 적을 다시 치면 튕겨 나감
    const pin = k.rt.rule('kabutoPin');
    if (pin && p.buildMove === 'unblockable') {
      if (k.moves.bind(mob, k.p(pin, 'bindMs', 1500), 'k_groundPin')) {
        this.pinned.add(mob);
        k.moves.fx('k_groundPin', { x: mob.x, y: mob.y }, { part: 'bind', fallbacks: ['katana_cleave_crack'] });
        k.fire('k_groundPin', 'pin');
      }
      return;
    }
    if (pin && this.pinned.has(mob)) {
      this.pinned.delete(mob);
      if (k.moves.unbind(mob)) {
        const pl = k.g.player;
        k.moves.slam(mob, { x: mob.x - pl.x, y: mob.y - pl.y }, k.p(pin, 'knockTiles', 3), 'k_groundPin', {
          slamMult: k.p(pin, 'slamMult', 0.6),
          slamStunMs: k.p(pin, 'slamStunMs', 600),
        });
        k.fire('k_groundPin', 'launch');
        return;
      }
    }
    // 칼등 띄우기: 비틀거리는 적 → 띄워 올림 (같은 적은 잠깐 쉼)
    const lift = k.rt.rule('launchStunned');
    if (lift && mob.isStunned(k.now) && !k.moves.isAirborne(mob) && k.now >= (this.liftReady.get(mob) ?? 0)) {
      const air = k.p(lift, 'airMs', 650);
      if (
        k.moves.launch(mob, 'k_edgeLift', {
          heightTiles: k.p(lift, 'heightTiles', 1.4),
          airMs: air,
          landRadiusTiles: k.p(lift, 'landRadiusTiles', 1.2),
          landMult: k.p(lift, 'landMult', 0.6),
        })
      ) {
        this.liftReady.set(mob, k.now + air + k.p(lift, 'cooldownMs', 900));
        k.fire('k_edgeLift', 'launch');
      }
    }
  }

  onKill(mob: Mob): void {
    const k = this.k;
    const at = { x: mob.x, y: mob.y };
    // 그림자 찌르기: 찌르기(마지막 타)로 쓰러뜨림 → 가까운 적을 그림자가 찌른다
    const echo = k.rt.rule('finisherKillEcho');
    if (echo && k.recentAttack(450, (p) => p.comboIndex !== undefined && p.comboIndex === (p.comboCount ?? 0) - 1)) {
      const next = k.rt.fx.nearest(at.x, at.y, T(k.p(echo, 'rangeTiles', 3)), new Set([mob]));
      if (next) {
        k.moves.fx('k_shadowThrust', at, {
          angle: Math.atan2(next.y - at.y, next.x - at.x),
          fallbacks: ['afterimage'],
        });
        k.cloneLine(
          at,
          { x: next.x - at.x, y: next.y - at.y },
          Math.hypot(next.x - at.x, next.y - at.y) + TILE * 0.5,
          TILE * 0.4,
          k.p(echo, 'damageMult', 0.8),
          BUILD_FX.COLOR.THROW,
        );
        k.fire('k_shadowThrust', 'echo');
      }
    }
    // 연쇄 발도: 발도로 쓰러뜨림 → 가장 가까운 적 앞까지 미끄러진다
    const chain = k.rt.rule('iaiKillDash');
    if (chain && k.now - this.iaiAt <= k.p(chain, 'windowMs', 600)) this.iaiDash(mob, chain);
    // 달빛 잇기: 달 분신이 벤 적이 쓰러짐 → 다음 적에게 옮겨 벤다
    const relay = k.rt.rule('moonRelay');
    const hitAt = this.moonHit.get(mob);
    this.moonHit.delete(mob);
    if (relay && hitAt !== undefined && k.now - hitAt <= 600) {
      const next = k.rt.fx.nearest(at.x, at.y, T(k.p(relay, 'rangeTiles', 4)), new Set([mob]));
      if (next)
        k.g.time.delayedCall(120, () => {
          if (!k.g.scene.isActive() || !next.active) return;
          k.moves.fx('k_moonRelay', at, {
            angle: Math.atan2(next.y - at.y, next.x - at.x),
            fallbacks: [BUILD_ART.FULLMOON],
          });
          const hits = k.cloneLine(
            at,
            { x: next.x - at.x, y: next.y - at.y },
            Math.hypot(next.x - at.x, next.y - at.y) + TILE * 0.5,
            TILE * 0.5,
            k.p(relay, 'damageMult', 0.8),
          );
          for (const m of hits) this.moonHit.set(m, k.now);
          k.fire('k_moonRelay', 'relay');
        });
    }
    for (const [m, t] of this.moonHit) if (!m.active || k.now - t > 2000) this.moonHit.delete(m);
    this.pinned.delete(mob);
  }

  private iaiDash(dead: Mob, r: ActiveRule): void {
    const k = this.k;
    const pl = k.g.player;
    const next = k.rt.fx.nearest(pl.x, pl.y, T(k.p(r, 'rangeTiles', 5)), new Set([dead]));
    if (!next) return;
    this.iaiAt = -Infinity; // 한 번의 발도에 한 번
    const d = Math.hypot(next.x - pl.x, next.y - pl.y);
    const dist = Math.max(0, d - T(k.p(r, 'stopTiles', 1)));
    if (dist < TILE * 0.5) return;
    const u = this.dirOf(next.x - pl.x, next.y - pl.y);
    const ms = k.p(r, 'dashMs', 160);
    k.rt.fx.clone(pl.x, pl.y);
    k.moves.fx('k_iaiChain', pl, { angle: Math.atan2(u.y, u.x), fallbacks: ['dash_trail', 'afterimage'] });
    pl.startLunge(u.x, u.y, dist, ms, k.now);
    pl.grantInvulnerable(k.now + ms);
    k.fire('k_iaiChain', 'dash');
  }

  destroy(): void {
    this.pinned.clear();
    this.moonHit.clear();
  }
}
