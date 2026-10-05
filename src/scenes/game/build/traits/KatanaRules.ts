/**
 * 61 G 칼 개성·셋째 갈래 '만월' 규칙: 그림자 찌르기 · 칼끝 겨누기(TraitRules.forceCrit) · 흘려 밀기 · 막으며 벼리기 · 스치는 칼바람 ·
 * 물러서며 베기 · 발도풍 · 칼집 되돌림 · 갈라진 투구 / 만월(패링 → 달 분신 베기 + 검기) · 삭월(분신이 일섬을 따라) ·
 * 보름(발도 때 분신 동시 발도) · 달빛 잇기 · 취월. 그림: 만월 `katana_fullmoon`(분신 자리, 없으면 윤곽).
 */
import { BUILD_ART, BUILD_FX, TILE } from '../../../../core/Constants';
import type { PlayerAttackPayload, PlayerSkillPayload } from '../../../../core/EventBus';
import type { Mob } from '../../../../objects/Mob';
import { PLAYER_RENDER_SCALE } from '../../../../systems/weapon/playerScale';
import { HIT_ORIGIN_UP_PX } from '../../shared';
import type { PerfectKind } from '../BuildPerfect';
import { T, type Pt, type RuleKit } from './RuleKit';

export class KatanaRules {
  /** 발도를 뗀 시각 (칼집 되돌림 창) */
  private iaiAt = -Infinity;
  /** 달 분신에 베인 적 → 시각 (달빛 잇기) */
  private readonly moonHit = new Map<Mob, number>();

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
      k.shot({ x: pl.x, y: pl.y - HIT_ORIGIN_UP_PX }, dir, k.p(wave, 'damageMult', 1), {
        tag: 'iaiWave',
        speedTiles: k.p(wave, 'speedTiles', 14),
        rangeTiles: k.p(wave, 'rangeTiles', 6),
        pierce: 99,
        tint: BUILD_FX.COLOR.MOON,
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

  onGuardBlock(): void {
    const r = this.k.rt.rule('guardKenki');
    if (!r) return;
    this.k.rt.combat.restoreResource({ kenkiStage: this.k.p(r, 'kenkiStage', 0.34) });
    this.k.fire('k_guardKenki', 'block');
  }

  onPerfect(kind: PerfectKind, dx: number, dy: number): void {
    const k = this.k;
    if (kind === 'perfectEvade') {
      const r = k.rt.rule('evadeKenki');
      if (r) {
        k.rt.combat.restoreResource({ kenkiStage: k.p(r, 'kenkiStage', 1) });
        k.fire('k_evadeKenki', 'evade');
      }
      return;
    }
    if (kind !== 'parry') return;
    const pl = k.g.player;
    // 흘려 밀기: 둘레 적을 밀쳐낸다
    const shove = k.rt.rule('parryShove');
    if (shove) {
      const r = T(k.p(shove, 'radiusTiles', 2));
      k.rt.fx.ring(pl.x, pl.y, r, BUILD_FX.COLOR.ECHO, 200);
      for (const m of k.rt.fx.inCircle(pl.x, pl.y, r)) {
        k.push(m, { x: m.x - pl.x, y: m.y - pl.y }, k.p(shove, 'knockTiles', 1.5));
        k.stun(m, k.p(shove, 'stunMs', 300));
      }
      k.fire('k_parryShove', 'push');
    }
    // 만월: 달 분신이 공격한 적을 따라 벤다 (취월: 취기 중이면 둘)
    const moon = k.rt.rule('moonClone');
    if (moon) {
      const n = k.rt.rule('moonDouble') && k.rt.drunkActive ? 2 : 1;
      for (let i = 0; i < n; i++)
        k.g.time.delayedCall(k.p(moon, 'delayMs', 220) + i * 160, () => this.moonSlash(dx, dy, i));
    }
  }

  /** 만월 분신 한 번: 패링 자리에서 공격한 쪽(가장 가까운 적)으로 선 베기 → 맞으면 검기 */
  private moonSlash(dx: number, dy: number, i: number): void {
    const k = this.k;
    const moon = k.rt.rule('moonClone');
    if (!moon || !k.g.scene.isActive()) return;
    const pl = k.g.player;
    const range = T(k.p(moon, 'rangeTiles', 4));
    const target = k.rt.fx.nearest(pl.x, pl.y, range);
    const dir = target ? this.dirOf(target.x - pl.x, target.y - pl.y) : this.dirOf(dx, dy);
    const side = i === 0 ? 0 : 1;
    const from = { x: pl.x + dir.y * TILE * 0.5 * side, y: pl.y - dir.x * TILE * 0.5 * side };
    k.rt.art.once(BUILD_ART.FULLMOON, from.x, from.y, { scaleMult: PLAYER_RENDER_SCALE });
    const hits = k.cloneLine(from, dir, range, (T(k.p(moon, 'widthTiles', 1)) * 1) / 2, k.p(moon, 'damageMult', 1.2));
    for (const m of hits) this.moonHit.set(m, k.now);
    if (hits.length > 0) k.rt.combat.restoreResource({ kenkiStage: k.p(moon, 'kenkiStage', 0.34) });
    k.fire('mangetsu', 'clone', { hits: hits.length, second: i > 0 });
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
        k.ring(
          { x: pl.x, y: pl.y - HIT_ORIGIN_UP_PX },
          T(k.p(back, 'radiusTiles', 1.5)),
          k.p(back, 'damageMult', 0.6),
          BUILD_FX.COLOR.SPIN,
        );
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
    const crack = k.rt.rule('unblockableCrack');
    if (crack && !died && p.buildMove === 'unblockable') {
      k.rt.combat.crackMob(mob, k.p(crack, 'ms', 3000));
      k.fire('k_kabutoCrack', 'crack');
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
    // 칼집 되돌림: 발도로 쓰러뜨림 → 검기 한 단
    const refund = k.rt.rule('iaiKillRefund');
    if (refund && k.now - this.iaiAt <= k.p(refund, 'windowMs', 600)) {
      k.rt.combat.restoreResource({ kenkiStage: k.p(refund, 'kenkiStage', 1) });
      k.fire('k_iaiRefund', 'refund');
    }
    // 달빛 잇기: 달 분신이 벤 적이 쓰러짐 → 다음 적에게 옮겨 벤다
    const relay = k.rt.rule('moonRelay');
    const hitAt = this.moonHit.get(mob);
    this.moonHit.delete(mob);
    if (relay && hitAt !== undefined && k.now - hitAt <= 600) {
      const next = k.rt.fx.nearest(at.x, at.y, T(k.p(relay, 'rangeTiles', 4)), new Set([mob]));
      if (next)
        k.g.time.delayedCall(120, () => {
          if (!k.g.scene.isActive() || !next.active) return;
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
  }
}
