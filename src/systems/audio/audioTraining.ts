/**
 * 61 단계 6 (P14 · 계약 sound §12) 음향 요청분 — 그림 속 입구 전환 · 수련장 (음향 제작 대기 id 는 없으면 무음).
 * 트리거 확정: `TRANSITION_BEGIN{mode}` (enterNode·training → transition_enter · exitRoom → transition_exit · floor → transition_floor),
 * `TRAINING_TASK{room,id}` → training_task · `TRAINING_STAMP{room,all}` → training_stamp. 수련장 BGM = 상태 'training' (`bgmByState.training`).
 * 62 H: mode 'fade'(지도에서 고른 뒤 짧은 암전 약 0.4초) → `transition_fade`(음향 요청 — 짧은 먹 번짐 0.4~0.6초), 없으면
 * transition_exit 를 작고 빠르게(FADE_FALLBACK — 소리 −6dB 쯤 · 재생 속도 1.2).
 */
import {
  Events,
  type TrainingStampPayload,
  type TrainingTaskPayload,
  type TransitionBeginPayload,
} from '../../core/EventBus';
import { t, type AudioTrigger } from './audioTrigger';

export const P14_SFX = {
  enter: 'sfx/transition_enter',
  exit: 'sfx/transition_exit',
  floor: 'sfx/transition_floor',
  task: 'sfx/training_task',
  stamp: 'sfx/training_stamp',
  /** 62 H 짧은 암전 (음향 제작 대기 — 없으면 exit 대체) */
  fade: 'sfx/transition_fade',
} as const;

/** 62 H: 'fade' 에 transition_exit 를 대신 쓸 때 — 음량 배율 · 재생 속도 (짧게) */
export const FADE_FALLBACK = { GAIN: 0.5, RATE: 1.2 } as const;

/** 수련장 BGM 상태 이름 (음향 manifest `bgmByState.training` = `bgm/training`) */
export const TRAINING_BGM_STATE = 'training';

const TRANSITION_SFX: Record<TransitionBeginPayload['mode'], readonly string[]> = {
  enterNode: [P14_SFX.enter],
  training: [P14_SFX.enter],
  exitRoom: [P14_SFX.exit],
  floor: [P14_SFX.floor, P14_SFX.enter],
  fade: [P14_SFX.fade, P14_SFX.exit],
};

/** 고른 효과음이 'fade' 의 exit 대체인가 */
const fadeFallback = (p: TransitionBeginPayload, id: string | undefined) => p.mode === 'fade' && id === P14_SFX.exit;

/**
 * 62 I (음향 manifest transition_fade 메모): 덮는 시간(durationMs)이 기준 400ms 에서 크게(±80ms 넘게) 다르면
 * 재생 속도 = clamp(380 / durationMs, 0.85, 1.2) — 먹이 다 덮이는 '툭'(380ms)을 덮임 순간에 맞춘다
 */
export const FADE_SYNC = { BASE_MS: 400, PEAK_MS: 380, TOLERANCE_MS: 80, MIN: 0.85, MAX: 1.2 } as const;

export function fadeRate(durationMs: number | undefined): number {
  const S = FADE_SYNC;
  if (!durationMs || durationMs <= 0 || Math.abs(durationMs - S.BASE_MS) <= S.TOLERANCE_MS) return 1;
  return Math.min(S.MAX, Math.max(S.MIN, S.PEAK_MS / durationMs));
}

export const TRAINING_AUDIO_TRIGGERS: readonly AudioTrigger[] = [
  t<TransitionBeginPayload>({
    event: Events.TRANSITION_BEGIN,
    note: '61 단계 6 그림 속 입구 전환 시작 → enterNode·training transition_enter · exitRoom transition_exit · floor transition_floor(없으면 enter) · 62 H fade transition_fade(없으면 exit 작고 빠르게)',
    sfx: (p) => TRANSITION_SFX[p.mode] ?? null,
    rate: (p, id) =>
      fadeFallback(p, id) ? FADE_FALLBACK.RATE : p.mode === 'fade' && id === P14_SFX.fade ? fadeRate(p.durationMs) : 1,
    gain: (p, id) => (fadeFallback(p, id) ? FADE_FALLBACK.GAIN : 1),
  }),
  t<TrainingTaskPayload>({
    event: Events.TRAINING_TASK,
    note: '61 단계 6 수련장 과제 완료 → training_task (짧은 맑은 종)',
    sfx: () => [P14_SFX.task],
  }),
  t<TrainingStampPayload>({
    event: Events.TRAINING_STAMP,
    note: '61 단계 6 수련장 방 도장 → training_stamp (인장 찍힘)',
    sfx: () => [P14_SFX.stamp],
  }),
];
