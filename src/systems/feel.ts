/**
 * 피격 피드백 "감각" 계층 (35라운드 1단계): 히트스톱·화면 흔들림·넉백 수식. Phaser 의존 없음(테스트 가능).
 * - 수치는 core/Constants `FEEL`, 강도 배율은 `feelSettings`(런타임, 디버그 `__lopad.setFeel` — 접근성 대비 0 으로 끌 수 있다).
 * - 시간은 씬 시계(`scene.time.now`) ms 를 그대로 받는다. 히트스톱 중에도 시계는 흐르므로 지속 시간은 실시간 기준.
 */
import { FEEL } from '../core/Constants';

export interface FeelSettings {
  /** 흔들림 진폭 배율 (0 = 끔) */
  shake: number;
  /** 히트스톱 길이 배율 (0 = 끔) */
  hitstop: number;
  /** 넉백 거리 배율 (0 = 끔) */
  knockback: number;
  /** 데미지 숫자 표시 */
  numbers: boolean;
  /** 잔상 궤적 리본 (42라운드) */
  trail: boolean;
  /** 화면 섬광·색 오버레이·채도 감소 (42라운드) */
  flash: boolean;
  /** 54라운드 Q7: 화면 기울기 배율 (보스 '세상이 돈다' 카메라 기울기·가장자리 흐림, 0 = 끔 — 흔들림 끄기와 같은 방식) */
  tilt: number;
}

export const DEFAULT_FEEL: FeelSettings = {
  shake: 1,
  hitstop: 1,
  knockback: 1,
  numbers: true,
  trail: true,
  flash: true,
  tilt: 1,
};

/** 게임 수명 동안 하나. 씬 재시작과 무관하게 유지 (저장은 하지 않음 — 설정 UI 는 추후 계약) */
export const feelSettings: FeelSettings = { ...DEFAULT_FEEL };

export function setFeel(patch: Partial<FeelSettings>): FeelSettings {
  if (typeof patch.shake === 'number' && patch.shake >= 0) feelSettings.shake = patch.shake;
  if (typeof patch.hitstop === 'number' && patch.hitstop >= 0) feelSettings.hitstop = patch.hitstop;
  if (typeof patch.knockback === 'number' && patch.knockback >= 0) feelSettings.knockback = patch.knockback;
  if (typeof patch.numbers === 'boolean') feelSettings.numbers = patch.numbers;
  if (typeof patch.trail === 'boolean') feelSettings.trail = patch.trail;
  if (typeof patch.flash === 'boolean') feelSettings.flash = patch.flash;
  if (typeof patch.tilt === 'number' && patch.tilt >= 0) feelSettings.tilt = patch.tilt;
  return { ...feelSettings };
}

/**
 * 히트스톱: 요청(`request`)이 들어오면 `until` 까지 정지. 마지막 시작 뒤 `MIN_GAP_MS` 안의 요청은 무시(연타 중첩 금지).
 * 더 긴 요청이 들어와 간격을 넘겼으면 종료 시각을 늘린다.
 */
export class HitStop {
  private until = -Infinity;
  private lastStartAt = -Infinity;
  /** 디버그: 시작 횟수 */
  count = 0;

  request(now: number, ms: number): boolean {
    const scaled = ms * feelSettings.hitstop;
    if (scaled <= 0) return false;
    if (now - this.lastStartAt < FEEL.HITSTOP.MIN_GAP_MS) return false;
    this.lastStartAt = now;
    this.until = Math.max(this.until, now + scaled);
    this.count += 1;
    return true;
  }

  active(now: number): boolean {
    return now < this.until;
  }

  /** 남은 ms (디버그) */
  remaining(now: number): number {
    return Math.max(0, this.until - now);
  }

  reset(): void {
    this.until = -Infinity;
    this.lastStartAt = -Infinity;
  }
}

interface ShakeEntry {
  px: number;
  start: number;
  until: number;
}

/**
 * 화면 흔들림: 활성 항목 중 가장 큰 "진폭 × 남은 비율" 을 현재 진폭으로 쓰고, 매 프레임 무작위 방향 정수 오프셋을 낸다.
 * 카메라는 스크롤 반올림 뒤에 이 오프셋을 더한다(추종 보간과 섞이지 않음).
 */
export class Shake {
  private entries: ShakeEntry[] = [];
  /** 마지막으로 낸 오프셋 (디버그) */
  readonly offset = { x: 0, y: 0 };
  /** 디버그: 요청 횟수·마지막 요청 */
  count = 0;
  last: { px: number; ms: number; at: number } | null = null;

  constructor(private readonly random: () => number = Math.random) {}

  add(now: number, px: number, ms: number): void {
    const amp = px * feelSettings.shake;
    if (amp <= 0 || ms <= 0) return;
    this.entries.push({ px: amp, start: now, until: now + ms });
    this.count += 1;
    this.last = { px, ms, at: now };
  }

  /** 현재 진폭 px (감쇠 적용, 0 이면 흔들림 없음) */
  amplitude(now: number): number {
    let amp = 0;
    this.entries = this.entries.filter((e) => now < e.until);
    for (const e of this.entries) {
      const t = (now - e.start) / (e.until - e.start);
      amp = Math.max(amp, e.px * (1 - t));
    }
    return amp;
  }

  /** 이번 프레임 오프셋 (정수). 진폭이 0.5 미만이면 0 */
  sample(now: number): { x: number; y: number } {
    const amp = this.amplitude(now);
    if (amp < 0.5) {
      this.offset.x = 0;
      this.offset.y = 0;
      return this.offset;
    }
    const a = this.random() * Math.PI * 2;
    this.offset.x = Math.round(Math.cos(a) * amp);
    this.offset.y = Math.round(Math.sin(a) * amp);
    return this.offset;
  }

  get activeCount(): number {
    return this.entries.length;
  }

  reset(): void {
    this.entries = [];
    this.offset.x = 0;
    this.offset.y = 0;
  }
}

/**
 * 넉백 초속: 선형 감쇠로 `ms` 동안 `distPx` 만큼 이동하는 속도(px/s). 거리는 ∫v0(1-t/T)dt = v0·T/2 → v0 = 2·d/T.
 * 배율 `feelSettings.knockback` 적용. 0 이면 0
 */
export function knockSpeed(distPx: number, ms: number): number {
  const d = distPx * feelSettings.knockback;
  if (d <= 0 || ms <= 0) return 0;
  return (2 * d) / (ms / 1000);
}

/** 선형 감쇠 비율: elapsed/ms → 1..0 (끝나면 0) */
export function knockFactor(elapsedMs: number, ms: number): number {
  if (ms <= 0) return 0;
  return Math.max(0, 1 - elapsedMs / ms);
}
