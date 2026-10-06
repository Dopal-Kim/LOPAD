/**
 * 대검 갈래 (60라운드 6-1 — BranchStrikes 에서 분리): 차지 균열(58 Q3, 모든 갈래 공통)에 갈래 효과를 더한다.
 * 1단 파쇄(균열 그림 1:1 교체·탄 지움)·중압(균열 대신 원형 진동) / 2단 지진(끝에서 3갈래)·반향(퍼펙트 가드 균열 반격)·
 * 거인(차지 4단 — 57 Q43, 진동 반경 5칸)·울혈(그로기 울분·폭발). (옛 각성 산붕 '4타 충격파' mountainFall 은 61 G 에서 규칙이 없어져 61 단계 5 에 코드도 뺐다)
 * 그림 (계약 art §20·§21): `greatsword_shatter_crack_t1~5`·`_snuff` · `greatsword_quake_ring`(lv1~3)·`greatsword_giant_ring`(lv4) ·
 * `greatsword_quake_fork` · `greatsword_echo_counter` · `greatsword_congest_aura`·`_burst`.
 */
import { BUILD_ART, BUILD_FX, DEPTH, TILE } from '../../../../core/Constants';
import { EventBus, Events, type PlayerAttackPayload, type PlayerSkillPayload } from '../../../../core/EventBus';
import type { Mob } from '../../../../objects/Mob';
import type { Projectile } from '../../../../objects/Projectile';
import { param, type ActiveRule } from '../../../../systems/build/buildMods';
import type { FxHandle } from '../../../../systems/fx/fx';
import { artScale } from '../../../../systems/sprites/spriteDefs';
import { PLAYER_RENDER_SCALE } from '../../../../systems/weapon/playerScale';
import { T, type BranchKit, type Dir } from './BranchKit';

/** 원형 진동 시트의 단계 행 반경 (그림 도트) */
type RingSheet = { radiusPxByStage?: Record<string, number>; radiusPx?: number };

export class GreatswordBranch {
  /** 산을 진 자 보스별 쿨 */
  private readonly bossStunAt = new Map<Mob, number>();
  private congestFx: FxHandle | null = null;

  constructor(private readonly k: BranchKit) {}

  /**
   * 대검 차지 균열 (58 Q3, CrackLineStrikes 가 판정 순간 부른다 — 갈래별 충격파 교체 지점):
   * 중압 = 기본 균열 대신 원형 진동(skip) · 파쇄 = 같은 tN 을 shatter 시트로 1:1 교체 + 균열 위 적 탄 지움 ·
   * 지진·각성 = 끝에서 3갈래 · 산을 진 자 = 최대 단계 보스 경직. 반환 sheet = 바꿔 그릴 균열 시트 (없으면 null)
   */
  onCrackLine(
    p: PlayerAttackPayload,
    origin: { x: number; y: number },
    dir: Dir,
    tiles: number,
    lengthPx: number,
  ): { skip: boolean; sheet: string | null } {
    const k = this.k;
    const g = k.g;
    const rt = k.rt;
    const cl = p.crackLine;
    if (!cl) return { skip: false, sheet: null };
    const stageIdx = Math.max(0, cl.stage - 1);
    if (rt.hasBranch('weight')) {
      this.quakeRing(origin, stageIdx, cl.stage);
      return { skip: true, sheet: null };
    }
    let sheet: string | null = null;
    if (rt.hasBranch('crush')) {
      const prefix = k.mpStr('crush', 'crackSheet');
      const id = prefix && tiles > 0 ? `${prefix}${Math.min(5, Math.max(1, tiles))}` : null;
      sheet = id && g.fx.has(id) ? id : null;
      const road = rt.rule('splitRoad');
      // 앞머리를 따라 몇 번 쓸어 지운다 (갈라진 길이면 반사)
      const sweeps = 4;
      for (let i = 0; i <= sweeps; i++)
        g.time.delayedCall((i * 320) / sweeps, () => {
          if (g.scene.isActive())
            this.clearShotsOnLine(origin, dir, (lengthPx * (i + 1)) / (sweeps + 1), cl.halfWidthPx, Boolean(road));
        });
      if (road) rt.combat.splitRoadUntil = k.now + param(road, 'ms');
    }
    const end = { x: origin.x + dir.x * lengthPx, y: origin.y + dir.y * lengthPx };
    const quake = rt.rule('quake') ?? rt.rule('allSplit');
    if (quake && lengthPx > 0) {
      const deg = param(quake, 'splitDeg', 25);
      // 60 Q3 아트 제안 채택: 갈래 각 2칸 (데이터 lengthTiles)
      const qlen = T(param(quake, 'lengthTiles', 2));
      g.time.delayedCall(param(quake, 'delayMs', 260), () => {
        if (!g.scene.isActive()) return;
        // greatsword_quake_fork: 균열 앞머리가 멈춘 끝점에 그 균열 각도로 1회 (그리면 3갈래 윤곽 대신)
        k.effect('quake', 'fork');
        const forkDrawn = rt.art.once(BUILD_ART.QUAKE_FORK, end.x, end.y, {
          angle: Math.atan2(dir.y, dir.x),
          depth: DEPTH.FX_GROUND,
          scaleMult: PLAYER_RENDER_SCALE,
        });
        for (const sgn of [-1, 0, 1]) {
          const a = Math.atan2(dir.y, dir.x) + (sgn * deg * Math.PI) / 180;
          k.line(
            end.x,
            end.y,
            { x: Math.cos(a), y: Math.sin(a) },
            qlen,
            cl.halfWidthPx,
            param(quake, 'damageMult', 0.6),
            'quake',
            { outline: !forkDrawn },
          );
        }
      });
    }
    const bear = rt.rule('bossStun');
    if (bear && cl.stage >= 3)
      for (const m of rt.fx.inLine(origin.x, origin.y, dir.x, dir.y, lengthPx, cl.halfWidthPx)) this.bossStun(m, bear);
    k.last = { move: 'crack', tiles, sheet, t: Math.round(k.now) };
    return { skip: false, sheet };
  }

  /** 균열 위 적 탄: 지움 (갈라진 길이면 반사) */
  private clearShotsOnLine(
    start: { x: number; y: number },
    dir: Dir,
    len: number,
    half: number,
    reflect: boolean,
  ): void {
    const k = this.k;
    for (const child of k.g.projectiles.getChildren()) {
      const pr = child as Projectile;
      if (!pr.active || pr.reflected || pr.owner !== 'enemy') continue;
      const dx = pr.x - start.x;
      const dy = pr.y - start.y;
      const along = dx * dir.x + dy * dir.y;
      if (along < 0 || along > len || Math.abs(dx * dir.y - dy * dir.x) > half + 4) continue;
      if (reflect) {
        pr.reflect(1);
        // 61 단계 5 (P13) 개성 '갈라진 길' 발동 (음향 TRAIT_PROC)
        k.rt.traits.moves.fx('splitRoad', pr, { fallbacks: ['katana_whirl_reflect', 'hit_spark'] });
        k.effect('splitRoad', 'reflect');
      } else {
        // 파쇄: 균열에 삼켜진 탄 자리 greatsword_shatter_snuff (+ 음향 gs_shatter_snuff)
        const snuff = k.mpStr('crush', 'snuffFx');
        if (snuff && k.g.fx.has(snuff)) k.g.fx.play(snuff, pr.x, pr.y, { depth: DEPTH.HIT_FX });
        EventBus.emit(Events.PLAYER_SKILL, {
          weapon: 'greatsword',
          move: 'crack',
          phase: 'snuff',
        } satisfies PlayerSkillPayload);
        pr.deactivate();
      }
    }
  }

  /**
   * 중압 원형 진동 (+ 짓눌린 숨 울분 · 술독 짓누르기 웅덩이 모으기). 거인 차지 4단(57 Q43)이면 반경 = ringRadiusTiles(5칸)·
   * 그림 `greatsword_giant_ring`(행 lv4). 음향(60 Q40): 1~3단 = `BRANCH_EFFECT{branch:weight,effect:ring,stack:단}` → gs_quake_ring ·
   * 거인 4단 = 이벤트 없음 (charge_slam_lv4 하나만)
   */
  private quakeRing(at: { x: number; y: number }, stageIdx: number, stage = stageIdx + 1): void {
    const k = this.k;
    const g = k.g;
    const rt = k.rt;
    const id = 'weight';
    const giant = rt.rule('giant');
    const lv4 = Boolean(giant) && stage >= 4;
    const r = lv4 ? T(param(giant!, 'ringRadiusTiles')) : T(k.mp(id, 'radiusTiles', stageIdx));
    if (!lv4) k.effect(id, 'ring', Math.min(3, Math.max(1, stage)));
    const pull = T(k.mp(id, 'pullTiles'));
    // fx greatsword_quake_ring (행 lv1~3 = 차지 단계, 중심 slam_point, 바닥 깊이) — 그림 반경에 판정 반경을 맞춘다
    const ringId = lv4 ? BUILD_ART.GIANT_RING : k.mpStr(id, 'ringFx');
    const ringDef = ringId && g.fx.has(ringId) ? g.fx.sheet(ringId) : null;
    if (ringDef && ringId) {
      const row = lv4 ? 'lv4' : `lv${Math.min(3, Math.max(1, stage))}`;
      const rs = ringDef as unknown as RingSheet;
      const dots = rs.radiusPxByStage?.[row] ?? rs.radiusPx;
      const drawnR = dots !== undefined ? dots * artScale(ringDef) : r;
      g.fx.play(ringId, at.x, at.y, { dir: row, depth: DEPTH.FX_GROUND, scaleMult: drawnR > 0 ? r / drawnR : 1 });
    } else {
      rt.fx.ring(at.x, at.y, r, BUILD_FX.COLOR.RING);
      g.combat.drawShockwave(at.x, at.y, r);
    }
    const mult = lv4 ? param(giant!, 'ringMult', 1) * k.mp(id, 'damageMult') : k.mp(id, 'damageMult');
    const hits = rt.fx.inCircle(at.x, at.y, r);
    // 61 단계 5 (P13) 짓눌린 숨: 진동 한가운데로 끌어모아 서로 부딪치게 (끌어당기기 대신)
    const gather = rt.rule('ringGather');
    for (const m of hits) {
      const d = { x: at.x - m.x, y: at.y - m.y };
      const died = k.strike(
        m,
        k.payload(at.x, at.y, { x: -d.x, y: -d.y }, mult, 'quakeRing'),
        { x: -d.x, y: -d.y },
        {
          stunMs: k.mp(id, 'stunMs'),
        },
      );
      if (died || m.isBoss || !m.active) continue;
      if (gather) {
        const moves = rt.traits.moves;
        moves.chainLine(m, at, BUILD_FX.COLOR.RING, 240);
        moves.pull(m, at, Math.hypot(d.x, d.y) / TILE, 'g_crushedBreath', {
          stopTiles: 0.3,
          slamMult: param(gather, 'slamMult', 0.4),
          slamStunMs: param(gather, 'slamStunMs', 500),
        });
      } else m.shove(d.x, d.y, Math.min(pull, Math.hypot(d.x, d.y)), 140);
    }
    if (gather && hits.length > 0) {
      rt.traits.moves.fx('g_crushedBreath', at, { depth: DEPTH.FX_GROUND });
      k.effect('g_crushedBreath', 'gather', hits.length);
    }
    const jar = rt.rule('jarCrush');
    if (jar) {
      const pools = rt.fx.poolsNear(at.x, at.y, r);
      if (pools.length > 0) {
        for (const q of pools) {
          rt.traits.moves.chainLine({ x: q.rect.centerX, y: q.rect.centerY }, at, BUILD_FX.COLOR.LIQUOR, 320);
          q.until = k.now;
        }
        k.effect('jarCrush', 'gather', pools.length);
        const big = rt.fx.liquorPool(at.x, at.y, T(param(jar, 'radiusTiles')), 8000);
        const burstR = T(param(jar, 'burstRadiusTiles'));
        big.spec.onIgnite = () => {
          if (!rt.traits.moves.fx('jarCrush', at, { part: 'burst', fallbacks: ['fire_bottle_burst'] }))
            rt.fx.ring(at.x, at.y, burstR, BUILD_FX.COLOR.BURN);
          k.effect('jarCrush', 'burst');
          for (const m of rt.fx.inCircle(at.x, at.y, burstR))
            rt.fx.damage(m, param(jar, 'burstMult'), { dirX: 0, dirY: 0 });
        };
      }
    }
    k.last = { move: 'quakeRing', r, stage, hits: hits.length, t: Math.round(k.now) };
  }

  private bossStun(m: Mob, r: ActiveRule): void {
    if (!m.isBoss || !m.active) return;
    const k = this.k;
    const at = this.bossStunAt.get(m) ?? -Infinity;
    if (k.now - at < param(r, 'cooldownMs')) return;
    this.bossStunAt.set(m, k.now);
    m.stun(k.now, param(r, 'stunMs'), 'hit');
    k.rt.record('bossStun');
  }

  /** 반향: 퍼펙트 가드 순간 울분 30% 소모 → 막은 방향 균열 반격 (greatsword_echo_counter — 오른쪽 = 막은 방향) */
  resonance(dx: number, dy: number, mult: number): void {
    const k = this.k;
    const r = k.rt.rule('resonance');
    const gr = k.g.player.gauges.grudge;
    if (!r || !gr) return;
    const cost = gr.max * param(r, 'grudgeCost');
    if (gr.value < cost) return;
    gr.value -= cost;
    const pl = k.g.player;
    const len = Math.hypot(dx, dy) || 1;
    const dir = { x: dx / len, y: dy / len };
    const counter = 1 + k.rt.stat('perfectCounterMult');
    k.effect('resonance', 'counter');
    const drawn = k.rt.art.once(BUILD_ART.ECHO_COUNTER, pl.x, pl.y, {
      angle: Math.atan2(dir.y, dir.x),
      scaleMult: PLAYER_RENDER_SCALE,
    });
    k.line(
      pl.x,
      pl.y,
      dir,
      T(param(r, 'lengthTiles')),
      T(param(r, 'widthTiles', 1)) / 2,
      param(r, 'damageMult') * mult * counter,
      'resonance',
      { outline: !drawn },
    );
    k.rt.record('resonance');
  }

  /** 가드로 막음 (각성 산붕 반향: 일반 가드도 울분 반격 50% — 같은 프레임 퍼펙트면 건너뜀) */
  onGuardBlock(): void {
    const k = this.k;
    const echo = k.rt.rule('guardEcho');
    if (echo && k.g.player.defense.lastOutcome !== 'perfect') {
      const f = k.g.player.facingVec;
      this.resonance(f.x, f.y, param(echo, 'mult', 0.5));
    }
  }

  /**
   * 울혈: 그로기 진입 울분 +50% (그로기 동안 greatsword_congest_aura) · 그로기가 풀릴 때 울분 가득이면 자동 진동 폭발
   * (60 Q3 아트 제안 채택: 반경 2.25칸 — 데이터 burstRadiusTiles, greatsword_congest_burst 반지름 144 도트)
   */
  onResource(event: string): void {
    const k = this.k;
    const r = k.rt.rule('clot');
    const gr = k.g.player?.gauges.grudge;
    if (!r || !gr) return;
    const pl = k.g.player;
    if (event === 'groggy') {
      gr.value = Math.min(gr.max, gr.value + gr.max * param(r, 'grudgeOnGroggy'));
      k.effect('clot', 'hold');
      if (k.g.fx.has(BUILD_ART.CONGEST_AURA))
        this.congestFx = k.g.fx.play(BUILD_ART.CONGEST_AURA, pl.x, pl.y, {
          follow: pl,
          depthOffset: -DEPTH.OVERLAY_STEP,
          scaleMult: PLAYER_RENDER_SCALE,
        });
    }
    if (event === 'recovered') {
      k.g.fx.stop(this.congestFx, 0, true);
      this.congestFx = null;
      k.effect('clot', gr.full ? 'burst' : 'end');
    }
    if (event === 'recovered' && gr.full) {
      gr.value = 0;
      const rad = T(param(r, 'burstRadiusTiles'));
      const sheet = k.g.fx.sheet(BUILD_ART.CONGEST_BURST);
      const dots = (sheet as unknown as RingSheet | null)?.radiusPx;
      const drawnR = sheet && dots ? dots * artScale(sheet) : 0;
      const drawn = k.rt.art.once(BUILD_ART.CONGEST_BURST, pl.x, pl.y, { scaleMult: drawnR > 0 ? rad / drawnR : 1 });
      if (!drawn) {
        k.rt.fx.ring(pl.x, pl.y, rad, BUILD_FX.COLOR.RING);
        k.g.combat.drawShockwave(pl.x, pl.y, rad);
      }
      for (const m of k.rt.fx.inCircle(pl.x, pl.y, rad))
        k.strike(m, k.payload(pl.x, pl.y, { x: m.x - pl.x, y: m.y - pl.y }, param(r, 'burstMult'), 'clot'), {
          x: m.x - pl.x,
          y: m.y - pl.y,
        });
      k.rt.record('clotBurst');
    }
  }

  destroy(): void {
    this.k.g.fx.stop(this.congestFx, 0, false);
    this.congestFx = null;
  }
}
