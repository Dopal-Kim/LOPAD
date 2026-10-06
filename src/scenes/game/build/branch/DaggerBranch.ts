/**
 * 단검 갈래 (60라운드 6-1 — BranchStrikes 에서 분리): 1단 쌍격(낙인 기폭 분신 교차)·질풍(부채꼴 투척) /
 * 2단 난무(분신 상주)·출혈(기폭 → 출혈)·비도(5자루 + 박힌 단검 그림자 걸음)·열풍(과열 반전 — 57 Q43 과열 범위 ×2·화상·무적) /
 * 각성 백귀(기폭마다 분신 3체).
 * 그림 (계약 art §20·§21): `dagger_fan_throw`·`dagger_thrown` · `dagger_cross_clone` · `dagger_frenzy_clone_in`·`_out` ·
 * `dagger_brand_bleed`·`dagger_brand_hop` · `dagger_stuck_blade` · `dagger_hotwind_trail`·(`dagger_hotwind_burst` = 과열 폭발 교체) ·
 * `dagger_hundred_ghosts` · `dagger_gale_wind`(질풍 1단 연격 변화 — 이동 중 90ms 마다).
 */
import Phaser from 'phaser';
import { BUILD_ART, BUILD_FX, DEPTH, TILE } from '../../../../core/Constants';
import { EventBus, Events, type PlayerAttackPayload, type PlayerSkillPayload } from '../../../../core/EventBus';
import { gameState } from '../../../../core/GameState';
import type { Mob } from '../../../../objects/Mob';
import type { Projectile } from '../../../../objects/Projectile';
import { param } from '../../../../systems/build/buildMods';
import type { FxHandle } from '../../../../systems/fx/fx';
import { facingOf } from '../../../../systems/sprites/spriteDefs';
import { PLAYER_RENDER_SCALE } from '../../../../systems/weapon/playerScale';
import { sheetLoopRange } from '../BuildArt';
import { T, type BranchKit, type Dir } from './BranchKit';

/** 61 단계 5: 돌아오는 칼 (되돌아오는 단검 — 꿰인 적을 끌고 온다) */
const RETURN_TAG = 'returnKnife';

/** 비도: 박힌 단검 (그림 = dagger_stuck_blade 수명 시트, 없으면 작은 사각형) */
interface StuckKnife {
  x: number;
  y: number;
  until: number;
  gfx: Phaser.GameObjects.Rectangle | null;
  fx: FxHandle | null;
}

export class DaggerBranch {
  private throwReadyAt = -Infinity;
  private stuck: StuckKnife[] = [];
  /** 열풍 자국 루프 중 (음향 켜기·끄기) */
  private trailOn = false;
  private danceUntil = -Infinity;
  /** 난무 상주 분신 자리 (나타남·사라짐 그림) */
  private danceAt: { x: number; y: number; dir: string } | null = null;
  private galeNextAt = -Infinity;

  constructor(private readonly k: BranchKit) {}

  private skill(move: PlayerSkillPayload['move'], phase: PlayerSkillPayload['phase']): void {
    EventBus.emit(Events.PLAYER_SKILL, { weapon: 'dagger', move, phase } satisfies PlayerSkillPayload);
  }

  /** 질풍: 부채꼴 투척 (대쉬 직후 좌클릭) — 적중 시 낙인. 비도 5개·45° + 박힌 단검 */
  fanThrow(dir: Dir): void {
    const k = this.k;
    const g = k.g;
    const rt = k.rt;
    const pl = g.player;
    const id = 'gale';
    const now = k.now;
    if (now < this.throwReadyAt) return;
    const wind = rt.rule('windBlade');
    const fly = rt.rule('flyknife');
    const count = fly ? param(fly, 'count', 5) : wind ? param(wind, 'count', 5) : k.mp(id, 'count');
    const spread = fly ? param(fly, 'spreadDeg', 45) : k.mp(id, 'spreadDeg');
    this.throwReadyAt = now + k.mp(id, 'cooldownMs') - (wind ? param(wind, 'cooldownCutMs') : 0);
    const res = pl.resource;
    if (res?.kind === 'heat') res.heatBy(res.max * (k.mp(id, 'heat') / 100), now);
    const sm = rt.combat.shotMods();
    const speed = k.mp(id, 'speedTiles') * sm.speedMult;
    const life = (T(k.mp(id, 'rangeTiles')) / (speed * TILE)) * 1000 * (1 + rt.stat('projectileRangeMult'));
    const { dmg, crit } = g.combat.rollDamage(k.mp(id, 'damageMult'), false, 'dashAttack');
    const bottle = rt.rule('liquorThrow');
    const base = Math.atan2(dir.y, dir.x);
    const sprite = k.mpStr(id, 'projectile');
    // 몸 dagger_fan_throw (releaseFrame 시작 = 투사체 생성) · fx 는 그보다 조금 앞 (아트 spawnAtMs)
    k.body(id, 1, dir, 220);
    this.skill('fan_throw', 'release');
    g.time.delayedCall(k.mp(id, 'throwFxAtMs'), () => {
      if (g.scene.isActive()) k.playFx(k.mpStr(id, 'throwFx'), pl.x, pl.y, dir, { follow: true });
    });
    const release = () => {
      if (!g.scene.isActive()) return;
      for (let i = 0; i < count; i++) {
        const t = count === 1 ? 0 : i / (count - 1) - 0.5;
        const a = base + ((spread * Math.PI) / 180) * t;
        const isBottle = Boolean(bottle) && i === Math.floor(count / 2);
        const s = rt.fx.shot(pl.x + Math.cos(a) * 6, pl.y - 6 + Math.sin(a) * 6, Math.cos(a), Math.sin(a), dmg, {
          tag: isBottle ? 'bottle' : 'fanThrow',
          speedTiles: speed,
          lifeMs: life,
          pierce: sm.pierceAdd,
          crit,
          ...(isBottle ? { tint: BUILD_FX.COLOR.LIQUOR } : sprite ? { sprite } : { tint: BUILD_FX.COLOR.THROW }),
        });
        // 61 G 개성 '돌아오는 칼': 끝에 닿으면 손으로 되돌아오며 한 번 더 벤다
        const back = !isBottle && rt.rule('throwReturn');
        if (s && (fly || isBottle || back))
          s.onEnd = (shot) => {
            if (fly || isBottle) this.onThrowEnd(shot);
            if (back) this.returnKnife(shot, param(back, 'damageMult', 0.6));
          };
      }
    };
    const at = k.mp(id, 'releaseAtMs');
    if (at > 0) g.time.delayedCall(at, release);
    else release();
    k.last = { move: 'fanThrow', count, t: Math.round(now) };
    rt.record('fanThrow', count);
  }

  /** 돌아오는 칼: 끝난 자리에서 주인공 쪽으로 한 자루 */
  private returnKnife(shot: Projectile, mult: number): void {
    const k = this.k;
    const pl = k.g.player;
    if (!k.g.scene.isActive() || !pl) return;
    const dx = pl.x - shot.x;
    const dy = pl.y - shot.y;
    const d = Math.hypot(dx, dy);
    if (d < TILE * 0.5) return;
    const speed = k.mp('gale', 'speedTiles') || 12;
    const { dmg, crit } = k.g.combat.rollDamage(mult, false, 'other');
    const sprite = k.mpStr('gale', 'projectile');
    k.rt.fx.shot(shot.x, shot.y, dx, dy, dmg, {
      tag: RETURN_TAG,
      speedTiles: speed,
      lifeMs: (d / (speed * TILE)) * 1000,
      crit,
      ...(sprite ? { sprite } : { tint: BUILD_FX.COLOR.THROW }),
    });
    k.effect('d_galeReturn', 'return');
  }

  /** 던진 단검·술병이 끝남 (벽·사거리) — 비도 박힘 · 술병 웅덩이 */
  private onThrowEnd(shot: Projectile): void {
    if (shot.buildTag === 'bottle') this.bottleSplash(shot.x, shot.y);
    else this.stick(shot.x, shot.y, shot.body.velocity.x < 0);
  }

  /** 빌드 투사체 적중 */
  onShotHit(shot: Projectile, mob: Mob, died: boolean): void {
    // 61 단계 5 (P13) 돌아오는 칼: 되돌아오는 단검에 꿰인 적을 손 쪽으로 끌고 온다
    if (shot.buildTag === RETURN_TAG) {
      const back = this.k.rt.rule('throwReturn');
      if (!died) this.k.g.strikes.brands.onHit(mob, shot.body.velocity.x, shot.body.velocity.y);
      if (back && !died && mob.active) {
        const pl = this.k.g.player;
        this.k.rt.traits.moves.chainLine(mob, pl, BUILD_FX.COLOR.THROW, 220);
        this.k.rt.traits.moves.fx(
          'd_galeReturn',
          { x: mob.x, y: mob.y - 8 },
          {
            fallbacks: ['dagger_brand_hop'],
            flipX: pl.x > mob.x,
          },
        );
        this.k.rt.traits.moves.pull(mob, pl, param(back, 'dragTiles', 2), 'd_galeReturn', {
          stopTiles: 0.8,
          endStunMs: 300,
        });
        this.k.effect('d_galeReturn', 'drag');
      }
      return;
    }
    if (shot.buildTag !== 'fanThrow' && shot.buildTag !== 'bottle') return;
    if (!died) this.k.g.strikes.brands.onHit(mob, shot.body.velocity.x, shot.body.velocity.y);
    if (shot.buildTag === 'bottle') this.bottleSplash(mob.x, mob.y);
    else if (this.k.rt.rule('flyknife')) this.stick(mob.x, mob.y, shot.body.velocity.x < 0);
  }

  private bottleSplash(x: number, y: number): void {
    const k = this.k;
    const b = k.rt.rule('liquorThrow');
    if (!b) return;
    const pool = k.rt.fx.liquorPool(x, y, T(param(b, 'radiusTiles', 1)), 6000);
    k.rt.traits.moves.fx('liquorThrow', { x, y }, { fallbacks: ['fire_bottle_burst'], scale: 0.6 });
    k.effect('liquorThrow', 'splash');
    const res = k.g.player.resource;
    if (res?.kind === 'heat' && res.value >= res.max * param(b, 'fireHeat', 0.5)) k.g.pools.ignite(pool);
  }

  /** 박힌 단검 (dagger_stuck_blade: 세워 그림, 왼쪽으로 던졌으면 flipX · 박힘 → 루프 → 수명 끝에 부서짐) */
  private stick(x: number, y: number, flipX: boolean): void {
    const k = this.k;
    const fly = k.rt.rule('flyknife');
    if (!fly) return;
    const ms = param(fly, 'stuckMs');
    const g = k.g;
    const range = sheetLoopRange(g.fx.sheet(BUILD_ART.STUCK_BLADE));
    const fx = g.fx.has(BUILD_ART.STUCK_BLADE)
      ? g.fx.play(BUILD_ART.STUCK_BLADE, x, y, {
          flipX,
          depth: DEPTH.PICKUP,
          durationMs: ms,
          hooks: false,
          ...(range ? { loopRange: range } : {}),
        })
      : null;
    k.effect('flyknife', 'stick');
    const s = BUILD_FX.STUCK_KNIFE_PX;
    const gfx = fx ? null : g.add.rectangle(x, y, s, s, BUILD_FX.COLOR.THROW, 0.9).setDepth(DEPTH.PICKUP);
    this.stuck.push({ x, y, until: k.now + ms, gfx, fx });
  }

  /** 비도: 그림자 걸음이 박힌 단검으로 (가장 최근) — 쓰면 가속 +10%(61라운드: 과열이 없어져 식힘 → 가속). 없으면 null. 도착 그림은 shadowstep_ghost(MotionFx) */
  takeStuckKnife(): { x: number; y: number } | null {
    const k = this.k;
    const fly = k.rt.rule('flyknife');
    if (!fly || this.stuck.length === 0) return null;
    const knife = this.stuck.pop()!;
    this.removeKnife(knife);
    k.effect('flyknife', 'step');
    const res = k.g.player.resource;
    if (res?.kind === 'heat') res.heatBy(res.max * param(fly, 'heatRefund'), k.now);
    return { x: knife.x, y: knife.y };
  }

  private removeKnife(knife: StuckKnife): void {
    knife.gfx?.destroy();
    this.k.g.fx.finish(knife.fx);
  }

  /** 낙인 기폭 배율 (쌍격 +30%, 표식 6 +40%) */
  brandBurstMult(): number {
    const k = this.k;
    let m = 1;
    if (k.rt.hasBranch('twin')) m *= 1 + k.mp('twin', 'burstBonus');
    const det = k.rt.rule('markDetonate');
    if (det) m *= 1 + param(det, 'brandBurstMult');
    return m;
  }

  /** 출혈(2단 β): 기폭 즉시 비율 (나머지는 출혈) — 없으면 1 */
  brandImmediateRatio(): number {
    const r = this.k.rt.rule('brandBleed');
    return r ? param(r, 'immediate', 1) : 1;
  }

  /** 낙인 기폭 뒤 (BrandMarks.explode): 쌍격 분신 교차 · 쌍낙인 · 난무 · 출혈 · 각성 백귀 */
  onBrandBurst(mob: Mob, marks: number, dmg: number, died: boolean): void {
    const k = this.k;
    const g = k.g;
    const rt = k.rt;
    // 61 단계 5: 낙인 폭발로 쓰러진 적은 이미 파괴돼 바디가 없다 (발 자리 + 몸 절반 높이로)
    const at = mob.body ? { x: mob.body.center.x, y: mob.body.center.y } : { x: mob.x, y: mob.y - 8 };
    const pl = g.player;
    const back = { x: at.x - pl.x, y: at.y - pl.y };
    const bl = Math.hypot(back.x, back.y) || 1;
    // 출혈: 나머지를 출혈로 (dagger_brand_bleed — 출혈 동안 적 몸에 루프)
    const bleed = rt.rule('brandBleed');
    if (bleed && !died && mob.active) {
      const rest = dmg * (1 / Math.max(0.01, param(bleed, 'immediate', 1)) - 1);
      const ticks = Math.max(1, Math.round(param(bleed, 'bleedMs') / param(bleed, 'tickMs')));
      const fast = rt.rule('fastBleed');
      const tickMs = param(bleed, 'tickMs') * (fast ? param(fast, 'tickMult', 1) : 1);
      const ms = ticks * tickMs * (1 + rt.stat('dotDurationMult'));
      rt.dots.apply(mob, 'bleed', k.now, ms, tickMs, Math.max(1, Math.round(rest / ticks)));
      rt.art.timedOnMob('bleed', BUILD_ART.BRAND_BLEED, mob, ms);
      k.effect('bleed', 'bleed');
    }
    // 쌍격: 반대편 분신 교차 베기 (×cloneMult)
    if (rt.hasBranch('twin')) {
      const cx = at.x + (back.x / bl) * TILE;
      const cy = at.y + (back.y / bl) * TILE;
      // fx dagger_cross_clone: 대상 히트박스 중심, 행 = 주인공이 그 적을 바라보는 방향, 생성 + 120ms 교차 베기
      const drawn = k.playFx(k.mpStr('twin', 'cloneFx'), at.x, at.y, { x: back.x / bl, y: back.y / bl });
      this.skill('cross_clone', 'clone');
      g.time.delayedCall(k.mp('twin', 'cloneDelayMs'), () => {
        if (!g.scene.isActive()) return;
        if (!drawn) rt.fx.clone(cx, cy);
        if (mob.active) rt.fx.raw(mob, dmg * k.mp('twin', 'cloneMult'), { dirX: -back.x, dirY: -back.y, heavy: true });
        rt.record('twinClone', marks);
        const tb = rt.rule('twinBrand');
        if (tb) {
          const next = rt.fx.nearest(at.x, at.y, T(param(tb, 'rangeTiles')), new Set([mob]));
          if (next) {
            rt.traits.moves.fx('twinBrand', { x: next.x, y: next.y - 8 }, { fallbacks: [] });
            this.hopBrands(at, next, param(tb, 'brands', 2), back);
          }
        }
      });
    }
    // 난무: 5스택 기폭 뒤 분신이 남아 연격을 따라 함 (각성 백귀 난무 = 6초) — 나타남 dagger_frenzy_clone_in (대상 건너편)
    const dance = rt.rule('dance');
    if (dance && marks >= param(dance, 'minMarks', 5)) {
      const long = rt.rule('danceLong');
      const fresh = k.now >= this.danceUntil;
      this.danceUntil = k.now + (long ? param(long, 'ms') : param(dance, 'ms'));
      const pos = { x: at.x + (back.x / bl) * TILE, y: mob.y + (back.y / bl) * TILE };
      const dir = facingOf(-back.x, -back.y, 'down');
      if (fresh) {
        rt.art.once(BUILD_ART.FRENZY_IN, pos.x, pos.y, { dir, scaleMult: PLAYER_RENDER_SCALE });
        k.effect('dance', 'clone_in');
      }
      this.danceAt = { ...pos, dir };
    }
    // 각성 백귀: 기폭마다 분신 3체 (dagger_hundred_ghosts — 대상 히트박스 중심 1회, 그리면 분신 윤곽 대신)
    const demons = rt.rule('hundredDemons');
    if (demons) {
      // 61 G 백귀: 기폭마다 그림자 clones — 둘레에서 대상 자리로 덮친다
      const n = param(demons, 'clones', 1);
      const drawn = rt.art.once(BUILD_ART.HUNDRED_GHOSTS, at.x, at.y, { scaleMult: PLAYER_RENDER_SCALE });
      const moves = rt.traits.moves;
      const bind = rt.rule('ghostBind');
      const fire = rt.rule('ghostIgnite');
      for (let i = 0; i < n; i++) {
        const a = (i / n) * Math.PI * 2;
        g.time.delayedCall(80 * (i + 1), () => {
          if (!g.scene.isActive()) return;
          const from = { x: at.x + Math.cos(a) * TILE, y: at.y + Math.sin(a) * TILE };
          if (!drawn) rt.fx.clone(from.x, from.y);
          // 61 단계 5 (P13) 개성 '취한 그림자': 덮치는 길의 술 웅덩이에 불
          if (fire) {
            const lit = moves.igniteLine(
              from,
              { x: at.x - from.x, y: at.y - from.y },
              TILE,
              T(param(fire, 'widthTiles', 0.8)) / 2,
            );
            if (lit + moves.igniteCircle(at, T(1)) > 0) {
              moves.fx('d_ghostFire', at, { depth: DEPTH.FX_GROUND, flipX: at.x < from.x });
              k.effect('d_ghostFire', 'ignite');
            } else moves.sparks(from);
          }
          for (const m of rt.fx.inCircle(at.x, at.y, T(1.5))) {
            rt.fx.damage(m, param(demons, 'cloneMult'), { dirX: -Math.cos(a), dirY: -Math.sin(a) });
            // 개성 '그림자 사냥': 그림자가 벤 적은 제 그림자에 묶인다
            if (bind && m.active && moves.bind(m, param(bind, 'bindMs', 900), 'd_ghostBind'))
              k.effect('d_ghostBind', 'bind');
          }
        });
      }
    }
  }

  /** 쌍낙인·귀화: 낙인이 다음 적으로 옮겨감 (dagger_brand_hop 이 날아가 도착하면 낙인 n) */
  hopBrands(from: { x: number; y: number }, to: Mob, n: number, dir: { x: number; y: number }): void {
    const g = this.k.g;
    this.k.effect('twinBrand', 'transfer');
    const land = () => {
      if (!g.scene.isActive() || !to.active) return;
      for (let i = 0; i < n; i++) g.strikes.brands.onHit(to, dir.x, dir.y);
    };
    if (!g.fx.has(BUILD_ART.BRAND_HOP)) {
      land();
      return;
    }
    const c = to.body.center;
    const h = g.fx.play(BUILD_ART.BRAND_HOP, from.x, from.y, {
      angle: Math.atan2(c.y - from.y, c.x - from.x),
      depth: DEPTH.HIT_FX,
      hooks: false,
      durationMs: BUILD_ART.BRAND_HOP_MS,
    });
    if (h) g.tweens.add({ targets: h.sprite, x: c.x, y: c.y, duration: BUILD_ART.BRAND_HOP_MS });
    g.time.delayedCall(BUILD_ART.BRAND_HOP_MS, land);
  }

  /** 난무 분신: 연격을 반대편에서 따라 함 (×damageMult) */
  onAttack(p: PlayerAttackPayload): void {
    const k = this.k;
    const dance = k.rt.rule('dance');
    if (!dance || k.now >= this.danceUntil || p.comboIndex === undefined) return;
    const g = k.g;
    const pl = g.player;
    const reach = gameState.weapon.reachPx;
    g.time.delayedCall(param(dance, 'delayMs', 120), () => {
      if (!g.scene.isActive()) return;
      const t = k.rt.fx.nearest(pl.x, pl.y, reach * 2);
      if (!t) return;
      const cx = t.x + (t.x - pl.x);
      const cy = t.y + (t.y - pl.y);
      k.rt.fx.clone(cx, cy);
      this.danceAt = { x: cx, y: cy, dir: facingOf(pl.x - t.x, pl.y - t.y, 'down') };
      k.rt.fx.damage(t, p.damageMult * param(dance, 'damageMult'), { dirX: pl.x - t.x, dirY: pl.y - t.y });
    });
  }

  /** 이동기 (대쉬·그림자 걸음) — 열풍: 과열 +10% */
  onPlayerMove(): void {
    const k = this.k;
    const hw = k.rt.rule('heatwave');
    const res = k.g.player?.resource;
    if (hw && res?.kind === 'heat') res.heatBy(res.max * param(hw, 'heatPerMove'), k.now);
  }

  /** 열풍: 가속 50% 이상이면 이동·공속 +20% */
  heatwaveMult(): number {
    const k = this.k;
    const hw = k.rt.rule('heatwave');
    const res = k.g.player?.resource;
    if (!hw || res?.kind !== 'heat') return 1;
    return res.value >= res.max * param(hw, 'hasteFrom') ? 1 + param(hw, 'haste') : 1;
  }

  /**
   * 열풍 가속 가득 폭발 (61라운드: 기본 과열 폭발이 없어져 열풍만): 가속 100% 에 닿으면 반경 burstRadiusTiles 안 낙인 일괄 폭발 ·
   * 적 화상 burnMs · 주인공 무적 invulnMs → 가속 0 부터 다시
   */
  private heatwaveTick(): void {
    const k = this.k;
    const hw = k.rt.rule('heatwave');
    const res = k.g.player?.resource;
    if (!hw || res?.kind !== 'heat' || res.value < res.max) return;
    res.refresh(0);
    const radiusPx = param(hw, 'burstRadiusTiles', 8) * TILE;
    k.g.strikes.brands.burstAround(radiusPx);
    const pl = k.g.player;
    pl.grantInvulnerable(k.now + param(hw, 'invulnMs'));
    for (const m of k.rt.fx.inCircle(pl.x, pl.y, radiusPx))
      k.rt.combat.applyDot(
        m,
        'burn',
        param(hw, 'burnMs'),
        param(hw, 'burnTickMs', 500),
        param(hw, 'burnTickMult', 0.15),
      );
    k.rt.record('heatwaveBurst');
  }

  update(now: number): void {
    const k = this.k;
    this.heatwaveTick();
    if (this.stuck.length > 0) {
      for (const s of this.stuck) if (now >= s.until) s.gfx?.destroy();
      this.stuck = this.stuck.filter((s) => now < s.until);
    }
    // 난무 분신이 사라짐 (dagger_frenzy_clone_out)
    if (this.danceAt && now >= this.danceUntil) {
      k.effect('dance', 'clone_out');
      k.rt.art.once(BUILD_ART.FRENZY_OUT, this.danceAt.x, this.danceAt.y, {
        dir: this.danceAt.dir,
        scaleMult: PLAYER_RENDER_SCALE,
      });
      this.danceAt = null;
    }
    const pl = k.g.player;
    if (!pl) return;
    const moving = pl.moving || pl.action === 'dash';
    // 열풍: 과열 50% 이상 + 이동 중 → dagger_hotwind_trail (행 = 이동 방향)
    const trail = this.heatwaveMult() > 1 && moving;
    if (trail) k.rt.art.playerLoop('hotwind', BUILD_ART.HOTWIND_TRAIL, pl.facingDir, { below: true });
    else k.rt.art.stopPlayerLoop('hotwind');
    // 음향 dagger_hotwind_loop 켜기·끄기 (바뀔 때만)
    if (trail !== this.trailOn) {
      this.trailOn = trail;
      k.effect('heatwave', trail ? 'trail_start' : 'trail_end');
    }
    // 질풍 1단 연격 변화: 이동 중 90ms 마다 발 피벗에 재 실루엣 (따라가지 않음, 행 = 이동 방향)
    if (k.rt.hasBranch('gale') && moving && now >= this.galeNextAt && k.g.fx.has(BUILD_ART.GALE_WIND)) {
      this.galeNextAt = now + BUILD_ART.GALE_WIND_INTERVAL_MS;
      k.g.fx.play(BUILD_ART.GALE_WIND, pl.x, pl.y, {
        dir: pl.facingDir,
        depth: pl.depth - DEPTH.OVERLAY_STEP,
        scaleMult: PLAYER_RENDER_SCALE,
        hooks: false,
      });
    }
  }

  debug(): Record<string, unknown> {
    return {
      stuck: this.stuck.length,
      dance: this.k.now < this.danceUntil,
      throwReadyIn: Math.max(0, Math.round(this.throwReadyAt - this.k.now)),
    };
  }

  destroy(): void {
    for (const s of this.stuck) this.removeKnife(s);
    this.stuck = [];
  }
}
