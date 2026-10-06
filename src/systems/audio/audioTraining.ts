/**
 * 61 단계 6 (P14 · 계약 sound §12) 음향 요청분 — 그림 속 입구 전환 · 수련장 (음향 제작 대기 id 는 없으면 무음).
 * 트리거 확정: `TRANSITION_BEGIN{mode}` (enterNode·training → transition_enter · exitRoom → transition_exit · floor → transition_floor),
 * `TRAINING_TASK{room,id}` → training_task · `TRAINING_STAMP{room,all}` → training_stamp. 수련장 BGM = 상태 'training' (`bgmByState.training`).
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
} as const;

/** 수련장 BGM 상태 이름 (음향 manifest `bgmByState.training` = `bgm/training`) */
export const TRAINING_BGM_STATE = 'training';

const TRANSITION_SFX: Record<TransitionBeginPayload['mode'], readonly string[]> = {
  enterNode: [P14_SFX.enter],
  training: [P14_SFX.enter],
  exitRoom: [P14_SFX.exit],
  floor: [P14_SFX.floor, P14_SFX.enter],
};

export const TRAINING_AUDIO_TRIGGERS: readonly AudioTrigger[] = [
  t<TransitionBeginPayload>({
    event: Events.TRANSITION_BEGIN,
    note: '61 단계 6 그림 속 입구 전환 시작 → enterNode·training transition_enter · exitRoom transition_exit · floor transition_floor(없으면 enter)',
    sfx: (p) => TRANSITION_SFX[p.mode] ?? null,
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
