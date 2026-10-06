/**
 * 활 갈래 (60라운드 6-1 — BranchStrikes 에서 분리): 1단 속사(연사 — 입력 쪽 BranchMoves)·저격(완벽 놓기 관통 화살) /
 * 2단 연궁(3발마다 분열)·무한통(처치·주운 화살)·필중(정밀 조준 치명)·천공(완벽 놓기 연결 스택·선 폭발) / 각성 유성.
 * 그림 (계약 art §20·§21): `bow_arrow_pierce`·`_pierce_hit` · `bow_snipe_full` · `bow_arrow_split`(+ 분열 화살 `bow_arrow_rapid`) ·
 * `bow_arrow_stuck`·`bow_arrow_recall` · `bow_deadeye_scope` · `bow_link_stack`(행 = 스택) · `bow_skypierce_line`(반복 타일) ·
 * `bow_meteor_arrow`.
 */
import { BUILD_ART, BUILD_FX, DEPTH, TILE } from '../../../../core/Constants';
import {
  EventBus,
  Events,
  type PlayerAttackPayload,
  type PlayerSecondaryPayload,
  type PlayerSkillPayload,
} from '../../../../core/EventBus';
import type { Mob } from '../../../../objects/Mob';
import type { Projectile } from '../../../../objects/Projectile';
import { currentAttackTag } from '../../../../systems/build/attackTags';
import { param, type ActiveRule } from '../../../../systems/build/buildMods';
import type { FxHandle } from '../../../../systems/fx/fx';
import { PLAYER_RENDER_SCALE } from '../../../../systems/weapon/playerScale';
import { sheetLoopRange } from '../BuildArt';
import { T, type BranchKit } from './BranchKit';

/** 무한통: 빗나가 떨어진 화살 */
interface StuckArrow {
  x: number;
  y: number;
  until: number;
  fx: FxHandle | null;
}

export class BowBranch {
  /** 연사 발 수 · 천공 연결 스택 · 유성 자동 화살비 */
  private volleyCount = 0;
  private stacks = 0;
  private meteorAt = -Infinity;
  private arrows: StuckArrow[] = [];
  private scopeFx: FxHandle | null = null;
  private scopeOn = false;

  constructor(private readonly k: BranchKit) {}

  onAttack(p: PlayerAttackPayload): void {
    const k = this.k;
    const g = k.g;
    // 천공: 완벽 놓기 연결 스택 (놓치면 0)
    if (p.kind === 'aimed' && p.bowPower !== 'perfect' && this.stacks > 0) {
      this.stacks = 0;
      if (k.rt.rule('skypierce')) k.effect('skypierce', 'link_break');
    }
    // 연궁: 연사 3발마다 분열 (각성 유성 = 매 발) — 분열 순간 bow_arrow_split, 갈라진 화살 = bow_arrow_rapid (재사용 매핑)
    const volley = k.rt.rule('volley');
    if (!volley || currentAttackTag() !== 'rapidVolley') return;
    this.volleyCount += 1;
    const every = k.rt.rule('splitEvery') ? 1 : param(volley, 'every', 3);
    if (this.volleyCount % every !== 0) return;
    g.time.delayedCall(Math.max(0, p.releaseDelayMs), () => {
      if (!g.scene.isActive()) return;
      const pl = g.player;
      const base = Math.atan2(p.dirY, p.dirX);
      const sp = (param(volley, 'spreadDeg', 14) * Math.PI) / 180;
      const { dmg } = g.combat.rollDamage(p.damageMult * param(volley, 'splitMult'), false, 'attack');
      k.rt.art.once(BUILD_ART.ARROW_SPLIT, pl.x, pl.y - 6, { angle: base, scaleMult: PLAYER_RENDER_SCALE });
      k.effect('volley', 'split');
      const sprite = g.fx.has(BUILD_ART.SPLIT_ARROW) ? { sprite: BUILD_ART.SPLIT_ARROW } : {};
      for (const s of [-1, 1])
        k.rt.fx.shot(pl.x, pl.y - 6, Math.cos(base + s * sp), Math.sin(base + s * sp), dmg, {
          tag: 'split',
          speedTiles: param(volley, 'splitSpeedTiles', 12),
          lifeMs: param(volley, 'splitLifeMs', 900),
          ...sprite,
        });
    });
  }

  /** 완벽 놓기 (활): 천공 스택 · 숨 고르기 */
  onPerfectRelease(): void {
    const k = this.k;
    const sky = k.rt.rule('skypierce');
    if (!sky) return;
    const cap = k.rt.rule('stackCap');
    const max = cap ? param(cap, 'maxStacks') : param(sky, 'maxStacks', 3);
    this.stacks = Math.min(max, this.stacks + 1);
    k.effect('skypierce', 'link', this.stacks);
    const breath = k.rt.rule('stackBreath');
    const br = k.g.player.gauges.breath;
    if (breath && br && this.stacks >= 3) br.value = br.max;
  }

  /** 저격 1단: 가득 당김(완벽 놓기 창 열림) 순간 bow_snipe_full (화살촉 근사 — 조준 쪽 활 높이) */
  onSecondary(p: PlayerSecondaryPayload): void {
    const k = this.k;
    if (p.kind !== 'aimedshot' || p.phase !== 'ready' || !k.rt.hasBranch('snipe')) return;
    const pl = k.g.player;
    const a = pl.aimAngle;
    k.rt.art.once(BUILD_ART.SNIPE_FULL, pl.x + Math.cos(a) * TILE, pl.y - TILE + Math.sin(a) * TILE, {
      scaleMult: PLAYER_RENDER_SCALE,
    });
  }

  /** 화살 발사 배율 (BowShots — 천공 스택 피해, 필중 정밀 조준 치명, 장교 사냥은 적중 때) */
  arrowBonus(p: PlayerAttackPayload): { mult: number; forceCrit: boolean; wallPierce: boolean; sizeMult: number } {
    const k = this.k;
    let mult = 1;
    let forceCrit = false;
    let wallPierce = false;
    let sizeMult = 1;
    if (p.bowPower === 'perfect') {
      // 저격 1단: 완벽 놓기 피해 +25%
      if (k.rt.hasBranch('snipe')) mult *= k.mp('snipe', 'perfectMult') || 1;
      const sky = k.rt.rule('skypierce');
      if (sky && this.stacks > 0) {
        mult *= 1 + this.stacks * param(sky, 'perStack');
        sizeMult *= 1 + this.stacks * param(sky, 'perStack');
        wallPierce = this.stacks >= 3;
      }
      if (k.rt.rule('deadeye') && k.g.player.gauges.focusing(k.now)) forceCrit = true;
    }
    return { mult, forceCrit, wallPierce, sizeMult };
  }

  /** 화살이 나감 (BowShots) — 저격 관통 화살 · 천공 3스택 선 폭발 · 불화살 · 무한통 떨어진 화살 */
  onArrowSpawn(shot: Projectile, p: PlayerAttackPayload): void {
    const k = this.k;
    const b = this.arrowBonus(p);
    // 저격 1단 관통 화살: 완벽 놓기 화살 = 최대 pierce 명 관통 + 전용 화살 그림 (bow_arrow 대신)
    if (p.bowPower === 'perfect' && k.rt.hasBranch('snipe')) {
      const n = k.mp('snipe', 'pierce');
      if (n > 0 && !k.rt.rule('skypierce')) shot.pierceLeft = n;
      k.rt.fx.restyle(shot, k.mpStr('snipe', 'arrowFx') ?? '');
    }
    if (b.wallPierce) {
      shot.wallPierce = true;
      const sky = k.rt.rule('skypierce')!;
      const from = { x: shot.x, y: shot.y };
      const v = shot.body.velocity;
      const dl = Math.hypot(v.x, v.y) || 1;
      const dir = { x: v.x / dl, y: v.y / dl };
      k.g.time.delayedCall(param(sky, 'lineDelayMs'), () => {
        if (!k.g.scene.isActive()) return;
        const len = Math.hypot(shot.x - from.x, shot.y - from.y) || T(8);
        k.effect('skypierce', 'line');
        // bow_skypierce_line: 화살이 지나간 선을 64 도트 타일로 이어 깔고 진행 각도로 회전
        k.line(
          from.x,
          from.y,
          dir,
          len,
          T(param(sky, 'lineWidthTiles', 0.8)) / 2,
          param(sky, 'lineMult'),
          'skypierce',
          {
            fx: BUILD_ART.SKYPIERCE_LINE,
          },
        );
      });
    }
    if (p.bowPower === 'perfect' && k.rt.rule('fireArrow')) {
      let lit = false;
      const tick = () => {
        if (!shot.active) return;
        if (k.g.pools.igniteAt(shot.x, shot.y) && !lit) {
          lit = true;
          k.rt.traits.moves.fx('fireArrow', shot, { depth: DEPTH.FX_GROUND });
          k.effect('fireArrow', 'ignite');
        }
        k.g.time.delayedCall(40, tick);
      };
      tick();
    }
    // 무한통: 빗나가 떨어진 화살 (밟으면 주움 — pickupArrows)
    const q = k.rt.rule('quiver');
    if (q && !shot.buildTag && !shot.onEnd) shot.onEnd = (s) => this.dropArrow(s.x, s.y, param(q, 'stuckMs', 6000));
  }

  /** 빌드 투사체·화살 적중 (GameCombat.onPlayerShotHit 뒤) — 저격 관통 자리 · 유성 하늘 화살 */
  onShotHit(shot: Projectile, mob: Mob): void {
    const k = this.k;
    if (k.rt.isPerfectShot(shot) && k.rt.hasBranch('snipe')) {
      const v = shot.body.velocity;
      const id = k.mpStr('snipe', 'pierceHitFx');
      // 쓰러진 적은 바디가 없다 (61 단계 5 정리 — 발 자리 + 몸 절반)
      const c = mob.body ? mob.body.center : { x: mob.x, y: mob.y - 8 };
      if (id && k.g.fx.has(id))
        k.g.fx.play(id, c.x, c.y, {
          angle: Math.atan2(v.y, v.x),
          flipY: v.x < 0,
          depth: DEPTH.HIT_FX,
        });
      EventBus.emit(Events.PLAYER_SKILL, { weapon: 'bow', move: 'pierce', phase: 'pass' } satisfies PlayerSkillPayload);
    }
    // 61 G 유성 (1차 갈래): 완벽 놓기 화살이 맞은 적 발밑에 하늘 화살 (bow_meteor_arrow — f3 시작이 판정)
    const meteor = k.rt.rule('meteor');
    if (meteor && !shot.buildTag && k.rt.isPerfectShot(shot) && mob.active) {
      const c = { x: mob.body.center.x, y: mob.body.center.y };
      const drawn = k.rt.art.once(BUILD_ART.METEOR_ARROW, mob.x, mob.y, { scaleMult: PLAYER_RENDER_SCALE });
      k.effect('meteor', 'sky');
      k.g.time.delayedCall(param(meteor, 'skyDelayMs', 120), () => {
        if (!k.g.scene.isActive()) return;
        const r = T(param(meteor, 'skyRadiusTiles', 0.8));
        if (!drawn) k.rt.fx.ring(c.x, c.y, r, BUILD_FX.COLOR.METEOR);
        this.skyLanded(c, r);
        for (const m of k.rt.fx.inCircle(c.x, c.y, r))
          k.rt.fx.damage(m, param(meteor, 'skyMult'), { dirX: 0, dirY: 1 });
        // 61 단계 5 (P13) 개성 '별 표적': 떨어진 자리로 둘레 적이 빨려 든다
        const well = k.rt.rule('skyGravity');
        if (well) this.skyWell(c, well);
      });
    }
  }

  /** 하늘 화살이 떨어진 자리 (개성 '술별': 술 웅덩이에 불) */
  private skyLanded(c: { x: number; y: number }, r: number): void {
    const k = this.k;
    const ig = k.rt.rule('skyIgnite');
    if (!ig) return;
    const n = k.rt.traits.moves.igniteCircle(c, Math.max(r, T(param(ig, 'radiusTiles', 1))));
    if (n > 0) {
      if (!k.rt.traits.moves.fx('b_starDrunk', c, { depth: DEPTH.FX_GROUND })) k.rt.traits.moves.sparks(c);
      k.effect('b_starDrunk', 'ignite', n);
    }
  }

  /** 별 표적 (61 단계 5): 하늘 화살 자리로 둘레 적을 빨아들여 한데 모은다 */
  private skyWell(c: { x: number; y: number }, r: ActiveRule): void {
    const k = this.k;
    const moves = k.rt.traits.moves;
    const rad = T(param(r, 'radiusTiles', 2.5));
    const hits = k.rt.fx.inCircle(c.x, c.y, rad).filter((m) => !m.isBoss);
    if (!moves.fx('b_starWell', c, { fallbacks: ['bow_link_stack'], depth: DEPTH.FX_GROUND }))
      k.rt.fx.ring(c.x, c.y, rad, BUILD_FX.COLOR.METEOR, 300);
    for (const m of hits) {
      moves.chainLine(m, c, BUILD_FX.COLOR.METEOR, 260);
      moves.pull(m, c, param(r, 'pullTiles', 1.6), 'b_starWell', {
        stopTiles: 0.3,
        endStunMs: param(r, 'stunMs', 400),
      });
    }
    if (hits.length > 0) k.effect('b_starWell', 'pull', hits.length);
  }

  /** 처치: 무한통 화살 +3 (적 발밑 bow_arrow_recall 1회) · 흩날리는 살 (61 단계 5) */
  onKill(mob: Mob): void {
    const k = this.k;
    const q = k.rt.rule('quiver');
    if (q) {
      k.rt.combat.restoreResource({ ammo: param(q, 'killArrows') });
      k.rt.art.once(BUILD_ART.ARROW_RECALL, mob.x, mob.y, { scaleMult: PLAYER_RENDER_SCALE });
      k.effect('quiver', 'recall');
    }
    // 61 단계 5 (P13) 흩날리는 살: 연사로 쓰러뜨리면 쓰러진 자리에서 화살이 사방으로
    const burst = k.rt.rule('volleyBurst');
    if (burst && k.g.player.branchMoves.volleying) {
      const n = param(burst, 'arrows', 6);
      const at = { x: mob.x, y: mob.y - 6 };
      const { dmg, crit } = k.g.combat.rollDamage(param(burst, 'damageMult', 0.35), false, 'other');
      const speed = param(burst, 'speedTiles', 12);
      const sprite = BUILD_ART.SPLIT_ARROW;
      for (let i = 0; i < n; i++) {
        const a = (i / n) * Math.PI * 2;
        k.rt.fx.shot(at.x, at.y, Math.cos(a), Math.sin(a), dmg, {
          tag: 'scatter',
          speedTiles: speed,
          lifeMs: (param(burst, 'rangeTiles', 3) / speed) * 1000,
          crit,
          ...(k.g.fx.has(sprite) ? { sprite } : { tint: BUILD_FX.COLOR.METEOR }),
        });
      }
      k.rt.traits.moves.fx('b_scatterVolley', at, { fallbacks: ['bow_arrow_split'] });
      k.effect('b_scatterVolley', 'burst', n);
    }
  }

  /** 무한통: 떨어진 화살 (bow_arrow_stuck 수명 시트) */
  private dropArrow(x: number, y: number, ms: number): void {
    const g = this.k.g;
    const range = sheetLoopRange(g.fx.sheet(BUILD_ART.ARROW_STUCK));
    const fx = g.fx.has(BUILD_ART.ARROW_STUCK)
      ? g.fx.play(BUILD_ART.ARROW_STUCK, x, y, {
          depth: DEPTH.PICKUP,
          durationMs: ms,
          hooks: false,
          ...(range ? { loopRange: range } : {}),
        })
      : null;
    this.arrows.push({ x, y, until: this.k.now + ms, fx });
  }

  /** 밟은 화살 줍기 (반경 반 칸) */
  private pickArrows(now: number): void {
    const k = this.k;
    const q = k.rt.rule('quiver');
    const pl = k.g.player;
    if (this.arrows.length === 0) return;
    this.arrows = this.arrows.filter((a) => {
      if (now >= a.until) return false;
      if (!q || !pl || Math.hypot(pl.x - a.x, pl.y - a.y) > TILE * 0.6) return true;
      k.rt.combat.restoreResource({ ammo: param(q, 'pickupArrows', 1) });
      k.g.fx.finish(a.fx);
      k.rt.art.once(BUILD_ART.ARROW_RECALL, a.x, a.y, { scaleMult: PLAYER_RENDER_SCALE });
      k.effect('quiver', 'recall');
      return false;
    });
  }

  update(now: number): void {
    const k = this.k;
    const rt = k.rt;
    // 61 G 성우 (유성 2차 길): autoRainMs 마다 자동 화살비 (가장 가까운 적 자리)
    const star = rt.rule('starfall');
    if (star && now - this.meteorAt >= param(star, 'autoRainMs', 3000)) {
      this.meteorAt = now;
      const pl = k.g.player;
      const t = rt.fx.nearest(pl.x, pl.y, T(param(star, 'rangeTiles', 10)));
      if (t) {
        const r = T(param(star, 'rainRadiusTiles'));
        const c = { x: t.x, y: t.y };
        if (!rt.art.once(BUILD_ART.METEOR_ARROW, t.x, t.y, { scaleMult: PLAYER_RENDER_SCALE }))
          rt.fx.ring(t.x, t.y, r, BUILD_FX.COLOR.METEOR);
        k.effect('starfall', 'rain');
        this.skyLanded(c, r);
        for (const m of rt.fx.inCircle(t.x, t.y, r)) rt.fx.damage(m, param(star, 'rainMult'), { dirX: 0, dirY: 1 });
      }
    }
    // 무한통 각성: 탄창 무한
    if (rt.rule('infiniteAmmo')) {
      const res = k.g.player?.resource;
      if (res?.kind === 'ammo') res.value = res.max;
    }
    this.pickArrows(now);
    // 천공 연결 스택 루프 (행 = 스택, 0 이면 끔)
    if (rt.rule('skypierce') && this.stacks > 0)
      rt.art.playerLoop('link', BUILD_ART.LINK_STACK, String(Math.min(3, this.stacks)), { below: true });
    else rt.art.stopPlayerLoop('link');
    this.syncScope(now);
  }

  /** 필중: 숨 집중(정밀 조준) 동안 커서에 bow_deadeye_scope (f0~5 좁혀 듦 → f6~9 반복) */
  private syncScope(now: number): void {
    const k = this.k;
    const g = k.g;
    const pl = g.player;
    const on = Boolean(k.rt.rule('deadeye') && pl?.gauges.focusing(now));
    if (on !== this.scopeOn) {
      this.scopeOn = on;
      // 음향 bow_deadeye_hold 루프 · 조준 고정 bow_deadeye_lock
      k.effect('deadeye', on ? 'hold_start' : 'hold_end');
      if (on) k.effect('deadeye', 'lock');
    }
    if (!on) {
      if (this.scopeFx) g.fx.stop(this.scopeFx, 0, true);
      this.scopeFx = null;
      return;
    }
    if (!g.fx.isActive(this.scopeFx)) {
      const range = sheetLoopRange(g.fx.sheet(BUILD_ART.DEADEYE_SCOPE));
      this.scopeFx = g.fx.has(BUILD_ART.DEADEYE_SCOPE)
        ? g.fx.play(BUILD_ART.DEADEYE_SCOPE, pl.aimPoint.x, pl.aimPoint.y, {
            depth: DEPTH.HIT_FX,
            hooks: false,
            ...(range ? { loopRange: range } : {}),
          })
        : null;
    }
    this.scopeFx?.sprite.setPosition(pl.aimPoint.x, pl.aimPoint.y);
  }

  debug(): Record<string, unknown> {
    return { stacks: this.stacks, arrows: this.arrows.length };
  }

  destroy(): void {
    for (const a of this.arrows) this.k.g.fx.stop(a.fx, 0, false);
    this.arrows = [];
    this.k.g.fx.stop(this.scopeFx, 0, false);
  }
}
