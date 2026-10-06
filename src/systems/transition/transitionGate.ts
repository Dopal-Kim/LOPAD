/**
 * 61 단계 6 (P14 §3, 계약 UI §19) 그림 속 입구 전환 문지기 — 씬 재시작을 넘어 살아 있는 하나의 상태 (Phaser 의존 없음).
 *
 * 순서: begin → `ui:transition-begin` (UI 가 덮기 시작) → UI `ui:transition-covered {id}` → onCovered(장면 교체 — 씬 재시작·지도 열기)
 * → 새 장면이 준비되면 ready() → `ui:transition-ready {id}` (UI 가 걷어냄) → UI `ui:transition-end {id}` → 입력 재개.
 * 안전장치: COVERED 가 COVER_TIMEOUT 안에 없으면 스스로 덮인 것으로 · READY 뒤 END 가 END_TIMEOUT 안에 없으면 스스로 끝.
 * UI 렌더러가 없으면(헤드리스·UI 미등록) 대체 덮기(fallback — 카메라 암전 등)를 쓰거나 바로 진행한다.
 * 진행 중에는 locked = true (Game 이 입력을 잠근다).
 */
import type { UiTransitionBegin, UiTransitionMode } from '../../contract/ui';

export const TRANSITION_TIMING = {
  /** UI 가 덮었다고 알리지 않을 때 스스로 진행 (계약 §19 안전장치 3초) */
  COVER_TIMEOUT_MS: 3000,
  /** READY 뒤 UI 가 END 를 주지 않을 때 스스로 입력 재개 */
  END_TIMEOUT_MS: 3000,
  /** 덮인 뒤 새 장면이 ready() 를 부르지 못했을 때(씬 오류 등) 스스로 READY — 검은 화면에 멈추지 않게 */
  READY_TIMEOUT_MS: 5000,
} as const;

export type TransitionPhase = 'covering' | 'covered' | 'revealing';

export interface TransitionDeps {
  /** UI 로 (uiBus) */
  emitUi(event: string, payload: unknown): void;
  /** 시스템 내부 (EventBus — 음향 TRANSITION_BEGIN{mode}) */
  emitInternal(payload: { id: number; mode: UiTransitionMode; region: string; nodeKind?: string }): void;
  rendererRegistered(): boolean;
  setTimer(ms: number, fn: () => void): unknown;
  clearTimer(handle: unknown): void;
}

export const TRANSITION_UI = {
  BEGIN: 'ui:transition-begin',
  COVERED: 'ui:transition-covered',
  READY: 'ui:transition-ready',
  END: 'ui:transition-end',
} as const;

interface Current {
  id: number;
  mode: UiTransitionMode;
  phase: TransitionPhase;
  onCovered: () => void;
  timer: unknown;
  /** UI 없이 진행 (대체 덮기) — ready 는 바로 끝 */
  noUi: boolean;
  /** 디버그: 안전장치로 넘어간 단계 */
  timedOut: string[];
}

export class TransitionGate {
  private seq = 0;
  private cur: Current | null = null;
  private deps: TransitionDeps | null = null;
  /** 디버그: 최근 전환 기록 */
  readonly log: { id: number; mode: UiTransitionMode; ev: string; info?: Record<string, unknown> }[] = [];

  attach(deps: TransitionDeps): void {
    this.deps = deps;
  }

  get locked(): boolean {
    return this.cur !== null;
  }

  get phase(): TransitionPhase | null {
    return this.cur?.phase ?? null;
  }

  get id(): number | null {
    return this.cur?.id ?? null;
  }

  /**
   * 전환 시작. 진행 중이면 거부(false). fallbackCover = UI 가 없을 때의 대체 덮기(끝나면 go 호출) — 없으면 바로 onCovered
   */
  begin(
    info: Omit<UiTransitionBegin, 'id' | 'skippable'> & { skippable?: boolean },
    onCovered: () => void,
    fallbackCover?: (go: () => void) => void,
  ): boolean {
    const d = this.deps;
    if (!d || this.cur) return false;
    const id = ++this.seq;
    const noUi = !d.rendererRegistered();
    const cur: Current = { id, mode: info.mode, phase: 'covering', onCovered, timer: null, noUi, timedOut: [] };
    this.cur = cur;
    const payload: UiTransitionBegin = { ...info, id, skippable: info.skippable ?? true };
    this.note(id, info.mode, 'begin', {
      region: info.region,
      nodeKind: info.nodeKind,
      doorKey: info.doorKey,
      from: info.from,
      nodeId: info.nodeId,
    });
    d.emitInternal({
      id,
      mode: info.mode,
      region: info.region,
      ...(info.nodeKind ? { nodeKind: info.nodeKind } : {}),
    });
    d.emitUi(TRANSITION_UI.BEGIN, payload);
    if (noUi) {
      if (fallbackCover) fallbackCover(() => this.cover(id));
      else this.cover(id);
      return true;
    }
    cur.timer = d.setTimer(TRANSITION_TIMING.COVER_TIMEOUT_MS, () => {
      cur.timedOut.push('covered');
      this.cover(id);
    });
    return true;
  }

  /** UI → 시스템: 다 덮임 */
  onUiCovered(p: { id?: number } | undefined): void {
    if (this.cur && p?.id === this.cur.id) this.cover(this.cur.id);
  }

  /**
   * 새 장면 준비됨 (덮인 상태에서만). UI 가 걷어낼 차례면 true — 호출한 쪽은 자기 밝아짐(카메라 fadeIn)을 생략한다.
   * UI 없이 진행 중이었으면 바로 끝내고 false
   */
  ready(): boolean {
    const c = this.cur;
    const d = this.deps;
    if (!c || !d || c.phase !== 'covered') return false;
    if (c.timer !== null) d.clearTimer(c.timer);
    c.timer = null;
    if (c.noUi) {
      this.note(c.id, c.mode, 'ready');
      this.finish(c.id);
      return false;
    }
    c.phase = 'revealing';
    this.note(c.id, c.mode, 'ready');
    d.emitUi(TRANSITION_UI.READY, { id: c.id });
    c.timer = d.setTimer(TRANSITION_TIMING.END_TIMEOUT_MS, () => {
      c.timedOut.push('end');
      this.finish(c.id);
    });
    return true;
  }

  /** UI → 시스템: 끝 (입력 재개) */
  onUiEnd(p: { id?: number } | undefined): void {
    if (this.cur && p?.id === this.cur.id && this.cur.phase === 'revealing') this.finish(this.cur.id);
  }

  /** 씬 정리·타이틀 등으로 전환을 버린다 — 덮인 화면이 남지 않게 READY 를 보내고 끝 */
  cancel(): void {
    const c = this.cur;
    if (!c || !this.deps) return;
    if (!c.noUi && c.phase !== 'revealing') this.deps.emitUi(TRANSITION_UI.READY, { id: c.id });
    this.note(c.id, c.mode, 'cancel');
    this.finish(c.id);
  }

  debug(): Record<string, unknown> {
    const c = this.cur;
    return {
      current: c ? { id: c.id, mode: c.mode, phase: c.phase, noUi: c.noUi, timedOut: [...c.timedOut] } : null,
      log: this.log.slice(-12),
    };
  }

  private cover(id: number): void {
    const c = this.cur;
    if (!c || c.id !== id || c.phase !== 'covering') return;
    if (c.timer !== null) this.deps?.clearTimer(c.timer);
    c.timer = null;
    c.phase = 'covered';
    this.note(id, c.mode, 'covered');
    c.timer = this.deps?.setTimer(TRANSITION_TIMING.READY_TIMEOUT_MS, () => {
      c.timedOut.push('ready');
      this.ready();
    });
    c.onCovered();
  }

  private finish(id: number): void {
    const c = this.cur;
    if (!c || c.id !== id) return;
    if (c.timer !== null) this.deps?.clearTimer(c.timer);
    this.note(id, c.mode, 'end');
    this.cur = null;
  }

  private note(id: number, mode: UiTransitionMode, ev: string, info?: Record<string, unknown>): void {
    this.log.push({ id, mode, ev, ...(info ? { info } : {}) });
    if (this.log.length > 40) this.log.shift();
  }
}

/** 게임 전체에 하나 (contract/host 가 attach) */
export const transitionGate = new TransitionGate();
