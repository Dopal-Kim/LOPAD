/**
 * 갈래 수단 공용 도우미 (60라운드 6-1 정리 — BranchStrikes 에서 분리, 동작 그대로): 노드 수치 읽기 · 한 타 피해 · 페이로드 ·
 * 몸 동작 · 수단 이펙트 재생 · 판정 배율 · 균열 한 줄 · 바쁨(강공 중) 표시. 무기별 갈래(Katana/Greatsword/Dagger/BowBranch)가 함께 쓴다.
 */
import { BUILD_FX, DEPTH, TILE, entityDepth } from '../../../../core/Constants';
import { EventBus, Events, type BranchEffectPayload, type PlayerAttackPayload } from '../../../../core/EventBus';
import { gameState } from '../../../../core/GameState';
import type { Mob } from '../../../../objects/Mob';
import { comboAction } from '../../../../systems/sprites/spriteActions';
import { facingOf, frameDurations, rowDirFor } from '../../../../systems/sprites/spriteDefs';
import { PLAYER_HIT_SCALE, PLAYER_RENDER_SCALE } from '../../../../systems/weapon/playerScale';
import type { Game } from '../../../Game';
import type { BuildRuntime } from '../BuildRuntime';

export const T = (tiles: number): number => tiles * TILE;

export type Dir = { x: number; y: number };
export type BranchPayload = PlayerAttackPayload & { buildMove?: string; ignoreGuard?: boolean };

export interface FxOpts {
  follow?: boolean;
  row?: string;
  /** 그림 배율 (기본 = 주인공 렌더 배율) */
  scaleMult?: number;
  depth?: number;
}

export class BranchKit {
  /** 갈래 동작 중 (강공 — 중량 6 감소·끊기지 않음) */
  busy = false;
  private busyUntil = -Infinity;
  /** 디버그: 마지막 갈래 동작 */
  last: Record<string, unknown> = {};

  constructor(
    readonly g: Game,
    readonly rt: BuildRuntime,
  ) {}

  get now(): number {
    return this.g.time.now;
  }

  /** 60라운드 음향 훅: 갈래 효과 순간 (BRANCH_EFFECT — branch = 시스템 노드 id) */
  effect(branch: string, effect: string, stack?: number): void {
    EventBus.emit(Events.BRANCH_EFFECT, {
      branch,
      effect,
      ...(stack !== undefined ? { stack } : {}),
    } satisfies BranchEffectPayload);
  }

  moveParams(id: string): Record<string, unknown> {
    return gameState.weapon.nodes.find((n) => n.id === id)?.moveParams ?? {};
  }

  /** 노드 수단 수치 (배열이면 단계 번호로) */
  mp(id: string, key: string, stageIdx = 0): number {
    const v = this.moveParams(id)[key];
    if (Array.isArray(v)) return Number(v[Math.max(0, Math.min(v.length - 1, stageIdx))]) || 0;
    return typeof v === 'number' ? v : 0;
  }

  /** 노드 수단 문자열 (fx 시트 id 등 — 없으면 null) */
  mpStr(id: string, key: string): string | null {
    const v = this.moveParams(id)[key];
    return typeof v === 'string' && v ? v : null;
  }

  /** 갈래 수단 한 타 (근접 타격 경로와 같은 순서: 빌드 배율 → 피해 → 처치 / 타격 뒤 효과) */
  strike(mob: Mob, p: BranchPayload, dir: Dir, opts: { stunMs?: number } = {}): boolean {
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
    else if (opts.stunMs) {
      mob.stun(this.now, opts.stunMs, 'hit');
      this.rt.art.stagger(mob, opts.stunMs);
    }
    this.rt.combat.afterStrike(mob, p, crit, died);
    if (!died) g.strikes.brands.onHit(mob, dir.x, dir.y);
    return died;
  }

  payload(
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
  body(nodeId: string, n: number, dir: Dir, ms: number, fromFrame = 0): void {
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
  playFx(id: unknown, x: number, y: number, dir: Dir, opts: FxOpts = {}): boolean {
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
        depth: opts.depth ?? entityDepth(y) + DEPTH.OVERLAY_STEP * 2,
        scaleMult: opts.scaleMult ?? PLAYER_RENDER_SCALE,
      }) !== null
    );
  }

  setBusy(ms: number): void {
    this.busy = true;
    this.busyUntil = Math.max(this.busyUntil, this.now + ms);
  }

  tickBusy(now: number): void {
    if (this.busy && now >= this.busyUntil) this.busy = false;
  }

  /** 갈래·강화 판정 배율 (그림 배율 = 판정 배율, 55 Q15) */
  hitScale(): number {
    const reach = gameState.weapon.hitbox.reach / Math.max(1, gameState.weapon.def.hitbox.reach);
    return reach * (gameState.weapon.def.kind === 'melee' ? PLAYER_HIT_SCALE : 1);
  }

  /**
   * 균열·선 한 줄 (판정 + 표시): fx 시트가 있으면 선 시작에서 회전해 그리고(`playLineFx`), 없거나 outline 이 true 면 윤곽.
   * 호출 쪽이 이미 그림을 그렸으면 outline: false
   */
  line(
    x: number,
    y: number,
    dir: Dir,
    len: number,
    half: number,
    mult: number,
    move: string,
    opts: { fx?: string | null; outline?: boolean } = {},
  ): void {
    if (len <= 0) return;
    const drawn = opts.fx ? this.playLineFx(opts.fx, x, y, dir, len) : false;
    if (!drawn && opts.outline !== false) this.rt.fx.lineFx(x, y, dir.x, dir.y, len, half, BUILD_FX.COLOR.CRACK);
    for (const m of this.rt.fx.inLine(x, y, dir.x, dir.y, len, half))
      this.strike(m, this.payload(x, y, dir, mult, move), dir);
  }

  /** 선 모양 fx (BuildArt.lineFx — 선 시작에서 회전, 반복 타일·길이 맞춤) */
  playLineFx(id: string, x: number, y: number, dir: Dir, len: number): boolean {
    return this.rt.art.lineFx(id, x, y, dir.x, dir.y, len);
  }
}
