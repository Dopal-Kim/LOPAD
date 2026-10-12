/**
 * 62 루프 2 UI D — 원치 않는 선택 막기 (도영 님: '렉 걸려서 원하지 않은 개성 발현 눌려서 답답'). Phaser 없음 (단위 테스트).
 *
 * 선택 메뉴(성장·유품·보상·사연·장터·결산·노드 지도 …)가 화면에 그려진 순간부터 **무장 시간** 동안은 고르기 입력을 받지 않는다.
 *  1. 무장: 그려진 시각 + armMs(계약 `UiMenu.armMs` · `UiRoute.armMs`, 없으면 `CHOICE_GATE.armMs`) + 여유 전의 클릭·숫자·Enter·Space·
 *     그만두기 키는 버린다. 입력 시각은 처리 시각이 아니라 **이벤트 시각**(`timeStamp`)으로 본다 — 렉으로 늦게 처리된 키도 눌린 때로 판정.
 *  2. 연타 막기: 무장 중에 고르기 입력이 오면 무장 끝을 `입력 + quietMs` 까지 민다(최대 열린 뒤 `maxArmMs`) — 전투하던 손이
 *     계속 두드리는 동안엔 무장되지 않는다.
 *  3. 열기 전부터 눌려 있던 키·마우스 버튼은 한 번 뗀 뒤의 입력만 인정한다 (`held`).
 *  4. 좌클릭은 같은 카드 위에서 눌렀다 뗀 경우만 고른다 (누름은 무장 뒤·새로 누른 것이어야 한다) — 부르는 쪽이 `pressOk`/`releaseOk`.
 * 고름 자리 옮기기(←→·A·D·마우스 올림)는 막지 않는다 — 고르기만 막는다.
 */

/** 무장 수치 (ms) */
export const CHOICE_GATE = {
  /** 계약 armMs 가 없을 때 무장 시간 */
  armMs: 400,
  /** 시스템 가드(같은 시계)보다 늦게 풀리게 두는 여유 — 시스템이 버리는 선택을 UI 가 보내지 않게 */
  marginMs: 30,
  /** 무장 중 고르기 입력이 오면 그 뒤 이만큼 조용해야 무장된다 */
  quietMs: 220,
  /** 연타로 미는 무장 끝의 상한 (그려진 뒤) */
  maxArmMs: 1100,
} as const;

/** 열 때 눌려 있던 것 */
export interface HeldInput {
  keys: Iterable<string>;
  mouse: boolean;
}

/** 마우스 버튼의 이름 (뗀 시각 조회용) */
export const MOUSE = 'Mouse';

export interface GateOptions {
  /** 계약 armMs (없으면 기본) */
  armMs?: number;
  held?: HeldInput;
  /** 이 키(또는 `MOUSE`)를 마지막으로 뗀 시각 (모르면 -Infinity) — 열린 뒤 뗐으면 '눌려 있던 것'에서 뺀다 */
  lastUp?: (code: string) => number;
}

/** 계약 armMs → 쓸 값 (숫자가 아니거나 음수면 기본값) */
export function armMsOf(v: unknown): number {
  return typeof v === 'number' && Number.isFinite(v) && v >= 0 ? v : CHOICE_GATE.armMs;
}

export class ChoiceGate {
  readonly shownAt: number;
  readonly armMs: number;
  private armAt: number;
  private readonly armCap: number;
  private held: Set<string>;
  private mouseHeld: boolean;
  /** 무장 뒤 새로 누른 클릭이 있었나 (뗄 때 확인) */
  private pressed = false;
  private lastUp: (code: string) => number;

  constructor(shownAt: number, opts: GateOptions = {}) {
    this.shownAt = shownAt;
    this.armMs = armMsOf(opts.armMs);
    this.armAt = shownAt + this.armMs + CHOICE_GATE.marginMs;
    this.armCap = Math.max(this.armAt, shownAt + CHOICE_GATE.maxArmMs);
    this.held = new Set(opts.held?.keys ?? []);
    this.mouseHeld = Boolean(opts.held?.mouse);
    this.lastUp = opts.lastUp ?? (() => -Infinity);
  }

  /** 열 때 눌려 있던 키를 그 뒤 뗐으면 놓아준다 */
  private stillHeld(code: string): boolean {
    if (!this.held.has(code)) return false;
    if (this.lastUp(code) >= this.shownAt) {
      this.held.delete(code);
      return false;
    }
    return true;
  }

  /** 무장이 끝나는 시각 */
  get armedAt(): number {
    return this.armAt;
  }

  armed(now: number): boolean {
    return now >= this.armAt;
  }

  /** 무장 진행 0..1 (그림용) */
  progress(now: number): number {
    const span = this.armAt - this.shownAt;
    if (span <= 0) return 1;
    return Math.max(0, Math.min(1, (now - this.shownAt) / span));
  }

  /** 무장 중 고르기 입력: 무장 끝을 민다 */
  private bump(t: number): void {
    this.armAt = Math.min(this.armCap, Math.max(this.armAt, t + CHOICE_GATE.quietMs));
  }

  /**
   * 고르는 키(숫자·Enter·Space·그만두기·Esc)가 눌렸다 — 고르기를 받아도 되면 true.
   * `code` = 물리 키(`KeyboardEvent.code`), `t` = 이벤트 시각, `repeat` = 자동 반복
   */
  keyOk(code: string, t: number, repeat = false): boolean {
    if (repeat) return false;
    if (code && this.stillHeld(code)) return false;
    // 그리기 전에 눌린 키 (렉으로 늦게 처리된 것)
    if (t < this.shownAt) return false;
    if (!this.armed(t)) {
      this.bump(t);
      return false;
    }
    return true;
  }

  /** 키를 뗐다 (열기 전부터 눌려 있던 키는 이제 다시 누르면 인정) */
  keyUp(code: string): void {
    this.held.delete(code);
  }

  /** 마우스 버튼을 눌렀다 — 이 누름을 '고르기 누름'으로 셀 수 있으면 true (뗄 때 releaseOk 로 마무리) */
  pressOk(t: number): boolean {
    this.pressed = false;
    if (this.mouseHeld && this.lastUp(MOUSE) >= this.shownAt) this.mouseHeld = false;
    if (this.mouseHeld || t < this.shownAt) return false;
    if (!this.armed(t)) {
      this.bump(t);
      return false;
    }
    this.pressed = true;
    return true;
  }

  /** 마우스 버튼을 뗐다 — 무장 뒤 새로 누른 클릭을 떼는 것이면 true (같은 카드인지는 부르는 쪽이 본다) */
  releaseOk(): boolean {
    const ok = this.pressed;
    this.pressed = false;
    this.mouseHeld = false;
    return ok;
  }

  /** 어디서든 마우스 버튼을 뗐다 (열기 전부터 누르던 버튼이면 이제 다음 누름부터 인정) */
  pointerUp(): void {
    this.mouseHeld = false;
  }
}

/**
 * 62 루프 2 시스템 E (`UiSnapshot.door.phase`): 주인공이 문으로 걸어 나가는 중·문 안·걸어 들어오는 중 — 입력이 잠긴 때라
 * HUD 는 조작 안내·키 막대를 숨긴다 (closed·open·없음이면 false)
 */
export function doorWalking(phase: string | null | undefined): boolean {
  return phase === 'walkOut' || phase === 'inside' || phase === 'walkIn';
}
