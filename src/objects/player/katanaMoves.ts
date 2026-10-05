/**
 * 칼 동작 (56라운드 2단계 Q40·Q53·Q55·Q60, 계약 art §18.7 → 61라운드 P1 4동사):
 * - 간파 반격 `katana_counter` — 패링 성공 직후 창 안 좌클릭: 조준 방향의 해부 왼쪽(화면 반시계 90°)으로 비켜서며 비대칭 호 반격
 * - 발도 `katana_iai` (옛 '대치 일격' + F 넣기 상태) — **좌 홀드**: 누름이 holdMs 를 넘으면 칼집에 손을 얹는 자세(들어감 1회 →
 *   유지 루프), 떼는 순간 발도 일격(언제 떼도 같은 일격). 검기를 전부 소모해 단마다 피해 +, critAtStages 이상이면 확정 치명
 *   (옛 '넣은 채 첫 타 = 발도 치명'을 흡수). 판정·끝은 뗀 시각 기준, 반짝임·납도 딸깍 터짐은 연출만, 칼집에 넣은 채 끝
 */
import { gameState } from '../../core/GameState';
import type { CounterMoveDef, IaiMoveDef } from '../../data/types';
import type { InputState } from '../../systems/InputSystem';
import { artCandidates, pickArt } from '../../systems/weapon/comboArt';
import { artScale, facingOf, frameDurations, type Facing } from '../../systems/sprites/spriteDefs';
import type { Player } from '../Player';
import { emitPlayerAttack } from './attackEmit';
import type { ComboStrike } from './heavyMoves';
import { addTravel, aimDir, emitHoldVerb, emitSkill, fireMoveStrike } from './moveStrike';

/** 간파 반격 시작. 반환 = 동작 길이 ms */
export function startCounter(p: Player, input: InputState, time: number, def: CounterMoveDef, moving: boolean): number {
  const a = aimDir(p, input);
  emitSkill('counter', 'start');
  const { total } = fireMoveStrike(p, input, time, def, { move: 'counter', moving });
  // Q55: 비켜섬 = 조준 방향의 해부 왼쪽 (화면 반시계 90° — (x, y) → (y, −x))
  addTravel(p, a.y, -a.x, def.sidestep, time);
  return total;
}

/** 몸 동작 `<무기>_<그림 키의 로드된 첫 후보>` (없으면 null) */
function moveBodyAction(p: Player, art: string): string | null {
  const id = gameState.weapon.id;
  const name = pickArt(artCandidates(gameState.weapon.def.combo, art, 'body'), (n) => p.visual.hasAction(`${id}_${n}`));
  return name ? `${id}_${name}` : null;
}

/** 열 목록 (시트 메모가 배열이면 그것, 아니면 fallback) */
function cols(v: unknown, fallback: number[]): number[] {
  return Array.isArray(v) && v.length > 0 && v.every((n) => typeof n === 'number') ? (v as number[]) : fallback;
}

/**
 * 대치 일격 유지 (눌러 있는 동안). update 가 false 를 돌려주면 끝(떼서 발도했거나 끊김) — BasicMoves 가 비운다
 */
export class IaiHold {
  readonly startedAt: number;
  private readonly dir: Facing;
  private readonly action: string | null;
  private looping = false;
  private readyShown = false;
  released = false;

  constructor(
    private readonly p: Player,
    private readonly def: IaiMoveDef,
    input: InputState,
    time: number,
  ) {
    this.startedAt = time;
    const a = aimDir(p, input);
    this.dir = facingOf(a.x, a.y, p.visual.facing);
    this.action = moveBodyAction(p, def.art);
    p.combo?.reset();
    p.clearLunges();
    // 칼집에 손을 얹은 자세 = 넣은 상태 (발도 뒤에도 넣은 채 — 다음 공격이 다시 뽑는다)
    p.gear.sheatheQuiet();
    // 들어감 열 1회 (시트 holdFrames 앞 열) → 다음 프레임부터 유지 루프
    const sheet = this.action ? p.visual.sheet(this.action) : undefined;
    const hold = cols(sheet?.holdFrames ?? sheet?.loopFrames, []);
    const enter = hold.length > 0 ? Array.from({ length: Math.min(...hold) }, (_, i) => i) : [];
    if (this.action && enter.length > 0) p.visual.playFrames(this.action, this.dir, enter, time);
    else this.looping = true;
    p.setAction('skill', 0);
    emitSkill('iai', 'hold');
  }

  /** 매 프레임 (눌러 있는 동안 유지 루프 · 0.5초 반짝임 · 떼면 발도). 계속이면 true */
  update(input: InputState, time: number, moving: boolean): boolean {
    const p = this.p;
    if (!input.attackHeld) {
      this.release(input, time, moving);
      return false;
    }
    const sheet = this.action ? p.visual.sheet(this.action) : undefined;
    if (!this.looping && !p.visual.isBusy(time) && this.action && sheet) {
      const loop = cols(sheet.loopFrames ?? sheet.holdFrames, []);
      if (loop.length > 0) p.visual.loopFrames(this.action, this.dir, loop, frameDurations(sheet)[loop[0]] ?? 120);
      this.looping = true;
    }
    // Q60: 유지 0.5초 반짝임 — 연출만 (칼집 입구 koiguchiAnchors)
    if (!this.readyShown && time - this.startedAt >= this.def.readyAfterHoldMs) {
      this.readyShown = true;
      emitSkill('iai', 'ready', { at: this.koiguchi() });
    }
    return true;
  }

  /** 칼집 입구 (월드) — 몸 시트 koiguchiAnchors[방향][지금 열], 없으면 발 위 */
  private koiguchi(): { x: number; y: number } {
    const p = this.p;
    const sheet = this.action ? p.visual.sheet(this.action) : undefined;
    const anchors = (sheet as { koiguchiAnchors?: Record<string, [number, number][]> } | undefined)?.koiguchiAnchors;
    const cur = p.anims.currentFrame;
    const col = sheet && cur ? Number(cur.frame.name) % sheet.frames : 0;
    const pt = anchors?.[this.dir]?.[col] ?? anchors?.[this.dir]?.[0];
    if (!sheet || !pt) return { x: p.x, y: p.y };
    const k = artScale(sheet) * p.visual.drawScale;
    return { x: p.x + (pt[0] - sheet.pivot.x) * k, y: p.y + (pt[1] - sheet.pivot.y) * k };
  }

  /** 끊김 (피격·워프·무기 교체) — 발도하지 않고 칼집 상태로 */
  cancel(): void {
    if (this.released) return;
    this.released = true;
    this.p.visual.release();
    emitSkill('iai', 'cancel');
    if (this.p.action === 'skill') this.p.setAction('normal', 0);
  }

  /** 뗌: releaseFrame 부터 끝까지 제 시간 재생, 판정 = 뗀 뒤 release.hitMs (언제 떼도 같은 일격 — Q53). 검기 전부 소모 */
  private release(input: InputState, time: number, moving: boolean): void {
    if (this.released) return;
    this.released = true;
    const p = this.p;
    const def = this.def;
    const res = p.resource;
    if (res?.def.kind === 'stamina' && def.staminaCost) res.spend(def.staminaCost, time);
    const sheet = this.action ? p.visual.sheet(this.action) : undefined;
    const rf = typeof sheet?.releaseFrame === 'number' ? sheet.releaseFrame : null;
    const frames = sheet && rf !== null ? Array.from({ length: sheet.frames - rf }, (_, i) => rf + i) : undefined;
    const R = def.release;
    // 뗀 뒤 시간표가 곧 이 타 (판정 = hitMs, 끝 = totalMs) — 시트가 없으면 같은 값으로 한 번 재생
    const hit = { ...def.hit, durationMs: R.totalMs, hitAtMs: R.hitMs, cancelFromMs: R.totalMs, activeMs: R.activeMs };
    // 61라운드: 검기 전부 소모 → 피해 배율 · 확정 치명 · (명경) 분신 잔상 베기
    const kenki = p.gauges.consumeKenki();
    const clones = p.gauges.meikyoClones(kenki.stages);
    const strike: ComboStrike = {
      index: 0,
      count: 1,
      hit,
      durationMs: R.totalMs,
      heavy: hit.heavy ?? true,
      ...(clones.length > 0 ? { extraFollowUps: clones } : {}),
    };
    const m = p.strikeMods(time, false);
    p.visual.release();
    emitSkill('iai', 'release', { kenkiStage: kenki.stages });
    emitHoldVerb('iai_draw');
    const payload = emitPlayerAttack(
      p,
      input,
      time,
      {
        kind: 'attack',
        damageMult: hit.damageMult * m.mult * kenki.damageMult,
        sizeMult: hit.sizeMult,
        forceCrit: m.forceCrit || kenki.crit,
        primed: m.primed,
      },
      strike,
      { move: 'iai_draw', kenkiStage: kenki.stages },
      frames,
    );
    // Q55: 칼집에 넣은 채 끝 (뽑은 상태로 바꾸지 않는다)
    p.gear.lastAttackAt = time;
    const total = Math.max(R.totalMs, p.visual.lastDurationMs);
    p.setAction('skill', time + total);
    p.slowUntil(time + total);
    // 내딛기: 방향키를 누를 때만 (몸 시트 stepPx.frames — 뗀 뒤 시간표의 같은 열)
    const step = hit.step;
    if (step && step.px > 0 && moving) {
      const sf = sheet?.stepPx?.frames;
      const a = Array.isArray(sf) && sf.length > 0 ? Math.min(...sf) : null;
      const b = Array.isArray(sf) && sf.length > 0 ? Math.max(...sf) : null;
      const st = p.visual.lastFrameStarts;
      const from = a !== null ? (st[a] ?? 0) : 0;
      const to = b !== null ? (st[b + 1] ?? from + step.ms) : step.ms;
      addTravel(p, payload.dirX, payload.dirY, { px: step.px, fromMs: from, ms: Math.max(1, to - from) }, time);
    }
  }
}
