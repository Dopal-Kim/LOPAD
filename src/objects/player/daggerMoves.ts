/**
 * 56라운드 2단계 단검 새 기본기 (Q42·Q55, 계약 art §18.9):
 * - 등 뒤 치명 찌르기 `dagger_backstab` — 그림자 걸음 직후 좌클릭: 기존 확정 치명(+암살 배율)을 전용 동작으로, 전용 섬광만
 * - 고속 난타 `dagger_flurry` — 좌클릭 홀드: 시작 열 1회 → 홀드 동안 루프(찌르기 열마다 판정, 초당 약 11타, 과열 빠르게) →
 *   떼면 지금 찌르기의 당김 열까지 마치고 끝 열. 찌르기 시각은 몸 애니의 실제 열을 따른다(히트스톱에 함께 멈춤).
 *   fx 는 몸과 같은 열을 과열 단계 시트로 바꿔 낌 — 씬(MoveStrikes)이 `FlurryHold.view` 를 읽는다
 */
import { EventBus, Events, type PlayerAttackPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import type { BackstabMoveDef, FlurryMoveDef } from '../../data/types';
import type { InputState } from '../../systems/InputSystem';
import { artCandidates, pickArt } from '../../systems/weapon/comboArt';
import { facingOf, frameDurations, type Facing } from '../../systems/sprites/spriteDefs';
import type { Player } from '../Player';
import { aimDir, emitSkill, fireMoveStrike } from './moveStrike';
import { heatLevelOf, stabsCrossed } from '../../systems/weapon/flurryMath';

/** 시트가 없을 때 찌르기 간격 (초당 약 11타) */
const FALLBACK_STAB_MS = 90;

/** 등 뒤 치명 찌르기. 반환 = 동작 길이 ms */
export function startBackstab(p: Player, input: InputState, time: number, def: BackstabMoveDef): number {
  emitSkill('backstab', 'start');
  return fireMoveStrike(p, input, time, def, { move: 'backstab', extra: { noImpactFx: true } }).total;
}

function cols(v: unknown, fallback: number[]): number[] {
  return Array.isArray(v) && v.length > 0 && v.every((n) => typeof n === 'number') ? (v as number[]) : fallback;
}

/** 씬이 읽는 난타 상태 (fx 를 몸과 같은 열로) */
export interface FlurryView {
  column: number;
  facing: Facing;
  /** 과열 단계 fx 이름 (`<무기>_<이름>`) */
  fx: string;
}

export class FlurryHold {
  private readonly dir: { x: number; y: number };
  private readonly facing: Facing;
  private readonly action: string | null;
  private readonly startCols: number[];
  private readonly loopCols: number[];
  private readonly endCols: number[];
  private readonly stabCols: number[];
  private phase: 'start' | 'loop' | 'end' = 'start';
  private releasing = false;
  private lastCol = -1;
  private endAt = 0;
  /** 시트가 없을 때 다음 찌르기 시각 */
  private nextStabAt = 0;
  /** 디버그: 찌른 수 */
  stabs = 0;

  constructor(
    private readonly p: Player,
    private readonly def: FlurryMoveDef,
    input: InputState,
    time: number,
  ) {
    const a = aimDir(p, input);
    this.dir = a;
    this.facing = facingOf(a.x, a.y, p.visual.facing);
    const id = gameState.weapon.id;
    const name = pickArt(artCandidates(gameState.weapon.def.combo, def.art, 'body'), (n) =>
      p.visual.hasAction(`${id}_${n}`),
    );
    this.action = name ? `${id}_${name}` : null;
    const sheet = this.action ? p.visual.sheet(this.action) : undefined;
    const memo = sheet as { startFrames?: unknown; endFrames?: unknown } | undefined;
    this.startCols = cols(memo?.startFrames, [0, 1]);
    this.loopCols = cols(sheet?.loopFrames, [2, 3, 4, 5, 6, 7]);
    this.endCols = cols(memo?.endFrames, [8, 9]);
    this.stabCols = cols(sheet?.hitFrames, [2, 4, 6]);
    p.combo?.reset();
    p.clearLunges();
    p.gear.markDrawn(time);
    p.setAction('skill', 0);
    p.skillMoveMult = def.moveMult;
    if (this.action) p.visual.playFrames(this.action, this.facing, this.startCols, time);
    this.nextStabAt = time + (this.action ? 0 : FALLBACK_STAB_MS);
    emitSkill('flurry', 'start');
  }

  /** 지금 몸 열 (애니가 없으면 -1) */
  private column(): number {
    const sheet = this.action ? this.p.visual.sheet(this.action) : undefined;
    const cur = this.p.anims.currentFrame;
    if (!sheet || !cur || !this.p.anims.isPlaying) return -1;
    const fi = Number(cur.frame.name);
    return Number.isFinite(fi) ? fi % sheet.frames : -1;
  }

  /** 씬 fx 용 (끝났으면 null) */
  get view(): FlurryView | null {
    const col = this.column();
    if (col < 0 || (this.phase === 'end' && !this.p.anims.isPlaying)) return null;
    const res = this.p.resource;
    const ratio = res?.kind === 'heat' ? res.value / Math.max(1, res.max) : 0;
    const lv = Math.min(this.def.heatFx.length - 1, heatLevelOf(ratio, this.def.heatBounds));
    return { column: col, facing: this.facing, fx: `${gameState.weapon.id}_${this.def.heatFx[lv]}` };
  }

  /** 매 프레임. 계속이면 true */
  update(input: InputState, time: number): boolean {
    const p = this.p;
    if (!input.attackHeld) this.releasing = true;
    if (this.phase === 'end') {
      if (time < this.endAt) return true;
      p.skillMoveMult = 0;
      if (p.action === 'skill') p.setAction('normal', 0);
      return false;
    }
    if (!this.action) return this.updateFallback(time);
    const sheet = p.visual.sheet(this.action)!;
    if (this.phase === 'start' && !p.visual.isBusy(time)) {
      if (this.releasing) return this.finish(time);
      this.phase = 'loop';
      p.visual.loopFrames(this.action, this.facing, this.loopCols, frameDurations(sheet)[this.loopCols[0]] ?? 45);
    }
    const col = this.column();
    if (col !== this.lastCol) {
      // 지난 열 → 지금 열 사이에 지나간 찌르기 열 수 (프레임이 길어 열을 건너뛰어도 빠뜨리지 않는다)
      const n = this.phase === 'loop' ? stabsCrossed(this.loopCols, this.stabCols, this.lastCol, col) : 0;
      // 떼면: 지금 찌르기의 당김 열까지 마치고(다음 찌르기 열에 들어가는 순간) 끝 열
      if (n > 0 && this.releasing) return this.finish(time);
      this.lastCol = col;
      for (let i = 0; i < n; i++) this.stab(time);
    }
    return true;
  }

  private updateFallback(time: number): boolean {
    if (this.releasing) return this.finish(time);
    if (time >= this.nextStabAt) {
      this.nextStabAt = time + FALLBACK_STAB_MS;
      this.stab(time);
    }
    return true;
  }

  /** 끝 열 재생 → 끝나면 일반 상태 */
  private finish(time: number): boolean {
    const p = this.p;
    this.phase = 'end';
    const ms = this.action ? p.visual.playFrames(this.action, this.facing, this.endCols, time) : 0;
    this.endAt = time + ms;
    p.setAction('skill', this.endAt);
    p.slowUntil(this.endAt);
    emitSkill('flurry', 'end');
    if (ms <= 0) {
      p.skillMoveMult = 0;
      p.setAction('normal', 0);
      return false;
    }
    return true;
  }

  /** 찌르기 한 번: 가열 → 판정(몸 애니 없이 PLAYER_ATTACKED — 씬이 판정 모양으로 즉시) · 소리 */
  private stab(time: number): void {
    const p = this.p;
    const def = this.def;
    const res = p.resource;
    if (res?.kind === 'heat') res.heatBy(def.heatPerStab, time);
    p.gear.lastAttackAt = time;
    this.stabs += 1;
    const hit = def.hit;
    const payload: PlayerAttackPayload = {
      x: p.x,
      y: p.y,
      dirX: this.dir.x,
      dirY: this.dir.y,
      damageMult: hit.damageMult,
      sizeMult: hit.sizeMult,
      kind: 'attack',
      forceCrit: false,
      primed: false,
      swingDelayMs: 0,
      releaseDelayMs: 0,
      comboIndex: 0,
      comboCount: 1,
      activeMs: hit.activeMs,
      durationMs: hit.durationMs,
      bodyAction: this.action ?? 'attack',
      heavy: false,
      art: hit.art ?? def.art,
      move: 'flurry',
      ...(hit.hitShape ? { hitShape: hit.hitShape } : {}),
      ...(res?.kind === 'heat' ? { heatStage: res.stage } : {}),
    };
    EventBus.emit(Events.PLAYER_ATTACKED, payload);
    emitSkill('flurry', 'stab');
  }

  /** 끊김 (피격·워프·무기 교체) */
  cancel(): void {
    this.p.skillMoveMult = 0;
    this.p.visual.release();
    if (this.p.action === 'skill') this.p.setAction('normal', 0);
    this.phase = 'end';
    this.endAt = 0;
  }
}
