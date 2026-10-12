/**
 * 62 루프 2 시스템 E — 메뉴 입력 가드 (Phaser 없음).
 * 눈금 도달·보상 등으로 게임이 멈추고 메뉴가 뜨는 사이, 전투 중 누르던 좌클릭·숫자·Space·Enter 가 메뉴 선택으로 새지 않게:
 * 1. 메뉴가 열린 뒤 armMs 동안(그리고 UI 가 '실제로 그렸다'고 알려 오면 그때부터 다시 armMs) 선택 명령을 무시한다.
 * 2. 시스템 임시 텍스트 메뉴(UI 렌더러 없음)의 숫자 키는 자동 반복(repeat)과 '메뉴가 열릴 때 이미 누르고 있던 키'를 무시한다 —
 *    뗐다가 다시 누른 것만 선택.
 * 시계 = performance.now() (UI 와 같은 시계 — 계약 `UiMenu.openedAt`).
 */

export type Clock = () => number;

const perfNow: Clock = () => (typeof performance !== 'undefined' ? performance.now() : Date.now());

/** 디버그·내부 경로(갈 길이 하나뿐일 때 자동 고르기 등)가 가드를 건너뛰는 중 */
let bypassDepth = 0;

/** fn 안에서 일어나는 선택은 가드를 건너뛴다 (헤드리스 디버그 훅 · 시스템 내부 호출) */
export function withoutMenuGuard<T>(fn: () => T): T {
  bypassDepth++;
  try {
    return fn();
  } finally {
    bypassDepth--;
  }
}

export function menuGuardBypassed(): boolean {
  return bypassDepth > 0;
}

export class MenuGuard {
  /** 연 시각 (-Infinity = 열린 적 없음) */
  openedAt = -Infinity;
  /** UI 가 화면에 그린 시각 (없으면 -Infinity) */
  shownAt = -Infinity;
  /** 막은 선택 수 (디버그) */
  blocked = 0;

  constructor(
    readonly armMs: number,
    private readonly enabled = true,
    private readonly clock: Clock = perfNow,
  ) {}

  /** 메뉴를 새로 열었다 */
  arm(): number {
    this.openedAt = this.clock();
    this.shownAt = -Infinity;
    return this.openedAt;
  }

  /** UI 가 메뉴를 실제로 그렸다 (기다림·애니 뒤) — 그때부터 다시 armMs */
  shown(): void {
    if (this.openedAt === -Infinity) return;
    this.shownAt = this.clock();
  }

  /** 선택을 받기 시작하는 시각 */
  get readyAt(): number {
    return Math.max(this.openedAt, this.shownAt) + this.armMs;
  }

  /** 지금 선택을 받는가 (받지 않으면 blocked 를 센다) */
  accepts(): boolean {
    if (!this.enabled || menuGuardBypassed() || this.clock() >= this.readyAt) return true;
    this.blocked++;
    return false;
  }
}

/**
 * 메뉴가 열릴 때 누르고 있던 키 — 그 키는 뗐다가 다시 눌러야 선택으로 친다 (자동 반복도 무시).
 * `down` 은 지금 눌린 키(KeyboardEvent.code) 집합 — `KeyTracker` 가 채운다
 */
export class HeldKeyFilter {
  private readonly held: Set<string>;

  constructor(downAtOpen: Iterable<string>) {
    this.held = new Set(downAtOpen);
  }

  /** keydown 하나를 선택으로 받는가 */
  acceptDown(code: string, repeat: boolean): boolean {
    if (repeat) return false;
    return !this.held.has(code);
  }

  /** keyup — 열릴 때 누르던 키를 뗐다 */
  up(code: string): void {
    this.held.delete(code);
  }

  get size(): number {
    return this.held.size;
  }
}

/** 지금 눌린 키 (window keydown/keyup — 한 번만 단다). 창이 포커스를 잃으면 비운다 */
export class KeyTracker {
  readonly down = new Set<string>();
  private installed = false;

  install(target: Pick<Window, 'addEventListener'> | null = typeof window !== 'undefined' ? window : null): void {
    if (this.installed || !target) return;
    this.installed = true;
    target.addEventListener('keydown', (e) => this.down.add((e as KeyboardEvent).code), true);
    target.addEventListener('keyup', (e) => this.down.delete((e as KeyboardEvent).code), true);
    target.addEventListener('blur', () => this.down.clear());
  }
}

export const keyTracker = new KeyTracker();
