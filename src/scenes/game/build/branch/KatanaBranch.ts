/**
 * 칼 갈래 (60라운드 6-1 — BranchStrikes 에서 분리): 1단 선풍(회전 베기)·투구가르기(가드 불가 내려베기) /
 * 2단 회오리(지속 회전·탄 반사)·잔월(달 궤적)·일도양단(균열·처형)·명경(검기 고리·패링 분신, 검기 통합 뒤 켬).
 * 그림 (계약 art §20·§21): `katana_spin`·`katana_spin_ready`·`katana_guardbreak` · `katana_whirl_loop`·`katana_whirl_reflect` ·
 * `katana_moon_trail` · `katana_cleave_crack`·`katana_execute` · `katana_mirror_ki`·`katana_mirror_parry`. 없으면 윤곽.
 */
import { BUILD_ART, BUILD_FX, DEPTH, TILE } from '../../../../core/Constants';
import { EventBus, Events, type PlayerSkillPayload } from '../../../../core/EventBus';
import { gameState } from '../../../../core/GameState';
import type { Mob } from '../../../../objects/Mob';
import type { Projectile } from '../../../../objects/Projectile';
import { param } from '../../../../systems/build/buildMods';
import type { FxHandle } from '../../../../systems/fx/fx';
import { facingOf } from '../../../../systems/sprites/spriteDefs';
import { PLAYER_RENDER_SCALE } from '../../../../systems/weapon/playerScale';
import { HIT_ORIGIN_UP_PX } from '../../shared';
import { sheetLoopRange } from '../BuildArt';
import { T, type BranchKit, type Dir } from './BranchKit';

/** 칼 회전 베기 판정 뒤 다시 도는 소리 속도 (음향 권장 1.05) */
const SECOND_SPIN_VARIANT = 2;

export class KatanaBranch {
  /** 회오리 지속 회전 */
  private vortex: { until: number; nextAt: number; moveMult: number } | null = null;
  private whirlFx: FxHandle | null = null;

  constructor(private readonly k: BranchKit) {}

  private skill(p: Omit<PlayerSkillPayload, 'weapon'>): void {
    EventBus.emit(Events.PLAYER_SKILL, { weapon: 'katana', ...p } satisfies PlayerSkillPayload);
  }

  /** 홀드 완료 반짝임 (katana_spin_ready — 칼끝 앵커 대신 조준 쪽 칼 높이 근사) · 시트가 없으면 몸 번쩍임 */
  onReady(move: string, dir: Dir): void {
    const pl = this.k.g.player;
    const ready = move === 'spin' ? (this.k.mpStr('iai', 'readyFx') ?? 'katana_spin_ready') : null;
    if (move === 'spin') this.skill({ move: 'spin', phase: 'ready' });
    if (!this.k.playFx(ready, pl.x + dir.x * TILE, pl.y - TILE * 1.5 + dir.y * TILE * 0.5, dir, { row: 'any' }))
      pl.flashColor(BUILD_FX.HOLD_READY_COLOR);
  }

  /** 칼 선풍: 회전 베기 (선딜 → 360° 원 · 검기 1단 소모 시 2회전) */
  spin(dir: Dir): void {
    const k = this.k;
    const g = k.g;
    const rt = k.rt;
    const pl = g.player;
    const id = 'iai';
    const windup = k.mp(id, 'windupMs');
    const recover = k.mp(id, 'recoverMs');
    let radius = T(k.mp(id, 'radiusTiles')) * k.hitScale();
    // 술 회오리 (이중 개성): 반경 안 웅덩이를 빨아들여 반경 +0.5칸 (최대 +1.5), 술불이면 술불 판정 추가
    const whirl = rt.rule('liquorWhirl');
    let fireExtra = 0;
    if (whirl) {
      const pools = rt.fx.poolsNear(pl.x, pl.y, T(param(whirl, 'pullTiles')));
      radius += Math.min(T(param(whirl, 'maxTiles')), pools.length * T(param(whirl, 'perPoolTiles')));
      if (pools.some((q) => g.pools.burning(q))) fireExtra = param(whirl, 'fireMult');
      for (const q of pools) q.until = k.now;
    }
    const res = pl.resource;
    if (res?.def.kind === 'stamina') res.spend(res.max * k.mp(id, 'staminaRatio'), k.now);
    const kg = pl.gauges.kenki;
    const kenkiSpent = kg && kg.stage >= k.mp(id, 'kenkiStages') && k.mp(id, 'kenkiStages') > 0;
    if (kenkiSpent && kg) kg.value = Math.max(0, kg.value - kg.def.perStage * k.mp(id, 'kenkiStages'));
    pl.setAction('skill', k.now + windup + recover);
    k.setBusy(windup + recover);
    k.body(id, 2, dir, windup + recover, k.mp(id, 'releaseFrame'));
    const mult = k.mp(id, 'damageMult') * gameState.weapon.reinforceMult;
    // fx katana_spin: 뗀 순간(몸 releaseFrame) 1회 — fx f1 = 판정. 2회전은 다시 재생 (아트 노트)
    const art = gameState.weapon.nodes[0]?.art?.fx?.[0];
    const drawn = k.playFx(art, pl.x, pl.y, dir, { follow: true });
    this.skill({ move: 'spin', phase: 'release' });
    const hitAll = (m: number, replay = false) => {
      if (!g.scene.isActive()) return;
      const p = k.payload(pl.x, pl.y, dir, m, 'spin');
      if (replay) {
        k.playFx(art, pl.x, pl.y, dir, { follow: true });
        this.skill({ move: 'spin', phase: 'release', variant: SECOND_SPIN_VARIANT });
      }
      // 판정 원점 = 발 위 (아트 hitOriginInFrame — 피벗 위 40 도트)
      const oy = pl.y - HIT_ORIGIN_UP_PX;
      if (!drawn) rt.fx.ring(pl.x, oy, radius, BUILD_FX.COLOR.SPIN);
      const hit = rt.fx.inCircle(pl.x, oy, radius);
      let kills = 0;
      for (const mob of hit) {
        const d = { x: mob.x - pl.x, y: mob.y - pl.y };
        if (k.strike(mob, p, d)) kills += 1;
        if (fireExtra > 0 && mob.active) rt.fx.damage(mob, fireExtra, { dirX: d.x, dirY: d.y, tick: true });
      }
      this.reflectShots(pl.x, pl.y, radius);
      // 피바람 (이중 개성): 처치마다 회전 판정 1회 추가 (최대 +3)
      const gale = rt.rule('spinChain');
      if (gale && kills > 0) {
        const n = Math.min(kills, param(gale, 'maxExtra', 3));
        for (let i = 1; i <= n; i++) g.time.delayedCall(param(gale, 'delayMs', 160) * i, () => hitAll(m * 0.7));
      }
      // 잔월: 검기를 쓴 회전이 지나간 자리에 달 궤적
      if (kenkiSpent) this.moonTrail(pl.x, pl.y, radius);
    };
    g.time.delayedCall(windup, () => hitAll(mult));
    if (kenkiSpent)
      g.time.delayedCall(windup + k.mp(id, 'secondSpinDelayMs'), () => hitAll(k.mp(id, 'secondSpinMult'), true));
    k.last = { move: 'spin', radius, kenki: kenkiSpent, t: Math.round(k.now) };
    rt.record('spin');
  }

  /** 회전 판정 안 적 탄 반사 (회오리) — 되받아친 탄 자리 katana_whirl_reflect (오른쪽 = 되돌아 나가는 방향) */
  private reflectShots(x: number, y: number, r: number): void {
    const k = this.k;
    if (!k.rt.rule('vortex')) return;
    for (const child of k.g.projectiles.getChildren()) {
      const pr = child as Projectile;
      if (!pr.active || pr.reflected || pr.owner !== 'enemy') continue;
      if (Math.hypot(pr.x - x, pr.y - y) > r) continue;
      pr.reflect(1);
      this.skill({ move: 'whirl', phase: 'reflect' });
      const v = pr.body.velocity;
      k.rt.art.once(BUILD_ART.WHIRL_REFLECT, pr.x, pr.y, {
        angle: Math.atan2(v.y, v.x),
        scaleMult: PLAYER_RENDER_SCALE,
      });
    }
  }

  /** 회오리: 홀드를 유지하면 지속 회전 (초당 hitsPerSec 타 ×damageMult, 이동 ×moveMult, 기력 초당 소모) */
  vortexStart(): void {
    const k = this.k;
    const r = k.rt.rule('vortex');
    if (!r || this.vortex) return;
    this.vortex = { until: k.now + param(r, 'maxMs'), nextAt: k.now, moveMult: param(r, 'moveMult') };
    this.skill({ move: 'whirl', phase: 'hold' });
    // katana_whirl_loop: 홀드 끝까지 주인공을 따라 반복 (손을 떼면 끔)
    const pl = k.g.player;
    if (k.g.fx.has(BUILD_ART.WHIRL_LOOP))
      this.whirlFx = k.g.fx.play(BUILD_ART.WHIRL_LOOP, pl.x, pl.y, {
        follow: pl,
        depthOffset: DEPTH.OVERLAY_STEP * 2,
        scaleMult: PLAYER_RENDER_SCALE * k.hitScale(),
      });
  }

  vortexEnd(): void {
    if (this.vortex) this.skill({ move: 'whirl', phase: 'end' });
    this.vortex = null;
    this.k.g.fx.stop(this.whirlFx, 0, false);
    this.whirlFx = null;
  }

  private vortexTick(now: number): void {
    const k = this.k;
    const v = this.vortex;
    const r = k.rt.rule('vortex');
    if (!v || !r) return;
    const pl = k.g.player;
    if (now >= v.until || !pl.active) {
      this.vortexEnd();
      return;
    }
    pl.setAction('skill', now + 120);
    pl.skillMoveMult = v.moveMult;
    k.setBusy(120);
    if (now < v.nextAt) return;
    v.nextAt = now + 1000 / Math.max(1, param(r, 'hitsPerSec', 4));
    const res = pl.resource;
    if (res?.def.kind === 'stamina') res.spend((res.max * param(r, 'staminaPerSec')) / param(r, 'hitsPerSec', 4), now);
    const radius = T(k.mp('iai', 'radiusTiles')) * k.hitScale();
    const dir = pl.facingVec;
    const p = k.payload(pl.x, pl.y, { x: dir.x, y: dir.y }, param(r, 'damageMult'), 'spin');
    if (!k.g.fx.isActive(this.whirlFx)) k.rt.fx.ring(pl.x, pl.y, radius, BUILD_FX.COLOR.SPIN, 160);
    for (const mob of k.rt.fx.inCircle(pl.x, pl.y, radius)) k.strike(mob, p, { x: mob.x - pl.x, y: mob.y - pl.y });
    this.reflectShots(pl.x, pl.y, radius);
  }

  /**
   * 잔월: 달 궤적 (trailMs 동안 tickMs 마다 ×tickMult) — katana_moon_trail 을 원 둘레 48 도트 간격으로, 진행(접선) 각도로 회전,
   * 바닥 깊이. f0~1 생김 → f2~5 루프 → 끝나면 f6~8 사라짐 (시트 loopRange)
   */
  private moonTrail(x: number, y: number, radius: number): void {
    const k = this.k;
    const r = k.rt.rule('zangetsu');
    if (!r) return;
    const ms = param(r, 'trailMs');
    const tick = param(r, 'tickMs');
    k.effect('zangetsu', 'trail');
    if (!this.placeMoonTrail(x, y, radius, ms)) k.rt.fx.zone(x, y, radius * 2, radius * 2, BUILD_FX.COLOR.MOON, ms);
    for (let t = tick; t <= ms; t += tick)
      k.g.time.delayedCall(t, () => {
        if (!k.g.scene.isActive()) return;
        for (const m of k.rt.fx.inCircle(x, y, radius))
          k.rt.fx.damage(m, param(r, 'tickMult'), { dirX: 0, dirY: 0, tick: true });
      });
  }

  private placeMoonTrail(x: number, y: number, radius: number, ms: number): boolean {
    const g = this.k.g;
    const id = BUILD_ART.MOON_TRAIL;
    if (!g.fx.has(id)) return false;
    const range = sheetLoopRange(g.fx.sheet(id));
    const n = Math.max(6, Math.round((Math.PI * 2 * radius) / BUILD_ART.MOON_TRAIL_GAP_PX));
    for (let i = 0; i < n; i++) {
      const a = (i / n) * Math.PI * 2;
      g.fx.play(id, x + Math.cos(a) * radius, y + Math.sin(a) * radius, {
        angle: a + Math.PI / 2,
        depth: DEPTH.FX_GROUND,
        belowLighting: false,
        durationMs: ms,
        hooks: false,
        ...(range ? { loopRange: range } : {}),
      });
    }
    return true;
  }

  /** 칼 투구가르기: 가드 불가 내려베기 (선딜 백열 → 정면 쐐기, 경직, 검기 1단 = 치명 확정) */
  unblockable(dir: Dir): void {
    const k = this.k;
    const g = k.g;
    const rt = k.rt;
    const pl = g.player;
    const id = 'batto';
    const windup = k.mp(id, 'windupMs');
    const recover = k.mp(id, 'recoverMs');
    const res = pl.resource;
    if (res?.def.kind === 'stamina') res.spend(res.max * k.mp(id, 'staminaRatio'), k.now);
    const kg = pl.gauges.kenki;
    const crit = Boolean(kg && k.mp(id, 'kenkiStages') > 0 && kg.stage >= k.mp(id, 'kenkiStages'));
    if (crit && kg) kg.value = Math.max(0, kg.value - kg.def.perStage * k.mp(id, 'kenkiStages'));
    pl.setAction('skill', k.now + windup + recover);
    k.setBusy(windup + recover);
    k.body(id, 3, dir, windup + recover, k.mp(id, 'releaseFrame'));
    // fx katana_guardbreak: 뗀 순간 1회 (뗀 자리 고정) — 없으면 윤곽
    const drawnGb = k.playFx(gameState.weapon.nodes[0]?.art?.fx?.[0], pl.x, pl.y, dir);
    if (!drawnGb) pl.flashColor(BUILD_FX.HOLD_READY_COLOR);
    this.skill({ move: 'guardbreak', phase: 'strike', impactDelayMs: windup });
    const len = T(k.mp(id, 'lengthTiles')) * k.hitScale();
    const half = (T(k.mp(id, 'widthTiles')) * k.hitScale()) / 2;
    const helm = rt.rule('helmBreak');
    const release = { x: pl.x, y: pl.y };
    g.time.delayedCall(windup, () => {
      if (!g.scene.isActive()) return;
      const x0 = pl.x;
      const y0 = pl.y - HIT_ORIGIN_UP_PX;
      if (!drawnGb) rt.fx.lineFx(x0, y0, dir.x, dir.y, len, half, BUILD_FX.COLOR.UNBLOCKABLE);
      let refunded = false;
      for (const mob of rt.fx.inLine(x0, y0, dir.x, dir.y, len, half)) {
        const stunned = mob.isStunned(k.now);
        const mult =
          k.mp(id, 'damageMult') * gameState.weapon.reinforceMult * (helm && stunned ? param(helm, 'mult') : 1);
        if (this.execute(mob, dir)) continue;
        k.strike(mob, k.payload(x0, y0, dir, mult, 'unblockable', { forceCrit: crit, ignoreGuard: true }), dir, {
          stunMs: k.mp(id, 'stunMs'),
        });
        if (helm && stunned && !refunded && res?.def.kind === 'stamina') {
          refunded = true;
          res.value = Math.min(res.max, res.value + res.max * param(helm, 'staminaRefund'));
        }
      }
      // 일도양단: 끝에서 직선 균열 (60 Q3 아트 제안 4칸 채택 — 데이터 crackTiles) · katana_cleave_crack 은 뗀 자리·4행, 판정 + 40ms
      const cl = rt.rule('cleave');
      if (cl) {
        const ex = x0 + dir.x * len;
        const ey = y0 + dir.y * len;
        const cl2 = T(param(cl, 'crackTiles'));
        const ch = T(param(cl, 'crackWidthTiles', 1)) / 2;
        const crackFx = () =>
          k.playFx(BUILD_ART.CLEAVE_CRACK, release.x, release.y, dir, {
            row: facingOf(dir.x, dir.y, pl.facingDir),
            depth: DEPTH.FX_GROUND,
          });
        const delay = param(cl, 'fxDelayMs', 40);
        if (!g.fx.has(BUILD_ART.CLEAVE_CRACK)) rt.fx.lineFx(ex, ey, dir.x, dir.y, cl2, ch, BUILD_FX.COLOR.CRACK);
        else g.time.delayedCall(delay, () => g.scene.isActive() && crackFx());
        // 음향 katana_cleave_crack = 균열 fx 시작(판정 + fxDelayMs)에 — manifest '가드 불가 내려베기 재생 + 140ms'
        this.skill({ move: 'guardbreak', phase: 'cleave', impactDelayMs: delay });
        for (const mob of rt.fx.inLine(ex, ey, dir.x, dir.y, cl2, ch))
          if (!this.execute(mob, dir))
            k.strike(mob, k.payload(ex, ey, dir, param(cl, 'crackMult'), 'unblockable', { ignoreGuard: true }), dir);
      }
    });
    k.last = { move: 'unblockable', crit, len, t: Math.round(k.now) };
    rt.record('unblockable');
  }

  /** 일도양단 처형: HP 비율 이하 일반 적 즉시 처치 (보스·엘리트는 피해 ×bossMult). 처리했으면 true */
  private execute(mob: Mob, dir: Dir): boolean {
    const k = this.k;
    const rt = k.rt;
    const cl = rt.rule('cleave');
    if (!cl || !mob.active) return false;
    const neck = rt.rule('neckCut');
    const ratio = neck ? param(neck, 'executeRatio') : param(cl, 'executeRatio');
    if (mob.hp / mob.maxHp > ratio) return false;
    if (mob.isBoss || mob.elite) {
      k.strike(
        mob,
        k.payload(mob.x, mob.y, dir, param(cl, 'bossMult') * k.mp('batto', 'damageMult'), 'unblockable', {
          ignoreGuard: true,
        }),
        dir,
      );
      return true;
    }
    rt.art.onceAtMob(BUILD_ART.EXECUTE, mob, { scaleMult: PLAYER_RENDER_SCALE });
    k.effect('cleave', 'execute');
    rt.fx.callout(BUILD_FX.TEXT.EXECUTE);
    rt.fx.raw(mob, mob.hp + 1, { dirX: dir.x, dirY: dir.y, heavy: true });
    if (neck) rt.combat.restoreResource({ kenkiStage: param(neck, 'kenkiStages', 1) });
    rt.record('execute');
    return true;
  }

  /** 명경 패링 (katana_mirror_parry — 오른쪽 = 공격이 들어온 쪽) */
  onParry(dx: number, dy: number): void {
    const k = this.k;
    if (!k.rt.rule('meikyo')) return;
    k.effect('meikyo', 'parry');
    const pl = k.g.player;
    k.rt.art.once(BUILD_ART.MIRROR_PARRY, pl.x + dx * TILE * 0.5, pl.y - HIT_ORIGIN_UP_PX + dy * TILE * 0.5, {
      angle: Math.atan2(dy, dx),
      scaleMult: PLAYER_RENDER_SCALE,
    });
  }

  /** 처치: 잔월 검기 1/3단 */
  onKill(): void {
    const z = this.k.rt.rule('zangetsu');
    if (z) this.k.rt.combat.restoreResource({ kenkiStage: param(z, 'killKenkiStage') });
  }

  update(now: number): void {
    this.vortexTick(now);
    // 명경: 검기 1단 이상이면 발밑 고리 루프 (행 = 단수 1~5)
    const art = this.k.rt.art;
    const kg = this.k.g.player?.gauges.kenki;
    if (this.k.rt.rule('meikyo') && kg && kg.stage > 0)
      art.playerLoop('mirror', BUILD_ART.MIRROR_KI, String(Math.min(5, kg.stage)), { below: true });
    else art.stopPlayerLoop('mirror');
  }

  debug(): Record<string, unknown> {
    return { vortex: Boolean(this.vortex) };
  }

  destroy(): void {
    this.vortexEnd();
  }
}
