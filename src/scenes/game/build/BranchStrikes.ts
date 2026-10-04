/**
 * 57라운드 갈래 재설계 — 수단·2단 규칙 실행 (씬 쪽, BuildRuntime 의 일부). 입력은 Player `BranchMoves`(PLAYER_BRANCH_MOVE).
 * 아트 시트가 아직 없어 기존 시트(연격 몸 동작)·플레이스홀더 윤곽으로 동작부터. 그림 배율 = 판정 배율(55 Q15).
 * 시트 키 제안 (계약 art §18.6 '미정' — 아트 확정 대기): `katana_spin` · `katana_unblockable` · `greatsword_crack_line`(파쇄 강화)·
 * `greatsword_quake_ring`(중압 진동) · `dagger_fan_throw` · `dagger_clone_cross` · `bow_rapid_volley` · `bow_pierce_arrow`.
 *
 * 1단: 칼 선풍(회전 베기)·투구가르기(가드 불가 내려베기) / 대검 파쇄(균열 강화·탄 지움)·중압(원형 진동) /
 *      단검 쌍격(낙인 기폭 분신 교차)·질풍(부채꼴 투척) / 활 속사(연사 — 입력 쪽)·저격(완벽 놓기 피해·거리).
 * 2단(시험장): 회오리·잔월·일도양단 / 지진·반향·거인·울혈 / 난무·출혈·비도·열풍 / 연궁·무한통·필중·천공 (명경은 칼 검기 작업과 합친 뒤).
 * 이중 개성·각성 규칙 중 갈래 동작에 붙는 것도 여기.
 */
import Phaser from 'phaser';
import { BUILD_FX, DEPTH, TILE, entityDepth } from '../../../core/Constants';
import {
  EventBus,
  Events,
  type PlayerAttackPayload,
  type PlayerBranchMovePayload,
  type PlayerSecondaryPayload,
} from '../../../core/EventBus';
import { gameState } from '../../../core/GameState';
import type { Mob } from '../../../objects/Mob';
import type { Projectile } from '../../../objects/Projectile';
import { param, type ActiveRule } from '../../../systems/build/buildMods';
import { comboAction } from '../../../systems/sprites/spriteActions';
import { currentAttackTag } from '../../../systems/build/attackTags';
import { artScale, facingOf, frameDurations, rowDirFor } from '../../../systems/sprites/spriteDefs';
import { PLAYER_HIT_SCALE, PLAYER_RENDER_SCALE } from '../../../systems/weapon/playerScale';
import { HIT_ORIGIN_UP_PX } from '../shared';
import type { Game } from '../../Game';
import type { BuildRuntime } from './BuildRuntime';
import type { PerfectKind } from './BuildPerfect';

const T = (tiles: number) => tiles * TILE;

type Dir = { x: number; y: number };
type BranchPayload = PlayerAttackPayload & { buildMove?: string; ignoreGuard?: boolean };

/** 비도: 박힌 단검 */
interface StuckKnife {
  x: number;
  y: number;
  until: number;
  gfx: Phaser.GameObjects.Rectangle;
}

export class BranchStrikes {
  /** 갈래 동작 중 (강공 — 중량 6 감소·끊기지 않음) */
  busy = false;
  private busyUntil = -Infinity;
  /** 회오리 지속 회전 */
  private vortex: { until: number; nextAt: number; moveMult: number } | null = null;
  /** 단검: 투척 쿨다운 · 박힌 단검 · 난무 분신 · 열풍 가속 */
  private throwReadyAt = -Infinity;
  private stuck: StuckKnife[] = [];
  private danceUntil = -Infinity;
  /** 활: 연사 발 수 · 천공 연결 스택 · 유성 자동 화살비 */
  private volleyCount = 0;
  private stacks = 0;
  private meteorAt = -Infinity;
  /** 대검: 산을 진 자 보스별 쿨 · 술독 짓누르기 큰 웅덩이 */
  private readonly bossStunAt = new Map<Mob, number>();
  /** 디버그 */
  private last: Record<string, unknown> = {};

  constructor(
    private readonly g: Game,
    private readonly rt: BuildRuntime,
  ) {
    EventBus.on(Events.PLAYER_BRANCH_MOVE, this.onMove, this);
    EventBus.on(Events.PLAYER_SECONDARY, this.onSecondary, this);
  }

  private get now(): number {
    return this.g.time.now;
  }

  private moveParams(id: string): Record<string, unknown> {
    return gameState.weapon.nodes.find((n) => n.id === id)?.moveParams ?? {};
  }

  private mp(id: string, key: string, stageIdx = 0): number {
    const v = this.moveParams(id)[key];
    if (Array.isArray(v)) return Number(v[Math.max(0, Math.min(v.length - 1, stageIdx))]) || 0;
    return typeof v === 'number' ? v : 0;
  }

  /** 갈래 수단 한 타 (근접 타격 경로와 같은 순서: 빌드 배율 → 피해 → 처치 / 타격 뒤 효과) */
  private strike(mob: Mob, p: BranchPayload, dir: Dir, opts: { stunMs?: number } = {}): boolean {
    const g = this.g;
    if (!mob.active) return false;
    const b = this.rt.combat.strikeBonus(mob, p);
    const { dmg, crit } = g.combat.rollDamage(p.damageMult * b.mult, p.forceCrit || b.forceCrit, p.kind, mob);
    const died = g.combat.hitMob(mob, dmg, {
      crit,
      dirX: dir.x,
      dirY: dir.y,
      heavy: true,
      ...(p.ignoreGuard ? { ignoreGuard: true } : {}),
    });
    if (died) g.progress.onKill(mob, p.kind === 'dashAttack' ? 'dashAttack' : 'attack');
    else if (opts.stunMs) mob.stun(this.now, opts.stunMs, 'hit');
    this.rt.combat.afterStrike(mob, p, crit, died);
    if (!died) g.strikes.brands.onHit(mob, dir.x, dir.y);
    return died;
  }

  private payload(
    x: number,
    y: number,
    dir: Dir,
    damageMult: number,
    move: string,
    extra: Partial<BranchPayload> = {},
  ): BranchPayload {
    return {
      x,
      y,
      dirX: dir.x,
      dirY: dir.y,
      damageMult,
      sizeMult: 1,
      kind: 'attack',
      forceCrit: false,
      primed: false,
      swingDelayMs: 0,
      releaseDelayMs: 0,
      buildMove: move,
      ...extra,
    } as BranchPayload;
  }

  /**
   * 몸 동작: 갈래 수단 시트(노드 art.body — `player_<무기>_<이름>`)가 있으면 그것 (fromFrame 부터 끝까지 제 시간으로),
   * 없으면 기존 연격 n타 시트를 ms 에 맞춰
   */
  private body(nodeId: string, n: number, dir: Dir, ms: number, fromFrame = 0): void {
    const pl = this.g.player;
    const v = pl.visual;
    const node = gameState.weapon.nodes.find((x) => x.id === nodeId);
    const name = node?.art?.body?.[0];
    const own = name ? `${gameState.weapon.id}_${name}` : null;
    if (own && v.hasAction(own)) {
      const sheet = v.sheet(own);
      const d = rowDirFor(sheet, dir.x, dir.y, v.facing);
      const total = sheet ? frameDurations(sheet).length : 0;
      if (fromFrame > 0 && total > fromFrame)
        v.playFrames(
          own,
          d,
          Array.from({ length: total - fromFrame }, (_, i) => fromFrame + i),
          this.now,
        );
      else v.oneShot(own, d, this.now);
      return;
    }
    const act = comboAction(gameState.weapon.id, n);
    if (v.hasAction(act)) v.oneShot(act, facingOf(dir.x, dir.y, v.facing), this.now, ms);
  }

  /** 수단 이펙트 시트 (있으면 재생, 없으면 false — 호출 쪽 플레이스홀더) */
  private playFx(id: unknown, x: number, y: number, dir: Dir, opts: { follow?: boolean; row?: string } = {}): boolean {
    const g = this.g;
    if (typeof id !== 'string' || !g.fx.has(id)) return false;
    const sheet = g.fx.sheet(id);
    const row =
      opts.row ??
      (sheet ? rowDirFor(sheet, dir.x, dir.y, g.player.facingDir) : facingOf(dir.x, dir.y, g.player.facingDir));
    return (
      g.fx.play(id, x, y, {
        dir: row,
        ...(opts.follow ? { follow: g.player } : {}),
        depth: entityDepth(y) + DEPTH.OVERLAY_STEP * 2,
        scaleMult: PLAYER_RENDER_SCALE,
      }) !== null
    );
  }

  private setBusy(ms: number): void {
    this.busy = true;
    this.busyUntil = Math.max(this.busyUntil, this.now + ms);
  }

  // --- 입력 사건 (Player BranchMoves) ---

  private onMove(e: PlayerBranchMovePayload): void {
    const dir = { x: e.dirX, y: e.dirY };
    if (e.phase === 'ready') {
      const pl = this.g.player;
      // 칼끝 준비 반짝임 (katana_spin_ready — 칼끝 앵커 대신 조준 쪽 칼 높이 근사) · 시트가 없으면 몸 번쩍임
      const ready = e.move === 'spin' ? (this.moveParams('iai').readyFx ?? 'katana_spin_ready') : null;
      if (!this.playFx(ready, pl.x + dir.x * TILE, pl.y - TILE * 1.5 + dir.y * TILE * 0.5, dir, { row: 'any' }))
        pl.flashColor(BUILD_FX.HOLD_READY_COLOR);
      return;
    }
    if (e.move === 'spin' && e.phase === 'release') this.spin(dir);
    else if (e.move === 'spin' && e.phase === 'sustain') this.vortexStart();
    else if (e.move === 'spin' && e.phase === 'end') this.vortex = null;
    else if (e.move === 'unblockable' && e.phase === 'release') this.unblockable(dir);
    else if (e.move === 'fanThrow' && e.phase === 'release') this.fanThrow(dir);
  }

  /** 칼 선풍: 회전 베기 (선딜 → 360° 원 · 검기 1단 소모 시 2회전) */
  private spin(dir: Dir): void {
    const g = this.g;
    const pl = g.player;
    const id = 'iai';
    const windup = this.mp(id, 'windupMs');
    const recover = this.mp(id, 'recoverMs');
    let radius = T(this.mp(id, 'radiusTiles')) * this.hitScale();
    // 술 회오리 (이중 개성): 반경 안 웅덩이를 빨아들여 반경 +0.5칸 (최대 +1.5), 술불이면 술불 판정 추가
    const whirl = this.rt.rule('liquorWhirl');
    let fireExtra = 0;
    if (whirl) {
      const pools = this.rt.fx.poolsNear(pl.x, pl.y, T(param(whirl, 'pullTiles')));
      radius += Math.min(T(param(whirl, 'maxTiles')), pools.length * T(param(whirl, 'perPoolTiles')));
      if (pools.some((q) => g.pools.burning(q))) fireExtra = param(whirl, 'fireMult');
      for (const q of pools) q.until = this.now;
    }
    const res = pl.resource;
    if (res?.def.kind === 'stamina') res.spend(res.max * this.mp(id, 'staminaRatio'), this.now);
    const k = pl.gauges.kenki;
    const kenkiSpent = k && k.stage >= this.mp(id, 'kenkiStages') && this.mp(id, 'kenkiStages') > 0;
    if (kenkiSpent && k) k.value = Math.max(0, k.value - k.def.perStage * this.mp(id, 'kenkiStages'));
    pl.setAction('skill', this.now + windup + recover);
    this.setBusy(windup + recover);
    this.body(id, 2, dir, windup + recover, this.mp(id, 'releaseFrame'));
    const mult = this.mp(id, 'damageMult') * gameState.weapon.reinforceMult;
    // fx katana_spin: 뗀 순간(몸 releaseFrame) 1회 — fx f1 = 판정. 2회전은 다시 재생 (아트 노트)
    const art = gameState.weapon.nodes[0]?.art?.fx?.[0];
    const drawn = this.playFx(art, pl.x, pl.y, dir, { follow: true });
    const hitAll = (m: number, replay = false) => {
      if (!g.scene.isActive()) return;
      const p = this.payload(pl.x, pl.y, dir, m, 'spin');
      if (replay) this.playFx(art, pl.x, pl.y, dir, { follow: true });
      // 판정 원점 = 발 위 (아트 hitOriginInFrame — 피벗 위 40 도트)
      const oy = pl.y - HIT_ORIGIN_UP_PX;
      if (!drawn) this.rt.fx.ring(pl.x, oy, radius, BUILD_FX.COLOR.SPIN);
      const hit = this.rt.fx.inCircle(pl.x, oy, radius);
      let kills = 0;
      for (const mob of hit) {
        const d = { x: mob.x - pl.x, y: mob.y - pl.y };
        if (this.strike(mob, p, d)) kills += 1;
        if (fireExtra > 0 && mob.active) this.rt.fx.damage(mob, fireExtra, { dirX: d.x, dirY: d.y, tick: true });
      }
      this.reflectShots(pl.x, pl.y, radius);
      // 피바람 (이중 개성): 처치마다 회전 판정 1회 추가 (최대 +3)
      const gale = this.rt.rule('spinChain');
      if (gale && kills > 0) {
        const n = Math.min(kills, param(gale, 'maxExtra', 3));
        for (let i = 1; i <= n; i++) g.time.delayedCall(param(gale, 'delayMs', 160) * i, () => hitAll(m * 0.7));
      }
      // 잔월: 검기를 쓴 회전이 지나간 자리에 달 궤적
      if (kenkiSpent) this.moonTrail(pl.x, pl.y, radius);
    };
    g.time.delayedCall(windup, () => hitAll(mult));
    if (kenkiSpent)
      g.time.delayedCall(windup + this.mp(id, 'secondSpinDelayMs'), () => hitAll(this.mp(id, 'secondSpinMult'), true));
    this.last = { move: 'spin', radius, kenki: kenkiSpent, t: Math.round(this.now) };
    this.rt.record('spin');
  }

  /** 회전 판정 안 적 탄 반사 (회오리) */
  private reflectShots(x: number, y: number, r: number): void {
    if (!this.rt.rule('vortex')) return;
    for (const child of this.g.projectiles.getChildren()) {
      const pr = child as Projectile;
      if (!pr.active || pr.reflected || pr.owner !== 'enemy') continue;
      if (Math.hypot(pr.x - x, pr.y - y) <= r) pr.reflect(1);
    }
  }

  /** 회오리: 홀드를 유지하면 지속 회전 (초당 hitsPerSec 타 ×damageMult, 이동 ×moveMult, 기력 초당 소모) */
  private vortexStart(): void {
    const r = this.rt.rule('vortex');
    if (!r || this.vortex) return;
    this.vortex = { until: this.now + param(r, 'maxMs'), nextAt: this.now, moveMult: param(r, 'moveMult') };
  }

  private vortexTick(now: number): void {
    const v = this.vortex;
    const r = this.rt.rule('vortex');
    if (!v || !r) return;
    const pl = this.g.player;
    if (now >= v.until || !pl.active) {
      this.vortex = null;
      return;
    }
    pl.setAction('skill', now + 120);
    pl.skillMoveMult = v.moveMult;
    this.setBusy(120);
    if (now < v.nextAt) return;
    v.nextAt = now + 1000 / Math.max(1, param(r, 'hitsPerSec', 4));
    const res = pl.resource;
    if (res?.def.kind === 'stamina') res.spend((res.max * param(r, 'staminaPerSec')) / param(r, 'hitsPerSec', 4), now);
    const radius = T(this.mp('iai', 'radiusTiles')) * this.hitScale();
    const dir = pl.facingVec;
    const p = this.payload(pl.x, pl.y, { x: dir.x, y: dir.y }, param(r, 'damageMult'), 'spin');
    this.rt.fx.ring(pl.x, pl.y, radius, BUILD_FX.COLOR.SPIN, 160);
    for (const mob of this.rt.fx.inCircle(pl.x, pl.y, radius))
      this.strike(mob, p, { x: mob.x - pl.x, y: mob.y - pl.y });
    this.reflectShots(pl.x, pl.y, radius);
  }

  /** 잔월: 달 궤적 (trailMs 동안 tickMs 마다 ×tickMult) */
  private moonTrail(x: number, y: number, radius: number): void {
    const r = this.rt.rule('zangetsu');
    if (!r) return;
    const ms = param(r, 'trailMs');
    const tick = param(r, 'tickMs');
    this.rt.fx.zone(x, y, radius * 2, radius * 2, BUILD_FX.COLOR.MOON, ms);
    for (let t = tick; t <= ms; t += tick)
      this.g.time.delayedCall(t, () => {
        if (!this.g.scene.isActive()) return;
        for (const m of this.rt.fx.inCircle(x, y, radius))
          this.rt.fx.damage(m, param(r, 'tickMult'), { dirX: 0, dirY: 0, tick: true });
      });
  }

  /** 칼 투구가르기: 가드 불가 내려베기 (선딜 백열 → 정면 쐐기, 경직, 검기 1단 = 치명 확정) */
  private unblockable(dir: Dir): void {
    const g = this.g;
    const pl = g.player;
    const id = 'batto';
    const windup = this.mp(id, 'windupMs');
    const recover = this.mp(id, 'recoverMs');
    const res = pl.resource;
    if (res?.def.kind === 'stamina') res.spend(res.max * this.mp(id, 'staminaRatio'), this.now);
    const k = pl.gauges.kenki;
    const crit = Boolean(k && this.mp(id, 'kenkiStages') > 0 && k.stage >= this.mp(id, 'kenkiStages'));
    if (crit && k) k.value = Math.max(0, k.value - k.def.perStage * this.mp(id, 'kenkiStages'));
    pl.setAction('skill', this.now + windup + recover);
    this.setBusy(windup + recover);
    this.body(id, 3, dir, windup + recover, this.mp(id, 'releaseFrame'));
    // fx katana_guardbreak: 뗀 순간 1회 (뗀 자리 고정) — 없으면 윤곽
    const drawnGb = this.playFx(gameState.weapon.nodes[0]?.art?.fx?.[0], pl.x, pl.y, dir);
    if (!drawnGb) pl.flashColor(BUILD_FX.HOLD_READY_COLOR);
    const len = T(this.mp(id, 'lengthTiles')) * this.hitScale();
    const half = (T(this.mp(id, 'widthTiles')) * this.hitScale()) / 2;
    const helm = this.rt.rule('helmBreak');
    g.time.delayedCall(windup, () => {
      if (!g.scene.isActive()) return;
      const x0 = pl.x;
      const y0 = pl.y - HIT_ORIGIN_UP_PX;
      if (!drawnGb) this.rt.fx.lineFx(x0, y0, dir.x, dir.y, len, half, BUILD_FX.COLOR.UNBLOCKABLE);
      let refunded = false;
      for (const mob of this.rt.fx.inLine(x0, y0, dir.x, dir.y, len, half)) {
        const stunned = mob.isStunned(this.now);
        const mult =
          this.mp(id, 'damageMult') * gameState.weapon.reinforceMult * (helm && stunned ? param(helm, 'mult') : 1);
        if (this.execute(mob, dir)) continue;
        this.strike(mob, this.payload(x0, y0, dir, mult, 'unblockable', { forceCrit: crit, ignoreGuard: true }), dir, {
          stunMs: this.mp(id, 'stunMs'),
        });
        if (helm && stunned && !refunded && res?.def.kind === 'stamina') {
          refunded = true;
          res.value = Math.min(res.max, res.value + res.max * param(helm, 'staminaRefund'));
        }
      }
      // 일도양단: 끝에서 직선 균열 4칸 (×1.2)
      const cl = this.rt.rule('cleave');
      if (cl) {
        const ex = x0 + dir.x * len;
        const ey = y0 + dir.y * len;
        const cl2 = T(param(cl, 'crackTiles'));
        const ch = T(param(cl, 'crackWidthTiles', 1)) / 2;
        this.rt.fx.lineFx(ex, ey, dir.x, dir.y, cl2, ch, BUILD_FX.COLOR.CRACK);
        for (const mob of this.rt.fx.inLine(ex, ey, dir.x, dir.y, cl2, ch))
          if (!this.execute(mob, dir))
            this.strike(
              mob,
              this.payload(ex, ey, dir, param(cl, 'crackMult'), 'unblockable', { ignoreGuard: true }),
              dir,
            );
      }
    });
    this.last = { move: 'unblockable', crit, len, t: Math.round(this.now) };
    this.rt.record('unblockable');
  }

  /** 일도양단 처형: HP 비율 이하 일반 적 즉시 처치 (보스·엘리트는 피해 ×bossMult). 처리했으면 true */
  private execute(mob: Mob, dir: Dir): boolean {
    const cl = this.rt.rule('cleave');
    if (!cl || !mob.active) return false;
    const neck = this.rt.rule('neckCut');
    const ratio = neck ? param(neck, 'executeRatio') : param(cl, 'executeRatio');
    if (mob.hp / mob.maxHp > ratio) return false;
    if (mob.isBoss) {
      this.strike(
        mob,
        this.payload(mob.x, mob.y, dir, param(cl, 'bossMult') * this.mp('batto', 'damageMult'), 'unblockable', {
          ignoreGuard: true,
        }),
        dir,
      );
      return true;
    }
    this.rt.fx.callout(BUILD_FX.TEXT.EXECUTE);
    this.rt.fx.raw(mob, mob.hp + 1, { dirX: dir.x, dirY: dir.y, heavy: true });
    if (neck) this.rt.combat.restoreResource({ kenkiStage: param(neck, 'kenkiStages', 1) });
    this.rt.record('execute');
    return true;
  }

  /** 갈래·강화 판정 배율 (그림 배율 = 판정 배율, 55 Q15) */
  private hitScale(): number {
    const reach = gameState.weapon.hitbox.reach / Math.max(1, gameState.weapon.def.hitbox.reach);
    return reach * (gameState.weapon.def.kind === 'melee' ? PLAYER_HIT_SCALE : 1);
  }

  // --- 대검: 차지 균열(58 Q3, 모든 갈래 공통)에 갈래 효과를 더한다 ---

  /** 공격 페이로드 (BuildCombat.onAttack 에서) */
  onAttack(p: PlayerAttackPayload): void {
    const w = gameState.weapon.id;
    if (w === 'greatsword') this.greatswordAttack(p);
    if (w === 'bow') this.bowAttack(p);
    if (w === 'dagger') this.danceEcho(p);
  }

  private greatswordAttack(p: PlayerAttackPayload): void {
    const g = this.g;
    // 각성 산붕: 4타(V) 내려찍기마다 충격파
    const fall = this.rt.rule('mountainFall');
    if (fall && p.comboIndex === param(fall, 'comboIndex', 3)) {
      g.time.delayedCall(Math.max(0, p.swingDelayMs), () => {
        const pl = g.player;
        const len = T(param(fall, 'waveTiles'));
        this.crackLine(pl.x, pl.y, { x: p.dirX, y: p.dirY }, len, TILE * 0.6, param(fall, 'waveMult'), 'mountainFall');
      });
    }
  }

  /**
   * 대검 차지 균열 (58 Q3, 시스템 A 의 CrackLineStrikes 가 판정 순간 부른다 — 갈래별 충격파 교체 지점):
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
    const g = this.g;
    const cl = p.crackLine;
    if (!cl) return { skip: false, sheet: null };
    const stageIdx = Math.max(0, cl.stage - 1);
    if (this.rt.hasBranch('weight')) {
      this.quakeRing(origin, stageIdx, cl.stage);
      return { skip: true, sheet: null };
    }
    let sheet: string | null = null;
    if (this.rt.hasBranch('crush')) {
      const prefix = this.moveParams('crush').crackSheet;
      const id = typeof prefix === 'string' && tiles > 0 ? `${prefix}${Math.min(5, Math.max(1, tiles))}` : null;
      sheet = id && g.fx.has(id) ? id : null;
      const road = this.rt.rule('splitRoad');
      // 앞머리를 따라 몇 번 쓸어 지운다 (갈라진 길이면 반사)
      const sweeps = 4;
      for (let i = 0; i <= sweeps; i++)
        g.time.delayedCall((i * 320) / sweeps, () => {
          if (g.scene.isActive())
            this.clearShotsOnLine(origin, dir, (lengthPx * (i + 1)) / (sweeps + 1), cl.halfWidthPx, Boolean(road));
        });
      if (road) this.rt.combat.splitRoadUntil = this.now + param(road, 'ms');
    }
    const end = { x: origin.x + dir.x * lengthPx, y: origin.y + dir.y * lengthPx };
    const quake = this.rt.rule('quake') ?? this.rt.rule('allSplit');
    if (quake && lengthPx > 0) {
      const deg = param(quake, 'splitDeg', 25);
      const qlen = T(param(quake, 'lengthTiles', 2.5));
      g.time.delayedCall(260, () => {
        if (!g.scene.isActive()) return;
        for (const sgn of [-1, 0, 1]) {
          const a = Math.atan2(dir.y, dir.x) + (sgn * deg * Math.PI) / 180;
          this.crackLine(
            end.x,
            end.y,
            { x: Math.cos(a), y: Math.sin(a) },
            qlen,
            cl.halfWidthPx,
            param(quake, 'damageMult', 0.6),
            'quake',
          );
        }
      });
    }
    const bear = this.rt.rule('bossStun');
    if (bear && cl.stage >= 3)
      for (const m of this.rt.fx.inLine(origin.x, origin.y, dir.x, dir.y, lengthPx, cl.halfWidthPx))
        this.bossStun(m, bear);
    this.last = { move: 'crack', tiles, sheet, t: Math.round(this.now) };
    return { skip: false, sheet };
  }

  /** 균열 한 줄 (판정 + 윤곽) */
  private crackLine(x: number, y: number, dir: Dir, len: number, half: number, mult: number, move: string): void {
    if (len <= 0) return;
    this.rt.fx.lineFx(x, y, dir.x, dir.y, len, half, BUILD_FX.COLOR.CRACK);
    for (const m of this.rt.fx.inLine(x, y, dir.x, dir.y, len, half))
      this.strike(m, this.payload(x, y, dir, mult, move), dir);
  }

  /** 균열 위 적 탄: 지움 (갈라진 길이면 반사) */
  private clearShotsOnLine(
    start: { x: number; y: number },
    dir: Dir,
    len: number,
    half: number,
    reflect: boolean,
  ): void {
    for (const child of this.g.projectiles.getChildren()) {
      const pr = child as Projectile;
      if (!pr.active || pr.reflected || pr.owner !== 'enemy') continue;
      const dx = pr.x - start.x;
      const dy = pr.y - start.y;
      const along = dx * dir.x + dy * dir.y;
      if (along < 0 || along > len || Math.abs(dx * dir.y - dy * dir.x) > half + 4) continue;
      if (reflect) pr.reflect(1);
      else {
        // 파쇄: 균열에 삼켜진 탄 자리 greatsword_shatter_snuff
        const snuff = this.moveParams('crush').snuffFx;
        if (typeof snuff === 'string' && this.g.fx.has(snuff))
          this.g.fx.play(snuff, pr.x, pr.y, { depth: DEPTH.HIT_FX });
        pr.deactivate();
      }
    }
  }

  /** 중압 원형 진동 (+ 짓눌린 숨 울분 · 술독 짓누르기 웅덩이 모으기) */
  private quakeRing(at: { x: number; y: number }, stageIdx: number, stage = stageIdx + 1): void {
    const g = this.g;
    const id = 'weight';
    const giant = this.rt.rule('giant');
    const r = giant && stageIdx >= 3 ? T(param(giant, 'ringRadiusTiles')) : T(this.mp(id, 'radiusTiles', stageIdx));
    const pull = T(this.mp(id, 'pullTiles'));
    // fx greatsword_quake_ring (행 lv1~3 = 차지 단계, 중심 slam_point, 바닥 깊이) — 그림 반경에 판정 반경을 맞춘다
    const ringId = this.moveParams(id).ringFx;
    const ringDef = typeof ringId === 'string' && g.fx.has(ringId) ? g.fx.sheet(ringId) : undefined;
    if (ringDef && typeof ringId === 'string') {
      const radii = (ringDef as { radiusPxByStage?: Record<string, number> }).radiusPxByStage;
      const row = `lv${Math.min(3, Math.max(1, stage))}`;
      const drawnR = (radii?.[row] ?? r / artScale(ringDef)) * artScale(ringDef);
      g.fx.play(ringId, at.x, at.y, { dir: row, depth: DEPTH.FX_GROUND, scaleMult: drawnR > 0 ? r / drawnR : 1 });
    } else {
      this.rt.fx.ring(at.x, at.y, r, BUILD_FX.COLOR.RING);
      g.combat.drawShockwave(at.x, at.y, r);
    }
    const hits = this.rt.fx.inCircle(at.x, at.y, r);
    for (const m of hits) {
      const d = { x: at.x - m.x, y: at.y - m.y };
      const died = this.strike(
        m,
        this.payload(at.x, at.y, { x: -d.x, y: -d.y }, this.mp(id, 'damageMult'), 'quakeRing'),
        { x: -d.x, y: -d.y },
        {
          stunMs: this.mp(id, 'stunMs'),
        },
      );
      if (!died && !m.isBoss && m.active) m.shove(d.x, d.y, Math.min(pull, Math.hypot(d.x, d.y)), 140);
    }
    const breath = this.rt.rule('ringGrudge');
    const gr = g.player.gauges.grudge;
    if (breath && gr) gr.value = Math.min(gr.max, gr.value + gr.max * param(breath, 'perHit') * hits.length);
    const jar = this.rt.rule('jarCrush');
    if (jar) {
      const pools = this.rt.fx.poolsNear(at.x, at.y, r);
      if (pools.length > 0) {
        for (const q of pools) q.until = this.now;
        const big = this.rt.fx.liquorPool(at.x, at.y, T(param(jar, 'radiusTiles')), 8000);
        const burstR = T(param(jar, 'burstRadiusTiles'));
        big.spec.onIgnite = () => {
          this.rt.fx.ring(at.x, at.y, burstR, BUILD_FX.COLOR.BURN);
          for (const m of this.rt.fx.inCircle(at.x, at.y, burstR))
            this.rt.fx.damage(m, param(jar, 'burstMult'), { dirX: 0, dirY: 0 });
        };
      }
    }
    this.last = { move: 'quakeRing', r, hits: hits.length, t: Math.round(this.now) };
  }

  private bossStun(m: Mob, r: ActiveRule): void {
    if (!m.isBoss || !m.active) return;
    const at = this.bossStunAt.get(m) ?? -Infinity;
    if (this.now - at < param(r, 'cooldownMs')) return;
    this.bossStunAt.set(m, this.now);
    m.stun(this.now, param(r, 'stunMs'), 'hit');
    this.rt.record('bossStun');
  }

  /** 반향: 퍼펙트 가드 순간 울분 30% 소모 → 막은 방향 균열 반격. 각성 산붕(반향): 일반 가드도 50% */
  onPerfect(kind: PerfectKind, _attack: number, dx: number, dy: number): void {
    if (kind === 'perfectGuard') this.resonance(dx, dy, 1);
    if (kind === 'perfectRelease') this.onPerfectRelease();
  }

  private onSecondary(p: PlayerSecondaryPayload): void {
    if (p.kind !== 'guard' || p.phase !== 'block') return;
    const echo = this.rt.rule('guardEcho');
    // 퍼펙트 가드는 onPerfect 가 따로 — 같은 프레임 퍼펙트면 건너뜀
    if (echo && this.g.player.defense.lastOutcome !== 'perfect') {
      const f = this.g.player.facingVec;
      this.resonance(f.x, f.y, param(echo, 'mult', 0.5));
    }
  }

  private resonance(dx: number, dy: number, mult: number): void {
    const r = this.rt.rule('resonance');
    const gr = this.g.player.gauges.grudge;
    if (!r || !gr) return;
    const cost = gr.max * param(r, 'grudgeCost');
    if (gr.value < cost) return;
    gr.value -= cost;
    const pl = this.g.player;
    const len = Math.hypot(dx, dy) || 1;
    const dir = { x: dx / len, y: dy / len };
    const counter = 1 + this.rt.stat('perfectCounterMult');
    this.crackLine(
      pl.x,
      pl.y,
      dir,
      T(param(r, 'lengthTiles')),
      T(param(r, 'widthTiles', 1)) / 2,
      param(r, 'damageMult') * mult * counter,
      'resonance',
    );
    this.rt.record('resonance');
  }

  /** 울혈: 그로기 진입 울분 +50% · 그로기가 풀릴 때 울분 가득이면 자동 진동 폭발 */
  onResource(event: string): void {
    const r = this.rt.rule('clot');
    const gr = this.g.player?.gauges.grudge;
    if (!r || !gr) return;
    if (event === 'groggy') gr.value = Math.min(gr.max, gr.value + gr.max * param(r, 'grudgeOnGroggy'));
    if (event === 'recovered' && gr.full) {
      gr.value = 0;
      const pl = this.g.player;
      const rad = T(param(r, 'burstRadiusTiles'));
      this.rt.fx.ring(pl.x, pl.y, rad, BUILD_FX.COLOR.RING);
      this.g.combat.drawShockwave(pl.x, pl.y, rad);
      for (const m of this.rt.fx.inCircle(pl.x, pl.y, rad))
        this.strike(m, this.payload(pl.x, pl.y, { x: m.x - pl.x, y: m.y - pl.y }, param(r, 'burstMult'), 'clot'), {
          x: m.x - pl.x,
          y: m.y - pl.y,
        });
      this.rt.record('clotBurst');
    }
  }

  // --- 단검 ---

  /** 질풍: 부채꼴 투척 (대쉬 직후 좌클릭) — 적중 시 낙인. 비도 5개·45° + 박힌 단검 */
  private fanThrow(dir: Dir): void {
    const g = this.g;
    const pl = g.player;
    const id = 'gale';
    const now = this.now;
    if (now < this.throwReadyAt) return;
    const wind = this.rt.rule('windBlade');
    const fly = this.rt.rule('flyknife');
    const count = fly ? param(fly, 'count', 5) : wind ? param(wind, 'count', 5) : this.mp(id, 'count');
    const spread = fly ? param(fly, 'spreadDeg', 45) : this.mp(id, 'spreadDeg');
    this.throwReadyAt = now + this.mp(id, 'cooldownMs') - (wind ? param(wind, 'cooldownCutMs') : 0);
    const res = pl.resource;
    if (res?.kind === 'heat') res.heatBy(res.max * (this.mp(id, 'heat') / 100), now);
    const sm = this.rt.combat.shotMods();
    const speed = this.mp(id, 'speedTiles') * sm.speedMult;
    const life = (T(this.mp(id, 'rangeTiles')) / (speed * TILE)) * 1000 * (1 + this.rt.stat('projectileRangeMult'));
    const { dmg, crit } = g.combat.rollDamage(this.mp(id, 'damageMult'), false, 'dashAttack');
    const bottle = this.rt.rule('liquorThrow');
    const base = Math.atan2(dir.y, dir.x);
    const sprite = this.moveParams(id).projectile;
    // 몸 dagger_fan_throw (releaseFrame 시작 = 투사체 생성) · fx 는 그보다 조금 앞 (아트 spawnAtMs)
    this.body(id, 1, dir, 220);
    g.time.delayedCall(this.mp(id, 'throwFxAtMs'), () => {
      if (g.scene.isActive()) this.playFx(this.moveParams(id).throwFx, pl.x, pl.y, dir, { follow: true });
    });
    const release = () => {
      if (!g.scene.isActive()) return;
      for (let i = 0; i < count; i++) {
        const t = count === 1 ? 0 : i / (count - 1) - 0.5;
        const a = base + ((spread * Math.PI) / 180) * t;
        const isBottle = Boolean(bottle) && i === Math.floor(count / 2);
        const s = this.rt.fx.shot(pl.x + Math.cos(a) * 6, pl.y - 6 + Math.sin(a) * 6, Math.cos(a), Math.sin(a), dmg, {
          tag: isBottle ? 'bottle' : 'fanThrow',
          speedTiles: speed,
          lifeMs: life,
          pierce: sm.pierceAdd,
          crit,
          ...(isBottle
            ? { tint: BUILD_FX.COLOR.LIQUOR }
            : typeof sprite === 'string'
              ? { sprite }
              : { tint: BUILD_FX.COLOR.THROW }),
        });
        if (s && (fly || isBottle)) s.onEnd = (shot) => this.onThrowEnd(shot);
      }
    };
    const at = this.mp(id, 'releaseAtMs');
    if (at > 0) g.time.delayedCall(at, release);
    else release();
    this.last = { move: 'fanThrow', count, t: Math.round(now) };
    this.rt.record('fanThrow', count);
  }

  /** 던진 단검·술병이 끝남 (벽·사거리) — 비도 박힘 · 술병 웅덩이 */
  private onThrowEnd(shot: Projectile): void {
    if (shot.buildTag === 'bottle') this.bottleSplash(shot.x, shot.y);
    else this.stick(shot.x, shot.y);
  }

  /** 빌드 투사체 적중 (GameCombat.onPlayerShotHit 뒤) */
  onShotHit(shot: Projectile, mob: Mob, died: boolean): void {
    // 저격 관통 화살이 꿰뚫는 자리 (진행 각도로)
    if (this.rt.isPerfectShot(shot) && this.rt.hasBranch('snipe')) {
      const v = shot.body.velocity;
      const id = this.moveParams('snipe').pierceHitFx;
      if (typeof id === 'string' && this.g.fx.has(id))
        this.g.fx.play(id, mob.body.center.x, mob.body.center.y, {
          angle: Math.atan2(v.y, v.x),
          flipY: v.x < 0,
          depth: DEPTH.HIT_FX,
        });
    }
    if (shot.buildTag === 'fanThrow' || shot.buildTag === 'bottle') {
      if (!died) this.g.strikes.brands.onHit(mob, shot.body.velocity.x, shot.body.velocity.y);
      if (shot.buildTag === 'bottle') this.bottleSplash(mob.x, mob.y);
      else if (this.rt.rule('flyknife')) this.stick(mob.x, mob.y);
    }
  }

  private bottleSplash(x: number, y: number): void {
    const b = this.rt.rule('liquorThrow');
    if (!b) return;
    const pool = this.rt.fx.liquorPool(x, y, T(param(b, 'radiusTiles', 1)), 6000);
    const res = this.g.player.resource;
    if (res?.kind === 'heat' && res.value >= res.max * param(b, 'fireHeat', 0.5)) this.g.pools.ignite(pool);
  }

  private stick(x: number, y: number): void {
    const fly = this.rt.rule('flyknife');
    if (!fly) return;
    const s = BUILD_FX.STUCK_KNIFE_PX;
    const gfx = this.g.add.rectangle(x, y, s, s, BUILD_FX.COLOR.THROW, 0.9).setDepth(DEPTH.PICKUP);
    this.stuck.push({ x, y, until: this.now + param(fly, 'stuckMs'), gfx });
  }

  /** 비도: 그림자 걸음이 박힌 단검으로 (가장 최근) — 쓰면 과열 −10%. 없으면 null */
  takeStuckKnife(): { x: number; y: number } | null {
    const fly = this.rt.rule('flyknife');
    if (!fly || this.stuck.length === 0) return null;
    const k = this.stuck.pop()!;
    k.gfx.destroy();
    const res = this.g.player.resource;
    if (res?.kind === 'heat' && !res.overheated)
      res.value = Math.max(0, res.value - res.max * param(fly, 'heatRefund'));
    return { x: k.x, y: k.y };
  }

  /** 낙인 기폭 배율 (쌍격 +30%, 표식 6 +40%) */
  brandBurstMult(): number {
    let m = 1;
    if (this.rt.hasBranch('twin')) m *= 1 + this.mp('twin', 'burstBonus');
    const det = this.rt.rule('markDetonate');
    if (det) m *= 1 + param(det, 'brandBurstMult');
    return m;
  }

  /** 출혈(2단 β): 기폭 즉시 비율 (나머지는 출혈) — 없으면 1 */
  brandImmediateRatio(): number {
    const r = this.rt.rule('brandBleed');
    return r ? param(r, 'immediate', 1) : 1;
  }

  /** 낙인 기폭 뒤 (BrandMarks.explode): 쌍격 분신 교차 · 쌍낙인 · 난무 · 출혈 · 각성 백귀 */
  onBrandBurst(mob: Mob, marks: number, dmg: number, died: boolean): void {
    const g = this.g;
    const at = { x: mob.body.center.x, y: mob.body.center.y };
    const pl = g.player;
    const back = { x: at.x - pl.x, y: at.y - pl.y };
    const bl = Math.hypot(back.x, back.y) || 1;
    // 출혈: 나머지를 출혈로
    const bleed = this.rt.rule('brandBleed');
    if (bleed && !died && mob.active) {
      const rest = dmg * (1 / Math.max(0.01, param(bleed, 'immediate', 1)) - 1);
      const ticks = Math.max(1, Math.round(param(bleed, 'bleedMs') / param(bleed, 'tickMs')));
      const fast = this.rt.rule('fastBleed');
      const tickMs = param(bleed, 'tickMs') * (fast ? param(fast, 'tickMult', 1) : 1);
      this.rt.dots.apply(
        mob,
        'bleed',
        this.now,
        ticks * tickMs * (1 + this.rt.stat('dotDurationMult')),
        tickMs,
        Math.max(1, Math.round(rest / ticks)),
      );
    }
    // 쌍격: 반대편 분신 교차 베기 (×cloneMult)
    if (this.rt.hasBranch('twin')) {
      const cx = at.x + (back.x / bl) * TILE;
      const cy = at.y + (back.y / bl) * TILE;
      // fx dagger_cross_clone: 대상 히트박스 중심, 행 = 주인공이 그 적을 바라보는 방향, 생성 + 120ms 교차 베기
      const drawn = this.playFx(this.moveParams('twin').cloneFx, at.x, at.y, { x: back.x / bl, y: back.y / bl });
      g.time.delayedCall(this.mp('twin', 'cloneDelayMs'), () => {
        if (!g.scene.isActive()) return;
        if (!drawn) this.rt.fx.clone(cx, cy);
        if (mob.active)
          this.rt.fx.raw(mob, dmg * this.mp('twin', 'cloneMult'), { dirX: -back.x, dirY: -back.y, heavy: true });
        this.rt.record('twinClone', marks);
        const tb = this.rt.rule('twinBrand');
        if (tb) {
          const next = this.rt.fx.nearest(at.x, at.y, T(param(tb, 'rangeTiles')), new Set([mob]));
          if (next) for (let i = 0; i < param(tb, 'brands', 2); i++) g.strikes.brands.onHit(next, back.x, back.y);
        }
      });
    }
    // 난무: 5스택 기폭 뒤 분신이 남아 연격을 따라 함 (각성 백귀 난무 = 6초)
    const dance = this.rt.rule('dance');
    if (dance && marks >= param(dance, 'minMarks', 5)) {
      const long = this.rt.rule('danceLong');
      this.danceUntil = this.now + (long ? param(long, 'ms') : param(dance, 'ms'));
    }
    // 각성 백귀: 기폭마다 분신 3체
    const demons = this.rt.rule('hundredDemons');
    if (demons) {
      const n = param(demons, 'clones', 3);
      for (let i = 0; i < n; i++) {
        const a = (i / n) * Math.PI * 2;
        g.time.delayedCall(80 * (i + 1), () => {
          if (!g.scene.isActive()) return;
          this.rt.fx.clone(at.x + Math.cos(a) * TILE, at.y + Math.sin(a) * TILE);
          for (const m of this.rt.fx.inCircle(at.x, at.y, T(1.5)))
            this.rt.fx.damage(m, param(demons, 'cloneMult'), { dirX: -Math.cos(a), dirY: -Math.sin(a) });
        });
      }
    }
  }

  /** 난무 분신: 연격을 반대편에서 따라 함 (×damageMult) */
  private danceEcho(p: PlayerAttackPayload): void {
    const dance = this.rt.rule('dance');
    if (!dance || this.now >= this.danceUntil || p.comboIndex === undefined) return;
    const g = this.g;
    const pl = g.player;
    const reach = gameState.weapon.hitbox.reach * 1.4;
    g.time.delayedCall(param(dance, 'delayMs', 120), () => {
      if (!g.scene.isActive()) return;
      const t = this.rt.fx.nearest(pl.x, pl.y, reach * 2);
      if (!t) return;
      const cx = t.x + (t.x - pl.x);
      const cy = t.y + (t.y - pl.y);
      this.rt.fx.clone(cx, cy);
      this.rt.fx.damage(t, p.damageMult * param(dance, 'damageMult'), { dirX: pl.x - t.x, dirY: pl.y - t.y });
    });
  }

  // --- 활 ---

  private bowAttack(p: PlayerAttackPayload): void {
    const g = this.g;
    // 천공: 완벽 놓기 연결 스택 (놓치면 0)
    if (p.kind === 'aimed') {
      if (p.bowPower !== 'perfect') this.stacks = 0;
    }
    // 연궁: 연사 3발마다 분열 (각성 유성 = 매 발)
    const volley = this.rt.rule('volley');
    if (volley && currentAttackTag() === 'rapidVolley') {
      this.volleyCount += 1;
      const every = this.rt.rule('splitEvery') ? 1 : param(volley, 'every', 3);
      if (this.volleyCount % every === 0) {
        g.time.delayedCall(Math.max(0, p.releaseDelayMs), () => {
          const pl = g.player;
          const base = Math.atan2(p.dirY, p.dirX);
          const sp = (param(volley, 'spreadDeg', 14) * Math.PI) / 180;
          const { dmg } = g.combat.rollDamage(p.damageMult * param(volley, 'splitMult'), false, 'attack');
          for (const s of [-1, 1])
            this.rt.fx.shot(pl.x, pl.y - 6, Math.cos(base + s * sp), Math.sin(base + s * sp), dmg, {
              tag: 'split',
              speedTiles: 12,
              lifeMs: 900,
            });
        });
      }
    }
  }

  /** 완벽 놓기 (활): 천공 스택 · 숨 고르기 · 유성 하늘 화살 */
  private onPerfectRelease(): void {
    const sky = this.rt.rule('skypierce');
    if (sky) {
      const cap = this.rt.rule('stackCap');
      const max = cap ? param(cap, 'maxStacks') : param(sky, 'maxStacks', 3);
      this.stacks = Math.min(max, this.stacks + 1);
      const breath = this.rt.rule('stackBreath');
      const br = this.g.player.gauges.breath;
      if (breath && br && this.stacks >= 3) br.value = br.max;
    }
  }

  /** 화살 발사 배율 (BowShots — 천공 스택 피해, 필중 정밀 조준 치명, 장교 사냥은 적중 때) */
  arrowBonus(p: PlayerAttackPayload): { mult: number; forceCrit: boolean; wallPierce: boolean; sizeMult: number } {
    let mult = 1;
    let forceCrit = false;
    let wallPierce = false;
    let sizeMult = 1;
    if (p.bowPower === 'perfect') {
      // 저격 1단: 완벽 놓기 피해 +25%
      if (this.rt.hasBranch('snipe')) mult *= this.mp('snipe', 'perfectMult') || 1;
      const sky = this.rt.rule('skypierce');
      if (sky && this.stacks > 0) {
        mult *= 1 + this.stacks * param(sky, 'perStack');
        sizeMult *= 1 + this.stacks * param(sky, 'perStack');
        wallPierce = this.stacks >= 3;
      }
      if (this.rt.rule('deadeye') && this.g.player.gauges.focusing(this.now)) forceCrit = true;
    }
    return { mult, forceCrit, wallPierce, sizeMult };
  }

  /** 화살이 나감 (BowShots) — 천공 3스택 선 폭발 · 불화살 한 발 · 유성 */
  onArrowSpawn(shot: Projectile, p: PlayerAttackPayload): void {
    const b = this.arrowBonus(p);
    // 저격 1단 관통 화살: 완벽 놓기 화살 = 최대 pierce 명 관통 + 전용 화살 그림 (bow_arrow 대신)
    if (p.bowPower === 'perfect' && this.rt.hasBranch('snipe')) {
      const n = this.mp('snipe', 'pierce');
      if (n > 0 && !this.rt.rule('skypierce')) shot.pierceLeft = n;
      this.rt.fx.restyle(shot, String(this.moveParams('snipe').arrowFx ?? ''));
    }
    if (b.wallPierce) {
      shot.wallPierce = true;
      const sky = this.rt.rule('skypierce')!;
      const from = { x: shot.x, y: shot.y };
      const v = shot.body.velocity;
      const dir = { x: v.x, y: v.y };
      const dl = Math.hypot(dir.x, dir.y) || 1;
      this.g.time.delayedCall(param(sky, 'lineDelayMs'), () => {
        if (!this.g.scene.isActive()) return;
        const len = Math.hypot(shot.x - from.x, shot.y - from.y) || T(8);
        this.crackLine(
          from.x,
          from.y,
          { x: dir.x / dl, y: dir.y / dl },
          len,
          T(param(sky, 'lineWidthTiles', 0.8)) / 2,
          param(sky, 'lineMult'),
          'skypierce',
        );
      });
    }
    if (p.bowPower === 'perfect' && this.rt.rule('fireArrow')) {
      const tick = () => {
        if (!shot.active) return;
        this.g.pools.igniteAt(shot.x, shot.y);
        this.g.time.delayedCall(40, tick);
      };
      tick();
    }
  }

  /** 화살 적중 (GameCombat.onPlayerShotHit 뒤): 장교 사냥은 BowShots 거리로 — 여기서는 유성 하늘 화살·무한통 */
  onArrowHit(shot: Projectile, mob: Mob): void {
    const meteor = this.rt.rule('meteor');
    if (meteor && !shot.buildTag && this.rt.isPerfectShot(shot) && mob.active) {
      const c = mob.body.center;
      this.g.time.delayedCall(180, () => {
        if (!this.g.scene.isActive()) return;
        this.rt.fx.ring(c.x, c.y, T(0.8), BUILD_FX.COLOR.METEOR);
        for (const m of this.rt.fx.inCircle(c.x, c.y, T(0.8)))
          this.rt.fx.damage(m, param(meteor, 'skyMult'), { dirX: 0, dirY: 1 });
      });
    }
  }

  /** 장교 사냥: 8칸 이상 거리 완벽 놓기 = 치명 확정 (BowShots 적중 배율) */
  longPerfectCrit(shot: Projectile, mob: Mob): boolean {
    const r = this.rt.rule('longPerfectCrit');
    if (!r || !this.rt.isPerfectShot(shot)) return false;
    return Math.hypot(mob.x - shot.originX, mob.y - shot.originY) >= T(param(r, 'minTiles'));
  }

  // --- 처치 · 이동기 · 배율 ---

  onKill(_mob: Mob, _kind: string, info: { marks: number; brands: number; hadDot: boolean }): void {
    // 잔월: 처치 시 검기 1/3단
    const z = this.rt.rule('zangetsu');
    if (z) this.rt.combat.restoreResource({ kenkiStage: param(z, 'killKenkiStage') });
    // 무한통: 처치 시 화살 +3 · 쏟아지는 비 (연사 처치 +1 — 근사: 처치마다)
    const q = this.rt.rule('quiver');
    if (q) this.rt.combat.restoreResource({ ammo: param(q, 'killArrows') });
    const rain = this.rt.rule('volleyRefill');
    if (rain) this.rt.combat.restoreResource({ ammo: param(rain, 'ammo') });
    // 번지는 피: 출혈 적 처치 시 과열 −25%
    const sb = this.rt.rule('bleedKillCool');
    if (sb && info.hadDot) this.rt.combat.restoreResource({ heat: param(sb, 'heat') });
  }

  /** 이동기 (대쉬·그림자 걸음) — 열풍: 과열 +10% */
  onPlayerMove(_kind: 'dash' | 'shadowstep'): void {
    const hw = this.rt.rule('heatwave');
    const res = this.g.player?.resource;
    if (hw && res?.kind === 'heat') res.heatBy(res.max * param(hw, 'heatPerMove'), this.now);
  }

  moveSpeedMult(_now: number): number {
    return this.heatwaveMult();
  }

  attackSpeedMult(_now: number): number {
    return this.heatwaveMult();
  }

  /** 열풍: 과열 50% 이상이면 이동·공속 +20% */
  private heatwaveMult(): number {
    const hw = this.rt.rule('heatwave');
    const res = this.g.player?.resource;
    if (!hw || res?.kind !== 'heat' || res.overheated) return 1;
    return res.value >= res.max * param(hw, 'hasteFrom') ? 1 + param(hw, 'haste') : 1;
  }

  update(now: number): void {
    if (this.busy && now >= this.busyUntil) this.busy = false;
    this.vortexTick(now);
    if (this.stuck.length > 0) {
      for (const k of this.stuck) if (now >= k.until) k.gfx.destroy();
      this.stuck = this.stuck.filter((k) => now < k.until);
    }
    // 각성 유성: 3초마다 자동 화살비 (가장 가까운 적 자리)
    const meteor = this.rt.rule('meteor');
    if (meteor && now - this.meteorAt >= param(meteor, 'autoRainMs')) {
      this.meteorAt = now;
      const pl = this.g.player;
      const t = this.rt.fx.nearest(pl.x, pl.y, T(10));
      if (t) {
        const r = T(param(meteor, 'rainRadiusTiles'));
        this.rt.fx.ring(t.x, t.y, r, BUILD_FX.COLOR.METEOR);
        for (const m of this.rt.fx.inCircle(t.x, t.y, r))
          this.rt.fx.damage(m, param(meteor, 'rainMult'), { dirX: 0, dirY: 1 });
      }
    }
    // 무한통 각성: 탄창 무한
    if (this.rt.rule('infiniteAmmo')) {
      const res = this.g.player?.resource;
      if (res?.kind === 'ammo') res.value = res.max;
    }
  }

  debug(): Record<string, unknown> {
    return {
      ...this.last,
      busy: this.busy,
      vortex: Boolean(this.vortex),
      stacks: this.stacks,
      stuck: this.stuck.length,
      dance: this.now < this.danceUntil,
      throwReadyIn: Math.max(0, Math.round(this.throwReadyAt - this.now)),
    };
  }

  destroy(): void {
    EventBus.off(Events.PLAYER_BRANCH_MOVE, this.onMove, this);
    EventBus.off(Events.PLAYER_SECONDARY, this.onSecondary, this);
    for (const k of this.stuck) k.gfx.destroy();
    this.stuck = [];
  }
}
