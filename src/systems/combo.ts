/**
 * 48라운드 Q2: 근접 연격 상태 머신. Phaser 의존 없음. (판정 모양 기하는 55라운드에 `hitShapes.ts` 로 분리)
 *
 * 흐름: 좌클릭 → `press(now)` 로 입력 버퍼에 넣는다 → 매 프레임 `poll(now, canAct)` 가 다음 타를 시작할 수 있으면
 * 타 번호(0부터)를 돌려준다. 다음 타는 직전 타 시작 + `cancelFromMs` 부터 허용(마지막 타는 + durationMs + finisherRecoverMs).
 * 직전 타가 끝나고(durationMs) `resetMs` 가 지나도록 다음 타가 없으면 1타로 돌아간다. 버퍼는 `bufferMs` 동안만 유효.
 * 55라운드 Q18 순환(`loop`): 마지막 타 다음도 회복 없이 1타로 이어진다(대검 H1→V→H2→V→H1…).
 * 막타(`heavy`, 없으면 순환이 아닌 연격의 마지막 타)는 기력이 바닥나면 1타로 바뀐다.
 */
import type { ComboDef, ComboHitDef } from '../data/types';

export class ComboTracker {
  /** 마지막으로 시작한 타 번호 (-1 = 아직 없음) */
  private index = -1;
  private startedAt = -Infinity;
  private bufferedAt = -Infinity;
  /** 이번 타의 다음 타 허용 시각 덮어쓰기 (아트 JSON cancelFromFrame, 이 타 시작부터 ms) */
  private cancelOverride: number | null = null;
  /** 49라운드: 공격 속도 배율 (단검 과열 단계). 타 시작 시점의 값을 그 타에 고정한다 */
  private speed = 1;
  private hitSpeed = 1;

  constructor(private readonly def: ComboDef) {}

  get hits(): readonly ComboHitDef[] {
    return this.def.hits;
  }

  /** 마지막으로 시작한 타 (디버그) */
  get lastIndex(): number {
    return this.index;
  }

  get lastStartedAt(): number {
    return this.startedAt;
  }

  /** 버퍼에 입력이 남아 있는지 */
  buffered(now: number): boolean {
    return now - this.bufferedAt <= this.def.bufferMs;
  }

  press(now: number): void {
    this.bufferedAt = now;
  }

  /** 55라운드 Q22: 누름을 차지가 가져갔으면 연격 버퍼를 비운다 */
  clearBuffer(): void {
    this.bufferedAt = -Infinity;
  }

  /** 49라운드: 다음 타부터 적용할 공격 속도 배율 (1 = 데이터 그대로, 1.3 = 30% 빠름) */
  setSpeed(mult: number): void {
    this.speed = mult > 0 ? mult : 1;
  }

  /** 지금 시작한 타의 속도 배율 (애니·판정 시간을 이 값으로 나눈다) */
  get currentSpeed(): number {
    return this.hitSpeed;
  }

  /** 타 길이 ms (속도 배율 반영) */
  durationOf(index: number): number {
    return this.def.hits[index].durationMs / this.hitSpeed;
  }

  /** 55라운드: 순환 연격 (마지막 타 뒤 회복 없음) */
  get loops(): boolean {
    return Boolean(this.def.loop);
  }

  /** 55라운드: 막타인가 (데이터 heavy, 없으면 순환이 아닌 연격의 마지막 타) */
  isHeavy(index: number): boolean {
    const h = this.def.hits[index];
    if (!h) return false;
    return h.heavy ?? (!this.def.loop && index === this.def.hits.length - 1);
  }

  /** 마지막 타 뒤 회복이 있는 마무리인가 (순환 연격은 없음) */
  private isClosing(index: number): boolean {
    return !this.def.loop && index >= this.def.hits.length - 1;
  }

  /** 다음 타를 시작할 수 있는 시각 */
  readyAt(): number {
    if (this.index < 0) return -Infinity;
    const h = this.def.hits[this.index];
    const k = this.hitSpeed;
    if (this.isClosing(this.index)) return this.startedAt + h.durationMs / k + this.def.finisherRecoverMs / k;
    return this.startedAt + (this.cancelOverride ?? h.cancelFromMs / k);
  }

  /** 지금 시작하면 몇 번째 타인가 (리셋 시간이 지났거나 마지막 타 뒤면 0, 순환이면 마지막 다음 = 0 으로 이어짐) */
  nextIndex(now: number): number {
    if (this.index < 0 || this.isClosing(this.index)) return 0;
    const h = this.def.hits[this.index];
    if (now > this.startedAt + h.durationMs / this.hitSpeed + this.def.resetMs) return 0;
    return (this.index + 1) % this.def.hits.length;
  }

  /**
   * 버퍼에 입력이 있고 시작 가능하면 타 번호를 돌려주고 시작 처리. 아니면 null (버퍼는 유효 시간 동안 유지).
   * 49라운드: allowHeavy 가 false(기력 바닥)면 막타 대신 1타로 돌아간다
   */
  poll(now: number, canAct: boolean, allowHeavy = true): number | null {
    if (!this.buffered(now) || !canAct) return null;
    if (now < this.readyAt()) return null;
    let next = this.nextIndex(now);
    if (!allowHeavy && this.isHeavy(next)) next = 0;
    this.index = next;
    this.startedAt = now;
    this.bufferedAt = -Infinity;
    this.cancelOverride = null;
    this.hitSpeed = this.speed;
    return next;
  }

  /** 방금 시작한 타의 다음 타 허용 시각을 바꾼다 (시트 cancelFromFrame 시작 ms, 이 타 길이 안으로 자름) */
  overrideCancel(ms: number): void {
    if (this.index < 0) return;
    this.cancelOverride = Math.max(0, Math.min(ms, this.def.hits[this.index].durationMs / this.hitSpeed));
  }

  /** 대쉬·피격 사망 등으로 연격을 끊는다 (버퍼도 비운다) */
  reset(): void {
    this.cancelOverride = null;
    this.hitSpeed = this.speed;
    this.index = -1;
    this.startedAt = -Infinity;
    this.bufferedAt = -Infinity;
  }
}
